# DESIGN: Panel / Edge-Loop Surfacing Ops for runner.py (a_4170)

Goal: extend runner.py beyond the single lofted ring-skin so it can express what a real hard-surface
subject(car) needs — **arbitrary character-lines** and **separate panels** — the documented structural
ceiling of box_model/loft/profile. Design first (this doc), implement after review.

## Problem recap (the ceiling)
box_model builds ONE closed surface from X-perpendicular rings. Its only edge-loops are (a) ring loops
(constant-X) and (b) the vertical side loops. `crease_bands` sharpens those. It CANNOT make a diagonal or
curved crease (belt-kink, fender swage, hood→headlight crease) or split into hood/door/fender panels.

## Key enabling bmesh ops (verified present, Blender 4.5)
- `bisect_plane(geom, plane_co, plane_no, clear_inner/outer=False)` — ★THE core op. cuts the mesh along an
  ARBITRARY plane → a new edge-loop exactly where a panel-seam/character-line runs, regardless of ring
  topology. chain several planes(or a swept series) to trace a curved line.
- `bevel(geom=edges, offset, segments, profile, ...)` — apply to a selected edge-loop → a crisp chamfer or a
  rounded character-line. offset small + segments 1 = sharp crease; segments 2-3 = a rolled highlight line.
- edge CREASE(float layer crease_edge) on a bisect-made loop → hold it crisp through subsurf(reuse existing
  crease infra) — a character-line that survives smoothing.
- `inset_region(faces, thickness, depth)` — recess a bounded face-set → door-shut-line / panel-gap.
- `split_edges(edges)` + separate → break the skin into independently-shadeable/movable panels.
- `connect_vert_pair` / `subdivide_edges` — add precise vert-loops to route a cut through desired points.

## Proposed NEW ops (added to runner.py dispatch)

### 1. `op: 'crease_line'` — arbitrary character-line on an existing body
```
{op:'crease_line', target:'body',
 plane_series:[ {co:[x,y,z], no:[nx,ny,nz]}, ... ],   # one bisect per entry, or
 path:[[x,y,z],...],                                   # OR a world-space polyline → auto-derive local
                                                        #   bisect planes tangent to the path
 bevel:{offset:0.01, segments:1, profile:0.7},         # optional crisp/rolled line
 crease:1.0}                                            # optional subsurf-hold weight
```
IMPL: for each segment, `bisect_plane` the target(clear=False, keep both sides) → collect the new edges
lying on the cut → apply bevel + crease to that edge-set. a `path` is converted to a swept series of small
bisect planes (plane normal ⟂ path tangent, in the char-line's cross direction).
USE: Model Y beltline-kink, fender shoulder line, hood-to-DRL crease — trace the blueprint's line as `path`.

### 2. `op: 'panel_cut'` — separate the skin into named panels
```
{op:'panel_cut', target:'body', cuts:[{plane_co, plane_no, name:'door'}...],
 gap:0.004}   # inset the cut boundary to leave a visible shut-line
```
IMPL: bisect along each plane, `split_edges` the seam, optionally `inset_region` the bounded faces by `gap`
for a reveal. panels stay one object(shared verts) unless `separate:true` → own objects(per-panel material).
USE: hood / front-door / rear-door / quarter-panel splits with shut-lines.

### 3. `op: 'panel_recess'` — a bounded inset (window-frame, grille, light housing)
```
{op:'panel_recess', target, region:{plane_bounds:[...] or face_normal+z_range}, depth, inset}
```
IMPL: select faces by normal+bbox, `inset_region` then push in by depth. (generalizes existing `inset` op.)

## Approach discipline
- BUILD ON the existing box_model body(don't replace it) — these ops POST-PROCESS the lofted skin. box_model
  still gives the base silhouette+proportion(already blueprint-matched 0.043); the new ops carve panels/lines
  onto it. incremental + reuses all prior work.
- VERIFY each op in isolation first(a flat test grid + one bisect+bevel) before applying to the car.
- keep it SCRIPTABLE(bmesh only, no interactive edit-mode) — matches the headless kbwrap pipeline.
- character-lines come from the BLUEPRINT(trace the side/top-view lines as `path` polylines) — same
  measure-from-ref discipline as the silhouette work.

## Build order (proposed)
1. `crease_line` via single-`bisect_plane` + bevel + crease. test on a cube(one diagonal crease). ← START
2. extend `crease_line` to a `path`→swept-planes(curved line). test on the car(one beltline).
3. `panel_cut`(bisect+split+inset gap). test hood-seam.
4. `panel_recess`(generalize inset). test window frame.
5. apply to Model Y: beltline-kink + fender line + hood-crease + door-seams, trace from blueprint.

RISK: bisect on a subdivided/high-poly mesh can make messy n-gons; do bisect on the BASE mesh(pre-subsurf)
then subsurf+crease. bevel offset too large self-intersects on tight curvature — keep small, verify per-render.

Basis: a_4170 user decision — invest in tool-extension for real panel/character-line surfacing. verified
bmesh ops present in Blender 4.5. design-before-implement per instruction.
