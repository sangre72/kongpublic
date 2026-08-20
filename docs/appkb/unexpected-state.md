# Unexpected-state FAST detect (orch+worker)

> Exception-screen ≠ goal-feature. Human spots fail/wrong-page instantly. Detect mismatch FAST, then **route**. Do not continue the planned feature. Research#1 (a_68). **No implement** here.

BAN: per-step shot-analyze (a_36) · new VL loop · type password · invent uncited methods.

---

## 0. Human analog (why FAST)

Human: glance URL/title + window chrome + 2–3 keywords + “is this the planned app/screen?” in **<200ms**. No SSIM. Exception → stop/handoff, not “keep doing the feature.”

---

## 1. How cited systems RUN (not abstracts)

| System | Signal | When checked | Extra cost | FP / recover |
|--------|--------|--------------|------------|--------------|
| **Claude Computer Use** | Screenshot VLM-judge in agent loop. Prompt-injection **classifier on every shot** → ask user before next act. Official tip: *after each step, screenshot + evaluate if outcome is right*. `wait` action. | **Every step** (model requests `screenshot`) | API VLM **~2–8s**/step (shot+reason). Classifier extra. | Classifier → confirm, not auto-act. Max-iter cap. Isolated VM. [docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool) |
| **OpenAI CUA / Operator** | Screenshot + CoT every loop. **Takeover** on login/pay (no shot of secrets). Confirm before order/email. Watch-mode on mail/finance. | **Every step** shot. Takeover **on sensitive field**. | Same order as CU (seconds/step). | Self-correct via next shot. Stuck → hand control to user. [Operator](https://openai.com/index/introducing-operator/) · [CUA](https://openai.com/index/computer-using-agent/) |
| **browser-use** | **URL + title + tabs + interactive DOM** every step. Shot only if `use_vision` on/`auto` requested. Structured `evaluation_previous_goal` = Success/Failed/Unknown. | **Every step** unless `flash_mode` (skips eval/thinking). | DOM/state **0.5–3s** + LLM. `TIMEOUT_BrowserStateRequestEvent` 30s. Vision extra. | `max_failures=3` then stop/final. Captcha = **stealth/cloud**, not in-loop solve. [params](https://docs.browser-use.com/open-source/customize/agent/all-parameters) · [github](https://github.com/browser-use/browser-use) |
| **Agent-S (S1–S3)** | Dual: shot (popup / did last act work?) + **a11y tree** + OCR fill-in (PaddleOCR/tesseract). Worker emits **previous-action-status** each step. Trajectory Reflector during subtask. Self-Evaluator at DONE/FAIL/max-steps. S3 **bBoN judge** at end (facts→narrative→pick best run). | Status **every step**. Reflect **during episode**. Eval **subtask/task end**. bBoN **end**. | Ubuntu a11y dump **3–26s** (OSWorld-efficiency). macOS AX **~0.33s** (ar_24). Reflect = extra LLM. | FAIL → Manager **replan**. Reflect: avoid-repeat. Judge vs official 78%; vs human 93%. [S1](https://arxiv.org/abs/2410.08164) · [S3](https://arxiv.org/abs/2510.02250) · [code](https://github.com/simular-ai/Agent-S) |
| **WebArena evaluator** | **End-only programmatic**: `url_match` · `string_match` (exact / must_include) · `program_html` (JS locator) · optional `fuzzy_match` (GPT-4). Agent **in-loop** sees a11y + URL (not DOM-full). | Eval = **end**. Agent obs = **every step**. | Eval **ms**. Agent a11y compact. | Deterministic locators → 0 VLM-FP. UA-hint: GPT-4 marked **55% of feasible** as impossible (stop-FP). [paper](https://arxiv.org/abs/2307.13854) |
| **VisualWebArena evaluator** | Same programmatic + image locators for visual tasks. Agent: a11y ± **SoM screenshot** / captioner. | Eval **end**. Agent **every step**. | SoM/caption GPU extra. | Same as WA. Human ~89% on 233-task sample. [repo](https://github.com/web-arena-x/visualwebarena) · [paper](https://arxiv.org/abs/2401.13649) |
| **OSWorld evaluator** | **End-only execution script** (file/app/DB state). **No LLM-judge** on success path. Agent in-loop: shot ± a11y. | Eval **end**. Agent **every step**. | a11y 3–26s Ubuntu. Shot cheaper. | Programmatic = 0 VLM-FP. [OSWorld](https://github.com/xlang-ai/osworld) · [Xie+2024](https://arxiv.org/abs/2404.07972) |
| **SeeAct / WebVoyager** | SeeAct: **every step** GPT-4V on shot+HTML → action then grounding. Error **banner on shot** → fix first (self-correct). WebVoyager: SoM shot every step; **GPT-4V judge at END** on last-k shots + task + reply (T=0, 3 runs). | SeeAct detect **in-loop**. Voyager judge **end**. | Seconds/step (GPT-4V). End-judge = extra 1–3 VLM. | SeeAct: no-login tasks (ethics). Voyager 3-run majority; auto-eval known noisy. [SeeAct](https://osu-nlp-group.github.io/SeeAct/) · [WebVoyager](https://arxiv.org/abs/2401.13919) |
| **Aria-UI + critic/reflection** | Aria-UI = **grounding only** (pure-vision, no AXTree). History (text or text+image) for context. **Not a fail-class detector.** Critic pattern lives in planner: Agent-S reflector · GUI-Reflection · MobileUse Action Reflector (before/after shot → “did act land?”). | Grounding **per click**. Critic **per act** (those systems). | Aria-UI 3.9B-act MoE, fast vs GPT-4V. Critic = extra VLM. | Grounding FP ≠ unexpected-class. Do not use Aria-UI as exception classifier. [Aria-UI](https://arxiv.org/abs/2412.16256) · [GUI-Reflection](https://arxiv.org/abs/2506.08012) · [MobileUse](https://arxiv.org/abs/2507.16853) |

**Not used by cited runtimes as primary detect:** pixel-hash / SSIM. Do not add.

---

## 2. Exception classes

| Class | Cheap signal (URL / a11y / keyword) | Escalate VL? | Route |
|-------|-------------------------------------|--------------|-------|
| **login-fail** | URL login/nid/accounts + a11y “비밀번호가 틀렸/incorrect password/로그인 실패” | only if cheap miss | STOP + tg KO + shot. **0 password type.** |
| **session-dead / login-wall** | host login + fields 아이디/비밀번호/Sign in + missing goal labels (inbox, etc.) | no if URL+fields hit | **→ [login-handoff.md](./login-handoff.md)** (a_67). Do not rewrite. |
| **captcha** | keyword captcha/recaptcha/클라우드플레어/I’m not a robot · iframe/challenge | 1 VL if unlabeled widget | STOP + tg + shot. No auto-solve (browser-use: stealth, not in-loop). |
| **error-toast-dialog** | `AXDialog`/`AXAlert`/`AXSheet` + 오류/에러/실패/Error/failed/unable | no if role+kw | Dismiss if known (확인/OK/닫기) **1 try** then re-check. Else STOP+tg. |
| **permission-popup** | dialog 위치/알림/카메라/마이크/Allow/Block/접근 허용 | no if role+kw | Known: click Deny/허용안함 if recipe says. Else STOP+tg. |
| **wrong-URL-or-app** | frontmost app ≠ expected · host/path ≠ step signature | no | STOP or recover-nav if 1-hop known. No continue feature. |
| **empty-or-crash** | a11y count ~0 / “응답 없음” / crash reporter / blank webarea | 1 VL if a11y empty (could be canvas) | STOP+tg. Do not invent content. |
| **not-the-planned-screen** | expected-signature labels **absent** + unexpected chrome present | **1 VL** “expected? Y/N + class” | N → class route. Y → continue. |

Naver wall already measured (ar_61): window=`NAVER 로그인` · fields 아이디/비밀번호 · URL nid/mail login. Inbox labels absent.

---

## 3. 1st recipe (kongtrol) — cheap first

Constraints: a11y-first (a_24) · no per-step shot-analyze (a_36) · remote VL only unlabeled · 0 password.

### Per-step expected-signature (planner writes, worker checks)

```
app: Chrome|Keynote|…
url_host: mail.naver.com          # web only; omit native
url_must_not: nid.naver.com, accounts.google.com
title_any: ["메일", "Inbox"]
need_any: ["받은메일함", "메일 목록"]   # ≥1 present = likely right
forbid_any: ["NAVER 로그인", "비밀번호", "captcha"]
expect_dialog: none | "저장" | "테마"    # expected sheet ≠ error
```

### Gate (every step, **no VL**)

1. **App** — frontmost vs `app`. Miss → `wrong-app`.
2. **URL/title** — host/path vs signature (ignore most query; **keep** login paths). Miss → `wrong-url` or `login-wall`.
3. **a11y cheap** (~0.33s dump, ar_24) — scan role + labels:
   - role contains `Dialog|Alert|Sheet` **and** not `expect_dialog` → toast/permission/error.
   - `forbid_any` hit (≥1 strong or 2 weak) → class.
   - `need_any` all absent → `not-planned` (cheap miss).
4. **a11y empty / crash keywords** → `empty-or-crash`.

Budget: URL/title **<10ms** + dump **~330ms** + scan **<5ms**. **≪ 1 VLM.**

### Escalate (only cheap miss)

**1 local VL** (`kongtrol see --vl "<prompt>"`, cf ar_942/943), one shot, prompt: `expected-signature? Y/N + class=<one of §2>`. Not per-step. Not grounding. Unlabeled only.
★measured (ar_942/943, 2026-08-19): binary/simple-count judgments (Y/N present, screen-type, 1–2 item count) = **4/5 correct, ~0.45s avg** — usable here since this gate is exactly that shape (Y/N + one-of-N class). Detailed judgments (exact count ≥3, verbatim text quote, full menu enumeration) = **0/5 correct** — do NOT use VL for those; stay a11y/computed. See README "VLM binary 판단 활용" for the split.

### Route

| Detected class | Action |
|----------------|--------|
| login-wall / session-dead / login-fail | **[login-handoff.md](./login-handoff.md)** — immediate tg method-shot, STOP, 0 password. |
| captcha | STOP + tg KO + shot. No solve. |
| error-dialog / permission | known dismiss 1× → re-gate. else STOP+tg. |
| wrong-url/app | 1 known hop (back / reopen app) **or** STOP+tg. |
| empty-or-crash | STOP+tg. |
| not-planned + VL=N | STOP+tg unless known recover. |
| VL=Y or cheap pass | continue recipe. |

STOP = needs-info. Shot for orch/user, **worker does not self-analyze** (a_36).

### FP rules (from cited)

- Dialog ≠ always error (save / theme / Keynote 생성). Gate with `expect_dialog`.
- One keyword is weak (로그인 appears in nav). Prefer **role+kw** or **2 kws** or **URL+kw**.
- WebArena UA-hint: over-stop is a real FP — do not treat “unsure” as fail. Cheap miss → **1 VL**, not STOP.
- `flash_mode` / skip-eval = faster + more drift. **Do not skip this gate.**
- Pixel-hash unused by cited systems — skip.

---

## 4. Detect → route (1 page)

```
step expected-signature
        │
        ▼
 [app] [URL/title] [a11y role=dialog/alert + keyword bank]   ← every step, ~0.3s
        │
   pass? ──yes──► continue feature
        │
        no (cheap miss)
        ▼
 1 remote VL: "expected? Y/N + class"     ← only here; a_36
        │
   Y ──► continue
   N ──► class:
           login-*     → login-handoff.md (a_67)
           captcha     → STOP + tg + shot
           dialog/perm → known dismiss 1× else STOP+tg
           wrong/empty/other → STOP + tg KO + shot
```

---

## 5. Keyword bank (seed; extend per site in appkb)

Strong: `비밀번호가 틀렸` `incorrect password` `session expired` `로그인하세요` `Sign in to continue` `captcha` `reCAPTCHA` `Access denied` `403` `404` `응답 없음` `quit unexpectedly`  
Weak (need 2 or +role/+URL): `로그인` `Sign in` `허용` `Allow` `오류` `Error` `확인`

Naver wall (ar_61/62): `NAVER 로그인` + `아이디 또는 전화번호` + `비밀번호` + nid host.

---

## 6. Leftover

- Recipe **not implemented** (research only).
- a11y dump today keeps labeled/clickable roles — unlabeled `AXDialog` may drop (see `a11y.rs` filter). Include Dialog/Alert/Sheet when implementing.
- Per-site banks beyond Naver = unfilled.
- VL class accuracy **measured for binary/simple-count shape** (ar_942/943, 4/5·~0.45s) — full multiclass §2 escalate prompt not separately re-tested, inherits binary-shape result since prompt asks Y/N+class not free enumeration.
- login-handoff.md = a_67 (cite only).
