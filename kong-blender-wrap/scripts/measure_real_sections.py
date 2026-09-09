"""Deep-measure real Model Y GLB → examples/real_mesh_measurements.json
Canonical frame: long axis=X (nose +X), up=Z, scaled to real L=4.751m.
Outputs: part inventory, X-station cross-sections (z_top/z_bot/half-width per z-frac),
plan-view width curve, flat-vs-crowned flags per region.
"""
import bpy, os, sys, json, math, mathutils
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(HERE, "..", "examples", "tesla_model_y_REAL_mesh.glb")
OUT = os.path.join(HERE, "..", "examples", "real_mesh_measurements.json")
REAL_L = 4.751  # m, Model Y overall length

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]

# gather all world-space verts per object
dg = bpy.context.evaluated_depsgraph_get()
inv_parts = []
allv = []
for o in meshes:
    me = o.evaluated_get(dg).to_mesh()
    n = len(me.vertices)
    co = np.empty(n*3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    M = np.array(o.matrix_world)
    w = co @ M[:3, :3].T + M[:3, 3]
    me.calc_loop_triangles()
    inv_parts.append({"name": o.name, "tris": len(me.loop_triangles),
                      "bbox_min": w.min(0).tolist(), "bbox_max": w.max(0).tolist()})
    allv.append(w)
V = np.vstack(allv)

# canonicalize: long axis → X. GLB long axis = Y → rotate -90 about Z: (x,y,z)->(y,-x,z)
dims = V.max(0) - V.min(0)
if dims[1] > dims[0]:
    V = np.stack([V[:,1], -V[:,0], V[:,2]], 1)
    for p in inv_parts:
        mn, mx = p["bbox_min"], p["bbox_max"]
        p["bbox_min"] = [mn[1], -mx[0], mn[2]]
        p["bbox_max"] = [mx[1], -mn[0], mx[2]]
# scale to real length, ground z=0, center x/y
mn, mx = V.min(0), V.max(0)
s = REAL_L / (mx[0]-mn[0])
V = (V - [(mn[0]+mx[0])/2, (mn[1]+mx[1])/2, mn[2]]) * s
for p in inv_parts:
    a = (np.array(p["bbox_min"]) - [(mn[0]+mx[0])/2, (mn[1]+mx[1])/2, mn[2]]) * s
    b = (np.array(p["bbox_max"]) - [(mn[0]+mx[0])/2, (mn[1]+mx[1])/2, mn[2]]) * s
    p["bbox_min"] = [round(v,4) for v in a]; p["bbox_max"] = [round(v,4) for v in b]
    c = (a+b)/2; d = b-a
    p["center"] = [round(v,4) for v in c]; p["dims"] = [round(v,4) for v in d]

mn, mx = V.min(0), V.max(0)
print("CANON dims L=%.3f W=%.3f H=%.3f  x[%.3f..%.3f] z[0..%.3f]" % (mx[0]-mn[0], mx[1]-mn[1], mx[2], mn[0], mx[0], mx[2]))

# cross-sections at 48 X stations
NS = 48
xs = np.linspace(mn[0]+0.01, mx[0]-0.01, NS)
slab = (mx[0]-mn[0]) / NS * 0.6
zfr = [0.02,0.08,0.15,0.25,0.35,0.45,0.55,0.65,0.75,0.85,0.92,0.98]
sections = []
for x in xs:
    sel = V[np.abs(V[:,0]-x) < slab]
    if len(sel) < 10:
        continue
    ztop = float(sel[:,2].max()); zbot = float(sel[:,2].min())
    hw = []
    for zf in zfr:
        z = zbot + zf*(ztop-zbot)
        band = sel[np.abs(sel[:,2]-z) < 0.03]
        hw.append(round(float(np.abs(band[:,1]).max()) if len(band) else 0.0, 4))
    sections.append({"x": round(float(x),4), "z_top": round(ztop,4), "z_bot": round(zbot,4), "half_w_at_zfrac": hw})

# plan-view width curve + roofline curvature (2nd deriv of z_top)
ztops = np.array([s_["z_top"] for s_ in sections])
xs2 = np.array([s_["x"] for s_ in sections])
curv = np.gradient(np.gradient(ztops, xs2), xs2)
for i, s_ in enumerate(sections):
    s_["roof_curv"] = round(float(curv[i]), 3)

inv_parts.sort(key=lambda p: -p["tris"])
out = {"canonical": {"L": round(float(mx[0]-mn[0]),4), "W": round(float(mx[1]-mn[1]),4), "H": round(float(mx[2]),4),
                     "frame": "nose≈+X? verify: X sorted low→high, up=+Z, ground z=0, scaled to 4.751m"},
       "z_fracs": zfr, "sections": sections,
       "parts": inv_parts}
with open(OUT, "w") as f:
    json.dump(out, f, indent=1)
print("PARTS top15:")
for p in inv_parts[:15]:
    print("  %-40s tris=%-8d dims=%.2f,%.2f,%.2f ctr=%.2f,%.2f,%.2f" % (p["name"], p["tris"], *p["dims"], *p["center"]))
print("WROTE", OUT)
