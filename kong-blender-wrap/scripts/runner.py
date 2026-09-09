"""
kong-blender-wrap runner — executes INSIDE Blender's python (bpy available).
Invoked headless by kbwrap.py as:
    blender --background --python runner.py -- <job_spec.json>
Reads a job spec (list of ops) and applies them via bpy, then renders.

This file is DATA-DRIVEN: kbwrap.py (system python) builds the JSON spec from
high-level CLI commands; this side just interprets it. Keep bpy usage here only.
"""
import bpy
import sys
import json
import math
import mathutils
import bmesh


def _argv_after_dashes():
    # Blender passes script args after a lone '--'
    argv = sys.argv
    return argv[argv.index("--") + 1:] if "--" in argv else []


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # ambient world light so materials (esp. metallic) don't render black in headless.
    world = bpy.data.worlds.new("kbw_world")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.55, 0.62, 0.72, 1.0)  # soft sky-grey
        bg.inputs["Strength"].default_value = 0.6
    bpy.context.scene.world = world


def set_world(op):
    """Override world background color/strength. op:{op:'world', color:[r,g,b], strength:N}"""
    world = bpy.context.scene.world
    bg = world.node_tree.nodes.get("Background")
    if bg:
        c = op.get("color", [0.55, 0.62, 0.72])
        bg.inputs["Color"].default_value = (c[0], c[1], c[2], 1.0)
        bg.inputs["Strength"].default_value = op.get("strength", 0.6)


def add_object(op):
    kind = op.get("kind", "cube")
    loc = tuple(op.get("location", [0, 0, 0]))
    size = op.get("size", 2.0)
    if kind == "cube":
        bpy.ops.mesh.primitive_cube_add(size=size, location=loc)
    elif kind == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=size / 2, location=loc)
    elif kind == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(radius=size / 2, depth=size, location=loc)
    elif kind == "cone":
        bpy.ops.mesh.primitive_cone_add(radius1=size / 2, depth=size, location=loc)
    elif kind == "plane":
        bpy.ops.mesh.primitive_plane_add(size=size, location=loc)
    elif kind == "monkey":
        bpy.ops.mesh.primitive_monkey_add(size=size, location=loc)
    elif kind == "torus":
        bpy.ops.mesh.primitive_torus_add(location=loc,
                                         major_radius=size / 2, minor_radius=size / 6)
    else:
        raise ValueError(f"unknown object kind: {kind}")
    obj = bpy.context.active_object
    if op.get("name"):
        obj.name = op["name"]
    if op.get("scale"):
        s = op["scale"]
        obj.scale = (s[0], s[1], s[2])
    if op.get("rotation"):
        obj.rotation_euler = [math.radians(a) for a in op["rotation"]]
    color = op.get("color")
    if color:
        mat = bpy.data.materials.new(name="kbw_mat")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            r, g, b = color[:3]
            bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
        obj.data.materials.append(mat)
    # per-object smooth shading (a_4170 selective-smoothing): round parts (wheels/arches) set
    # smooth:true → look round; body panels stay flat-shaded. default false = flat (crisp facets).
    if op.get("smooth", False):
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


def _resolve(target):
    """target = object name (str) or 'camera'. returns the bpy object."""
    if target == "camera":
        return bpy.context.scene.camera
    return bpy.data.objects.get(target)


# ─────────────────────────────────────────────────────────────────────────────
# PANEL / EDGE-LOOP SURFACING OPS (a_4170) — post-process a lofted body to add
# arbitrary CHARACTER-LINES and PANEL SEAMS that box_model's ring topology can't.
# Core mechanism: bisect_plane cuts an arbitrary plane → a new edge-loop exactly
# where a line/seam goes, independent of the ring loops. Then bevel/crease it.
# ─────────────────────────────────────────────────────────────────────────────

def _bm_from(obj):
    bm = bmesh.new(); bm.from_mesh(obj.data); return bm

def _bm_to(bm, obj):
    bm.normal_update(); bm.to_mesh(obj.data); bm.free()

def _bisect_collect(bm, plane_co, plane_no):
    """bisect the whole bmesh along a plane, keeping both halves; return the NEW cut edges."""
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5,
                                 plane_co=plane_co, plane_no=plane_no,
                                 clear_inner=False, clear_outer=False)
    return [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]

