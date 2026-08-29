# kong-models learning methodology

Each sub-model learns cross-app patterns for its menu type: item labels,
shortcuts, submenu structure, and per-app data useful for future speed
(cached lookup-path shortcuts, per-app quirks) — NOT raw pixel coordinates.

## ★★★ NO ABSOLUTE COORDINATES (2026-08-27 user "해상도 배율이 사람마다 제각각")
Raw pixel/logical coords are NOT portable across users(different resolution/
scale/window-size). Learned data MUST be resolution-independent:
- **primary lookup = a11y role+label path** (e.g. "AXMenuBar > AXMenu[File] >
  AXMenuItem[Save]"), NOT (x,y). This is what actually generalizes.
- if coords are cached at all, store as **relative fraction of window/screen
  bounds**, computed from a live a11y query's own frame each session — never
  store/reuse absolute pixels cross-machine.
- runtime flow: `see --a11y` → resolve path/label on THIS user's screen →
  click resolved coord. The model speeds up the LOOKUP(skip full-tree scan),
  not the coordinate itself.

## ★★★ SAFETY — no destructive clicks (2026-08-27 user "잘못하면 삭제될 수도 있으니 조심")
- OBSERVE-ONLY by default: `see --a11y` to READ item labels/paths WITHOUT
  clicking destructive-sounding items(Delete/Empty Trash/Erase/Remove/Reset/
  Format/Clear-all/Overwrite/Quit-without-save etc).
- ambiguous label → record from read-only menu-open state only, don't click
  to "test" what it does.
- SAFE-to-click for verifying behavior: Save/Open/New/Copy/Undo/View-toggles/
  Zoom — reversible, low-risk only.
- genuinely unsure → skip, note "unverified-behavior", don't guess by clicking.

## ★★★ MOE(Mixture-of-Experts) LOADING(2026-08-27 user "메모리 적게 차지하게 MOE형태로")
Master orchestrator = router only, does NOT hold all menu-type data in memory
at once. Each menu-type(file/edit/view/window/...) = a separate "expert" —
loaded on-demand only when that specific menu is being worked with, unloaded
after. This design already fits naturally(per-menu-type JSON files, not one
giant blob) — just enforce the LOADING discipline explicitly:
- runtime: master identifies target menu-type from task context → loads ONLY
  that menu-type's JSON(+relevant per-app file within it) → uses it → drops
  from memory when task moves to a different menu-type/app.
- do NOT preload all menu-types "just in case" — that defeats the point.
- data-format stays flat/per-file(no single merged mega-file) so partial
  loading is trivial(just read the 1 relevant JSON, not parse-then-filter
  a combined structure).

## Data captured per app (JSON per menu-type per app)
- item label (native lang, per K7 app-label-exception)
- a11y role+label PATH (resolution-independent, the real learned asset)
- keyboard shortcut if present(most portable option — prefer over any click)
- submenu structure if nested
- notes: quirks, gotchas, verified-date

Basis: user 2026-08-27 "표준 메뉴부터 학습해서 각 모델 만들자, 로컬 앱 구동하며 학습".

## ★OPEN SCOPE ITEM(tier-2, not blocking current tier-1) — 2026-08-27
Finder(and similarly-complex apps) may need deeper-than-top-menu coverage if/when a richer model is built: Get-Info panel fields, Tags UI, Share-sheet options, right-click context-menu items(distinct from menu-bar items). Current tier-1(lookup-table, top-level File/Edit menu only) does NOT cover this — noted as future scope, not addressed now.
