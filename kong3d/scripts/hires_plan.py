"""Hi-res cel plan: (1) 16-color median-cut quantization -> many small flat zones
   with the ref's actual colors (not 7 hand-labels). (2) DENSE smooth outline
   polylines traced along EVERY region boundary (not sparse sfs ticks): for each
   quantized color, its region edge is walked into ordered chains -> continuous
   thin dark lines. (3) detail hints kept implicitly via the small zones.
usage: python3 hires_plan.py <ref.jpg> <out.json>
"""
import sys, json
import numpy as np
from PIL import Image, ImageFilter
from collections import defaultdict

path, out = sys.argv[1], sys.argv[2]
GW, GH = 260, 195                       # higher grid than 200x150
NCOL = 16
im = Image.open(path).convert("RGB").resize((GW, GH))
im = im.filter(ImageFilter.MedianFilter(3))     # denoise so zones are clean
CWID, CHT = 1000/GW, 740/GH
def CX(gx): return round(float(gx)*CWID, 1)
def CY(gy): return round(float(gy)*CHT, 1)

# ---- 16-color quantize (median cut) ----
pq = im.quantize(colors=NCOL, method=Image.MEDIANCUT).convert("P")
idx = np.asarray(pq)                      # GH x GW palette indices
pal = pq.getpalette()[:NCOL*3]
hexof = {i: "#%02x%02x%02x" % (pal[i*3], pal[i*3+1], pal[i*3+2]) for i in range(NCOL)}
lumof = {i: 0.299*pal[i*3]+0.587*pal[i*3+1]+0.114*pal[i*3+2] for i in range(NCOL)}

# ---- fills: horizontal runs per palette index, painted dark->light (light on top reads better) ----
runs_by = defaultdict(list)
for gy in range(GH):
    x = 0
    while x < GW:
        L = idx[gy, x]; x2 = x
        while x2+1 < GW and idx[gy, x2+1] == L:
            x2 += 1
        runs_by[L].append((CY(gy), CX(x), CX(x2+1)))
        x = x2 + 1
order = sorted(range(NCOL), key=lambda i: lumof[i])   # dark first
fills = [{"c": hexof[i], "runs": runs_by[i]} for i in order if runs_by.get(i)]

# ---- DENSE smooth outlines: boundary pixels (label differs from right/down neighbour),
#      walked into ordered chains via 8-neighbour tracing -> continuous polylines ----
H, W = idx.shape
boundary = np.zeros((H, W), bool)
boundary[:, :-1] |= idx[:, :-1] != idx[:, 1:]
boundary[:-1, :] |= idx[:-1, :] != idx[1:, :]
# thin the field a touch: only keep boundaries between sufficiently different lums
# (skip near-identical adjacent shades so we don't outline every micro-step)
diff = np.zeros((H, W), bool)
for gy in range(H):
    for gx in range(W-1):
        if idx[gy,gx]!=idx[gy,gx+1] and abs(lumof[idx[gy,gx]]-lumof[idx[gy,gx+1]])>18:
            diff[gy,gx]=True
    for gx in range(W):
        if gy<H-1 and idx[gy,gx]!=idx[gy+1,gx] and abs(lumof[idx[gy,gx]]-lumof[idx[gy+1,gx]])>18:
            diff[gy,gx]=True
edges = boundary & diff

vis = np.zeros_like(edges, bool)
def nb(y, x):
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            if dy or dx:
                ny,nx=y+dy,x+dx
                if 0<=ny<H and 0<=nx<W and edges[ny,nx] and not vis[ny,nx]:
                    yield ny,nx
def rdp(pts, eps=1.2):
    if len(pts)<3: return pts
    a,b=pts[0],pts[-1]; import math
    dx,dy=b[0]-a[0],b[1]-a[1]; L=math.hypot(dx,dy) or 1
    mi,md=0,0
    for i in range(1,len(pts)-1):
        d=abs((pts[i][0]-a[0])*dy-(pts[i][1]-a[1])*dx)/L
        if d>md: md,mi=d,i
    if md>eps:
        return rdp(pts[:mi+1],eps)[:-1]+rdp(pts[mi:],eps)
    return [a,b]

contours=[]
ys,xs=np.where(edges)
for sy,sx in zip(ys,xs):
    if vis[sy,sx]: continue
    ch=[(sy,sx)]; vis[sy,sx]=True; cy,cx=sy,sx
    while True:
        n=next(nb(cy,cx),None)
        if n is None: break
        vis[n]=True; ch.append(n); cy,cx=n
    if len(ch)>=8:
        poly=[[CX(x),CY(y)] for (y,x) in ch]
        poly=rdp(poly,1.2)                 # smooth: fewer, cleaner points
        if len(poly)>=3: contours.append(poly)

json.dump({"fills":fills,"contours":contours}, open(out,"w"))
print("colors",len(fills),"fill-runs",sum(len(f["runs"]) for f in fills),
      "contours",len(contours),"contour-pts",sum(len(c) for c in contours))