def crease_line(op):
    """Arbitrary character-line on an existing body via bisect(s) + bevel + crease.
    op: {op:'crease_line', target,
         plane_series:[{co:[x,y,z], no:[nx,ny,nz]}...]  OR
         path:[[x,y,z]...] (world polyline → swept bisect planes, normal ⟂ tangent in +z-cross),
         bevel:{offset,segments,profile}, crease:0..1,
         limit:{x:[lo,hi]} optional — only crease cut-edges whose midpoint x∈range (localize the line)}"""
    obj = _resolve(op["target"])
    if not obj or obj.type != "MESH":
        print("KBW_WARN: crease_line target invalid"); return
    bm = _bm_from(obj)
    # bmesh verts are in LOCAL space; path/planes come in WORLD space → transform to local.
    inv = obj.matrix_world.inverted()
    inv3 = inv.to_3x3()
    def w2l_co(v): return inv @ mathutils.Vector(v)
    def w2l_no(v): return (inv3 @ mathutils.Vector(v)).normalized()
    planes = [{"co": list(w2l_co(pl["co"])), "no": list(w2l_no(pl["no"]))}
              for pl in op.get("plane_series", [])]
    if op.get("path"):
        p = [list(w2l_co(pt)) for pt in op["path"]]
        for i in range(len(p) - 1):
            a = mathutils.Vector(p[i]); b = mathutils.Vector(p[i + 1])
            mid = (a + b) * 0.5
            tang = (b - a).normalized()
            # The cut plane must CONTAIN the path segment (so the new loop follows the line) and be
            # roughly perpendicular to the body surface at the line. `sweep_axis` (default +Y = flank
            # normal for a side line) sets which way the plane faces; the plane normal is then
            # perpendicular to BOTH the tangent and that surface-out axis → the cut runs along the path
            # around the body. For a horizontal beltline (tangent≈X, surface-out≈Y) this gives normal≈Z
            # (a horizontal loop). For a vertical pillar line, pass sweep_axis:[1,0,0].
            surf = w2l_no(op.get("sweep_axis", [0, 1, 0]))
            no = tang.cross(surf)
            if no.length < 1e-6:
                no = mathutils.Vector((0, 0, 1))
            planes.append({"co": list(mid), "no": list(no.normalized())})
    lim = op.get("limit", {}).get("x")
    all_cut = []
    for pl in planes:
        cut = _bisect_collect(bm, tuple(pl["co"]), tuple(pl["no"]))
        if lim:
            cut = [e for e in cut if lim[0] <= (e.verts[0].co.x + e.verts[1].co.x) * 0.5 <= lim[1]]
        all_cut += cut
    all_cut = list({e.index: e for e in all_cut if e.is_valid}.values())
    bv = op.get("bevel")
    if bv and all_cut:
        bmesh.ops.bevel(bm, geom=all_cut, offset=bv.get("offset", 0.02),
                        segments=bv.get("segments", 1), profile=bv.get("profile", 0.7),
                        affect="EDGES")
    cw = op.get("crease")
    if cw is not None and all_cut:
        cl = bm.edges.layers.float.get("crease_edge") or bm.edges.layers.float.new("crease_edge")
        for e in all_cut:
            if e.is_valid: e[cl] = cw
    _bm_to(bm, obj)
    print(f"KBW: crease_line '{op['target']}' — {len(planes)} plane(s), {len(all_cut)} cut edges")
    return obj

def panel_cut(op):
    """Separate the skin into panels along bisect planes, with an optional shut-line gap.
    op: {op:'panel_cut', target, cuts:[{co,no}...], gap:0.004 (inset seam faces), crease:0..1}"""
    obj = _resolve(op["target"])
    if not obj or obj.type != "MESH":
        print("KBW_WARN: panel_cut target invalid"); return
    bm = _bm_from(obj)
    inv = obj.matrix_world.inverted(); inv3 = inv.to_3x3()
    seam_edges = []
    for c in op.get("cuts", []):
        co = inv @ mathutils.Vector(c["co"])
        no = (inv3 @ mathutils.Vector(c["no"])).normalized()
        seam_edges += _bisect_collect(bm, tuple(co), tuple(no))
    seam_edges = [e for e in seam_edges if e.is_valid]
    if op.get("gap"):
        # inset the faces adjacent to the seam inward → a visible reveal line
        faces = list({f.index: f for e in seam_edges for f in e.link_faces}.values())
        if faces:
            bmesh.ops.inset_region(bm, faces=faces, thickness=op["gap"], depth=-op["gap"])
    cw = op.get("crease")
    if cw is not None and seam_edges:
        cl = bm.edges.layers.float.get("crease_edge") or bm.edges.layers.float.new("crease_edge")
        for e in seam_edges:
            if e.is_valid: e[cl] = cw
    _bm_to(bm, obj)
    print(f"KBW: panel_cut '{op['target']}' — {len(op.get('cuts',[]))} cut(s), {len(seam_edges)} seam edges")
    return obj

def panel_recess(op):
    """Bounded inset+push-in for a window frame / grille / light housing.
    op: {op:'panel_recess', target, face_normal:[x,y,z] (select faces facing this ±),
         x_range:[lo,hi], z_range:[lo,hi], thickness, depth}"""
    obj = _resolve(op["target"])
    if not obj or obj.type != "MESH":
        print("KBW_WARN: panel_recess target invalid"); return
    bm = _bm_from(obj)
    nrm = mathutils.Vector(op.get("face_normal", [0, 1, 0])).normalized()
    xr = op.get("x_range", [-1e9, 1e9]); zr = op.get("z_range", [-1e9, 1e9])
    sel = []
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.normalized().dot(nrm) > 0.5 and xr[0] <= c.x <= xr[1] and zr[0] <= c.z <= zr[1]:
            sel.append(f)
    if sel:
        bmesh.ops.inset_region(bm, faces=sel, thickness=op.get("thickness", 0.02),
                               depth=-abs(op.get("depth", 0.02)))
    _bm_to(bm, obj)
    print(f"KBW: panel_recess '{op['target']}' — {len(sel)} faces recessed")
    return obj


def _aim_camera_at(cam, look_at):
    direction = mathutils.Vector(look_at) - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


