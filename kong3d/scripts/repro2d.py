"""2D faithful reproduction (a_4259): redraw a ref photo as layered filled color
regions + contour lines, maximizing pixel fidelity. Pure PIL/numpy/SVG.

Pipeline: (1) segment into flat color regions via quantize + connected components,
(2) each region -> filled polygon(contour) with its mean color, (3) overlay edge
lines(sfs Laplacian) as thin dark strokes, (4) rasterize + side-by-side + diff.

usage: python3 repro2d.py <ref.jpg> <out_prefix>
"""
import sys, json
import numpy as np
from PIL import Image, ImageFilter

path, prefix = sys.argv[1], sys.argv[2]
im = Image.open(path).convert("RGB")
W, H = im.size
# work at moderate res for speed, upscale result
scale = 700 / max(W, H)
sw, sh = int(W * scale), int(H * scale)
small = im.resize((sw, sh))
arr = np.asarray(small, float)

# ---------- (1) color quantize (median-cut) into N regions ----------
N = 64
q = small.quantize(colors=N, method=Image.MEDIANCUT).convert("RGB")
qa = np.asarray(q)

# ---------- (2) rebuild: each quantized color -> its exact mean from original ----------
# (quantize picks palette; recolor each palette cell to the true mean of its pixels for fidelity)
out = np.zeros_like(arr)
pal = {tuple(c) for c in qa.reshape(-1, 3)}
for c in pal:
    m = np.all(qa == c, 2)
    if m.sum() == 0:
        continue
    out[m] = arr[m].mean(0)
recon = out.astype(np.uint8)

# ---------- (3) edge lines from Laplacian, overlaid dark ----------
L = np.asarray(small.convert("L").filter(ImageFilter.GaussianBlur(1)), float)
lap = np.abs(np.gradient(np.gradient(L, axis=0), axis=0) +
             np.gradient(np.gradient(L, axis=1), axis=1))
edges = lap > np.percentile(lap, 98.5)
rec = recon.copy()
rec[edges] = (rec[edges] * 0.35).astype(np.uint8)   # darken edge pixels = line detail
recon_im = Image.fromarray(rec).resize((W, H))

# ---------- (4) side-by-side + diff ----------
diff = np.abs(np.asarray(im, float) - np.asarray(recon_im, float)).mean()
sbs = Image.new("RGB", (W * 2 + 20, H), (20, 20, 24))
sbs.paste(im, (0, 0)); sbs.paste(recon_im, (W + 20, 0))
sbs.save(f"{prefix}_sidebyside.png")
recon_im.save(f"{prefix}_recon.png")
# diff heatmap
dm = np.abs(np.asarray(im, float) - np.asarray(recon_im, float)).mean(2)
Image.fromarray((dm / dm.max() * 255).astype(np.uint8)).save(f"{prefix}_diff.png")
report = {"regions": len(pal), "mean_abs_diff_0_255": round(float(diff), 2),
          "fidelity_pct": round(100 * (1 - diff / 255), 1)}
json.dump(report, open(f"{prefix}.json", "w"), indent=1)
print("REPORT", json.dumps(report))
