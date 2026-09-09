"""Curved-stroke plan: trace edge contours into ordered polyline CHAINS (not dots).
Outlines = long chained strokes following contours. Fills = broad directional sweeps
per region, stroke direction following form (trees=vertical/arced, grass=upward sweep,
sky/clouds=horizontal-arced). Output: stroke list, each = [color, size, [[x,y]...]] canvas pts.

usage: python3 stroke_plan.py <ref.jpg> <out.json>
"""
import sys, json
import numpy as np
from PIL import Image, ImageFilter

path, out = sys.argv[1], sys.argv[2]
GW, GH = 200, 150
im = Image.open(path).convert("RGB").resize((GW, GH))
sm = im.filter(ImageFilter.GaussianBlur(1.4))
a = np.asarray(sm, float)
q = sm.quantize(colors=14, method=Image.MEDIANCUT).convert("RGB")
qa = np.asarray(q)
cw, ch = 1000/GW, 740/GH
CX = lambda gx: round(gx*cw, 1)
CY = lambda gy: round(gy*ch, 1)
strokes = []   # {c,size,pts}

# ---- FILLS as broad directional sweeps per region band ----
# group by color; for each, sweep strokes across its bounding rows in form-direction.
# heuristic: sky(top, cool)=horizontal; foliage(green)=short upward arcs; grass(bottom)=upward sweeps.
from collections import defaultdict
cells = defaultdict(list)
for gy in range(GH):
    for gx in range(GW):
        cells[tuple(qa[gy, gx])].append((gx, gy))
for c, pts in sorted(cells.items(), key=lambda kv: -len(kv[1])):
    if len(pts) < 30:
        continue
    arr = np.array(pts)
    ys = arr[:, 1]; hexc = "#%02x%02x%02x" % c
    ymid = ys.mean()/GH
    rr, gg, bb = c
    is_green = gg > rr and gg > bb
    # sweep rows every 3 grid-rows, drawing a horizontal-ish stroke across that row's extent,
    # arced by following the region's x-extent per row (broad directional stroke)
    for gy in range(int(ys.min()), int(ys.max())+1, 3):
        xs = arr[arr[:, 1] == gy][:, 0]
        if len(xs) < 2:
            continue
        x0, x1 = int(xs.min()), int(xs.max())
        # arc: midpoint lifted for canopy, dipped for grass sweep — few control pts = curved
        if is_green and ymid < 0.55:   # foliage: gentle downward arc (canopy)
            mid = [CX((x0+x1)/2), CY(gy-1.2)]
        elif is_green:                  # grass: upward sweep
            mid = [CX((x0+x1)/2), CY(gy-1.5)]
        else:                           # sky/other: near-flat slight arc
            mid = [CX((x0+x1)/2), CY(gy-0.4)]
        strokes.append({"c": hexc, "size": 9,
                        "pts": [[CX(x0), CY(gy)], mid, [CX(x1), CY(gy)]]})

# ---- OUTLINES as chained contour strokes ----
L = np.asarray(q.convert("L").filter(ImageFilter.GaussianBlur(0.6)), float)
lap = np.abs(np.gradient(np.gradient(L, axis=0), axis=0) + np.gradient(np.gradient(L, axis=1), axis=1))
edges = lap > np.percentile(lap, 92)
# trace: for each edge pixel not visited, walk to 8-neighbours building an ordered chain
vis = np.zeros_like(edges, bool)
def neighbours(y, x):
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                ny, nx = y+dy, x+dx
                if 0 <= ny < GH and 0 <= nx < GW and edges[ny, nx] and not vis[ny, nx]:
                    yield ny, nx
ys, xs = np.where(edges)
for sy, sx in zip(ys, xs):
    if vis[sy, sx]:
        continue
    chain = [(sy, sx)]; vis[sy, sx] = True
    cy, cx = sy, sx
    while True:
        nxt = next(neighbours(cy, cx), None)
        if nxt is None:
            break
        vis[nxt] = True; chain.append(nxt); cy, cx = nxt
    if len(chain) >= 4:   # only meaningful contours
        # simplify to every 2nd pt = curved polyline
        pts = [[CX(x), CY(y)] for (y, x) in chain[::2]]
        if len(pts) >= 2:
            strokes.append({"c": "#161616", "size": 4, "pts": pts})

json.dump({"strokes": strokes}, open(out, "w"))
n_fill = sum(1 for s in strokes if s["c"] != "#161616")
print("strokes", len(strokes), "fills", n_fill, "outlines", len(strokes)-n_fill,
      "total-pts", sum(len(s["pts"]) for s in strokes))
