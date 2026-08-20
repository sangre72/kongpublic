# kong-bot

*English | [한국어](./README.ko.md)*

> An AI agent system that looks at the screen and acts like a human — observing, judging, and operating the mouse/keyboard the way a person would.
> Takes instructions over Telegram and completes tasks by physically operating GUI apps (Krita, Keynote, browsers, etc.).

## Motivation

MCPs, skills, and APIs are all great — but as products mature and user bases grow, most of them eventually get monetized in some way. That's a reasonable business decision, but it also means every new integration tends to come with a new subscription, a new API key, a new bill.

This project started from a different premise: I already own a desktop, and I already own (or can freely use) a set of real applications — a drawing tool, a presentation tool, a browser. Instead of paying again for an AI-native version of each of those, why not let an AI agent simply *use the apps I already have*, the same way I would — by looking at the screen and operating the mouse and keyboard?

kong-bot exists to make that possible: giving AI free, direct access to any app you already own or can use for free, without requiring a new paid integration for every tool.

## Demo

Each clip below records the same end-to-end automated flow: **start screen recording → open AlDente and change its battery charge-limit (%) → quit the app → stop screen recording.** Nothing is scripted or faked — every step is the agent actually looking at the screen and physically clicking/typing, the same way a person would.

This clip records the very first time kong-bot ran/operated the AlDente app, triggered by a live user request.

![kong-bot demo preview](./docs/media/kongbot-aldente-demo-preview.gif)

*Sped up ~9x (real elapsed ~13.5 min compressed to 90s). Full clip: [docs/media/kongbot-aldente-demo-90s.mp4](./docs/media/kongbot-aldente-demo-90s.mp4)*

**After the recipe was learned** (same task — AlDente charge-limit change + close), a second run reused the saved recipe and finished in ~3.3 min real time (807s → 198s), about 4x faster than the first, first-contact run — with no trial-and-error on the window-close step this time.

![kong-bot demo preview (recipe reused)](./docs/media/kongbot-aldente-demo2-preview.gif)

*Sped up ~2.2x (real elapsed ~3.3 min compressed to 90s). Full clip: [docs/media/kongbot-aldente-demo2-90s.mp4](./docs/media/kongbot-aldente-demo2-90s.mp4)*

