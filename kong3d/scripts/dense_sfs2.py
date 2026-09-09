"""Dense SfS v2 (a_4257): infer THROUGH speculars, not just mask.
 (1) normal inpainting: fill masked specular holes by harmonic/Poisson interpolation of
     surrounding valid normals (smooth car surface = well-posed boundary fill).
 (2) highlight-as-curvature cue: a specular streak's elongation encodes curvature —
     thin/long = low curvature along its axis; tight/round = high curvature. add as prior.
Validate RMSE vs GLB hood GT, compare to 0.41 baseline.

usage: python3 dense_sfs2.py <ref.jpg> <out_prefix> [x0 y0 x1 y1]
"""
import sys, json
import numpy as np
from PIL import Image

path, prefix = sys.argv[1], sys.argv[2]
hx0, hy0, hx1, hy1 = (float(a) for a in (sys.argv[3:7] if len(sys.argv) >= 7
                                         else (0.22, 0.55, 0.80, 0.75)))
im = Image.open(path).convert("RGB")
W, H = im.size
crop = im.crop((int(hx0*W), int(hy0*H), int(hx1*W), int(hy1*H)))
cw, ch = crop.size
rgb = np.asarray(crop, float) / 255.0
lum = rgb @ [0.299, 0.587, 0.114]

mx = rgb.max(2); mn = rgb.min(2); sat = (mx-mn)/(mx+1e-6)
bright = lum > 0.90
colored = sat > 0.22
mask_bad = bright | colored

# ---------- (1) normal inpainting via harmonic (Laplace) solve ----------
gy, gx = np.gradient(lum)
s = 0.15
nx0, ny0, nz0 = -gx, -gy, np.full_like(lum, s)
def harmonic_inpaint(field, bad, iters=400):
    a = field.copy()
    valid = ~bad
    a[bad] = np.mean(field[valid]) if valid.any() else 0.0
    for _ in range(iters):
        up=np.roll(a,1,0); dn=np.roll(a,-1,0); lf=np.roll(a,1,1); rt=np.roll(a,-1,1)
        lap=(up+dn+lf+rt)/4.0
        a[bad]=lap[bad]              # Dirichlet on valid, harmonic in holes
    return a
nx = harmonic_inpaint(nx0, mask_bad)
ny = harmonic_inpaint(ny0, mask_bad)
nz = np.full_like(lum, s)

# ---------- (2) highlight-curvature cue ----------
# find specular blobs, measure elongation (eigenratio of blob covariance) -> curvature prior.
from collections import deque
def blobs(mask):
    seen=np.zeros_like(mask,bool); out=[]
    ys,xs=np.where(mask)
    idx={}
    for y,x in zip(ys,xs): idx[(y,x)]=True
    for y,x in zip(ys,xs):
        if seen[y,x]: continue
        q=deque([(y,x)]); seen[y,x]=True; comp=[]
        while q:
            cy,cx=q.popleft(); comp.append((cy,cx))
            for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                ny_,nx_=cy+dy,cx+dx
                if 0<=ny_<ch and 0<=nx_<cw and mask[ny_,nx_] and not seen[ny_,nx_]:
                    seen[ny_,nx_]=True; q.append((ny_,nx_))
        if len(comp)>30: out.append(np.array(comp))
    return out
cue = 0.0; ncue = 0
for c in blobs(bright):
    p = c - c.mean(0)
    if len(p) < 5: continue
    cov = np.cov(p.T)
    ev = np.linalg.eigvalsh(cov)
    if ev[0] < 1e-6: continue
    elong = ev[1]/ev[0]          # >1 elongated=low curvature; ~1 round=high curvature
    cue += 1.0/elong; ncue += 1  # avg local curvature proxy
cue = cue/ncue if ncue else 0.0

# ---------- integrate (Frankot-Chellappa) ----------
p = -nx/(nz+1e-6); q = -ny/(nz+1e-6)
fy=np.fft.fftfreq(ch)[:,None]; fx=np.fft.fftfreq(cw)[None,:]
den=(2j*np.pi*fx)**2+(2j*np.pi*fy)**2; den[0,0]=1
Z=np.fft.ifft2((np.fft.fft2(p)*(2j*np.pi*fx)+np.fft.fft2(q)*(2j*np.pi*fy))/den).real
Z-=Z.min(); Zm=Z/(Z.max()+1e-6)*0.12

# ---------- validate ----------
report={"crop_px":[cw,ch],"masked_frac":round(float(mask_bad.mean()),3),
        "highlight_curv_cue":round(float(cue),3),"n_highlight_blobs":ncue,
        "height_crown_m":round(float(Zm.max()),4),"baseline_rmse":0.41}
try:
    gt=json.load(open("kong3d/refs/glb_hood_section.json"))
    prof=Zm[:,cw//2]; prof=prof/(prof.max()+1e-6)
    g=np.array(gt["centerline_norm"]); g=np.interp(np.linspace(0,1,len(prof)),np.linspace(0,1,len(g)),g)
    report["gt_rmse_norm"]=round(float(np.sqrt(np.mean((prof-g)**2))),4)
    report["improved"]=report["gt_rmse_norm"]<0.41
except Exception as e: report["gt_err"]=str(e)

Image.fromarray(((np.stack([nx,ny,nz],2)*0.5+0.5)*255).clip(0,255).astype(np.uint8)).save(f"{prefix}_normals.png")
Image.fromarray((Zm/Zm.max()*255).astype(np.uint8)).save(f"{prefix}_height.png")
json.dump({"report":report},open(f"{prefix}.json","w"),indent=1)
print("REPORT",json.dumps(report))
