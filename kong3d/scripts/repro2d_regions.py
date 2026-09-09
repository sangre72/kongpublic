"""Export ordered region draw-data (contours + fill colors) for progressive canvas render."""
import sys, json
import numpy as np
from PIL import Image, ImageFilter

path, out = sys.argv[1], sys.argv[2]
im = Image.open(path).convert("RGB")
W, H = im.size
scale = 640 / max(W, H)
sw, sh = int(W * scale), int(H * scale)
small = im.resize((sw, sh))
arr = np.asarray(small, float)
N = 64
q = small.quantize(colors=N, method=Image.MEDIANCUT).convert("RGB")
qa = np.asarray(q)

# per palette color: mask, mean-color, bbox, pixel-run-length encoding for exact fill
regions = []
for c in {tuple(x) for x in qa.reshape(-1, 3)}:
    m = np.all(qa == c, 2)
    if m.sum() < 20:
        continue
    col = arr[m].mean(0).astype(int).tolist()
    # RLE per row: list of [y, x_start, x_len]
    runs = []
    for y in range(sh):
        row = m[y]
        if not row.any():
            continue
        xs = np.where(row)[0]
        s = xs[0]; prev = xs[0]
        for x in xs[1:]:
            if x != prev + 1:
                runs.append([y, int(s), int(prev - s + 1)]); s = x
            prev = x
        runs.append([y, int(s), int(prev - s + 1)])
    regions.append({"color": col, "area": int(m.sum()), "runs": runs})
regions.sort(key=lambda r: -r["area"])   # big regions first (background, body)

# edge lines
L = np.asarray(small.convert("L").filter(ImageFilter.GaussianBlur(1)), float)
lap = np.abs(np.gradient(np.gradient(L, axis=0), axis=0) + np.gradient(np.gradient(L, axis=1), axis=1))
edges = lap > np.percentile(lap, 98.5)
epx = [[int(x), int(y)] for y, x in zip(*np.where(edges))]

json.dump({"w": sw, "h": sh, "regions": regions, "edges": epx},
          open(out, "w"))
print("regions", len(regions), "edges", len(epx), "->", out)