**Third run, zero-detour**: after a coordinate-calculation bug surfaced and got root-caused (screenshot-pixel-to-logical-coordinate math turned out to be fundamentally unreliable in this environment — see [Limitations](#limitations) — and was replaced with an a11y-anchor method), this run executed the full sequence — start recording, relaunch AlDente, set charge-limit to 75%, fully quit the app, stop recording — with **zero retries on any single click**. Real elapsed time: ~2.1 min (128s), the fastest of the three runs, despite doing a full app-quit (not just closing a window) this time. The recipe itself has now been reused cleanly across 4 separate runs.

![kong-bot demo preview (zero-detour run)](./docs/media/kongbot-aldente-demo3-clean-preview.gif)

*Sped up ~1.4x (real elapsed ~2.1 min compressed to 90s). Full clip: [docs/media/kongbot-aldente-demo3-clean-90s.mp4](./docs/media/kongbot-aldente-demo3-clean-90s.mp4)*

| Run | Task | Real elapsed | Notes |
|---|---|---|---|
| 1 | first contact w/ AlDente, set 80%, close window | 807s (~13.5 min) | recipe built from scratch, several dead-ends |
| 2 | reuse recipe, set 90%, close window | 198s (~3.3 min) | learned recipe reused verbatim, no trial-and-error on close |
| 3 | reuse recipe, set 75%, full quit, zero-detour | 128s (~2.1 min) | a coordinate-math root-cause fix (pixel-math → a11y-anchor) made this run fully clean — every click succeeded on the first try |

See [How recipes get built](./docs/appkb/recipe-howto.md) for the methodology behind this learn-once-reuse-forever loop.

## Overview

kong-bot runs as a two-role collaboration between a **Orchestrator (orch)** session and a **Worker** session, both powered by Claude.

- The **user** sends natural-language instructions over Telegram.
- The **Orchestrator** turns those instructions into executable task specs (`a_*`), hands them to the Worker, verifies the results (`ar_*`), and reports back over Telegram.
- The **Worker** looks at the real screen (`kongtrol see`), decides what to do, and physically operates the mouse/keyboard (`kongtrol input`) to carry it out.

The core principle is **"never fabricate the deliverable via script."** Whether it's a slide deck or a drawing, the output must be produced by actually operating the target app like a human would — no shortcut of generating the artifact directly from code or a whole-image paste. There's also no per-app hardcoded control logic: a single generic core drives whatever app is on screen, and app-specific knowledge accumulates as reusable data (`kaymaps/`) rather than as branching code.

## Purpose

1. **Human-like GUI automation**: not a macro with pre-baked coordinates, but a real-time loop of [observe → judge → physical input].
2. **A generic agent core**: no per-app driver code — one core handles any GUI app.
3. **Accumulated learning**: once a manipulation (click coordinates, menu path, color-selection formula, etc.) is verified, it's saved as a recipe and reused without re-deriving it from scratch.
4. **Remote collaboration**: issue instructions and watch progress from anywhere via Telegram.

## Architecture

```
                          User (Telegram)
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Orchestrator (orch)   │
                    │  - refine instruction    │
                    │    (u_ → a_)             │
                    │  - verify result (ar_)   │
                    │  - report/ask via Telegram│
                    └───────────┬───────────┘
                                │ protocol/{a,ar}
                                ▼
                    ┌───────────────────────┐
                    │        Worker           │
                    │  ┌─────────────────┐  │
                    │  │  BRAIN (judge)   │  │
                    │  │  "what to do"    │  │
                    │  └────────▲────────┘  │
                    │           │ screen info/decision│
                    │  ┌────────┴────────┐  │
                    │  │ EYES  │  HANDS  │  │
                    │  │(see)  │ (act)   │  │
                    │  └───────┴─────────┘  │
                    └───────────┬───────────┘
                                │ kongtrol CLI
                                ▼
                    ┌───────────────────────┐
                    │      Target GUI app      │
                    │  (Krita, Keynote, ...)  │
                    └───────────────────────┘
```

### Layer responsibilities

| Layer | Implementation | Role |
|-------|-----------------|------|
| **Eyes** | `kongtrol see --a11y`, screenshots | Extracts UI elements (role/label/coords) as logical points, plus pixel-level visual info |
| **Hands** | `kongtrol input` (click/move/drag/text/key) | Injects real mouse/keyboard events (CGEvent-based, with human-paced timing) |
| **Brain** | Claude (Worker session) | Decides the next action from the screen state. Coordinates are computed, but *what* to click is judged visually |
| **Protocol** | `telegram_bot/orchestrator/protocol/{u,a,ar}` | Exchange of instruction/result files between orch and worker |
| **Recipe** | `kaymaps/<app>/RECIPE_*.txt` | Reusable storage of verified manipulations per app (exact coordinates, menu paths, formulas, etc.) |

### Screen scale

Click coordinates must always be **a11y logical coordinates + `kongtrol input click --scale 1.0`** — never raw pixel coordinates from a screenshot.

- This dev environment's actual display scale is **2x (Retina)**. A screenshot's pixel size (e.g. 4112x2658) is not the same as the logical coordinate space the click layer expects — pixel coordinates must be divided by the scale factor before use.
- Any external model that returns coordinates from an image (local VL server, OmniParser, etc.) returns **screenshot-pixel-based** coordinates. Never feed those directly into a click — always convert to logical coordinates first.
- When in doubt, prefer `kongtrol see --a11y` output (already logical) over deriving coordinates from a screenshot.

### Using VLM binary judgment (`kongtrol see --vl`)

`kongtrol see --vl "<prompt>"` captures a screenshot, resizes it to 640px, and sends it to a local VL server (Qwen3-VL-8B) for a text judgment. It's a fallback for canvas-rendered UIs (CapCut, Google Flow, etc.) where `--a11y` returns few or no labeled elements — a11y stays the first choice everywhere it works.

**When to use (measured, ar_942/ar_943):**

| Judgment shape | Accuracy | Avg latency | Verdict |
|---|---|---|---|
| Binary presence ("is X open/visible?") | 4/5 correct | ~0.45s | ✅ usable |
| Small count (1–2 items) | 4/5 correct | ~0.45s | ✅ usable |
| Screen-type classification | good | ~2–5s | ✅ usable |
| Exact count (3+ items) | 0/5 correct | ~2–5s | ❌ do not use |
| Verbatim text quote | 0/5 correct | ~2–5s | ❌ do not use, hallucinates |
| Full menu/list enumeration | 0/5 correct | ~2–5s | ❌ do not use, hallucinates |

The failure mode on the "do not use" side isn't just wrong answers — it fabricates plausible-looking UI that isn't there (e.g. inventing menu items, quoting text that was never on screen). Never trust VL output for anything you'd act on without an independent check when the judgment is in that category.

**Example**: `kongtrol see --vl "Is a transition icon present at the clip boundary? yes/no"` — appropriate. `kongtrol see --vl "List every item in the left sidebar"` — not appropriate, use `--a11y` or read the screenshot directly instead.

## Limitations

- **VLM judgment is unreliable for detail**: the local VL model (`kongtrol see --vl`) is only trustworthy for binary presence/absence and small counts (see measured table below). For exact counts, verbatim text, or full-list enumeration, it hallucinates plausible-looking-but-wrong answers (0/5 accuracy, measured) — those cases require `--a11y` or a zoomed screenshot crop read directly instead.
- **GUI-grounding benchmark models not yet adopted**: specialized click/grounding models (e.g. UI-TARS-style) were evaluated early on but the integration was deferred — the current pipeline relies on `--a11y` logical coordinates as the primary source and VLM only as a binary-judgment fallback, not a full grounding replacement.
- **Occasional unexplained dev-server stalls**: one integration target (a local `uvicorn --reload` dev server used in an early demo) intermittently stopped responding for 20–80s at a time with no confirmed root cause (the server's own source lives outside this repo, so only black-box, read-only diagnosis was possible). The current workaround is wait-and-retry; a code-level fix would require access to that server's source.
- **Coordinate/text-input recipes are accumulated empirically, not exhaustively**: `kaymaps/` only covers the apps and UI elements the agent has actually encountered and verified — coverage grows recipe-by-recipe through real use, not from a pre-built UI catalog.

## Roadmap

- Broaden recipe coverage across more apps/UI-element types (the empirical-learning model in `kaymaps/` scales with usage, not upfront effort).
- Strengthen the single-worker/single-fork discipline in the orchestrator↔worker protocol (avoid duplicate/parallel actuation on the same physical mouse/keyboard target).
- Continue hardening long-running-session stability (crash/trust-dialog/session-liveness watchdogs already exist; keep extending coverage as new failure modes surface).
- Revisit dedicated GUI-grounding models if/when the `--a11y`-first + VLM-binary-fallback approach hits a coverage wall on canvas-heavy apps.

## Directory structure

```
kongtrol/               Rust-based pure-IO tool (screen perception + mouse/keyboard CLI)
telegram_bot/            Telegram bot + orchestrator/worker protocol
  orchestrator/
    protocol/{u,a,ar,done}   user instructions · task specs · result reports
kaymaps/                  Verified per-app manipulation recipes (accumulated learning)
  _common/                App-agnostic general principles/lessons
  krita/, keynote/        Per-app coordinates, formulas, procedures
docs/                     ADRs, app knowledge base, research notes
```

## License

This project is distributed under the [PolyForm Noncommercial License 1.0.0](./LICENSE).

- **Personal / noncommercial use** (research, learning, hobby projects, nonprofits, educational institutions, etc.): free to use, modify, and distribute.
- **Commercial use** (companies, etc.): requires a separate commercial license agreement. Contact the repository maintainer to inquire.
