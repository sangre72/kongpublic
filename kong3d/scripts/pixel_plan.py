"""Plotter pixel-draw plan: downscale ref to grid, quantize, RLE per row → list of
same-color horizontal runs with canvas coords. Output JSON for kongtrol to drag.

usage: python3 pixel_plan.py <ref.jpg> <out.json> [gridW gridH]
"""
import sys, json
import numpy as np
from PIL import Image

path, out = sys.argv[1], sys.argv[2]
GW = int(sys.argv[3]) if len(sys.argv) > 3 else 160
GH = int(sys.argv[4]) if len(sys.argv) > 4 else 120
im = Image.open(path).convert("RGB").resize((GW, GH))
# quantize to a compact palette so runs are longer / fewer color-changes
q = im.quantize(colors=48, method=Image.MEDIANCUT).convert("RGB")
arr = np.asarray(q)

# canvas mapping: paint area canvas 0..1000 x 0..740; cell size
cellW = 1000 / GW
cellH = 740 / GH
runs = []   # [canvasY, canvasX0, canvasX1, "#hex"]
for gy in range(GH):
    x = 0
    while x < GW:
        c = tuple(arr[gy, x]); x2 = x
        while x2 + 1 < GW and tuple(arr[gy, x2 + 1]) == c:
            x2 += 1
        cy = round((gy + 0.5) * cellH, 1)
        cx0 = round(x * cellW, 1)
        cx1 = round((x2 + 1) * cellW, 1)
        runs.append([cy, cx0, cx1, "#%02x%02x%02x" % c])
        x = x2 + 1
# order rows top-down; group by color within a row already
json.dump({"gridW": GW, "gridH": GH, "cellH": round(cellH, 2), "runs": runs}, open(out, "w"))
print("rows", GH, "runs", len(runs), "colors", len({r[3] for r in runs}))
