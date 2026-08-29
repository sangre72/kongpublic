# kong-models — per-menu-type sub-model data

Master orchestrator coordinates specialized sub-models per STANDARD menu category
(File/Edit/View/Window/etc — macOS menu-bar convention).

Full learning methodology/spec → [docs/LEARNING.md](docs/LEARNING.md).

## Structure
```
kong-models/<menu-type>/<app-name>.json   # per-app learned data
kong-models/docs/                          # learning methodology docs
```

## Menu-type dirs
- file/, edit/, view/, window/ — add more as needed, don't pre-create empty categories.

Basis: user 2026-08-27 "표준 메뉴부터 학습해서 각 모델 만들자".
