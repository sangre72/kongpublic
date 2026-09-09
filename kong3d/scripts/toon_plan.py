"""Toon/cel plan: posterize ref to few shade bands (flat color zones) + bold outline
paths from sfs Laplacian edges. Output: fill-runs (RLE per row, big cells) + outline
polylines. Draws as flat fills + brush outline strokes.

usage: python3 toon_plan.py <ref.jpg> <out.json>
"""
import sys, json
import numpy as np
from PIL import Image, ImageFilter

path, out = sys.argv[1], sys.argv[2]
GW, GH = 128, 96
im = Image.open(path).convert("RGB").resize((GW, GH))
# smooth then posterize to few levels per channel -> flat cel bands
sm = im.filter(ImageFilter.GaussianBlur(1.2))
a = np.asarray(sm, float)
# quantize each region by mapping to a small palette (cel look = few colors)
q = sm.quantize(colors=14, method=Image.MEDIANCUT).convert("RGB")
qa = np.asarray(q)
cw, ch = 1000/GW, 740/GH
runs = []
for gy in range(GH):
    x = 0
    while x < GW:
        c = tuple(qa[gy, x]); x2 = x
        while x2+1 < GW and tuple(qa[gy, x2+1]) == c:
            x2 += 1
        runs.append([round((gy+0.5)*ch, 1), round(x*cw, 1), round((x2+1)*cw, 1), "#%02x%02x%02x" % c])
        x = x2 + 1
from collections import defaultdict
bc = defaultdict(list)
for cy, x0, x1, c in runs:
    bc[c].append((cy, x0, x1))
fills = [{"c": c, "runs": r} for c, r in sorted(bc.items(), key=lambda kv: -len(kv[1]))]

# bold outlines: strong Laplacian edges on the posterized image (region boundaries)
L = np.asarray(q.convert("L").filter(ImageFilter.GaussianBlur(0.6)), float)
lap = np.abs(np.gradient(np.gradient(L, axis=0), axis=0) + np.gradient(np.gradient(L, axis=1), axis=1))
edges = lap > np.percentile(lap, 90)
# emit outline as short horizontal run segments per row (bold = brush drawn dark)
outline = []
for gy in range(GH):
    row = edges[gy]
    x = 0
    while x < GW:
        if row[x]:
            x2 = x
            while x2+1 < GW and row[x2+1]:
                x2 += 1
            outline.append([round((gy+0.5)*ch, 1), round(x*cw, 1), round((x2+1)*cw, 1)])
            x = x2 + 1
        else:
            x += 1
json.dump({"cellH": round(ch, 2), "fills": fills, "outline": outline,
           "n_fill_runs": len(runs), "n_outline": len(outline), "colors": len(bc)},
          open(out, "w"))
print("fill-runs", len(runs), "colors", len(bc), "outline-segs", len(outline))
