# kongtrol Base Reference (MUST — user 2026-08-20)

> **kongtrol = macOS automation CLI.** Native binary at `kongtrol/target/release/kongtrol`. Always verify binary exists before task. Reference commands here as base—don't invent, don't guess.

Applies: all worker UI automation tasks (kongtrol input).

---

## Binary Location & Verification

```bash
# Verify binary exists
test -x /Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol && echo "OK" || echo "MISSING"

# Use in scripts
KT=/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol
$KT <COMMAND>
```

**Never** assume binary exists. Always check before first use in a task.

---

## Core Commands (reference only — use per recipe)

### 1. see (read screen via a11y)
```bash
$KT see --a11y                           # full a11y tree (focused app)
$KT see --a11y --pid <PID>              # specific app by PID
$KT see --a11y --compact                # condensed output (elements only)
$KT see --a11y --pid <PID> --compact    # specific app, condensed

# Examples
$KT see --a11y | grep -i "button"       # find all buttons
$KT see --pid $(pgrep -x "Google Chrome") --a11y | head -20
```

**Output format**:
```
AXButton               @(X,Y) [WxH] · label-text
AXTextField            @(X,Y) [WxH] · placeholder
AXCheckBox             @(X,Y) [WxH] · label
AXComboBox             @(X,Y) [WxH] · current-value
AXIncrementor          @(X,Y) [WxH] · label (for spinners)
```

**Use case**: discover coords before input, verify element presence/state.

---

### 2. input (send keyboard/mouse/text)

#### 2a. Click
```bash
$KT input click <X> <Y> --yes          # click at logical coord (X,Y)
# --yes = confirm action
```

#### 2b. Key (single keys)
```bash
$KT input key <key-name> --yes         # key press (★--yes MUST, DANGEROUS-tier — absent→"user declined action" exit=2)
# ★2026-08-23 verified(ar_2053): supported key-names = left/right/up/down/space/enter/esc/tab/backspace/delete/single-char-ONLY.
#   pagedown/pageup/return = "unsupported key-name" error(--help output ≠ actual — re-verify --help recommended).
#   scroll = `down` arrow-key repeated(via --repeat option) substitute.
# Examples:
$KT input key esc --yes                # close dialog
$KT input key down --repeat 10 --yes   # scroll down (pagedown substitute)
$KT input key enter --yes              # confirm (enter, ¬return)
```
★2026-08-23 verified(ar_2053): `input key` — same as click, absent `--yes` ALWAYS→UserDeclined(exit=2) — ¬Chrome-focus-loss, simply missing-flag. IF click-works-but-key-declined(asymmetric symptom) → suspect missing `--yes` FIRST(before focus-loss diagnosis).

#### 2c. Chord (modifier + key, 1 modifier only)
```bash
$KT input chord <mod> <key> --yes      # modifier + key (★--yes MUST, DANGEROUS-tier)
# Modifiers: cmd, shift, ctrl, alt (only 1 per chord)
# Examples:
# ❌ cmd a(전체선택) = 금지. 아래 '입력칸 텍스트 지우기' 절 참고(u_4965/5002/5017/5029)
$KT input chord cmd c --yes            # Cmd+C (copy)
$KT input chord shift tab --yes        # Shift+Tab (reverse tab)
# ❌ WRONG: $KT input chord cmd shift g  (2 modifiers = not supported)
```

#### 2d. Text (direct typing)
```bash
$KT input text "<string>" --yes         # type text directly (★--yes MUST, DANGEROUS-tier)
# Examples:
$KT input text "hello world" --yes
$KT input text "2026-08-24" --yes
# Limitations: no copy-paste, direct keyboard input only
```

#### 2e. Drag (cross-app drag-drop)
```bash
$KT input drag <SRC_X> <SRC_Y> <DST_X> <DST_Y> --yes [--human]
# --yes = DANGEROUS-command MUST(absent→refused), --human = human-speed interpolation (reliability boost)
# Examples:
$KT input drag 1318 274 1002 777 --yes --human   # Finder → Chrome dropzone
```

---

## Coordinate System

> ★★★ MANDATORY MOUSE RULE(u_3402~3404 2026-09-02 established·absolute). Root-fix detail: kaymaps/_common/RECIPE_coordinate_targeting_standard.txt. UI-task wake = default-injected(orch_wake_worker.sh --ui).

**CORE FACT(orch-measured, click 1222,459 direct-success):** kongtrol click-log = "physical(X,Y)→logical(X,Y)" = **1:1, ¬conversion**. a11y `@(X,Y)` == `kongtrol click X Y`(SAME logical-coord-system). ★×2·scale-calc·transform = FORBIDDEN(makes-it-wrong) — click a11y-coord AS-IS.
- "which-takes-priority: scale·resolution·pointer, calc?"(u_3403) answer = **¬calc, a11y-logical-coord DIRECT**.
- screencapture-png pixels(e.g. 4112×2658) ≠ logical-coords → **measuring coord from screenshot→click = WRONG**. coord=a11y-ONLY, screenshot=visual-verify-ONLY.
- ★REPEATED-VIOLATION(2026-09-05 u_3969, multiple prior same-day incidents): despite this rule being documented, worker repeatedly falls back to screenshot-then-eyeball for web-UI elements(popups/dialogs especially) instead of `kongtrol see --a11y | grep <label-text>`. This is a compliance gap, not a documentation gap — before EVERY click on a web-page element, default reflex = a11y text-search first, screenshot only as a last-resort fallback when a11y genuinely returns no match.

