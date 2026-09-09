"""River-only fill: classify the central water corridor and emit water-color runs.
Water in ref_4264 = center-right channel, y~0.58-0.78, low-saturation grey-brown,
recedes to a vanishing point near center. Spatially gated to avoid grabbing trees.
usage: python3 river_plan.py <ref.jpg> <out.json>
"""
import sys, json
import numpy as np
from PIL import Image

path, out = sys.argv[1], sys.argv[2]
GW, GH = 200, 150
im = Image.open(path).convert("RGB").resize((GW, GH))
a = np.asarray(im, float)
cw, ch = 1000/GW, 740/GH
CX = lambda gx: round(gx*cw, 1); CY = lambda gy: round(gy*ch, 1)
R, G, B = a[..., 0], a[..., 1], a[..., 2]
lum = a.mean(2)
sat = a.max(2) - a.min(2)

WATER = "#9aa0968f"  # will strip alpha below; use opaque grey-brown
WATER = "#96988c"

yy, xx = np.mgrid[0:GH, 0:GW]
fy, fx = yy/GH, xx/GW
# spatial gate: central-right corridor that narrows upward (perspective)
# bottom band wide, upper band narrow toward vanishing pt ~ (0.5,0.58)
corridor = (fy > 0.58) & (fy < 0.80) & (fx > (0.5 - (fy-0.55)*1.4)) & (fx < (0.5 + (fy-0.55)*2.2))
# water look: low saturation, mid luminance, not deep-green
is_water = corridor & (sat < 45) & (lum > 70) & (lum < 165) & ~((G > R+6) & (G > B+6))

from collections import defaultdict
runs = []
for gy in range(GH):
    x = 0
    while x < GW:
        if not is_water[gy, x]:
            x += 1; continue
        x2 = x
        while x2+1 < GW and is_water[gy, x2+1]:
            x2 += 1
        if x2 - x >= 1:
            runs.append((CY(gy), CX(x), CX(x2+1)))
        x = x2 + 1

json.dump({"fills": [{"c": WATER, "runs": runs}], "contours": []}, open(out, "w"))
print("water-runs", len(runs))
