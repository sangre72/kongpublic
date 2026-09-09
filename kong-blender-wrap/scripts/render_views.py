"""Render a kbwrap spec in 4 canonical views matching REALREF_* framing.
usage: blender --background --python scripts/render_views.py -- <spec.json> <prefix>
"""
import bpy, sys, os, math, mathutils
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import runner

args = sys.argv[sys.argv.index("--")+1:]
spec_path, prefix = args[0], args[1]
runner.do_render = lambda *a, **k: None
sys.argv = ["blender", "--", spec_path]
runner.main()

scene = bpy.context.scene
objs = [o for o in bpy.data.objects if o.type == "MESH" and o.name != "road"]
mn = [1e9]*3; mx = [-1e9]*3
for o in objs:
    for c in o.bound_box:
        w = o.matrix_world @ mathutils.Vector(c)
        for i in range(3):
            mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
cx, cy, cz = [(mn[i]+mx[i])/2 for i in range(3)]
L = mx[0]-mn[0]
def shoot(loc, name, ortho_scale=None, lens=40):
    c = bpy.data.cameras.new(name); co = bpy.data.objects.new(name, c)
    scene.collection.objects.link(co); co.location = loc
    d = mathutils.Vector(loc) - mathutils.Vector((cx, cy, cz))
    co.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    if ortho_scale: c.type = 'ORTHO'; c.ortho_scale = ortho_scale
    else: c.lens = lens
    scene.camera = co
    scene.render.resolution_x = 1600; scene.render.resolution_y = 1000
    scene.render.filepath = os.path.join(HERE, "..", "output", prefix + "_" + name + ".png")
    bpy.ops.render.render(write_still=True)
    print("SHOT", scene.render.filepath)
shoot((cx, cy-8, cz), "side", ortho_scale=L*1.15)
shoot((cx-8, cy, cz), "front", ortho_scale=2.6)
shoot((cx, cy, cz+8), "top", ortho_scale=L*1.15)
shoot((cx-4.5, cy-4.5, cz+2.6), "hero")
print("DONE")