**MANDATORY CLICK PROTOCOL(∀ click·UI-task, unconditional):**
1. **FOREGROUND**: `open -a "<App>" && sleep 1.5`(background-click = silent no-op).
2. **COORD from a11y ONLY**(screenshot-pixel·eyeball·stale-coord = FORBIDDEN).
3. **`--yes` ALWAYS**(absent→UserDeclined, no visible-error).
4. **VERIFY after**: post-click a11y-requery for state-change → unchanged→re-check 1~3·re-click.
5. **FRESH per step**: screen-changed→re-query-coord.

- ★**TEXT from screenshots is banned too**(2026-09-13 ar_4845): the no-pixels rule covers not just
  coordinates but any STRING read off an image — IDs, URLs, filenames, codes. A YouTube video id was
  transcribed from a screenshot crop as `rZhRXrBIjz4` (capital I) when it was `rZhRXrBljz4`
  (lowercase l), costing two failed attempts. Glyph pairs that look identical in a render
  (I/l/1, O/0, rn/m) make OCR-by-eye unreliable. FIX: get the string from the source — copy the
  address bar (`cmd+l`, `cmd+c`), read a11y `AXValue`, or read the file — never retype from pixels.
- **Logical coords** used by kongtrol (not display pixels)
- **Always use logical coords** in `see --a11y` output directly (no conversion)
- kongtrol auto-translates to physical input

**Example**:
- a11y reports: `AXButton @(838,354)`
- Click: `$KT input click 838 354 --yes` ← use exact coord from a11y

---

## Focus Management (critical)

**Before input, ensure app is frontmost**:
```bash
open -a "Google Chrome"     # bring app to front
sleep 2                     # wait for focus transfer
# NOW do input (click, key, text, drag)
```

**Why**: input goes to focused app. If background, click/key silently fails (no error msg).

**Verify focus**:
```bash
$KT see --a11y --compact | wc -l    # few lines = background (menus only)
$KT see --a11y --compact | head -10 # inspect output for app title
```

---

## Timing & Reliability

| Operation | Delay | Reason |
|-----------|-------|--------|
| `open -a "App"` → `click` | `sleep 2` | focus transfer latency |
| `click` → `see --a11y` | `sleep 0.5` | UI redraw |
| `text input` → `click next` | `sleep 0.3` | text processing |
| Page navigate → `see` | `sleep 1+` | DOM render time |
| Drag-drop → verify | `sleep 1` | file process start |

**Default: sleep 1 between major ops** unless recipe specifies tighter timing.

---

## Common Patterns (from recipes)

### Pattern A: Click + A11y verify
```bash
$KT see --a11y | grep -i "button-name" | head -1   # find coord
# Extract coord from output: AXButton @(X,Y)
$KT input click X Y --yes
sleep 0.5
$KT see --a11y | grep -i "state-changed"           # verify new state
```

### Pattern B: Date/number incrementor
```bash
# AXIncrementor @(X,Y) for day/month/year
$KT input click X Y --yes    # click incrementor
sleep 0.3
$KT input key up --yes        # or down, arrow keys work
# Or: multiple clicks to increment
$KT input click X Y --yes && sleep 0.2
$KT input click X Y --yes && sleep 0.2
$KT input click X Y --yes
```

### Pattern C: Text input + replace  (★cmd a 금지)
```bash
$KT input click X Y --yes                    # focus field
sleep 0.2
$KT input key backspace --repeat 40 --yes    # 기존 내용 지우기(넉넉히)
sleep 0.2
$KT input text "new value" --yes             # replace
sleep 0.3
$KT input key enter --yes                    # confirm
```

### Pattern D: Drag-drop cross-app
```bash
open -a "Google Chrome" && sleep 2           # focus dest
$KT input drag SRC_X SRC_Y DST_X DST_Y --yes --human
sleep 1                                      # verify drop processed
screencapture -x out.png                     # confirm visually
```

---

## Error Handling (no exceptions thrown)

**kongtrol does NOT throw exceptions.** Instead:
- Silent fail on wrong coords (click goes to wrong element, no error)
- Silent fail on invalid PID (falls back to focused app)
- Wrong key name = exit with message (e.g. "unrecognized key")

**Mitigation**:
1. Always verify coords via `see --a11y` before click
2. Always verify focus via `see --a11y --compact` before input
3. Always screenshot after ops to confirm state change

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Input silent-fails (no-op) | app not frontmost | `open -a "App" && sleep 2` before input |
| Click goes to wrong element | outdated coord (scroll/resize) | re-query `see --a11y`, don't hardcode coords |
| Chord fails (e.g. cmd-shift-g) | 2+ modifiers | kongtrol supports 1 mod only; use workaround (e.g. input drag for NSOpenPanel) |
| Text typed wrong/incomplete | timing issue (field not focused) | add `sleep 0.5` before `input text`, clear with `input key backspace --repeat N`(¬cmd a) |
| Drag doesn't work | source/dest not visible | verify via screenshot first, try `--human` flag |

