"""Dense per-pixel shape-from-shading (a_4255): luminance→normal→heightfield→mesh.
Lambertian assumption, specular/reflection masking. Validates hood reconstruction
against the real GLB hood cross-section (ground truth).

usage: python3 dense_sfs.py <ref.jpg> <out_prefix> [x0 y0 x1 y1 as fracs of hood region]
"""
import sys, json
import numpy as np
from PIL import Image

path, prefix = sys.argv[1], sys.argv[2]
# hood region fracs (front photo): default from measured body
hx0, hy0, hx1, hy1 = (float(a) for a in (sys.argv[3:7] if len(sys.argv) >= 7
                                         else (0.22, 0.55, 0.80, 0.75)))

im = Image.open(path).convert("RGB")
W, H = im.size
crop = im.crop((int(hx0 * W), int(hy0 * H), int(hx1 * W), int(hy1 * H)))
cw, ch = crop.size
rgb = np.asarray(crop, float) / 255.0
lum = rgb @ [0.299, 0.587, 0.114]

# ---------- specular / reflection mask ----------
# glossy paint reflections = very bright OR high local color-variance (sky/lights reflected).
# Lambertian SfS is invalid there -> mask and inpaint-from-neighbours.
bright = lum > 0.92
# color saturation high = reflected colored object, not body paint
mx = rgb.max(2); mn = rgb.min(2)
sat = (mx - mn) / (mx + 1e-6)
colored = sat > 0.25
mask_bad = bright | colored
# smooth-fill masked luminance from surrounding (iterative blur inpaint)
L = lum.copy()
L[mask_bad] = np.nan
for _ in range(40):
    m = np.isnan(L)
    if not m.any():
        break
    filled = L.copy()
    filled[m] = 0
    from scipy.ndimage import uniform_filter  # noqa
L = lum.copy()  # (scipy may be absent; do a pure-numpy fill below)

def numpy_inpaint(a, bad, iters=60):
    a = a.copy(); a[bad] = 0.5
    for _ in range(iters):
        up = np.roll(a, 1, 0); dn = np.roll(a, -1, 0)
        lf = np.roll(a, 1, 1); rt = np.roll(a, -1, 1)
        avg = (up + dn + lf + rt) / 4.0
        a[bad] = avg[bad]
    return a
L = numpy_inpaint(lum, mask_bad)

# ---------- luminance -> surface normal (Lambertian, light ~ from top-front) ----------
# I = max(0, N . Ld). assume Ld ~ (0, sinθ, cosθ) roughly from above-front.
# recover slope from brightness: brighter = normal more toward light.
# gradient of luminance ~ curvature; integrate a proxy height directly:
#   treat (1 - L) as depth-ish (darker = facing away/down). smooth heavily.
gy, gx = np.gradient(L)
# normal ~ (-gx, -gy, s); pick s so slopes are moderate
s = 0.15
nx, ny, nz = -gx, -gy, np.full_like(L, s)
nn = np.sqrt(nx*nx + ny*ny + nz*nz) + 1e-6
nx, ny, nz = nx/nn, ny/nn, nz/nn

# ---------- integrate normals -> heightfield (Frankot-Chellappa, FFT) ----------
p = -nx / (nz + 1e-6)   # dz/dx
q = -ny / (nz + 1e-6)   # dz/dy
fy = np.fft.fftfreq(ch)[:, None]
fx = np.fft.fftfreq(cw)[None, :]
denom = (2j*np.pi*fx)**2 + (2j*np.pi*fy)**2
denom[0, 0] = 1
Z = np.fft.ifft2((np.fft.fft2(p)*(2j*np.pi*fx) + np.fft.fft2(q)*(2j*np.pi*fy)) / denom).real
Z -= Z.min()
# hood is broad and gently crowned; normalize height to plausible ~0.12m crown
Zm = Z / (Z.max() + 1e-6) * 0.12

# ---------- ground-truth validation vs GLB hood cross-section ----------
gt = None
try:
    gt = json.load(open("kong3d/refs/glb_hood_section.json"))
except Exception:
    pass
report = {"crop_px": [cw, ch], "masked_frac": round(float(mask_bad.mean()), 3),
          "height_crown_m": round(float(Zm.max()), 4)}
if gt:
    # compare centerline profile (Z along mid-column) to gt normalized
    prof = Zm[:, cw//2]; prof = prof/prof.max()
    g = np.array(gt["centerline_norm"]); g = np.interp(np.linspace(0,1,len(prof)), np.linspace(0,1,len(g)), g)
    err = np.sqrt(np.mean((prof-g)**2))
    report["gt_rmse_norm"] = round(float(err), 4)

# ---------- outputs: normal map viz + heightfield + coarse mesh verts ----------
Image.fromarray(((np.stack([nx, ny, nz], 2)*0.5+0.5)*255).astype(np.uint8)).save(f"{prefix}_normals.png")
Image.fromarray((Zm/Zm.max()*255).astype(np.uint8)).save(f"{prefix}_height.png")
Image.fromarray(((~mask_bad)*255).astype(np.uint8)).save(f"{prefix}_validmask.png")
# decimated mesh grid (32x sample) -> world-ish verts (frac x,z + height y)
sy = max(1, ch//24); sx = max(1, cw//32)
verts = [[round(c/cw,3), round(float(Zm[r,c]),4), round(r/ch,3)]
         for r in range(0, ch, sy) for c in range(0, cw, sx)]
report["mesh_sample_verts"] = len(verts)
json.dump({"report": report, "verts_fracXY_heightY": verts[:400]},
          open(f"{prefix}.json", "w"), indent=1)
print("REPORT", json.dumps(report))
print("WROTE", prefix)
