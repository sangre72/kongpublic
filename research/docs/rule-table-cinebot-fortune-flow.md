# Rule Table: CineBot Fortune-Flow (extracted from RECIPE_fortune_12_full_flow.txt)

Task 2 proof-of-concept: converting a mature natural-language recipe into an explicit
IF(condition) THEN(action) rule table — machine-queryable, not prose to re-read/re-interpret
each time.

Source: `kaymaps/localhost-cinebot/RECIPE_fortune_12_full_flow.txt` (verified_runs=1, a_953~970)

## Format
| ID | IF (state/signal) | THEN (action) | CONFIDENCE | SOURCE-STEP |

## Rules

| ID | IF | THEN | CONFIDENCE | SOURCE |
|----|----|------|-----------|--------|
| R1 | `see --a11y --compact` on Chrome PID returns ≤~10 elements(메뉴바만) | Chrome is backgrounded → click Dock icon OR `open -a "Google Chrome"` + sleep 2 | HIGH(1 verified run) | STEP1 |
| R2 | `kongtrol input key` fails("사용자가 작업을 거부했습니다") but `input click` succeeds | NOT a permission bug — Chrome focus-loss signal → apply R1, do NOT escalate to needs-info first | HIGH | STEP1 |
| R3 | Need to verify AXIncrementor(날짜필드) value | a11y value attribute absent + VLM unreliable(repeat-query gives different answers) → use zoom-crop screencapture(`screencapture -R<x>,<y-17>,300,40`) + Read for exact value | HIGH | STEP3, RECIPE_zoom_crop_value_verify.txt |
| R4 | Need real-time batch progress | `curl localhost:15000/fortune/progress?date=X` JSON is ground truth, NOT UI a11y "처리중:X" text(can be stale) | HIGH | STEP7 |
| R5 | `curl localhost:15000/...` returns HTTP 000(connection refused), repeated | 15000(uvicorn) intermittent event-loop hang, process still alive(verify `ps -p <pid>`) — NOT a crash | HIGH(3-4 occurrences observed, 2026-08-19) | STEP8, 증상A |
| R6 | R5 condition true, elapsed < 80s | WAIT, re-curl every 5s. Do NOT retry-click, do NOT restart. UI stays stale(not a display bug) | HIGH | 증상A 1차대처 |
| R7 | R5 condition true, elapsed > 5min, still HTTP 000 | STOP, needs-info to orch for restart authorization(never restart 15000 without explicit a_ approval) | HIGH | 증상A 2차대처, CON |
| R8 | "⚠ zodiac Qwen(18081) 기동실패" banner visible | Do NOT treat as failure signal by itself — likely false-positive(confirmed false in 100% of observed cases, u_999/a_968) | HIGH | STEP9, 증상B |
| R9 | Need to judge if a batch of N labeled items(e.g. 12 zodiac fortunes) completed | Prefer `see --a11y --pid <PID> --compact \| grep -E "label1\|label2\|..."` text-match over full-screenshot eyeball-count — ~30ms vs ~170ms+(5x+ faster), and avoids OCR-equivalent misread risk | HIGH(measured 2026-08-31) | STEP10 |
| R10 | a11y label-match(R9) fails or ambiguous for a specific item(icon-only, no text) | Fall back to zoom-crop on JUST that item(not full-screen) | MEDIUM | STEP10 |
| R11 | Button coordinates from a prior run/session | Do NOT hardcode — page-scroll position shifts coordinates. Re-query `see --a11y --compact` every time before click | HIGH | STEP4, STEP11, STEP12, LIMIT |
| R12 | Judging final completion of a generation batch(e.g. slide-gen) | Require 3-way confirmation: (a) status badge text(e.g. "N/N") + (b) button-label reverted to its "done" variant + (c) visual thumbnail/content actually rendered(not blank). A single indicator(esp. a11y-only static text) can be stale | HIGH(from 966/968 incident) | STEP14 |
| R13 | A known button(e.g. "전체 슬라이드 생성") isn't found near its "expected" UI region | Check adjacent-but-distinct panel(e.g. scenario-tab's scene-list panel top, NOT the fortune-tab) — button location can differ from naive assumption | HIGH(a_969 correction) | STEP12 |

## Additional rules(from RECIPE_slide_generate.txt — same button-family, corrected findings)

| ID | IF | THEN | CONFIDENCE | SOURCE |
|----|----|------|-----------|--------|
| R14 | Looking for "전체 슬라이드 생성" button | It is NOT at page-top and NOT at scenario-textarea-top — it's BELOW the "N개 씬/M초" summary box and scene-tab row, same row as regen/play/model-select controls. Landmark = scene-tab-row, not any "top" | HIGH(corrected 2026-08-25, u_2321 — an earlier recipe version had this WRONG) | STEP4 |
| R15 | `see --a11y --compact \| grep "전체 슬라이드 생성"` returns empty | Do NOT give up — exact-text grep can fail(observed). Fall back to direct screenshot of the scene-tab-row area, 1 retry max before switching method(not infinite grep-retry) | MEDIUM | STEP4 |
| R16 | About to click "전체 슬라이드 생성" | FIRST verify scene-count badge("N개 씬") + page title matches the INTENDED full set — a stale PARTIAL scenario(e.g. leftover 6-scene draft) can be on-screen and look plausible. Click only after count-match confirmed | HIGH(explicit trap noted, R16 prevents silent wrong-batch execution) | STEP4 |

## Meta-rules(cross-recipe, not fortune-flow-specific — candidates for promotion to kaymaps/_common/)

| ID | IF | THEN |
|----|----|------|
| M1 | Any status signal(banner/static-text) contradicts a countable/API-verifiable ground truth | Trust the countable/API source, treat the banner/text as advisory only, verify before discarding results |
| M2 | About to hardcode a UI coordinate into a recipe for reuse | Store as label+element-type instead(e.g. "button labeled '전체 슬라이드 생성'"), re-query a11y for actual (x,y) at execution time |
| M3 | A dev-owned external server(not launchd-managed by this repo) appears hung | Never kill/restart without explicit per-instance a_ authorization — wait for natural recovery first(observed: most hangs self-resolve in 20-80s) |

## Notes on this extraction exercise
- This is a MANUAL extraction(LLM-assisted read-through), not automated NLP parsing — task 2's original framing
  ("자동 변환") is more accurately "manual structuring with recipe as source of truth," at least at this stage.
- Value observed: rules R4-R7(15000 hang handling) and R9(a11y-count-first) are now lookup-able in O(1) instead
  of requiring re-reading ~50 lines of prose recipe each time a similar symptom appears.
- Next: repeat this extraction for 2-3 more mature recipes(RECIPE_worker_session_recovery.txt, shopping-site recipes)
  to see if a common rule-table SCHEMA emerges that could become a shared structure(e.g. a JSON index of rules
  queryable by a small classifier — ties into research task 3/4).
- ★observed pattern across R13/R14: coordinate-region descriptions("above X, below Y, same row as Z") are more
  durable than literal pixel coords AND more durable than exact-text grep(R15 shows even grep can silently fail).
  This suggests rule-table entries should store STRUCTURAL anchors(relative-to-landmark) as a 3rd fallback tier:
  a11y-label-match(fast) → relative-structural-position(medium) → zoom-crop visual(slow, last resort).