---

## Commands NOT Available

❌ `scroll` — kongtrol has no scroll command (use `key pagedown` or `input drag` instead)  
❌ `wait` — kongtrol has no wait (use bash `sleep`)  
❌ `screenshot` — kongtrol has no capture (use bash `screencapture -x`)  
❌ `eval` — kongtrol does not evaluate expressions

**For these, use bash + existing tools** (screencapture, sleep, curl for API, etc).

---

## Reference Commands (copy-paste base)

```bash
KT=/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol

# Focus app
open -a "Google Chrome" && sleep 2

# Read a11y (verify target app is frontmost first)
PID=$(pgrep -x "Google Chrome")
$KT see --pid $PID --a11y | grep -i "button" | head -5

# Extract coord from a11y output line
# AXButton @(1197,867) [106x46] · 운세 생성
# → click $KT input click 1197 867 --yes

# Basic input sequence
$KT input click 1197 867 --yes && sleep 0.5
$KT input key backspace --repeat 40 --yes && sleep 0.2
$KT input text "value" --yes && sleep 0.3
$KT input key enter --yes && sleep 1

# Drag
$KT input drag 100 200 500 600 --yes --human && sleep 1

# Verify via screenshot
screencapture -x /tmp/verify.png && echo "done"
```

---

---

## Source Reference

Full kongtrol source: `/Users/bumsuklee/git/kong-bot/kongtrol/src/main.rs`  
CLI definition (clap): `kongtrol/src/main.rs` — `#[derive(Parser)]` Cli struct  
Specific command impl: `kongtrol/src/{sys,process,service,input}.rs`  

**For command details not listed above, consult source or run**:
```bash
$KT --help
$KT input --help
$KT see --help
```

Basis: user "kongtrol is base tool, reference commands here — don't invent new commands, always verify binary exists first, use per recipe STEPS". Source reference: kongtrol/src/main.rs.

---

## ★ Codesign / TCC — silent total input failure (MUST, 2026-09-12 incident)

**Symptom**: `kongtrol input click` / `input key` report success but NOTHING happens on screen —
no error, no exception, zero pixels change. Both mouse AND keyboard are dead.

**Root cause**: the binary's codesign identifier changed or vanished. macOS TCC keys the
Accessibility grant to that identifier, so an unsigned/re-signed binary is treated as a different
app and its permission is revoked. `cargo build` produces an unsigned binary, so ANY rebuild can
trigger this.

**Diagnose first (10 seconds, before blaming the app/page/game)**:
```bash
kongtrol see --a11y --compact     # "권한 부족" => permission problem, ¬target-app problem
codesign -dvvv kongtrol/target/release/kongtrol 2>&1 | head -3
#   "code object is not signed at all"  -> unsigned, THIS bug
#   Identifier=<random hash>            -> random identifier, THIS bug
#   Identifier=com.kongbot.kongtrol     -> signature fine, look elsewhere
```

**Fix**:
```bash
bash kongtrol/build_and_sign.sh          # build + sign with the fixed identifier
# or sign only:
codesign -s - --force --identifier "com.kongbot.kongtrol" kongtrol/target/release/kongtrol
```
Then the owner must re-approve it once: 시스템 설정 > 개인정보 보호 및 보안 > 손쉬운 사용 →
toggle kongtrol off/on (or remove with − and re-add with +). Verify with `see --a11y` again.

★ALWAYS build via `kongtrol/build_and_sign.sh`, never bare `cargo build --release` — the script
re-signs with the fixed identifier so the grant survives. Identifier `com.kongbot.kongtrol` is
FIXED; changing it forces re-authorization.

**Misdiagnosis to avoid**(cost ~1h on 2026-09-12): a keyboard-driven web game appeared to "not
accept arrow keys" while mouse levels had worked earlier in the session. The real state was that
ALL input had died mid-session. Rule: when an input stops working, test the OTHER input kind and
run `see --a11y` BEFORE theorising about the target application.


## ★ 입력칸 텍스트 지우기 = 백스페이스 연속 (MUST — u_5002/u_5017, 2회 지적)

`cmd+a` 로 전체선택 후 덮어쓰기 **금지**. 포커스가 입력칸이 아니면 페이지 전체가
선택돼 화면이 파랗게 물들고(캡처 데이터 오염), 브라우저 주소창에서도 의도치 않게
동작한다. 실제로 이 세션에서 두 번 지적받았다.

```bash
KT=kongtrol/target/release/kongtrol
$KT input click <X> <Y> --yes            # 입력칸 포커스
$KT input key backspace --repeat 40 --yes  # 기존 내용 지우기(넉넉히)
$KT input text "새 내용" --yes
```
`--repeat` 는 실측 동작 확인됨. 지울 글자 수를 모르면 넉넉히 준다(빈 칸에서 여분의
백스페이스는 무해).
