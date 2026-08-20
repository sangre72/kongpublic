# How recipes get built

kong-bot's `kaymaps/` directory is a growing library of verified, reusable manipulation procedures — click coordinates, menu paths, text-entry workarounds, window-lifecycle patterns — accumulated from real task execution rather than pre-built from a UI catalog. This doc explains the methodology behind that accumulation loop, so the pattern is consistent across every new app the agent touches.

## The core loop

1. Worker attempts a task with no existing recipe (or an incomplete one).
2. It hits friction — a click that misses, a field that behaves unexpectedly, an app that ignores a standard shortcut.
3. It diagnoses the friction, finds a working method, and **writes that method down immediately** — not "later," not "once everything's polished."
4. The next time the same task comes up, the recipe is reused as-is. If it works cleanly, a verification counter goes up. If it doesn't, the recipe gets corrected on the spot.

This is deliberately different from writing documentation after the fact. The recipe *is* the record of what actually happened, written by the same agent that just lived through the friction — which is why it captures failure modes ("tried X, didn't work, here's why") as precisely as it captures the successful method.

## (a) Compressed-format convention (K7)

Recipes are **not written as Korean prose or long narrative explanations.** They follow a compressed, keyword-driven format — the same discipline applied to `a_`/`ar_` task-protocol files elsewhere in this project (see `telegram_bot/orchestrator/worker_1.txt`'s COMPRESSED-EN-REPLY rule).

Standard section keywords, in order:

```
RECIPE: <name>(<app>, <short context>)
REG: <task-id that created/last-touched this>(<date>)
WHY: <what problem this solves, 1-3 sentences, terse>

STEPS:
1. <step>
2. <step>
   - FAIL(tried, NOT working): <method> — <why it failed>
   - ✓WORKING: <method that actually works>
...

VERIFY:
- <how to confirm the step/recipe succeeded, concretely — a command, a visual check, a file existing>

LIMIT/OPEN:
- <unresolved questions, environment-specific caveats, things not yet empirically tested>
```

**One exception**: actual UI label text (a button's real on-screen name, a menu item's exact wording) stays in its native language — e.g. `"설정 열기"` stays Korean even in an otherwise-English recipe, because that's literally what's rendered on screen and matching it precisely matters more than translating it.

Real example — `kaymaps/aldente/RECIPE_set_charge_limit.txt` opens with:

```
RECIPE: set_charge_limit(AlDente, macOS menubar app)
REG: a_982(2026-08-20), retrofit-compressed a_985
WHY: dashboard "충전 제한"(K7 app-label, keep-orig) field=custom AXTextField, std
delete/backspace NOT working(digits just append, 100→10080 pollution repeat)...
```

## (b) GATE_POLICY — verification before trust

A recipe that "worked once" is not automatically trusted. `kaymaps/GATE_POLICY.txt` defines the promotion path:

1. **1st success** → mark `tentative`, `verified_runs: 0`. Don't register it in the app's `RECIPE_index.json` yet.
2. **2nd successful reproduction** (separate run, ideally with the exact same procedure) → promote to `verified_runs: 1`, register in the index with `gate: "2-run-verified"`.
3. Each further clean reuse increments the counter — `kaymaps/aldente/RECIPE_index.json`'s `set_charge_limit` entry reached `verified_runs: 4` after four separately-executed, independently-successful runs.
4. If reproduction **fails or diverges**, the recipe is **not** promoted — the divergence gets logged in the task's result report (`ar_*`) instead of silently overwriting the recipe.

Why this matters: a recipe born from a single lucky run can encode an accident rather than a real method (this project has a documented case — a 3x-corrected recipe from early in the project's history that looked right after one try and wasn't). The gate forces a second independent confirmation before the recipe is trusted as a standing reference.

## (c) FIX-THEN-RECIPE-SYNC — no lag between discovery and documentation

When a problem is found and fixed **mid-task**, the recipe gets corrected in the same turn, not deferred to a follow-up pass. This project hit this concretely: a coordinate-calculation bug (screenshot-pixel-to-logical-coordinate math, assumed-resolution constants that turned out unreliable — see (d) below) was diagnosed and fixed live while a task was still in progress, and the fix was written into `kaymaps/_common/RECIPE_screenshot_coord_conversion.txt` and the two recipes that depended on it (`RECIPE_close_app_dock.txt`, `RECIPE_set_charge_limit.txt`) **before** the task itself was reported complete.

The rule of thumb: if the next person (or the next agent run) reading the recipe today would hit the same wall you just climbed out of, the recipe isn't done yet — even if the *task* is.

## (d) Prefer a11y-anchor over pixel-math

A specific, hard-earned lesson worth calling out on its own: **deriving click coordinates from screenshot pixel measurements plus an assumed display-scale constant is unreliable in this environment**, and should not be the default approach.

Across several runs, multiple different "actual" resolution values were tried (a carried-over assumption, a value read from `system_profiler`'s text output, a *different* value from that same command's own `-json` output) — every pixel-math attempt using any of them produced coordinates that missed small targets like menubar icons, sometimes repeatedly.

The fix that actually worked: query the accessibility tree (`kongtrol see --a11y`) for the target window's `AXWindow @(center_x,center_y)[width,height]`, and derive click targets from that — either directly (for a11y-exposed buttons/fields, which is always the first choice) or by a small fixed offset from the computed window corner (for un-labeled chrome elements like traffic-light buttons, which often aren't individually exposed to a11y). This coordinate space is already what `kongtrol input click` expects — no scale-factor conversion, no resolution query, no ambiguity.

See `kaymaps/_common/RECIPE_screenshot_coord_conversion.txt` for the full failure-mode writeup and `kaymaps/_common/RECIPE_window_lifecycle.txt` for how this applies across an app's Quit/Minimize/Close decision tree.

## (e) Where recipes live

- **`kaymaps/<app>/`** — app-specific recipes (e.g. `kaymaps/aldente/RECIPE_set_charge_limit.txt`). One file per distinct manipulation; an app with multiple learned procedures gets multiple files plus a `RECIPE_index.json` listing them with their verification status.
- **`kaymaps/_common/`** — cross-app, general-purpose recipes: things that apply regardless of which app is on screen. Examples from this project: `RECIPE_close_app_dock.txt` (generic app-close-via-Dock pattern), `RECIPE_screenshot_coord_conversion.txt` (the a11y-anchor principle above), `RECIPE_screen_recording.txt` (macOS screen-recording start/stop, all 3 capture modes), `RECIPE_window_lifecycle.txt` (Quit vs Minimize vs Close decision tree).
- **`RECIPE_index.json`** (one per directory that has multiple recipes) — the GATE_POLICY-tracked registry: `{name, app, desc, verified_runs, gate, file}` per entry.

A recipe that turns out to be broadly applicable often starts life inside an app-specific file and gets promoted/extracted to `_common/` once a second, unrelated app hits the same underlying problem — that's exactly how the coordinate-conversion lesson above moved from being an AlDente-specific note into a standalone `_common/` recipe referenced by multiple app recipes.
