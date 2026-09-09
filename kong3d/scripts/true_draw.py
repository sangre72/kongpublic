"""TRUE drawing (a_4265): observe→simplified vector paths→polygon fill→brush strokes.
NO pixel masks copied. Output is only draw-ops (polygons w/ few control pts + strokes)
on a blank canvas. Exports draw-program JSON for the canvas page to execute live.

usage: python3 true_draw.py <ref.jpg> <out.json>
"""
import sys, json
import numpy as np
from PIL import Image, ImageFilter

path, out = sys.argv[1], sys.argv[2]
im = Image.open(path).convert("RGB")
W, H = im.size
scale = 520 / max(W, H)
sw, sh = int(W*scale), int(H*scale)
small = im.resize((sw, sh))
arr = np.asarray(small, float)

# coarse segmentation only to FIND shapes (not to copy) — 20 regions
N = 20
q = np.asarray(small.quantize(colors=N, method=Image.MEDIANCUT).convert("RGB"))

def contour_of(mask):
    """boundary pixels ordered by angle around centroid (coarse outline)."""
    ys, xs = np.where(mask)
    if len(xs) < 40:
        return None
    cx, cy = xs.mean(), ys.mean()
    # boundary = mask pixels with a non-mask 4-neighbour
    b = mask & ~(np.roll(mask,1,0)&np.roll(mask,-1,0)&np.roll(mask,1,1)&np.roll(mask,-1,1))
    by, bx = np.where(b)
    if len(bx) < 8:
        return None
    ang = np.arctan2(by-cy, bx-cx)
    o = np.argsort(ang)
    return list(zip(bx[o].tolist(), by[o].tolist())), (cx, cy)

def rdp(pts, eps):
    """Douglas-Peucker simplify."""
    if len(pts) < 3:
        return pts
    p = np.array(pts, float)
    a, b = p[0], p[-1]
    d = b - a; L = np.hypot(*d) + 1e-9
    dist = np.abs((p[:,0]-a[0])*d[1]-(p[:,1]-a[1])*d[0])/L
    i = int(dist.argmax())
    if dist[i] > eps:
        left = rdp(pts[:i+1], eps); right = rdp(pts[i:], eps)
        return left[:-1] + right
    return [pts[0], pts[-1]]

shapes = []
for c in {tuple(x) for x in q.reshape(-1,3)}:
    m = np.all(q == c, 2)
    if m.sum() < 200:
        continue
    res = contour_of(m)
    if not res:
        continue
    outline, (cx, cy) = res
    # angular subsample then RDP -> tens of control points, NOT pixel-exact
    step = max(1, len(outline)//60)
    coarse = outline[::step]
    simp = rdp(coarse, eps=3.0)
    if len(simp) < 3:
        continue
    col = arr[m].mean(0).astype(int).tolist()
    shapes.append({"poly": [[round(x/sw,4), round(y/sh,4)] for x,y in simp],
                   "color": col, "area": int(m.sum()),
                   # brush strokes: sample a few interior points + local gradient dir
                   })

# brush strokes: follow luminance gradient direction, short segments, sampled colors
Lg = np.asarray(small.convert("L").filter(ImageFilter.GaussianBlur(2)), float)
gy, gx = np.gradient(Lg)
strokes = []
rng = np.random.default_rng(7)
for _ in range(900):
    x = int(rng.integers(0, sw)); y = int(rng.integers(0, sh))
    ang = np.arctan2(gy[y,x], gx[y,x]) + np.pi/2   # along iso-luminance (surface flow)
    ln = 6
    dx, dy = np.cos(ang)*ln, np.sin(ang)*ln
    col = arr[y,x].astype(int).tolist()
    strokes.append({"x0": round(x/sw,4), "y0": round(y/sh,4),
                    "x1": round((x+dx)/sw,4), "y1": round((y+dy)/sh,4),
                    "color": col})

shapes.sort(key=lambda s: -s["area"])
json.dump({"w": sw, "h": sh, "shapes": shapes, "strokes": strokes}, open(out, "w"))
print("shapes", len(shapes), "ctrl-pts", sum(len(s["poly"]) for s in shapes),
      "strokes", len(strokes))
