"""Shape-from-shading v2 (a_4253) — finer extraction.
Upgrades over v1:
 (a) sub-pixel edge localization: parabola-fit the gradient/Laplacian peak per scanline.
 (b) multi-scale Laplacian: fine sigma(thin creases) + coarse sigma(panel boundaries).
 (c) adaptive per-region threshold: local window percentile, so creases in bright hood
     AND in shadowed areas both survive (global thr misses bright-zone creases).
 (d) gradient-DIRECTION field: quantized orientation map (surface curvature orientation).
 (e) repeatability: report extracted-line position stats across refs (caller aggregates).

usage: python3 shape_from_shading2.py <ref.jpg> <out_prefix>
"""
import sys, json
import numpy as np
from PIL import Image, ImageFilter

path, prefix = sys.argv[1], sys.argv[2]
im = Image.open(path).convert("RGB")
W, H = im.size
L = np.asarray(im.convert("L"), float)

def blur(sigma):
    return np.asarray(im.convert("L").filter(ImageFilter.GaussianBlur(sigma)), float)

# ---------- (a)+(b) multi-scale Laplacian, sub-pixel peak ----------
def laplacian(a):
    return (np.gradient(np.gradient(a, axis=0), axis=0) +
            np.gradient(np.gradient(a, axis=1), axis=1))
fine = np.abs(laplacian(blur(1.0)))    # thin creases
coarse = np.abs(laplacian(blur(4.0)))  # panel boundaries
# normalize each scale to its own 99.5pct so both contribute
fine_n = fine / (np.percentile(fine, 99.5) + 1e-6)
coarse_n = coarse / (np.percentile(coarse, 99.5) + 1e-6)

# ---------- (c) adaptive threshold via local-window mean+k*std ----------
def adaptive_edges(resp, win=41, k=3.0, floor=0.35):
    # downsample-box local stats (fast approx of local percentile)
    from PIL import Image as I
    small = I.fromarray((resp * 40).clip(0, 255).astype(np.uint8))
    loc = np.asarray(small.filter(ImageFilter.BoxBlur(win // 2)), float) / 40.0
    locsq = np.asarray(I.fromarray(((resp ** 2) * 8).clip(0, 255).astype(np.uint8))
                       .filter(ImageFilter.BoxBlur(win // 2)), float) / 8.0
    std = np.sqrt(np.maximum(locsq - loc ** 2, 0))
    return (resp > (loc + k * std)) & (resp > floor)
edges_fine = adaptive_edges(fine_n, k=4.0, floor=0.45)
edges_coarse = adaptive_edges(coarse_n, win=81, k=3.5, floor=0.4)

# ---------- (d) gradient-direction field, quantized ----------
sm = blur(1.5)
gy, gx = np.gradient(sm)
gmag = np.hypot(gx, gy)
gdir = (np.degrees(np.arctan2(gy, gx)) + 180) % 180   # 0..180 (undirected)
# quantize to 8 bins over regions with meaningful gradient
strong = gmag > np.percentile(gmag, 85)
dir_bins = np.full(gdir.shape, -1)
dir_bins[strong] = (gdir[strong] // 22.5).astype(int)
# per-cell(12x8 grid) dominant orientation
gh, gw = 8, 12
dir_field = []
for r in range(gh):
    row = []
    for c in range(gw):
        y0, y1 = r * H // gh, (r + 1) * H // gh
        x0, x1 = c * W // gw, (c + 1) * W // gw
        cell = dir_bins[y0:y1, x0:x1]
        v = cell[cell >= 0]
        row.append(int(np.bincount(v).argmax()) if len(v) else -1)
    dir_field.append(row)

# ---------- sub-pixel crease polyline (parabola fit on fine response per column) ----------
def subpixel_line(resp, mask, y_lo, y_hi, step):
    pts = []
    for x in range(0, W, step):
        yl, yh = int(y_lo * H), int(y_hi * H)
        col_m = mask[yl:yh, x]
        if not col_m.any():
            continue
        col_r = resp[yl:yh, x]
        yi = np.argmax(col_r * col_m)
        # parabola vertex refine
        if 0 < yi < len(col_r) - 1:
            a, b, c = col_r[yi - 1], col_r[yi], col_r[yi + 1]
            denom = (a - 2 * b + c)
            off = 0.5 * (a - c) / denom if abs(denom) > 1e-6 else 0.0
        else:
            off = 0.0
        y = yl + yi + off
        pts.append([round(x / W, 4), round(y / H, 4)])
    return pts

step = max(3, W // 90)
hood_crease = subpixel_line(fine_n, edges_fine, 0.55, 0.72, step)   # thin hood-V
panel_edge = subpixel_line(coarse_n, edges_coarse, 0.30, 0.90, step)  # panel boundary

# specular ridge sub-pixel (brightest, adaptive)
spec_mask = L > np.percentile(L, 97)
spec_ridge = subpixel_line(L, spec_mask, 0.30, 0.70, step)

out = {
    "image": path, "W": W, "H": H,
    "hood_crease_subpix_frac": hood_crease,
    "panel_edge_subpix_frac": panel_edge,
    "specular_ridge_subpix_frac": spec_ridge,
    "gradient_direction_field_8x12_bins": dir_field,   # -1 flat, 0-7 = 22.5deg bins
    "scales": {"fine_sigma": 1.0, "coarse_sigma": 4.0},
}
json.dump(out, open(f"{prefix}.json", "w"), indent=1)

# overlays
def save_gray(a, name):
    a = a.astype(float); a = (a - a.min()) / (np.ptp(a) + 1e-6) * 255
    Image.fromarray(a.astype(np.uint8)).save(name)
save_gray(fine_n, f"{prefix}_fine.png")
save_gray(coarse_n, f"{prefix}_coarse.png")
ov = np.asarray(im).copy()
ov[edges_fine] = [255, 60, 60]       # thin creases red
ov[edges_coarse & ~edges_fine] = [60, 160, 255]  # panel boundaries blue
Image.fromarray(ov).save(f"{prefix}_overlay2.png")
print("hood pts:", len(hood_crease), "panel pts:", len(panel_edge), "spec pts:", len(spec_ridge))
print("WROTE", prefix)
