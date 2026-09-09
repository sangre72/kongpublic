import bpy, sys, os, json, math, mathutils
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import runner

def tri_count(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    total = 0
    for o in objs:
        if o.type != "MESH": continue
        me = o.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        total += len(me.loop_triangles)
    return total

def bbox(objs):
    mn = [1e9]*3; mx = [-1e9]*3
    for o in objs:
        if o.type != "MESH": continue
        for c in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(c)
            for i in range(3):
                mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
    return [mx[i]-mn[i] for i in range(3)], mn, mx

# 1. build bm56 (no render)
runner.do_render = lambda *a, **k: None
sys.argv = ["blender", "--", os.path.join(HERE, "..", "examples", "bm56_h.json")]
runner.main()
ours = [o for o in bpy.data.objects if o.type == "MESH" and o.name not in ("road",) and "plane" not in o.name.lower()]
ours_n = len(ours)
ours_tris = tri_count(ours)
ours_dim, ours_mn, ours_mx = bbox(ours)

# 2. import real GLB
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, "..", "examples", "tesla_model_y_REAL_mesh.glb"))
real = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
real_n = len(real)
real_tris = tri_count(real)
real_dim, real_mn, real_mx = bbox(real)

print("KBW_STATS ours_meshes=%d ours_tris=%d ours_dims_XYZ=%.3f,%.3f,%.3f" % (ours_n, ours_tris, *ours_dim))
print("KBW_STATS real_meshes=%d real_tris=%d real_dims_XYZ=%.3f,%.3f,%.3f" % (real_n, real_tris, *real_dim))
print("KBW_RATIO parts=%.1fx tris=%.1fx" % (real_n/max(ours_n,1), real_tris/max(ours_tris,1)))

# 3. side-by-side: scale real to same overall length (longest axis), place beside ours
ours_len = max(ours_dim); real_len = max(real_dim)
s = ours_len / real_len
root = bpy.data.objects.new("real_root", None)
bpy.context.scene.collection.objects.link(root)
for o in real:
    if o.parent is None:
        o.parent = root
# some glTF have hierarchy under empties; parent all top-level imported nodes
for o in bpy.data.objects:
    if o not in before and o.parent is None and o is not root:
        o.parent = root
root.scale = (s, s, s)
# align long axis: real GLB faces along +Y, ours along X → rotate -90° about Z
if real_dim[1] > real_dim[0]:
    root.rotation_euler = (0, 0, -math.pi/2)
bpy.context.view_layer.update()
rdim, rmn, rmx = bbox(real)
odim, omn, omx = ours_dim, ours_mn, ours_mx
# align: center both at z-min ground, offset real in +Y by (ours_widthY + gap)
root.location.x += ( (omn[0]+omx[0])/2 - (rmn[0]+rmx[0])/2 )
root.location.z += ( omn[2] - rmn[2] )
gap = odim[1]*1.4
root.location.y += ( (omn[1]+omx[1])/2 - (rmn[1]+rmx[1])/2 ) + gap
bpy.context.view_layer.update()

# 4. renders: 3/4 hero + pure side, both cars in frame
scene = bpy.context.scene
cam = scene.camera
allpts = []
for objs in (ours, real):
    d, mn, mx = bbox(objs)
    allpts += [mn, mx]
cx = sum(p[0] for p in allpts)/len(allpts); cy = sum(p[1] for p in allpts)/len(allpts); cz = sum(p[2] for p in allpts)/len(allpts)
span = max(max(p[0] for p in allpts)-min(p[0] for p in allpts), max(p[1] for p in allpts)-min(p[1] for p in allpts))
def shoot(loc, name, ortho=False):
    c = bpy.data.cameras.new(name); co = bpy.data.objects.new(name, c)
    scene.collection.objects.link(co); co.location = loc
    d = co.location - mathutils.Vector((cx, cy, cz))
    co.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    if ortho:
        c.type = 'ORTHO'; c.ortho_scale = span*1.3
    else:
        c.lens = 35
    scene.camera = co
    scene.render.resolution_x = 1600; scene.render.resolution_y = 1000
    scene.render.filepath = os.path.join(HERE, "..", "output", name + ".png")
    bpy.ops.render.render(write_still=True)
    print("KBW_SHOT", scene.render.filepath)

shoot((cx + span*1.1, cy - span*0.9, cz + span*0.6), "COMPARE_bm56_vs_real_hero")
shoot((cx + span*2.0, cy, cz + odim[2]*0.5), "COMPARE_bm56_vs_real_side", ortho=True)
print("KBW_DONE")
