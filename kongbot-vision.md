# kongbot-vision.md

> compressed-symbolic spec (K7). human-like vision-driven action agent.
> src-of-truth: memory[kongtrol-direction-ai-realtime, kongtrol-universal-agent-core, vision-gui-complex-limit, breakthrough-a11y-uitars, compute-vs-ai-split] + adr/0007 + demo/vision_gui_agent_research.md + docs/appkb/keynote.md.

---

## §0 ONE-LINE
`kongbot = AI-brain(judge) + human-like real-time IO(eyes+hands) + zero app-specific hardcode`.
= a human sitting at the machine: sees screen, decides, moves mouse/types. NOT a scripted macro, NOT a coded app-driver.

---

## §1 PURPOSE (why exists)
- **P1 human-like IO**: interact w/ any GUI via [see→judge→physical mouse/keyboard] loop, like a person. speed-agnostic (slow ok), observation-synced (act on what's actually on screen, not on assumed state).
- **P2 pure-vision + no-coding-final-artifact**: the deliverable(slide·doc·game-move) produced ONLY by real app manipulation. FORBIDDEN: generate result via code/script/file-inject, screenshot-as-whole-image shortcut. cf memory[no-screenshot-shortcut-build-directly].
  - EXCEPTION: extending/installing the tool itself (kongtrol self-extension) = allowed.
- **P3 no app-specific fixed-logic**: no per-app branch trees. one generic core drives Keynote·browser·minesweeper·anything. app-knowledge lives as DATA (appkb recipes), not as hardcoded control-flow. cf memory[kongtrol-universal-agent-core].
- **P4 pure-IO only**: keyboard·mouse·screen ONLY. NO System Events / osascript auto-control. (browser for VIEWING screen = ok.) cf memory[pure-io-no-system-events].

---

## §2 ARCHITECTURE (eyes + hands + brain)
```
        ┌─────────────── BRAIN (AI judge) ───────────────┐
        │  judge "WHAT to do / WHICH element"  (visual)   │
        │  NOT coord-math (compute locally). cf §6        │
        └───────────▲──────────────────────┬─────────────┘
                    │ elements/screenshot   │ decision(click X / type T / key K)
        ┌───────────┴──────────┐  ┌─────────▼──────────────┐
        │  EYES                │  │  HANDS                 │
        │  kongtrol see --a11y │  │  kongtrol input        │
        │  = AXUIElement dump  │  │  click/move/drag/text/ │
        │  role·label·cx·cy    │  │  chord/key(bs·del)     │
        │  (logical pt, <100ms)│  │  = enigo+CGEvent IO    │
        │  + xcap screenshot   │  │  --human pacing        │
        └──────────────────────┘  └────────────────────────┘
```
- **eyes** = `see --a11y`(main.rs:127) → per-element {role,label,cx,cy,x,y,w,h} in LOGICAL pt. + xcap screenshot for visual/canvas.
- **hands** = `input`(main.rs:161) → enigo+CGEvent. click/move/drag(scale-aware)·text·type-file·chord·key. key incl backspace/delete(a_40). drag=a_49 G6.
- **brain** = Claude(orch writes a_ instr; worker executes) OR future local model. judges visual-only; coords are COMPUTED not guessed.

---

## §3 STATE — WHAT WORKS (실증 완료)
| id | capability | proof | recipe/loc |
|----|-----------|-------|-----------|
| S1 | a11y element dump | minesweeper·Keynote elements resolved | `see --a11y` main.rs:127 |
| S2 | physical mouse/kbd IO | click·type·chord·key all fire | `input` main.rs:161 |
| S3 | ★coord-system RESOLVED | 2× empirical | a11y logical + `click --scale 1.0`. cf memory[keynote-two-coordinate-systems] |
| S4 | object delete | Keynote shape/img delete | `input key backspace` (a_40) |
| S5 | shape place (numeric) | rect W/H/X/Y exact | RECIPE-RECT-VERIFIED, appkb§12 |
| S6 | text create+edit | title-layout placeholder dbl-click→type | RECIPE-TEXT-VERIFIED, appkb§12 |
| S7 | color-contrast fix | white-on-white→dark text | memory[keynote-text-invisible-color-contrast] |
| S8 | minesweeper closed-loop | sense→judge→click cycles | perception/runner.rs, adr0007 M7 |
| S9 | grid auto-detect | no coord-dictation, locator finds window | perception/locator.rs (u_15) |
| S10 | ★end-to-end direct build | skytalent #about → 2 Keynote slides, NO shortcut | memory[about-direct-build-success], .key 571KB |
| S11 | plan-first workflow | plan→baseline-dump-once→continuous exec (no per-step screenshot-judge) | memory[plan-first-not-per-step-analysis] (K8) |
| S12 | press-drag-release | `input drag x1 y1 x2 y2 --scale 1.0` CGEvent LeftMouseDragged | actor.rs drag + a_49 live desktop |

---

## §4 GAPS — 미진한 부분 (must-fix / weak)
| gid | gap | impact | current cope | fix-direction |
|-----|-----|--------|--------------|---------------|
| G1 | ★text-box create UNSTABLE | blank-page toolbar text-button unreliable; a11y misses new AXTextArea (ar_41 M6) | RECIPE-TEXT-A (placeholder) / B (shape-as-container). Do NOT chase toolbar 텍스트 btn | keep A/B; VL only unlabeled |
| G2 | ★a11y CANVAS blind-spot | custom-render(canvas·chart·img·shape) invisible to AXUIElement | hybrid a11y + remote grounding (Holo when served; Qwen+consensus interim) | Holo1.5-7B @ 192.168.45.183 (user GPU PENDING). local UI-TARS rejected (u_43+90s) |
| G3 | worker context hygiene | long session quality collapse | ★RESOLVED: Grok auto_compact 70% (~350k/500k)+two_pass+memory_flush/pruning; CC autoCompactWindow 300k (ar_26) | keep short-a_ + save-every-2-3 (R5) |
| G4 | complex-GUI ceiling | pure-vision+no-coding hits limit on dense/nested UI | narrow scope, one-focus | hybrid a11y+remote-VL, recipe library growth. cf memory[vision-gui-complex-limit] |
| G5 | worker "done"≠real | report ≠ actual saved artifact | orch cross-verify (.key find + screenshot) | keep orch verify mandatory; save every 2-3 elements |
| G6 | drag (press-drag-release) | text-box draw / free drag | ★VERIFIED a_49: `input drag x1 y1 x2 y2 --scale 1.0` CGEvent LeftMouseDown→LeftMouseDragged*→Up; live desktop cursor travel. about-deck untouched | remaining R7: scroll + multi-select |
| G7 | single-app-at-a-time | multi-window/app-switch orchestration untested | raise=`open -a` verified (a_48: unfocused menu-only → `open -a Keynote` + open existing .key → toolbar 도형/차트 a11y) | window-focus mgmt via a11y; raise=open -a (no SE) |
| G8 | no self-recovery | tangle→needs human/orch reset | restart | detect-degradation→auto checkpoint+restart |
| G9 | speed = still slow | a11y<100ms but judge-loop + human-pacing slow | acceptable (speed-agnostic P1) | plan-first(S11) cuts per-step judge; remote VL ~0.3s warm (not local UI-TARS) |

---

## §5 REINFORCE — 보강할 부분 (build-out)
| rid | reinforce | why | how |
|-----|----------|-----|-----|
| R1 | ★REMOTE Holo1.5-7B fallback | closes G2 canvas. ScreenSpot-Pro 57.94 vs Qwen~29. Apache. vLLM | ground_vl.sh Holo-ready (0-1000→shot→LOGICAL). local UI-TARS = rejected (u_43+90s). User GPU install PENDING |
| R2 | ★appkb recipe library = the real asset | P3 no-hardcode means app-knowledge = DATA. recipes are how generic core drives specific apps | grow docs/appkb/*.md per app. each verified recipe = permanent capability. cf memory[tool-recipe-learning] |
| R3 | hybrid eyes (a11y⊕remote-VL) | a11y fast+exact labeled chrome; VL unlabeled | ground_hybrid.sh a11y-FIRST → NOTFOUND → remote VL. contract FOUND lx ly a11y-or-vl LOGICAL |
| R4 | compute/AI split discipline | speed+precision: coord-transform·a11y-coord=LOCAL compute; visual-judge only=AI | enforce: no AI for math. cf memory[compute-vs-ai-split] (u_85) |
| R5 | worker session hygiene | leftover after G3 resolved | keep short-a_ + save-every-2-3. auto-compact already on (Grok 70% / CC 300k) |
| R6 | orch cross-verify standard | G5 | always: worker report → orch screenshot + file-existence check |
| R7 | richer input verbs | G6 drag done (a_49) | remaining: scroll, multi-select in actor |
| R8 | K7/K8 discipline as default | consistency | a_/ar_=compressed-english (app UI labels stay Korean for a11y-match, memory[k7-app-label-exception]); plan-first standard (K8) |

---

## §6 INVARIANTS (must never break)
- **INV1 coord**: a11y logical + `--scale 1.0`. NO screenshot-pixel eyeballing, NO ×2/÷4 guess. (root-cause of all past misses.)
- **INV2 compute-vs-AI**: computable(coord-transform, a11y-derived position) = LOCAL compute. AI ONLY for "must-see-to-know" visual judgment. (u_85)
- **INV3 no-shortcut**: build the artifact by real app manipulation. screenshot-as-image / code-inject = BANNED. tool-self-extension = OK.
- **INV4 pure-IO**: keyboard·mouse·screen only. NO System Events/osascript control. (browser view ok.)
- **INV5 no app-hardcode**: generic core + recipe DATA. no per-app control-flow branch trees.
- **INV6 orch verify**: worker "done" ≠ real. orch confirms via file + screenshot.
- **INV7 respond-first(P1)**: user/telegram request → reply via ask_telegram.py BEFORE other work.

---

## §7 FINAL GOAL (최종 목적)
> **A universal, app-agnostic, pure-vision autonomous agent that operates ANY GUI like a human — eyes(see) + hands(physical IO) + brain(AI judge) — with ZERO app-specific fixed-logic.**

trajectory:
```
NOW ──────────────────────────────────────────────► GOAL
minesweeper loop            hybrid a11y+remote-VL      any-app, any-task
+ Keynote #about   ──►      LOGICAL contract;     ──►  self-recovering,
(recipe-per-app,            Holo when served;          session-hygienic,
 orch+worker,               Qwen+consensus interim;    generic core +
 auto-compact ON)           drag/scroll/window         growing recipe DATA
```
- milestone-next = **Holo on 192.168.45.183 + hybrid LOGICAL contract** (adapter ready; GPU install = user-other-PC).
- success-metric = drive a NEW app (never-scripted) to a correct visual outcome using only [see→judge→IO] + a freshly-learned recipe, no code, no shortcut, orch-verified.

---

## §9 HOW — driving an app w/ keyboard+mouse (실측 조작법)

### §9.1 the universal loop
```
SEE ──► LOCATE ──► ACT ──► VERIFY ──► (repeat)
 │        │         │        │
 │        │         │        └ re-capture: popup up? object created? text entered?
 │        │         └ click(cx,cy --scale 1.0) / input text / input key / chord
 │        └ a11y element {role,label,cx,cy} = LOGICAL pt  (canvas → remote VL fallback)
 └ see --a11y  (+ xcap screenshot for visual)
```
- **plan-first(K8)**: write plan(what/where-xywh/tool/color) → baseline dump ONCE → execute continuous. NO per-step LLM screenshot-analysis (worker executes deterministic coords/seq; screenshot = orch-verify only). memory[no-screenshot-self-analysis].

### §9.2 primitive ops (how each maps to kbd/mouse)
| op | mechanism | cmd |
|----|-----------|-----|
| point-click | move cursor→left-click at logical(cx,cy) | `input click cx cy --scale 1.0` |
| double-click (enter-edit) | 2× click same coord | `input click cx cy` ×2 |
| right-click | context menu | `input click cx cy --right` |
| ★drag | move start→LeftMouseDown→LeftMouseDragged interpolate→Up | `input drag x1 y1 x2 y2 --scale 1.0` (a_49 G6; --human paces) |
| type | unicode char stream | `input text "<s>"` |
| type-from-file | large text | `input type-file <path>` |
| shortcut | modifier+key | `input chord cmd a` (⌘A), `chord cmd n` (⌘N), `chord cmd s` |
| nav/game key | arrow·space·enter·esc·tab | `input key <name>` |
| ★object-delete | ⌫/forward-del | `input key backspace` / `input key delete` (a_40) |
- coord always LOGICAL + `--scale 1.0` (a11y-derived). window moved → re-dump a11y once, re-fix coords.

### §9.3 verified compound recipes (Keynote — the pattern generalizes)
- **new-doc**: `chord cmd n` → theme-card click(fixed coord) → "생성" click. deterministic, no screenshot-analysis. (RECIPE-NEWDOC)
- **precise shape place** (★no drag): 도형-btn → palette shape click → 정렬 tab → each field [click→⌘A→type value→enter]: W/H/X/Y in slide-pt(1024×768). drag = inaccurate/overlap → BANNED. (RECIPE-RECT-VERIFIED)
- **text create+edit**: title-layout slide → placeholder [double-click] → ⌘A → `input text` → esc. (blank-page toolbar text-btn = unreliable, see §10-F1). (RECIPE-TEXT-VERIFIED-A)
- **text-in-shape** (cards): shape selected → `input key enter` → `input text` → esc. shape = text container, sidesteps empty-textbox bug. (RECIPE-TEXT-VERIFIED-B)
- **save**: esc(exit edit fully) → File menu → 저장… → name → save. (⌘S mid-edit may fail, §10-F8)
- **field-edit rule**: click field → ⌘A(select existing) → type → tab(next)/enter. skip ⌘A → value appends to old.

---

## §10 WHY-FAIL — 왜 잘 안 되는가 (실패원인·원인·대책)
> every entry = empirically hit this session. cause → cope.

| fid | failure | root cause | cope / fix |
|-----|---------|-----------|-----------|
| F1 | ★blank-page text-box won't create | toolbar "텍스트" btn on empty slide only opens Text-tab, no AXTextArea spawns; a11y then reports 0 | RECIPE-TEXT-A placeholder / B shape-as-container (§9.3). Do NOT chase toolbar 텍스트 btn |
| F2 | ★a11y blind to canvas objects | AXUIElement exposes native UI chrome, NOT custom-render (canvas·chart·image·drawn shape) | hybrid: a11y labeled; remote VL unlabeled (Holo when served, Qwen+consensus interim) |
| F3 | ★coord miss (click lands wrong) | eyeballing screenshot-pixels + resolution triple-confusion(4112 shot / 3456 phys / 2056 logical) + wrong ×2/÷4 guess | RESOLVED: a11y logical + `--scale 1.0`. click code = X/scale(main.rs:195) → logical value+scale1.0 is exact. INV1 |
| F4 | ★text created but INVISIBLE | white text on white bg = contrast 0 → looks like "create failed" (it wasn't) | dark/black text on white bg. text-tab→color swatch. memory[keynote-text-invisible-color-contrast] |
| F5 | text hidden behind bg-shape | white bg-rect drawn last = on top, covers text | send bg [맨뒤로] or text [맨앞으로] (포맷>정렬 z-order) |
| F6 | worker context collapse | long session quality drop | ★auto-compact ON (Grok 70% + CC 300k). cope=auto-compact + short a_ + save-every-2-3 (R5) |
| F7 | ★⌘D-copy select-tracking tangle | duplicating cards via ⌘D then 정렬탭 X/Y → selection jumps to wrong object (applied to title box by mistake) | NO ⌘D. generate each card independently (shape→place→enter-text→deselect) repeat |
| F8 | ⌘S doesn't save | issued inside text-edit context → routes to text-select not save | esc to fully exit edit (canvas/thumbnail focus) THEN ⌘S, or File menu path |
| F9 | text goes to wrong box | double-clicked box holds edit focus; wrong box → text appends there | esc → re-double-click correct box. one box = one context |
| F10 | text wraps vertical / narrow | numeric width < font natural-width → forces vertical wrap | shrink font first, then set width ≥ natural. or accept placeholder default |
| F11 | field value appends to old | typed without clearing | ALWAYS ⌘A before typing in a field |
| F12 | text flipped/rotated | mis-click [뒤집기]/[각도] while setting color | 정렬탭 angle=0, un-flip |
| F13 | worker "done" ≠ real artifact | report trust; Keynote closed w/ unsaved | orch cross-verify: `find *.key` + screenshot. INV6 |
| F14 | complex/dense GUI ceiling | pure-vision+no-code limit on nested/dense UI | narrow scope, one-focus, grow recipes, hybrid eyes. memory[vision-gui-complex-limit] |
| F15 | app-activation missing | kongtrol can't focus/raise an app window | workaround: fresh doc / blank layout / toolbar btn brings focus. (candidate tool-self-extension) |
| F16 | single-modifier chord only | can't do ⌘⇧-combos in one chord | sequence or extend actor (candidate) |

---

## §11 APP-FUNCTION-MAP — 앱 기능 목록화 + 실시간 작동 현황
> legend: ✅ live now (verified working via [see→judge→IO], no code/shortcut) · ◐ partial/workaround · ✗ not yet · (n/a)
> "실시간 작동" = right now a human-like loop drives it on real screen.

### §11.1 Keynote (primary proven app)
| fn-id | function | kbd/mouse recipe | live? | note |
|-------|----------|------------------|:----:|------|
| KN-NEWDOC | new presentation | ⌘N → theme-card → 생성 | ✅ | RECIPE-NEWDOC, fixed coords |
| KN-ADDSLIDE | add slide (layout) | 슬라이드추가 btn → layout popup click | ✅ | title/blank layouts verified |
| KN-DELSLIDE | delete slide | thumbnail select → delete | ◐ | plausible, less-exercised |
| KN-TEXT-PH | text via placeholder | title-layout → dbl-click → ⌘A → type → esc | ✅ | RECIPE-TEXT-VERIFIED-A |
| KN-TEXT-BOX | text via toolbar box | toolbar 텍스트 btn (blank page) | ✗ | F1 — unstable, avoid |
| KN-TEXT-SHAPE | text inside shape | shape sel → enter → type → esc | ✅ | RECIPE-TEXT-VERIFIED-B (cards) |
| KN-SHAPE | insert shape | 도형 btn → palette → click | ✅ | rect/rounded-rect verified |
| KN-PLACE | precise position/size | 정렬 tab → W/H/X/Y numeric | ✅ | ★RECIPE-RECT-VERIFIED, no-drag |
| KN-FILL | shape fill color | 스타일 tab → 채우기 swatch → palette | ✅ | white/green picked |
| KN-TEXTCOLOR | text color | 텍스트 tab → color swatch | ✅ | contrast fix (F4) |
| KN-ZORDER | front/back order | 포맷>정렬>맨앞/맨뒤 | ◐ | used to fix F5 |
| KN-DELOBJ | delete object | select → key backspace | ✅ | a_40 |
| KN-SAVE | save file | esc → File>저장 → name | ✅ | RECIPE-SAVE, orch-verified .key |
| KN-IMAGE | insert image/media | 미디어 btn / drag file | ◐ | canvas=a11y-blind (F2); hybrid VL exists, accuracy waits Holo |
| KN-CHART | insert chart+data | 차트 btn → 2D → type → 데이터편집 | ✗ | not exercised; canvas-heavy |
| KN-TABLE | insert table | 표 btn → style → cell dbl-click | ✗ | not exercised |
| KN-ALIGN-MULTI | multi-select align | shift-click → 포맷>정렬 | ✗ | drag-box/shift multi untested |

**Keynote E2E proven**: skytalent #about → 2 full slides (hero text + 5 blue cards), NO shortcut, orch-verified 571KB. memory[about-direct-build-success].

### §11.2 minesweeper (native app — closed-loop proof)
| fn-id | function | mechanism | live? |
|-------|----------|-----------|:----:|
| MS-DETECT | auto-detect grid/window | locator (no coord-dictation) | ✅ |
| MS-SENSE | read board state | sensor + grid model | ✅ |
| MS-JUDGE | decide open/flag | perception/minesweeper.rs | ✅ |
| MS-ACT | click cell / flag | physical click | ✅ |
| MS-LOOP | sense→judge→act cycles | runner.rs (adr0007 M7) | ✅ |

### §11.3 generic input (any app, app-agnostic core)
| fn-id | function | live? | note |
|-------|----------|:----:|------|
| IN-SEE | a11y element dump | ✅ | native UI only (F2 canvas gap) |
| IN-SHOT | screenshot capture | ✅ | xcap |
| IN-CLICK/MOVE | mouse | ✅ | scale-aware |
| IN-TYPE | keyboard text | ✅ | unicode |
| IN-CHORD | shortcut | ◐ | single-modifier (F16) |
| IN-KEY | arrow/enter/esc/tab/bs/del | ✅ | a_40 |
| IN-DRAG | press-drag-release | ✅ | a_49: `input drag x1 y1 x2 y2 --scale 1.0` CGEvent press-drag-release; live desktop; about-deck off-limits |
| IN-SCROLL | wheel scroll | ✗ | not impl |
| IN-VISION-GROUND | remote VL coord for canvas | ◐ | hybrid exists (ground_hybrid.sh LOGICAL); accuracy waits Holo |

### §11.4 what "live now" sums to
- ✅ **drive Keynote to a designed slide deck** end-to-end (text·shape·color·place·delete·save) via pure human-like IO.
- ✅ **play minesweeper** self-detecting + closed-loop.
- ✅ **generic mouse/keyboard/see/drag** on any native-UI app (`input drag` a_49).
- ◐ **canvas-content apps** (image/chart/table/drawing): hybrid a11y+remote-VL exists; accuracy waits Holo @ 192.168.45.183 (§7).

---

## §12 CROSS-REF
- adr: docs/adr/0007-perception-decision-loop
- code: kongtrol/src/main.rs (dispatch_see·dispatch_input·dispatch_game), perception/{a11y,actor,locator,runner,minesweeper}.rs; actor.drag + cli InputVerb::Drag (a_49)
- appkb: docs/appkb/keynote.md §12 (verified recipes)
- research: kongtrol/demo/vision_gui_agent_research.md (UI-TARS·Agent-S2·a11y bench)
- memory: kongtrol-direction-ai-realtime · kongtrol-universal-agent-core · vision-gui-complex-limit · breakthrough-a11y-uitars · compute-vs-ai-split · keynote-two-coordinate-systems · plan-first-not-per-step-analysis · about-direct-build-success · worker-session-no-autocompact · pure-io-no-system-events · tool-recipe-learning · no-screenshot-shortcut-build-directly · keynote-text-invisible-color-contrast
