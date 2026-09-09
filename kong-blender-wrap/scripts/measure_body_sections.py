"""Body-shell-only sections (exterior BIW: 103_body_*, 101_fenders, glass_body, 48_black cladding)
→ examples/real_body_sections.json + 4 ortho reference renders of the REAL mesh (canonical frame).
Frame: nose=-X, rear=+X, up=Z, ground z=0, L=4.751m (matches real_mesh_measurements.json).
"""
import bpy, os, json, math, mathutils
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(HERE, "..", "examples", "tesla_model_y_REAL_mesh.glb")
OUT = os.path.join(HERE, "..", "examples", "real_body_sections.json")
REAL_L = 4.751

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]

def is_body(n):
    return ("body_0" in n and "glass" not in n) or "fenders" in n or n.startswith("48_black")
def is_glass(n):
    return "glass_body" in n

dg = bpy.context.evaluated_depsgraph_get()
def verts(objs):
    out = []
    for o in objs:
        me = o.evaluated_get(dg).to_mesh()
        co = np.empty(len(me.vertices)*3)
        me.vertices.foreach_get("co", co)
        M = np.array(o.matrix_world)
        out.append(co.reshape(-1,3) @ M[:3,:3].T + M[:3,3])
    return np.vstack(out)

Vall = verts(meshes)
Vbody = verts([o for o in meshes if is_body(o.name)])
Vglass = verts([o for o in meshes if is_glass(o.name)])

def canon(V, ref):
    mn, mx = ref.min(0), ref.max(0)
    W = np.stack([V[:,1], -V[:,0], V[:,2]], 1)
    rmn = np.array([mn[1], -mx[0], mn[2]]); rmx = np.array([mx[1], -mn[0], mx[2]])
    s = REAL_L/(rmx[0]-rmn[0])
    return (W - [(rmn[0]+rmx[0])/2, (rmn[1]+rmx[1])/2, rmn[2]])*s

Vb = canon(Vbody, Vall); Vg = canon(Vglass, Vall)

def sections(V, ns, zbins):
    mn, mx = V.min(0), V.max(0)
    xs = np.linspace(mn[0]+0.005, mx[0]-0.005, ns)
    slab = (mx[0]-mn[0])/ns*0.6
    res = []
    for x in xs:
        sel = V[np.abs(V[:,0]-x)<slab]
        if len(sel)<8: res.append(None); continue
        zt, zb = float(sel[:,2].max()), float(sel[:,2].min())
        prof = []
        for zf in np.linspace(0.02, 0.98, zbins):
            z = zb+zf*(zt-zb)
            band = sel[np.abs(sel[:,2]-z)<0.025]
            prof.append(round(float(np.abs(band[:,1]).max()) if len(band) else 0.0,4))
        # crown: y-spread of the top 3cm (flat roof → wide spread; crowned → narrow)
        topband = sel[sel[:,2]>zt-0.03]
        crown_w = round(float(np.abs(topband[:,1]).max()*2),4)
        res.append({"x":round(float(x),4),"z_top":round(zt,4),"z_bot":round(zb,4),
                    "half_w":prof,"top_flat_w":crown_w})
    return [r for r in res if r]

body_s = sections(Vb, 64, 16)
glass_s = sections(Vg, 40, 8)
out = {"frame":"nose=-X rear=+X up=Z ground z=0 L=4.751",
       "body_dims":[round(float(v),4) for v in (Vb.max(0)-Vb.min(0))],
       "glass_dims":[round(float(v),4) for v in (Vg.max(0)-Vg.min(0))],
       "glass_bbox":[[round(float(v),4) for v in Vg.min(0)],[round(float(v),4) for v in Vg.max(0)]],
       "z_fracs":"linspace(0.02,0.98,16)","body_sections":body_s,"glass_sections":glass_s}
json.dump(out, open(OUT,"w"), indent=1)
print("BODY dims", out["body_dims"], "GLASS bbox", out["glass_bbox"])
print("WROTE", OUT)

# ---- reference ortho renders of the REAL mesh, canonical orientation ----
root = bpy.data.objects.new("rt", None)
bpy.context.scene.collection.objects.link(root)
for o in bpy.data.objects:
    if o is not root and o.parent is None: o.parent = root
root.rotation_euler = (0,0,-math.pi/2)
mnA, mxA = Vall.min(0), Vall.max(0)
s = REAL_L/(mxA[1]-mnA[1])
root.scale=(s,s,s)
bpy.context.view_layer.update()
# recompute canonical full bbox
Vc = canon(Vall, Vall)
mn, mx = Vc.min(0), Vc.max(0)
root.location = (-( (mnA[1]+mxA[1])/2 )*0 ,0,0)  # canon() math already matches rotation+scale w/ origin offset below
# place root so world matches canon: canon subtracts centers → set location accordingly
root.location = (-( (mnA[1]+mxA[1])/2 )*s + 0, ((mnA[0]+mxA[0])/2)*s + 0, -mnA[2]*s)
bpy.context.view_layer.update()
scene = bpy.context.scene
w = bpy.data.worlds.new("w"); w.use_nodes=True; scene.world=w
w.node_tree.nodes["Background"].inputs[0].default_value=(0.9,0.92,0.95,1)
ld = bpy.data.lights.new("sun","SUN"); ld.energy=3
lo = bpy.data.objects.new("sun",ld); scene.collection.objects.link(lo)
lo.rotation_euler=(math.radians(50),0,math.radians(30))
cx,cy,cz = (mn[0]+mx[0])/2,(mn[1]+mx[1])/2,(mn[2]+mx[2])/2
L = mx[0]-mn[0]
def shoot(loc, name, ortho_scale=None, lens=40):
    c = bpy.data.cameras.new(name); co=bpy.data.objects.new(name,c)
    scene.collection.objects.link(co); co.location=loc
    d = mathutils.Vector(loc)-mathutils.Vector((cx,cy,cz))
    co.rotation_euler = d.to_track_quat('Z','Y').to_euler()
    if ortho_scale: c.type='ORTHO'; c.ortho_scale=ortho_scale
    else: c.lens=lens
    scene.camera=co
    scene.render.resolution_x=1600; scene.render.resolution_y=1000
    scene.render.filepath=os.path.join(HERE,"..","output","REALREF_"+name+".png")
    bpy.ops.render.render(write_still=True)
    print("SHOT", scene.render.filepath)
shoot((cx, cy-8, cz), "side", ortho_scale=L*1.15)
shoot((cx-8, cy, cz), "front", ortho_scale=2.6)
shoot((cx, cy, cz+8), "top", ortho_scale=L*1.15)
shoot((cx-4.5, cy-4.5, cz+2.6), "hero")
print("DONE")