def mesh_from_profile(op):
    """Build ONE continuous solid from a 2D side-profile (list of [x,z] points, CCW outline),
    extruded symmetrically along Y to `width`. Bmesh-based (precise vertex construction, no
    edit-mode-op fragility). This is the real fix for a continuous car silhouette (hood→windshield
    →roof→fastback→rear as one flowing surface, vs 2 boolean-unioned boxes).
    op: {op:'profile', name, profile:[[x,z],...], width, location:[x,y,z], color, ...}"""
    prof = op["profile"]
    half = op.get("width", 1.0) / 2.0
    yb = op.get("location", [0, 0, 0])[1]
    mesh = bpy.data.meshes.new(op["name"])
    bm = bmesh.new()
    n = len(prof)
    left = [bm.verts.new((x, yb - half, z)) for (x, z) in prof]
    right = [bm.verts.new((x, yb + half, z)) for (x, z) in prof]
    bm.verts.ensure_lookup_table()
    # side walls (the profile faces on each side)
    bm.faces.new(left)
    bm.faces.new(list(reversed(right)))
    # connect the two profiles into a closed tube (quads between consecutive profile edges)
    for i in range(n):
        a, b = left[i], left[(i + 1) % n]
        c, d = right[(i + 1) % n], right[i]
        bm.faces.new((a, b, c, d))
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(op["name"], mesh)
    loc = op.get("location", [0, 0, 0])
    obj.location = (loc[0], 0, loc[2])   # y already baked into verts
    bpy.context.collection.objects.link(obj)
    # smoothing modifiers optional
    if op.get("bevel"):
        m = obj.modifiers.new(name="bevel", type="BEVEL")
        m.width = op["bevel"]; m.segments = op.get("bevel_segments", 2)
    if op.get("subdivide"):
        m = obj.modifiers.new(name="subsurf", type="SUBSURF")
        m.levels = op["subdivide"]; m.render_levels = op["subdivide"]
    if op.get("smooth", True):
        for p in obj.data.polygons:
            p.use_smooth = True
    color = op.get("color")
    if color:
        mat = bpy.data.materials.new(name=f"kbw_{obj.name}")
        mat.use_nodes = True
        b = mat.node_tree.nodes.get("Principled BSDF")
        if b:
            b.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
            if "metallic" in op: b.inputs["Metallic"].default_value = op["metallic"]
            if "roughness" in op: b.inputs["Roughness"].default_value = op["roughness"]
        obj.data.materials.append(mat)
    return obj


