# Keynote seq-write rule (standing)

> **파이프라인 (u_312 · 유일 경로)**: ①학습된 액션 좌표(텍스트·이미지·메뉴·well)를 **먼저** 표로 수집 ②Keynote 실행 ③전체 화면이 아니면 전체 화면(창 W×H ≈ display, 메뉴만 보지 말 것) ④딜레이 넣은 **한** seq를 순서대로 **한 번** 실행. BAN: 실행 중 다른 메뉴/경로 실험. 실패 시 상태 dump → 룰에 원인 1줄 추가 → 같은 경로 재시도 금지.

> **한 줄**: 스크립트 쓰기 **전에** 오브젝트 표(좌표·크기·HEX·pt·문구)를 먼저 확정하고, well→HEX·size→비율해제→W/H 순으로 **한 번** 돌린다.

## Screen coords (u_307)
Dump in **fullscreen** → click only in **fullscreen**. Windowed + FS-coords = miss (Grok/wrong control). To continue windowed: dump-NOW in that window. BAN mix.

## State-gate (u_309)
After each click: dump (or orch shot) and read **state**. Next click only if preconditions hold. BAN repeat a failed path (HEX-without-glyph, click_label 텍스트, 포맷 with no selection, color while inspector x > display).
White-text preconditions: FS on · inspector right-edge < display · Google in text-edit · glyphs selected (cmd-a). Else STOP and report state — do not click color.

## When
Any Keynote build via `kongtrol input run` / `seq_*.txt` (Google remake, ABOUT, cards, …).

## Before ANY build — PLAN TABLE (required)
Write rows **before** creating/editing `seq_*.txt`:

| col | meaning |
|-----|---------|
| obj | name (bg, logo, pill, btn1, …) |
| kind | `text` \| `round-rect` \| `slide-rect` \| other |
| x, y | top-left on **slide space** (not screen) |
| w, h | size in slide pt |
| fill HEX | e.g. `202124`, `303134`, `FFFFFF` (no `#`) |
| font-size | pt for text (e.g. 72, 14) |
| text | string or `—` |

Defaults: slide **16:9 = 1920×1080** unless dump says otherwise. Convert centers → top-left: `x = cx - w/2`, `y = cy - h/2`. Integers only.

## Then write seq file
Path: `kaymaps/keynote/seq_<name>.txt`

### Header comments
- PLAN TABLE (copy rows)
- DUMP coords used (toolbar / wells / align fields / HEX)
- Diagnose notes if retry of a failed a_

### Waits (standard)
| step | ms |
|------|-----|
| menu open | 400 |
| well / HEX / shape place | 800 |
| text insert | 400–1000 |
| after field enter | 400–500 |

### Order (hard)
1. **delete-all once** at start (`click canvas` → `chord cmd a` → `key delete`).
2. **BG** = full-slide `slide-rect` (or large rect) at `0,0,W,H` fill **dark HEX first** — not unreliable slide `현재 채우기` alone.
3. **well-first then HEX** for every fill/text-color (Colors panel). Never HEX-only hoping a free well binds.
4. **Text**: size field **first** → confirm intent (e.g. 72) → **비율 유지 off** (align tab) → **W/H/X/Y** → re-check size (resize can reset pt).
5. **세로 텍스트** off when horizontal wordmarks required.
6. After each object’s size/pos: prefer **dump-confirm** size+W (seq: `dump` before next `click_label`; worker post-check if seq cannot branch).
7. **ONE** `input run` per job attempt (max 2 only if instruction allows retry). **0** per-step VL. **0** mid-stop on white canvas.
8. Orch verifies **END shot only**.

### Field focus
- **Numeric fields = click → wait 200 → `chord cmd a` → text → enter.** Never dbl-only (dbl does not clear; values concatenate e.g. size→1000pt).
- If focus misses, digits land on the **slide as new text** (junk like `"0"`). Treat as drift → fix seq, not silent continue.
- After bg size: dump-confirm W=1920 H=1080 before more objects; retry fields once if wrong.

### Labels
- `click_label` uses **last dump only**. Always `dump` after creating an object before `click_label <its name>`.
- Duplicate names (`모서리가 둥근 직사각형`×N): resolve picks **smallest area** — size newly inserted shapes before the next insert, or select by list **xy**.

### BAN
재생 · 전체 화면 종료 · green traffic-light · invent coords · osascript · code-`.key` · Naver unless job says · AskUserQuestion

## Working recipes
- Keep successful `seq_*.txt` as recipes (do not delete).
- Coord dumps: `kaymaps/keynote/coordmap.md`, `prod_controls.md`.
- This rule: `kaymaps/keynote/SEQ_RULE.md` (canonical).

## Minimal checklist
- [ ] PLAN TABLE filled with integers
- [ ] seq header has plan + dump coords
- [ ] delete-all first
- [ ] BG dark via rect + well→HEX
- [ ] text: size → aspect off → W/H → color well→HEX
- [ ] dump before each click_label
- [ ] one run; end shot for orch

## Failure log
- a_312 (2026-08-15): FS geom OK (2056×1290≈2056×1329) but inspector 정렬 tab a11y x=2192>display 2056 · 텍스트 색상 well absent after Google select — cannot bind white; STOP (state-gate).
