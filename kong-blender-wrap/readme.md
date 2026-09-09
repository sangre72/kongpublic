# kong-blender-wrap

Headless [Blender](https://www.blender.org/) wrapper for kong-bot — drive Blender's `bpy` programmatically from a simple CLI / JSON job-spec, no GUI.

Sibling to the other `kong-*` projects. Same spirit as `kongtrol` (a thin CLI over a capability) but for **3D scene build + render** instead of OS input.

## Install
Blender (macOS Apple Silicon) via Homebrew cask:
```bash
brew install --cask blender     # installs /Applications/Blender.app + `blender` CLI
blender --version               # verify (built + tested on 4.5.13 LTS)
```
No extra Python deps — `bpy` ships inside Blender; the CLI uses only system python stdlib.

## Architecture
- **`kbwrap.py`** (system python) — CLI dispatcher. Builds a JSON job-spec, invokes Blender headless:
  `blender --background --python scripts/runner.py -- <spec.json>`.
- **`scripts/runner.py`** (runs INSIDE Blender's python, `bpy` available) — data-driven interpreter: reads the spec's `ops` list and applies them via `bpy`, then renders.
- Split = kong-bot's fire-and-collect pattern: caller composes a spec (pure data), one headless invocation renders a PNG. No long-running socket server (unlike blender-mcp addons — overkill for batch automation).

## Usage
```bash
# smoke test — cube on a plane, sun light, auto camera
python3 kbwrap.py smoke --out output/smoke.png

# render from a JSON spec
python3 kbwrap.py render-spec examples/scene.json

# print Blender version
python3 kbwrap.py version
```

## Job spec format
```json
{
  "output": "output/out.png",
  "ops": [
    {"op":"add","kind":"cube","location":[0,0,0],"size":2,"color":[0.8,0.2,0.2]},
    {"op":"add","kind":"plane","location":[0,0,-1],"size":20},
    {"op":"camera","location":[7,-7,5],"look_at":[0,0,0]},
    {"op":"light","location":[4,-4,8],"energy":3.0,"light_type":"SUN"},
    {"op":"render","width":640,"height":480,"transparent":false}
  ]
}
```
- `add.kind`: cube / sphere / cylinder / cone / plane / monkey. `color` = optional RGB 0–1 (Principled BSDF base color).
- `camera`: `location` + `look_at` (auto-aims). If omitted, a default camera is added.
- `light`: `light_type` SUN/POINT/AREA/SPOT, `energy`. If omitted, a default sun is added.
- `render`: `width`/`height`/`transparent`. Engine auto-selects EEVEE-Next → EEVEE → Cycles.

## Video / animation (a_3829)
Add an `animation` block + `motion` ops to the spec → the wrapper renders the frame range headless and **ffmpeg-muxes to mp4** automatically (h264/yuv420p).

```json
{
  "output": "output/orbit.mp4",
  "animation": {"frame_start": 1, "frame_end": 96, "fps": 24},
  "ops": [
    {"op":"add","kind":"sphere","name":"hub","location":[0,0,0],"size":2,"color":[0.2,0.4,0.9]},
    {"op":"add","kind":"cube","name":"runner","location":[4,0,0],"size":1,"color":[0.9,0.2,0.2]},
    {"op":"light","location":[5,-4,9],"energy":4.0},
    {"op":"camera","location":[10,-10,6],"look_at":[0,0,0]},
    {"op":"motion","motion":"orbit","target":"runner","center":[0,0,0],"radius":4,"turns":1.0},
    {"op":"motion","motion":"orbit_camera","center":[0,0,0],"radius":12,"height":6,"turns":0.5},
    {"op":"render","width":640,"height":480}
  ]
}
```
Run: `python3 kbwrap.py render-spec examples/orbit_scenario.json --out output/orbit.mp4`

### Motion primitives (v1)
- `orbit` — object circles a `center` (radius/height/turns) on XY plane.
- `orbit_camera` — camera circles the scene at fixed height, always aiming at `center`.
- `move` — object goes `from` → `to` (straight line).
- `spin` — object rotates on an `axis` (X/Y/Z) for N `turns`.
- `scale` — object scales `from` → `to`.
- All keyframes use LINEAR interpolation (constant motion). Objects are referenced by `name` (set on the `add` op); `"camera"` is the special camera target.

### Scenario → spec pattern
The wrapper is a **dumb executor** — natural-language scenario → JSON spec translation happens at the CALLING layer (orch/worker composes the JSON), matching kong-bot's data-driven pattern (no LLM inside the wrapper). Example scenario `"a red cube orbits a blue sphere, camera circling, ~4s loop"` → `examples/orbit_scenario.json` (see its `_scenario` field). Add `_scenario` as a doc-only key; the runner ignores unknown top-level keys.

### Frames → mp4
ffmpeg muxes `frame_%04d.png` at the spec's `fps` into h264/yuv420p mp4, auto-padding to even dims. Frame-seq rendered to a temp dir, cleaned after mux. (Verify real motion via first-vs-last-frame PSNR — <28dB = genuine movement, per repo convention.)

## Pipeline op reference (by 3D-workflow stage, a_3830)
The op-set mirrors a standard Blender workflow. Compose ops in stage order in the `ops` list.

### 1. Modeling
- `add` — primitive. `kind`: cube / sphere / cylinder / cone / plane / monkey / **torus**. `name` (for later reference), `location`, `size`, optional flat `color`, **`scale`:[x,y,z]** (per-axis, non-uniform), **`rotation`:[deg,deg,deg]**.
- `group` — parent named `members` under an empty (named `name`) so a multi-part assembly moves/animates as ONE object (e.g. a car rig). The group name becomes a valid `move`/`spin`/motion target.
- ★**Modeling a REAL object from reference photos** — standing workflow: gather multiple references (side = primary silhouette, front/rear = detail placement), extract the side silhouette (transparent-PNG alpha-trace if available, else vision-trace [x,z] points faithful to the real shape), feed to `profile`, place details against front/rear refs, iterate by rendering a PURE SIDE view and comparing to the reference. Full method: `kaymaps/localhost-comfyui/RECIPE_blender_reference_photo_to_profile.txt`. Example: `examples/model_y_from_photo.json` (Model Y traced from a Wikimedia side photo). Don't guess proportions from text dimensions — that yields a generic shape, not the object.
- `loft` — ★build a smooth DOUBLY-CURVED body by lofting between width-varying cross-`sections` ([{x, section:[[y,z]...]}...], same vert-count each). Curves in BOTH profile and width → real aero surfaces (no flat slab sides). Use instead of `profile` when surface-smoothness matters; `profile` (constant-width extrude) is fine for quick/blocky shapes. Keep subdiv LOW (1) so structure survives. See a_3841 / RECIPE.
- `profile` — build ONE continuous solid from a 2D side-`profile` (list of `[x,z]` outline points, CCW), extruded symmetrically along Y to `width`. bmesh-based (precise vertex construction). This is how to get a **continuous flowing silhouette** (e.g. a car's hood→windshield→roof→fastback→rear as a single unbroken surface) — impossible with stacked/boolean-unioned boxes, which always seam. Options: `bevel`, `subdivide` (Catmull-Clark rounds the extruded cage into a smooth body), `smooth`, `color`/`metallic`/`roughness`. See `examples/model_y_scenario.json`.
- `modify` — mesh edit on a `target` (by name): `modify`:
  - `subdivide` (`levels`) — SUBSURF, smooths geometry.
  - `bevel` (`width`, `segments`) — bevel edges.
  - `smooth` — shade-smooth (removes facet look).
  - `loop_cut` (`cuts`) — add edge loops (subdivide in edit mode) for finer shaping control.
  - `taper` (`axis`, `end` max/min, `factor`) — shrink one end's cross-section → sloped/tapered form (e.g. roofline slope).
- `inset` — bmesh face-inset (panel-lines / door-seams / recessed light-lenses). `select_dir`:[x,y,z] face-normal filter, `z_range`:[lo,hi] height band, `thickness`, `depth` (negative = recess in). Selects faces by direction+band, no manual selection.
- `mirror` — mirror modifier about WORLD CENTER (auto pivot at origin), `axis`, `apply`. Model a part once on one side → mirror for perfect symmetry (wheels, handles, side-mirrors, cladding). `apply:true` merges L+R into one mesh (fine for a wheel — spin the merged mesh; use `apply:false` to animate sides independently).
- Hard-surface detailing workflow (panel-lines + small parts layered on the `profile` silhouette): see `RECIPE_blender_reference_photo_to_profile.txt` and `examples/model_y_detailed.json`.
- `boolean` — `target` ⊕ `tool` (`operation`: UNION / DIFFERENCE / INTERSECT, `delete_tool`). NOTE: boolean-union then subdivide-smooth does NOT yield a clean continuous rounded surface (union n-gons defeat Catmull-Clark) — use separate subdiv-smoothed pieces for smooth compound forms. Boolean is best for hard-edged cuts (window openings, notches).
- `world` — ambient background (`color`, `strength`). Headless default world is now soft sky-grey so metallic/PBR materials don't render black (auto-set in reset; override with this op).

### 2. UV mapping
- `uv` — auto-unwrap a `target` mesh so textures map correctly. `method`: `smart` (Smart UV Project, default) / `cube` / `sphere` / `unwrap`.

### 3. Shading (PBR)
- `material` — real Principled-BSDF material on a `target`: `color` (base, RGB 0–1), `roughness`, `metallic`, `emission` (RGB) + `emission_strength`. Replaces any flat `add.color`. (Metallic+low-roughness = reflective; high-roughness = matte.)
- `text` — 3D text object: `body`, `location`, `rotation` (degrees XYZ), `size`, `extrude` (depth), `align`, `color`, `name`.

### 4. Animation → video
(see the Video section above) — `animation` block + `motion` / `camera_path` ops:
- `motion`: `orbit` / `orbit_camera` / `move` / `spin` / `scale`.
- `camera_path` — multi-keypoint camera: `points:[{frame_frac, location, look_at}]` (cinematic arcs beyond simple orbit).

### Full pipeline example (all stages, E2E → video)
`examples/full_pipeline.json` — subdivided+smoothed sphere → UV-unwrapped → glossy blue PBR, metallic torus orbiting, 3D title, camera arcing on a path → `output/full_pipeline.mp4`. Run:
```bash
python3 kbwrap.py render-spec examples/full_pipeline.json --out output/full_pipeline.mp4
```
Proves modeling → UV → shading → animation compose in one spec (verified: 640x480/72f/24fps/3s, first-vs-mid PSNR 11.7dB = real motion; loop returns to start by design).

Still showcase of the modeling/shading ops: `examples/ops_showcase.json` → `output/ops_showcase.png`.

Compound-object example (car composed from primitives, grouped, driven): `examples/car_scenario.json` → `output/car.mp4` — a stylized low-poly car (beveled body + cabin + 4 wheels via per-axis scale/rotation, `group`ed into one rig) driving on a road with a tracking camera. Shows the wrapper is general-purpose (no "car" op needed). Fidelity is toy/low-poly — curved car surfaces would need extrude/loop-cut ops (not yet supported; only subdivide/bevel/smooth).

## Env
- `KBW_BLENDER` — override Blender binary path (default `/Applications/Blender.app/Contents/MacOS/Blender`, PATH `blender` as fallback).

## Extending
Add a new op → handle it in `runner.py`'s `main()` dispatch + a helper (mirror `add_object`/`add_camera`). The CLI stays generic; capability lives in the bpy-side interpreter. Keep `bpy` imports only in `runner.py` (system python can't import bpy).

## Smoke test (verified)
`python3 kbwrap.py smoke` → renders `output/smoke.png` (orange cube on green plane, headless EEVEE). See ar_3828.

## Render engine / GPU (a_3851)
- Default engine = **EEVEE-Next**, which is GPU/Metal-accelerated by default on macOS (verified: 64 samples in ~0.8s). Renders were never the bottleneck — per-checkpoint "minutes" was iteration overhead (many renders + inspection per turn), not one slow render.
- Safety net: if the engine ever falls back to **Cycles**, `_set_engine()` now forces Metal GPU (`compute_device_type='METAL'`, enables the Metal device, disables CPU, `cycles.device='GPU'`). Verified it enables "Apple M3 Max (GPU - 40 cores)". Prevents a silent Cycles-CPU fallback.
- `KBW_ENGINE:` line is printed at render time so the active engine/device is always visible in the runner log.
