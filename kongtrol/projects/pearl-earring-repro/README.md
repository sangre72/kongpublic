# Pearl Earring Reproduction — Krita mouse-only drawing experiment

Date: 2026-08-16
Task chain: a_423/424, a_455~a_543 (kongewalker/kong-bot session)

## Goal
Reproduce Vermeer's "Girl with a Pearl Earring" in Krita using pure mouse/keyboard IO
(no scripting/API calls to Krita itself), as a capability test for kongtrol.

## Method evolution
1. Freehand outline sketch (flat single-color, ~30-35% fidelity)
2. 15x15 grid mosaic, 3-tier brightness bucket (grayscale-only bug found, fixed)
3. 15x15 grid mosaic, empirically-verified 3-color palette (~35-40% fidelity)
4. Fresh-canvas freehand attempt with contrast colors (~30-35% fidelity)
5. 20x25 (500-cell) grid, real per-cell RGB extraction, mapped to 2 calibrated
   hue points via nearest-neighbor (~35-40% fidelity — same ceiling as smaller
   grids; bottleneck is color-wheel hue-angle precision, not cell count)

## Key finding
Krita's docked "고급 색상 선택기" (Advanced Color Selector) wheel CAN produce
accurate, non-gray hues when wheel center+radius are precisely measured via
pixel-color-detection (not eyeballed from a screenshot). Only 2 hue points were
calibrated this session (mint-green @ screen-angle 0°, tan @ screen-angle 180°).
True continuous hue targeting would need ~10-12 calibration points + curve fit.

The floating Hex-input "색상 선택" dialog (opened via foreground-swatch double-click)
was UNRELIABLE across the entire session — confirmed non-functional on repeated,
carefully-coordinated attempts. Treat as broken for this Krita install/session;
use the docked wheel instead.

## Files (top level = current generation only)
- `reference_painting.png` — cropped reference image (622x741px)
- `grid_70x100.bin` — current grid data (7000 cells, 70x100, from dithered downscale), BINARY format(see below), supersedes grid_500.bin(deleted 2026-08-17)
- `chunks/` — grid_70x100.bin split into 10 row-band chunks(binary, see below)
- `README.md` — this file

## archive/ (superseded intermediates, kept for history)
- `reference_wiki_page.png` — full Wikipedia screenshot (context only)
- `result_final_v3.png` — earlier freehand-outline attempt screenshot
- (all grid_*.json files DELETED per a_550 — JSON format discarded entirely in favor of binary)

## Binary grid format v2(a_551/552, self-describing header — 2026-08-16, supersedes a_550's headerless version)

### File header(5 bytes, every .bin file starts with this)
little-endian `struct` format `<BHH`
| field | type | bytes | notes |
|---|---|---|---|
| format_code | uint8 | 1 | 1=uint8 coords(grid dim≤255), 2=uint16 coords(≤65535), 3=uint32(larger, unlikely needed) |
| rows | uint16 | 2 | total grid rows(full grid, even inside a chunk file — chunk record-count is implicit from file size) |
| cols | uint16 | 2 | total grid cols |

### Per-cell record(size depends on format_code)
- format_code=1(current, 20x25 grid — both dims≤255): `<BBBBB` = row(u8)+col(u8)+R+G+B(u8 each) = **5 bytes**
- format_code=2(legacy a_550 format, dims≤65535): `<HHBBBx` = row(u16)+col(u16)+R+G+B(u8)+pad = 8 bytes
- format_code=3(dims>65535, not used yet): `<IIBBBx` = row(u32)+col(u32)+R+G+B(u8)+pad

Reader logic: read 5-byte header first → get format_code → select record struct format →
remaining bytes = `(filesize-5)/record_size` records, parse sequentially. Fully
self-contained, no external metadata file needed.

Read example(Python):
```python
fc, rows, cols = struct.unpack_from('<BHH', data, 0)
rec_fmt = {1:'<BBBBB', 2:'<HHBBBx', 3:'<IIBBBx'}[fc]
rec_size = struct.calcsize(rec_fmt)
row, col, r, g, b = struct.unpack_from(rec_fmt, data, 5 + i*rec_size)  # record i
```

Size comparison(current 70x100=7000-cell grid): 5-byte header + 7000×5-byte records = **35005 bytes**
(format_code=1 still valid since both dims≤255).

`grid_70x100.bin`(2026-08-17, from `reference_painting.png` resized to 70x100 + Floyd-Steinberg
dithered to 64-color adaptive palette before per-cell RGB extraction — dithering pre-quantizes
colors so grid cells sample from a reduced, higher-contrast palette instead of raw photo noise) —
header reads format_code=1, rows=100, cols=70.

`chunks/chunk_NNN.bin` — 10 files, EACH gets its own 5-byte header(same format_code/rows/cols
as the parent, since chunks reference the same full-grid coordinate space) + 700 records(3500 bytes)
= 3505 bytes/chunk. Self-contained: any chunk file alone is fully parseable without the original.

Canvas coordinate mapping(NOT stored in binary, kept as a formula since it's derivable and layout-dependent):
`canvas_x = CX1 + (col+0.5)*cell_w`, `canvas_y = CY1 + (row+0.5)*cell_h` — recompute per session using current canvas bounds(CX1,CY1 etc.) rather than storing stale absolute coords that break when window layout changes(this was a real issue this session — layout changed between attempts).

## Recipes produced (see kaymaps/krita/)
RECIPE_draw_line.txt, RECIPE_draw_dot.txt, RECIPE_fill_area.txt, RECIPE_erase.txt,
RECIPE_set_fill_color.txt, RECIPE_brush_size.txt — all verified 2x+, reusable for
future Krita automation tasks.

## Honest fidelity ceiling
~35-40% recognizability at best across all methods tried. Mouse-drag/click-based
flat-fill primitives cannot achieve painterly/photorealistic reproduction. Further
improvement requires solving continuous hue-angle calibration (not attempted due
to time), not more cells/grid resolution.
