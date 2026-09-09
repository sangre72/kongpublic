# 모델Y 모델링 (Model Y Modeling) — CHECKPOINT

**Status: REAL-MESH DRIVEN + PANELED** (bm55, a_4170) — roofline+DLO measured from real Sketchfab GLB(0.06 vs real), boxy flat body, door panel-seams at real positions, beltline char-line, selective-smooth wheels, details re-seated. Real mesh=examples/tesla_model_y_REAL_mesh.glb.
(prior: BLUEPRINT-MATCHED + DETAILS CLEAN (bm49, a_4170) — silhouette 0.043 vs blueprint, official proportions, details re-seated proportionate. Master ref=examples/modely_blueprint_MASTER_4view.png.

## Method
True multi-view box-modeling (`box` op, scripts/runner.py) — side_outline (length×height) + front_widthcurve (tumblehome) triangulated. See RECIPE_blender_reference_photo_to_profile.txt top-banner for full method + this-session learnings.

## Current state (checkpoint = examples/checkpoint_model_y_modeling.json = bm13)
Render: output/bm13.png (hero output/bm13_hero.png) (hero), output/bm8_side.png (pure-side). Recognizable modern SUV: flat-high roof plateau, blunt bumpers, 4 seated wheels, greenhouse glass on flank.

## DONE this session (a_4170)
- Glass panes SEATED onto flank via flank_at(x,z) (was floating/sunken).
- 4 WHEELS added — cylinder rot[90,0,0] axle-along-Y, width via scale[1,1,0.30], tucked to flank, wheelbase ±1.45, r~0.38.
- Body SILHOUETTE reshaped smooth-dome→SUV: low-flat hood → steep windshield → FLAT HIGH roof plateau (peaks early, held flat) → gentle fastback → blunt raised tail.
- END-BLUNTNESS box-param added (runner.py) — 0.6 keeps bumpers full-width (was pinched-to-points beetle-tell).
- x_stations densified 17→37 (holds windshield/cabin crispness, extra-dense through windshield x1.4-0.4 + hatch).

## Known issues (next iters)
- Front nose still rounds into a slight snout ahead of front wheel (want crisper vertical front face + defined hood edge).
- Greenhouse glass reads as roof-top panes, not side-DLO windows — reposition lower onto the flank + reshape to window profile.
- Overall subdiv-soft (UNRESOLVED loft/box+subdiv roof-round tension per recipe top-banner — needs edge-crease op, not yet built).
- Wheel-arch cutouts into body not done (wheels abut flank).
- Details TODO: mirrors, cladding, DRL/taillight refinement, rear diffuser.

## Preserved (all intact, verified this session)
- Code: scripts/runner.py (box op + end_bluntness), kbwrap.py — parse OK.
- Specs: checkpoint_model_y_modeling.json (=bm8), plus bm3..bm8 iteration specs in examples/.
- Renders: bm1..bm8 (+_side) in output/.
- Refs: tesla_model_y_official_pure_side.jpg, ..._front.jpg.

## Run
KBW_BLENDER=/usr/local/bin/blender python3 kbwrap.py render-spec examples/<spec>.json

## ABANDONED (2026-09-07, u_4216 — a_4170 closed stopped-by-user)
- Final state: bm56 spec (16 mesh/13,144 tris) + measured-comparison assets. Real GLB=113 mesh/2,432,105 tris (7.1x parts / 185x tris denser). Renders: output/COMPARE_bm56_vs_real_{hero,side}.png, REALREF_{side,front,top,hero}.png.
- Deep-measure data (kept, reusable): examples/real_mesh_measurements.json (48-station full sections+part inventory), examples/real_body_sections.json (64-station body-shell + 40-station glass sections), scripts/measure_*.py, scripts/render_views.py.
- bm57 loft-from-measurements experiment (examples/bm57_biw.json, output/BM57_*.png) = lumpy, superseded by GUI-modeling pivot (u_4214) which was then abandoned (u_4216).
- GUI-modeling attempt log: Blender 4.5.13 Intel/Rosetta crashed 2x (SIGSEGV) during File>Import glTF flow (2nd during filename typing). a11y tree=0 elements (custom GL UI) → coord-from-screenshot fallback used. Menu coords learned: File(44,79)→Import(75,363)→glTF(303,583), scale logical=px×2056/1400.
- No further work planned. Blender app closed.