def box_model(op):
    """TRUE multi-view box-model (a_3856): build a mesh by TRIANGULATING two orthographic views.
    - side_outline: [[x,z],...] closed side silhouette (length x height) — from the SIDE ref.
    - front_widthcurve: [[z_frac, halfwidth_frac],...] width-vs-height from the FRONT ref
      (z_frac 0=bottom..1=top of body; halfwidth_frac 0..1 relative to max half-width = TUMBLEHOME).
    at each x-station, cross-section height range = side-outline [zbot..ztop] at that x; the width at
    each height = base_halfwidth * front_widthcurve(interpolated at that height's z_frac). so WIDTH
    comes from the FRONT view + LENGTH/HEIGHT from the SIDE view = real 2-view triangulation, not one
    silhouette. rings bridged into a closed solid (bmesh), ends capped.
    op: {op:'box', name, side_outline, front_widthcurve, base_halfwidth, x_stations:[...], subdivide, ...}"""
    side = op["side_outline"]
    fwc = sorted(op["front_widthcurve"])          # [(zfrac, hwfrac)]
    base_hw = op.get("base_halfwidth", 0.9)
    xs = [p[0] for p in side]; xmin, xmax = min(xs), max(xs)
    tops = sorted([p for p in side if p[1] > 0.45]); bots = sorted([p for p in side if p[1] <= 0.45])
    def _interp(pts, xq):
        for i in range(len(pts) - 1):
            if pts[i][0] <= xq <= pts[i + 1][0]:
                (x0, z0), (x1, z1) = pts[i], pts[i + 1]
                t = (xq - x0) / (x1 - x0 + 1e-9); return z0 + t * (z1 - z0)
        return min(pts, key=lambda p: abs(p[0] - xq))[1]
    def top_at(xq): return _interp(tops, xq)
    def bot_at(xq): return _interp(bots, xq)
    def width_frac(zf):                            # front-view tumblehome at height-frac zf
        zf = max(0.0, min(1.0, zf))
        for i in range(len(fwc) - 1):
            if fwc[i][0] <= zf <= fwc[i + 1][0]:
                (a0, w0), (a1, w1) = fwc[i], fwc[i + 1]
                t = (zf - a0) / (a1 - a0 + 1e-9); return w0 + t * (w1 - w0)
        return fwc[min(range(len(fwc)), key=lambda i: abs(fwc[i][0] - zf))][1]
    # nose/tail length taper (front-view width applies to mid; ends narrow).
    # `end_bluntness` (0..1, default 0 = original mild taper) keeps the bumpers WIDE so
    # nose/tail read as blunt vertical faces (SUV/Model-Y) instead of pinching to a point
    # (a_4170: pointed ends = beetle tell; Model Y front/rear are near-full-width blunt walls).
    _blunt = op.get("end_bluntness", 0.0)
    def x_taper(xq):
        t = (xq - xmin) / (xmax - xmin)
        f = 1.0 - 0.30 * (2 * t - 1) ** 2
        if t > 0.9: f *= 0.8
        if t < 0.08: f *= 0.85
        # lerp toward 1.0 (no taper = full-width blunt end) by end_bluntness
        return f + (1.0 - f) * _blunt
    NV = op.get("ring_verts", 14)  # verts per ring (up one side, across top, down other) — even.
    if NV % 2: NV += 1              # denser rings (a_4170) = finer facets that hold flatness under subdiv
    # ★a_4170: higher ring_verts + low subdivide preserves the box cross-section (flat door-sides,
    # crisp shoulder) that a coarse 14-vert ring loses to smoothing. widthcurve sets the SHAPE;
    # ring_verts sets how many flat facets sample it; subdivide sets how much they round.
    mesh = bpy.data.meshes.new(op["name"]); bm = bmesh.new()
    rings = []
    for xq in op["x_stations"]:
        zt, zb = top_at(xq), bot_at(xq); hwmax = base_hw * x_taper(xq)
        # build a closed ring: sample heights bottom->top on +y side, then top->bottom on -y side
        heights = [zb + (zt - zb) * (k / (NV // 2 - 1)) for k in range(NV // 2)]
        ring = []
        for z in heights:                          # +y side, bottom to top
            zf = (z - zb) / (zt - zb + 1e-9)
            ring.append(bm.verts.new((xq, hwmax * width_frac(zf), z)))
        for z in reversed(heights):                # -y side, top to bottom
            zf = (z - zb) / (zt - zb + 1e-9)
            ring.append(bm.verts.new((xq, -hwmax * width_frac(zf), z)))
        rings.append(ring)
    bm.verts.ensure_lookup_table()
    n = len(rings[0])
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bm.normal_update()
    # ── EDGE-CREASE (a_4170): hold crisp beltline / roof-rail through subsurf while
    #    sides+roof stay smooth. `crease_bands` = list of {z_frac:[lo,hi], x_range:[lo,hi], weight}
    #    creases the HORIZONTAL ring-to-ring edges whose vert z-fraction ∈ band (both y sides),
    #    over the x_range. NV//2 height samples per side → height-index k maps to z_frac k/(NV//2-1).
    #    This is the missing edge-crease op the recipe flagged: crisp beltline = window reads as
    #    a side-window, crisp roof-rail = flat SUV roof holds instead of doming.
    bands = op.get("crease_bands")
    if bands:
        # Blender 4.x: edge crease is a named float layer 'crease_edge' (old bm.edges.layers.crease removed)
        cl = bm.edges.layers.float.get("crease_edge") or bm.edges.layers.float.new("crease_edge")
        half = NV // 2
        xstations = op["x_stations"]
        def zf_of_index(i):   # ring index i → z_frac (0=bottom..1=top), symmetric across the two y-sides
            if i < half: return i / (half - 1)
            return (2 * half - 1 - i) / (half - 1)
        for a, b in zip(rings[:-1], rings[1:]):
            # x of this ring-pair (use a's station)
            xa = xstations[rings.index(a)] if False else None
        # simpler: iterate stations paired
        for si in range(len(rings) - 1):
            a, b = rings[si], rings[si + 1]
            xmid = 0.5 * (xstations[si] + xstations[si + 1])
            for i in range(n):
                # world-z of this vert (avg the ring-pair) — a real beltline is constant WORLD-z,
                # not constant z_frac (roof height varies → z_frac drifts, a_4170 finding)
                zw = 0.5 * (a[i].co.z + b[i].co.z)
                zf = zf_of_index(i)
                for bd in bands:
                    xlo, xhi = bd.get("x_range", [xmin, xmax])
                    if not (xlo <= xmid <= xhi):
                        continue
                    ok = False
                    if "z_world" in bd:
                        zlo, zhi = bd["z_world"]; ok = zlo <= zw <= zhi
                    else:
                        zlo, zhi = bd["z_frac"]; ok = zlo <= zf <= zhi
                    if ok:
                        e = bm.edges.get((a[i], b[i]))
                        if e: e[cl] = bd.get("weight", 1.0)
        # vertical pillar creases (A/C-pillar): crease WITHIN-ring edges at given x-stations
        pillars = op.get("crease_pillars")  # list of x positions
        if pillars:
            for si, xs_ in enumerate(xstations):
                if any(abs(xs_ - px) < 0.08 for px in pillars):
                    ring = rings[si]
                    for i in range(n - 1):
                        e = bm.edges.get((ring[i], ring[i + 1]))
                        if e: e[cl] = max(e[cl], 0.5)
    bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new(op["name"], mesh); bpy.context.collection.objects.link(obj)
    if op.get("subdivide"):
        m = obj.modifiers.new(name="subsurf", type="SUBSURF"); m.levels = op["subdivide"]; m.render_levels = op["subdivide"]
    if op.get("smooth", True):
        for p in obj.data.polygons: p.use_smooth = True
    color = op.get("color")
    if color:
        mat = bpy.data.materials.new(name=f"kbw_{obj.name}"); mat.use_nodes = True
        b = mat.node_tree.nodes.get("Principled BSDF")
        if b:
            b.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
            if "metallic" in op: b.inputs["Metallic"].default_value = op["metallic"]
            if "roughness" in op: b.inputs["Roughness"].default_value = op["roughness"]
        obj.data.materials.append(mat)
    return obj


def loft_sections(op):
    """Build ONE smooth doubly-curved solid by LOFTING between width-varying cross-sections.
    Fixes the constant-width `profile` boxiness: a car curves in BOTH side-profile AND plan
    (width) — loft interpolates a closed body between rings at different x positions.
    op: {op:'loft', name, sections:[{x, section:[[y,z],...]} ...] (each = a closed cross-section
         outline in the Y-Z plane at that x; same vert-count per section, ordered consistently),
         subdivide, bevel, smooth, color/metallic/roughness}
    Sections ordered front→rear (or any monotone x). Ends are capped."""
    secs = op["sections"]
    n = len(secs[0]["section"])
    mesh = bpy.data.meshes.new(op["name"])
    bm = bmesh.new()
    rings = []
    for sc in secs:
        x = sc["x"]
        ring = [bm.verts.new((x, y, z)) for (y, z) in sc["section"]]
        rings.append(ring)
    bm.verts.ensure_lookup_table()
    # bridge consecutive rings with quads
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    # cap front + rear (fan)
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bm.normal_update()
    bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new(op["name"], mesh)
    bpy.context.collection.objects.link(obj)
    if op.get("bevel"):
        m = obj.modifiers.new(name="bevel", type="BEVEL"); m.width = op["bevel"]; m.segments = op.get("bevel_segments", 2)
    if op.get("subdivide"):
        m = obj.modifiers.new(name="subsurf", type="SUBSURF"); m.levels = op["subdivide"]; m.render_levels = op["subdivide"]
    if op.get("smooth", True):
        for p in obj.data.polygons: p.use_smooth = True
    color = op.get("color")
    if color:
        mat = bpy.data.materials.new(name=f"kbw_{obj.name}"); mat.use_nodes = True
        b = mat.node_tree.nodes.get("Principled BSDF")
        if b:
            b.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
            if "metallic" in op: b.inputs["Metallic"].default_value = op["metallic"]
            if "roughness" in op: b.inputs["Roughness"].default_value = op["roughness"]
        obj.data.materials.append(mat)
    return obj


def make_group(op):
    """Parent multiple named objects under a new empty, so they move as one rig.
    op: {op:'group', name:'car', members:['body','wheel1',...], location:[x,y,z]}
    The empty (named op.name) can then be a `move`/`spin` target."""
    loc = tuple(op.get("location", [0, 0, 0]))
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=loc)
    empty = bpy.context.active_object
    empty.name = op["name"]
    for m in op.get("members", []):
        obj = bpy.data.objects.get(m)
        if obj:
            obj.parent = empty
            obj.matrix_parent_inverse = empty.matrix_world.inverted()
    return empty


def apply_motion(op, frame_start, frame_end):
    """Keyframe a motion primitive across [frame_start, frame_end]."""
    kind = op["motion"]
    scene = bpy.context.scene
    if kind == "orbit_camera":
        # camera circles the subject on the XY plane at fixed height, always aiming at center
        cam = bpy.context.scene.camera
        center = mathutils.Vector(op.get("center", [0, 0, 0]))
        radius = op.get("radius", 8.0)
        height = op.get("height", 4.0)
        turns = op.get("turns", 1.0)
        for f in range(frame_start, frame_end + 1):
            t = (f - frame_start) / max(1, (frame_end - frame_start))
            ang = t * turns * 2 * math.pi
            cam.location = (center.x + radius * math.cos(ang),
                            center.y + radius * math.sin(ang),
                            center.z + height)
            _aim_camera_at(cam, center)
            cam.keyframe_insert(data_path="location", frame=f)
            cam.keyframe_insert(data_path="rotation_euler", frame=f)
    elif kind == "orbit":
        # object circles a center point on the XY plane
        obj = _resolve(op["target"])
        center = mathutils.Vector(op.get("center", [0, 0, 0]))
        radius = op.get("radius", 4.0)
        height = op.get("height", 0.0)
        turns = op.get("turns", 1.0)
        for f in range(frame_start, frame_end + 1):
            t = (f - frame_start) / max(1, (frame_end - frame_start))
            ang = t * turns * 2 * math.pi
            obj.location = (center.x + radius * math.cos(ang),
                            center.y + radius * math.sin(ang),
                            center.z + height)
            obj.keyframe_insert(data_path="location", frame=f)
    elif kind == "move":
        obj = _resolve(op["target"])
        a = mathutils.Vector(op["from"]); b = mathutils.Vector(op["to"])
        obj.location = a; obj.keyframe_insert(data_path="location", frame=frame_start)
        obj.location = b; obj.keyframe_insert(data_path="location", frame=frame_end)
    elif kind == "spin":
        obj = _resolve(op["target"])
        axis = op.get("axis", "Z"); turns = op.get("turns", 1.0)
        idx = {"X": 0, "Y": 1, "Z": 2}[axis]
        e0 = list(obj.rotation_euler)
        obj.rotation_euler = e0; obj.keyframe_insert(data_path="rotation_euler", frame=frame_start)
        e1 = list(e0); e1[idx] += turns * 2 * math.pi
        obj.rotation_euler = e1; obj.keyframe_insert(data_path="rotation_euler", frame=frame_end)
    elif kind == "scale":
        obj = _resolve(op["target"])
        s0 = op.get("from", 1.0); s1 = op.get("to", 2.0)
        obj.scale = (s0, s0, s0); obj.keyframe_insert(data_path="scale", frame=frame_start)
        obj.scale = (s1, s1, s1); obj.keyframe_insert(data_path="scale", frame=frame_end)
    else:
        print(f"KBW_WARN: unknown motion '{kind}' skipped")
    # linear interpolation for smooth constant motion
    for obj in bpy.data.objects:
        if obj.animation_data and obj.animation_data.action:
            for fc in obj.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = 'LINEAR'


def add_camera(op):
    loc = tuple(op.get("location", [7.0, -7.0, 5.0]))
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.active_object
    look_at = op.get("look_at", [0, 0, 0])
    # point camera at target
    import mathutils
    direction = mathutils.Vector(look_at) - mathutils.Vector(loc)
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    # orthographic option (a_4170): ortho side render = geometry-accurate silhouette for
    # pixel-trace comparison vs the ref (perspective distorts the trace). {ortho:true, ortho_scale:N}
    if op.get("ortho"):
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = op.get("ortho_scale", 5.0)
    bpy.context.scene.camera = cam
    return cam


def ref_plane(op):
    """Load a reference photo as a Blender Empty-Image plane in 3D space (real 'reference image'
    workflow, scriptable). Scaled so the car's pixel-length maps to a known world length → the
    silhouette can be traced/verified directly against it in an ortho side render.
    op: {op:'ref_plane', image:'<abs path>', size (world height of the image), location, rotation}"""
    img = bpy.data.images.load(op["image"])
    empty = bpy.data.objects.new(op.get("name", "ref"), None)
    empty.empty_display_type = 'IMAGE'
    empty.data = img
    empty.empty_display_size = op.get("size", 4.0)
    empty.location = tuple(op.get("location", [0, 0.9, 0.9]))
    # default: face the -Y side camera (image in the X-Z plane)
    rot = op.get("rotation", [90, 0, 0])
    empty.rotation_euler = [math.radians(a) for a in rot]
    empty.use_empty_image_alpha = True
    empty.color[3] = op.get("opacity", 0.5)
    bpy.context.collection.objects.link(empty)
    return empty


def add_light(op):
    loc = tuple(op.get("location", [4.0, -4.0, 8.0]))
    energy = op.get("energy", 1000.0)
    ltype = op.get("light_type", "SUN")
    bpy.ops.object.light_add(type=ltype, location=loc)
    light = bpy.context.active_object
    light.data.energy = energy
    return light


def set_material(op):
    """Real PBR material on an existing named object via Principled BSDF."""
    obj = _resolve(op["target"])
    if obj is None:
        print(f"KBW_WARN: material target '{op.get('target')}' not found")
        return
    mat = bpy.data.materials.new(name=f"kbw_{obj.name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        c = op.get("color", [0.8, 0.8, 0.8])
        bsdf.inputs["Base Color"].default_value = (c[0], c[1], c[2], 1.0)
        if "roughness" in op:
            bsdf.inputs["Roughness"].default_value = op["roughness"]
        if "metallic" in op:
            bsdf.inputs["Metallic"].default_value = op["metallic"]
        if "emission" in op:
            e = op["emission"]
            # emission color + strength (input names vary by version)
            for cn in ("Emission Color", "Emission"):
                if cn in bsdf.inputs:
                    bsdf.inputs[cn].default_value = (e[0], e[1], e[2], 1.0)
                    break
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = op.get("emission_strength", 3.0)
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def add_text(op):
    """3D text object."""
    loc = tuple(op.get("location", [0, 0, 0]))
    bpy.ops.object.text_add(location=loc)
    txt = bpy.context.active_object
    txt.data.body = op.get("body", "TEXT")
    txt.data.extrude = op.get("extrude", 0.1)
    txt.data.align_x = op.get("align", "CENTER")
    txt.data.size = op.get("size", 1.0)
    if op.get("name"):
        txt.name = op["name"]
    if op.get("rotation"):
        import math as _m
        txt.rotation_euler = [_m.radians(a) for a in op["rotation"]]
    color = op.get("color")
    if color:
        mat = bpy.data.materials.new(name="kbw_text")
        mat.use_nodes = True
        b = mat.node_tree.nodes.get("Principled BSDF")
        if b:
            b.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
        txt.data.materials.append(mat)
    return txt


def modify_mesh(op):
    """Mesh-edit ops on an existing object: subdivide / bevel / shade_smooth."""
    obj = _resolve(op["target"])
    if obj is None:
        print(f"KBW_WARN: modify target '{op.get('target')}' not found")
        return
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    mod = op.get("modify")
    if mod == "subdivide":
        m = obj.modifiers.new(name="subsurf", type="SUBSURF")
        m.levels = op.get("levels", 2)
        m.render_levels = op.get("levels", 2)
    elif mod == "bevel":
        m = obj.modifiers.new(name="bevel", type="BEVEL")
        m.width = op.get("width", 0.1)
        m.segments = op.get("segments", 3)
    elif mod == "smooth":
        bpy.ops.object.shade_smooth()
    elif mod == "loop_cut":
        # add N evenly-spaced edge loops along the object (subdiv in edit mode)
        cuts = op.get("cuts", 1)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.subdivide(number_cuts=cuts)
        bpy.ops.object.mode_set(mode="OBJECT")
    elif mod == "taper":
        # scale the +axis end faces toward center → sloped/tapered form (roofline).
        # axis: 'x'/'y'/'z', end: 'max'/'min', factor: 0..1 (how much to shrink that end)
        axis = {"x": 0, "y": 1, "z": 2}[op.get("axis", "x")]
        end = op.get("end", "max")
        factor = op.get("factor", 0.5)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")
        import mathutils as _mu
        me = obj.data
        coords = [v.co[axis] for v in me.vertices]
        lo, hi = min(coords), max(coords)
        thresh = hi - (hi - lo) * 0.4 if end == "max" else lo + (hi - lo) * 0.4
        # shrink the perpendicular dims of verts at that end toward the axis-line center
        perp = [i for i in range(3) if i != axis]
        cx = sum(v.co[perp[0]] for v in me.vertices) / len(me.vertices)
        cy = sum(v.co[perp[1]] for v in me.vertices) / len(me.vertices)
        for v in me.vertices:
            at_end = v.co[axis] >= thresh if end == "max" else v.co[axis] <= thresh
            if at_end:
                v.co[perp[0]] = cx + (v.co[perp[0]] - cx) * factor
                v.co[perp[1]] = cy + (v.co[perp[1]] - cy) * factor
    else:
        print(f"KBW_WARN: unknown modify '{mod}'")


def inset_faces(op):
    """bmesh face-inset to create panel-line / door-seam recesses.
    op: {op:'inset', target, select_dir:[x,y,z] (face-normal filter, e.g. side [0,1,0]),
         thickness, depth (negative=recess in), z_range:[lo,hi] optional band filter}"""
    obj = _resolve(op["target"])
    if obj is None or obj.type != "MESH":
        print(f"KBW_WARN: inset target invalid"); return
    me = obj.data
    bm = bmesh.new(); bm.from_mesh(me)
    d = op.get("select_dir")
    zr = op.get("z_range")
    sel = []
    for f in bm.faces:
        ok = True
        if d:
            n = f.normal
            dot = n.x * d[0] + n.y * d[1] + n.z * d[2]
            ok = dot > op.get("dir_thresh", 0.5)
        if ok and zr:
            zc = sum(v.co.z for v in f.verts) / len(f.verts)
            ok = zr[0] <= zc <= zr[1]
        if ok:
            sel.append(f)
    if sel:
        res = bmesh.ops.inset_individual(bm, faces=sel,
                                         thickness=op.get("thickness", 0.03),
                                         depth=op.get("depth", -0.02))
    bm.to_mesh(me); bm.free()
    print(f"KBW: inset {len(sel)} faces on {obj.name}")


def mirror_object(op):
    """Non-destructive mirror modifier. op:{op:'mirror', target, axis:'x'|'y'|'z', merge}"""
    obj = _resolve(op["target"])
    if obj is None:
        print(f"KBW_WARN: mirror target not found"); return
    m = obj.modifiers.new(name="mirror", type="MIRROR")
    ax = op.get("axis", "y")
    m.use_axis[0] = ax == "x"
    m.use_axis[1] = ax == "y"
    m.use_axis[2] = ax == "z"
    m.use_mirror_merge = op.get("merge", False)
    # mirror about WORLD origin (car centerline), not the object's own local origin,
    # so a part placed off-center (e.g. left mirror at y=+0.9) reflects to the other side.
    if op.get("mirror_object"):
        mo = bpy.data.objects.get(op["mirror_object"])
        if mo: m.mirror_object = mo
    elif op.get("world_center", True):
        piv = bpy.data.objects.get("kbw_mirror_pivot")
        if piv is None:
            bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
            piv = bpy.context.active_object
            piv.name = "kbw_mirror_pivot"
        m.mirror_object = piv
    if op.get("apply", True):
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=m.name)


def boolean_op(op):
    """Boolean between two named objects. op:{op:'boolean', target, tool, operation:'UNION'|'DIFFERENCE'|'INTERSECT', delete_tool}"""
    obj = _resolve(op["target"]); tool = _resolve(op["tool"])
    if obj is None or tool is None:
        print(f"KBW_WARN: boolean target/tool not found"); return
    m = obj.modifiers.new(name="bool", type="BOOLEAN")
    m.operation = op.get("operation", "UNION")
    m.object = tool
    m.solver = "EXACT"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=m.name)
    if op.get("delete_tool", True):
        bpy.data.objects.remove(tool, do_unlink=True)


def uv_unwrap(op):
    """Auto UV-unwrap an existing object (smart UV project)."""
    obj = _resolve(op["target"])
    if obj is None or obj.type != "MESH":
        print(f"KBW_WARN: uv target '{op.get('target')}' not a mesh")
        return
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    method = op.get("method", "smart")
    if method == "smart":
        bpy.ops.uv.smart_project(angle_limit=op.get("angle_limit", 1.15))
    elif method == "cube":
        bpy.ops.uv.cube_project()
    elif method == "sphere":
        bpy.ops.uv.sphere_project()
    else:
        bpy.ops.uv.unwrap()
    bpy.ops.object.mode_set(mode="OBJECT")


def apply_camera_path(op, frame_start, frame_end):
    """Multi-keypoint camera path: list of {frame_frac, location, look_at}."""
    cam = bpy.context.scene.camera
    pts = op["points"]
    for p in pts:
        frac = p.get("frame_frac", 0.0)
        f = int(frame_start + frac * (frame_end - frame_start))
        cam.location = tuple(p["location"])
        _aim_camera_at(cam, p.get("look_at", [0, 0, 0]))
        cam.keyframe_insert(data_path="location", frame=f)
        cam.keyframe_insert(data_path="rotation_euler", frame=f)


def _enable_cycles_metal():
    """Safety net: if Cycles is ever used, force GPU/Metal (Cycles defaults to CPU)."""
    try:
        prefs = bpy.context.preferences.addons.get("cycles")
        if not prefs:
            return "no-cycles-addon"
        cprefs = prefs.preferences
        cprefs.compute_device_type = "METAL"
        cprefs.get_devices()
        enabled = []
        for dev in cprefs.devices:
            # enable Metal GPU devices, leave CPU off (or on as fallback)
            if dev.type == "METAL":
                dev.use = True; enabled.append(dev.name)
            elif dev.type == "CPU":
                dev.use = False
        return "METAL:" + ",".join(enabled) if enabled else "METAL-no-device"
    except Exception as e:
        return f"metal-cfg-fail:{e}"


def _set_engine():
    scene = bpy.context.scene
    chosen = None
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
        try:
            scene.render.engine = eng
            chosen = eng
            break
        except (TypeError, Exception):
            continue
    if chosen == "CYCLES":
        metal = _enable_cycles_metal()
        scene.cycles.device = "GPU"
        print(f"KBW_ENGINE: CYCLES device=GPU metal={metal}")
    else:
        print(f"KBW_ENGINE: {chosen} (EEVEE=GPU/Metal by default on macOS)")


def do_render(op, out_path):
    scene = bpy.context.scene
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = out_path
    scene.render.resolution_x = op.get("width", 640)
    scene.render.resolution_y = op.get("height", 480)
    scene.render.resolution_percentage = 100
    _set_engine()
    scene.render.film_transparent = op.get("transparent", False)
    bpy.ops.render.render(write_still=True)


def do_render_animation(anim, render_op, frames_dir):
    """Render frame_start..frame_end as frames_dir/frame_%04d.png"""
    scene = bpy.context.scene
    scene.render.image_settings.file_format = "PNG"
    scene.render.resolution_x = render_op.get("width", 640)
    scene.render.resolution_y = render_op.get("height", 480)
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = render_op.get("transparent", False)
    _set_engine()
    fs = anim.get("frame_start", 1)
    fe = anim.get("frame_end", 48)
    scene.frame_start = fs
    scene.frame_end = fe
    # Blender fills %04d for filepath ending without extension when animation=True
    scene.render.filepath = frames_dir + "/frame_"
    bpy.ops.render.render(animation=True)
    return fs, fe


def main():
    args = _argv_after_dashes()
    if not args:
        print("KBW_ERROR: no job spec path")
        sys.exit(1)
    spec = json.load(open(args[0]))

    reset_scene()
    render_op = {"width": 640, "height": 480}
    motions = []
    for op in spec.get("ops", []):
        t = op["op"]
        if t == "add":
            add_object(op)
        elif t == "profile":
            mesh_from_profile(op)
        elif t == "loft":
            loft_sections(op)
        elif t == "box":
            box_model(op)
        elif t == "camera":
            add_camera(op)
        elif t == "light":
            add_light(op)
        elif t == "text":
            add_text(op)
        elif t == "modify":
            modify_mesh(op)
        elif t == "uv":
            uv_unwrap(op)
        elif t == "material":
            set_material(op)
        elif t == "group":
            make_group(op)
        elif t == "boolean":
            boolean_op(op)
        elif t == "inset":
            inset_faces(op)
        elif t == "crease_line":
            crease_line(op)
        elif t == "panel_cut":
            panel_cut(op)
        elif t == "panel_recess":
            panel_recess(op)
        elif t == "mirror":
            mirror_object(op)
        elif t == "world":
            set_world(op)
        elif t == "ref_plane":
            ref_plane(op)
        elif t == "render":
            render_op = op
        elif t in ("motion", "camera_path"):
            motions.append(op)   # applied after scene built (needs frame range)
        else:
            print(f"KBW_WARN: unknown op '{t}' skipped")

    if not bpy.context.scene.camera:
        add_camera({})
    if not any(o.type == "LIGHT" for o in bpy.data.objects):
        add_light({})

    anim = spec.get("animation")
    if anim:
        fs = anim.get("frame_start", 1)
        fe = anim.get("frame_end", 48)
        for m in motions:
            if m["op"] == "camera_path":
                apply_camera_path(m, fs, fe)
            else:
                apply_motion(m, fs, fe)
        frames_dir = args[1] if len(args) > 1 else "/tmp/kbw_frames"
        fs, fe = do_render_animation(anim, render_op, frames_dir)
        print(f"KBW_OK: rendered animation frames {fs}-{fe} -> {frames_dir}")
    else:
        out_path = spec.get("output", "//output/render.png")
        do_render(render_op, out_path)
        print(f"KBW_OK: rendered -> {out_path}")


if __name__ == "__main__":
    main()
