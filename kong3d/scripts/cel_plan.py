"""Cel plan v2: (1) flat color ZONES with CORRECT colors — region map from ref,
    fills as solid horizontal runs per zone (clean, not muddy sweeps).
   (2) LONG continuous contour outlines — trace sfs edges into chains, keep only
    LONG chains (>=12 pts), each = one unbroken polyline drag sequence.

usage: python3 cel_plan.py <ref.jpg> <out.json>
"""
import sys, json
import numpy as np
from PIL import Image, ImageFilter

path, out = sys.argv[1], sys.argv[2]
GW, GH = 200, 150
im = Image.open(path).convert("RGB").resize((GW, GH))
a = np.asarray(im, float)
cw, ch = 1000/GW, 740/GH
CX = lambda gx: round(gx*cw, 1); CY = lambda gy: round(gy*ch, 1)

# ---- classify each pixel into a small CEL palette with correct semantic colors ----
R, G, B = a[..., 0], a[..., 1], a[..., 2]
lum = a.mean(2)
label = np.zeros((GH, GW), int)
# 0 sky-blue,1 cloud-white,2 tree-dark,3 tree-mid,4 tree-light,5 bank-brown,6 grass
is_blue = (B > R+8) & (B > 90) & (G > 90)
is_white = (lum > 175) & (np.abs(R-G) < 25) & (np.abs(G-B) < 25)
is_green = (G > R+4) & (G > B+2)
is_brown = (R > G) & (G > B) & (lum < 150) & ~is_green
label[:] = 6  # default grass
label[is_green & (lum < 70)] = 2
label[is_green & (lum >= 70) & (lum < 115)] = 3
label[is_green & (lum >= 115)] = 4
label[is_brown] = 5
label[is_white] = 1
label[is_blue & ~is_white] = 0
PAL = {0:"#8fb0d6",1:"#eef2f6",2:"#2f4230",3:"#4d6b3f",4:"#7fa04f",5:"#7d6a4c",6:"#8aa54a"}

# fills = solid horizontal runs per row by label
from collections import defaultdict
runs_by = defaultdict(list)
for gy in range(GH):
    x = 0
    while x < GW:
        L = label[gy, x]; x2 = x
        while x2+1 < GW and label[gy, x2+1] == L:
            x2 += 1
        runs_by[PAL[L]].append((CY(gy), CX(x), CX(x2+1)))
        x = x2 + 1
# paint zones back-to-front: sky, cloud, greens dark→light, bank, grass
order = ["#8fb0d6","#eef2f6","#2f4230","#4d6b3f","#7fa04f","#7d6a4c","#8aa54a"]
fills = [{"c": c, "runs": runs_by[c]} for c in order if runs_by.get(c)]

# ---- silhouette contour: the treeline (sky <-> non-sky boundary) ----
# The one meaningful toon outline = where tree/ground meets sky. Trace the
# lowest sky pixel per column -> a single continuous horizon/treeline polyline.
is_sky = (label == 0) | (label == 1)
contours = []
line = []
for gx in range(GW):
    col = np.where(is_sky[:, gx])[0]
    if len(col) == 0:
        continue
    gy = col.max()            # bottom of the sky in this column = treeline top
    if gy >= GH - 2:          # column is all sky-ish -> skip (no treeline here)
        continue
    line.append([CX(gx), CY(gy)])
# simplify: keep every 3rd point to smooth jitter, split on big vertical jumps
if line:
    seg = [line[0]]
    for i in range(1, len(line)):
        if abs(line[i][1] - seg[-1][1]) > 120:   # big jump = discontinuity -> new segment
            if len(seg) >= 6: contours.append(seg[::2])
            seg = [line[i]]
        else:
            seg.append(line[i])
    if len(seg) >= 6: contours.append(seg[::2])

json.dump({"fills": fills, "contours": contours}, open(out, "w"))
print("zones", len(fills), "fill-runs", sum(len(f["runs"]) for f in fills),
      "long-contours", len(contours), "contour-pts", sum(len(c) for c in contours))
