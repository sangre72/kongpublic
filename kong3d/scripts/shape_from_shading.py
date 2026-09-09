"""Shape-from-shading-lite: extract crease lines, curvature ridges, part regions
from a reference photo via PIL/numpy. Outputs coordinate data (image-frac) +
diagnostic overlays. Pure compute — no ML.

usage: python3 shape_from_shading.py <ref.jpg> <out_prefix>
"""
import sys, json
import numpy as np
from PIL import Image, ImageFilter

path, prefix = sys.argv[1], sys.argv[2]
im = Image.open(path).convert("RGB")
W, H = im.size
rgb = np.asarray(im, float)
lum = rgb @ [0.299, 0.587, 0.114]           # luminance

# ---------- (a) luminance gradient ----------
# smooth first to kill sensor noise; keep structure
sm = np.asarray(im.convert("L").filter(ImageFilter.GaussianBlur(2)), float)
gy, gx = np.gradient(sm)
gmag = np.hypot(gx, gy)
gdir = np.arctan2(gy, gx)

# ---------- crease/panel edges = sharp value STEPS ----------
# second derivative magnitude (Laplacian-of-Gaussian style) picks discontinuities
lap = np.abs(np.gradient(np.gradient(sm, axis=0), axis=0) +
             np.gradient(np.gradient(sm, axis=1), axis=1))
edge_thr = np.percentile(lap, 99.3)
edges = lap > edge_thr

# ---------- (b) specular highlight ridges = brightest streaks ----------
spec_thr = np.percentile(sm, 98.5)
spec = sm > spec_thr

# ---------- (c) color-region segmentation = part boundaries ----------
# coarse quantize into value bands -> body/glass/trim/light
Lb = np.asarray(im.convert("L"), float)
bands = np.digitize(Lb, [40, 90, 150, 205])   # 0=very dark(glass/trim) ..4=highlight
# region centroids per band (image-frac), body-region excluded (largest mid band)
region_fracs = {}
for b in range(5):
    m = bands == b
    if m.sum() > 0.002 * W * H:
        ys, xs = np.where(m)
        region_fracs[b] = {
            "px": round(m.sum() / (W * H), 3),
            "cx": round(xs.mean() / W, 3), "cy": round(ys.mean() / H, 3),
            "x_range": [round(xs.min() / W, 3), round(xs.max() / W, 3)],
            "y_range": [round(ys.min() / H, 3), round(ys.max() / H, 3)],
        }

# ---------- extract crease POLYLINES: strongest edge pixel per column in mid-band ----------
def line_from_edges(mask, y_lo, y_hi, step=None):
    step = step or max(4, W // 60)
    pts = []
    for x in range(0, W, step):
        col = mask[int(y_lo * H):int(y_hi * H), x]
        if col.any():
            ys = np.where(col)[0]
            y = ys[len(ys) // 2] + int(y_lo * H)
            pts.append([round(x / W, 3), round(y / H, 3)])
    return pts

hood_edge = line_from_edges(edges, 0.35, 0.75)      # hood/fascia region
belt_spec = line_from_edges(spec, 0.30, 0.70)       # shoulder highlight streak

out = {
    "image": path, "W": W, "H": H,
    "grad_mean": round(float(gmag.mean()), 2),
    "edge_thr": round(float(edge_thr), 1),
    "crease_polyline_frac": hood_edge,
    "specular_ridge_frac": belt_spec,
    "regions_by_value_band": region_fracs,
}
json.dump(out, open(f"{prefix}.json", "w"), indent=1)

# diagnostic overlays
def save_gray(arr, name):
    a = arr.astype(float); a = (a - a.min()) / (np.ptp(a) + 1e-6) * 255
    Image.fromarray(a.astype(np.uint8)).save(name)
save_gray(gmag, f"{prefix}_gradient.png")
save_gray(lap, f"{prefix}_edges.png")
ov = np.asarray(im).copy()
ov[edges] = [255, 60, 60]
ov[spec] = [60, 160, 255]
Image.fromarray(ov).save(f"{prefix}_overlay.png")
print("crease pts:", len(hood_edge), "spec pts:", len(belt_spec), "bands:", list(region_fracs))
print("WROTE", prefix + ".json/_gradient/_edges/_overlay")
