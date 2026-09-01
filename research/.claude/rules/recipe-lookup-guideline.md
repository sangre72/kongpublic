# Recipe Lookup Guideline (MUST — user 2026-08-20)

> **Always consult existing recipes BEFORE starting any new task.** Recipe = ground truth for established workflows. Prevents re-invention, ensures consistency, surfaces known pitfalls.

Applies: all worker tasks (UI automation, app interaction, batch workflows).

---

## Recipe Search Order (per context type)

### 1. App-based task (e.g. Keynote, Krita, VSCode, CineBot)
**Search by app name** in `kaymaps/` directory:
```
kaymaps/<app-or-domain>/RECIPE_*.txt
```
- Example: CineBot fortune gen → `kaymaps/localhost-cinebot/RECIPE_fortune_12_full_flow.txt`
- Example: YouTube upload → `kaymaps/chrome/youtube/RECIPE_scheduled_upload.txt`
- Example: Keynote placement → `kaymaps/keynote/RECIPE_*.txt`

**Lookup method**:
```bash
find kaymaps -name "*<app-name-or-domain>*" -type d
ls kaymaps/<app-or-domain>/RECIPE_*.txt
grep -r "<feature>" kaymaps/<app-or-domain>/
```

### 2. Browser URL-based task (e.g. localhost:4000, web service)
**Search by URL/port** in `kaymaps/` directory:
```
kaymaps/localhost-<port>/RECIPE_*.txt
kaymaps/chrome/<service>/RECIPE_*.txt
```
- Example: localhost:4000 → `kaymaps/localhost-cinebot/` (app name = CineBot)
- Example: localhost:3000 → check `kaymaps/localhost-*/`
- Example: YouTube Studio → `kaymaps/chrome/youtube/`

**Lookup method**:
```bash
# Find by port/domain
ls kaymaps/localhost-*/RECIPE_*.txt
ls kaymaps/chrome/*/RECIPE_*.txt

# Grep for URL patterns
grep -r "localhost:4000" kaymaps/
```

### 3. Common/cross-app utilities
**Search in common dir**:
```
kaymaps/_common/RECIPE_*.txt
```
- Example: Finder ops → `RECIPE_finder_common.txt`
- Example: Value verification → `RECIPE_zoom_crop_value_verify.txt`
- Example: Coordinate discovery → `RECIPE_a11y_*.txt`

---

## Recipe Content Structure (expected fields)

Every recipe should contain:
- **RECIPE**: name/ID
- **GATE**: verified status + date/user
- **REG**: registry (what scope/app/URL it covers)
- **WHY**: reason recipe exists (pitfall avoided, workflow standardized)
- **STEPS**: ordered procedure (coords, keys, timing, a11y queries, verification)
- **VERIFY**: validation checklist (API response, UI state, screenshot)
- **LIMIT/OPEN**: known gaps or future enhancements

---

## Workflow: "Recipe → Task → ar_"

1. **New task arrives** (a_XXXX):
   - Search `kaymaps/` by **app name** or **URL** (per §1–3 above)
   - If recipe exists → **read full STEPS + VERIFY section** before starting
   - If recipe missing → note it + proceed with best-effort + **record findings in ar_ for future recipe creation**

2. **Execute per recipe STEPS**:
   - Follow **exact coords/keys** from recipe (not guesswork)
   - Use **a11y queries** from recipe to re-verify coords (page scroll/layout changes invalidate fixed coords)
   - Apply **verification methods** (zoom-crop, API, screenshot) from VERIFY section
   - If coord drifts → **update recipe** (ar_ note: "coord shifted from X to Y, recorded for next run")

3. **ar_ documentation**:
   - If followed existing recipe → cite it: `[REF] RECIPE_<name>`
   - If recipe missing but created workflow → plan to extract recipe: `[NEXT] Extract this flow into kaymaps/<domain>/RECIPE_<newname>.txt`
   - If recipe error found → flag + update: `[FIX] RECIPE_<name> coord X wrong → actually Y`

---

## Anti-patterns (violations)

| Violation | Result | Fix |
|-----------|--------|-----|
| Skip recipe search, start immediately | re-invent wheel, miss pitfalls | always search first, cite recipe in ar_ |
| Use hardcoded coords from past run, no re-verify | layout drift invalidates coords → silent fail | query a11y every time, update recipe if shifted |
| Recipe exists but written in Korean/verbose | hard to follow, slow to execute | rewrite recipe in compressed EN symbols + STEPS format |
| Recipe outdated (app UI changed) | stale coords, wrong STEPS sequence | update recipe after every successful run (coord drift, new UI) |
| No recipe for common flow, each task re-invents | inconsistency, time waste | extract recipe after 2nd identical task, add to kaymaps + cite in ar_ |

---

## Recipe Update Discipline

**After successful task execution**:
- [ ] Coords exact match recipe? If no → **update recipe with real coords** (date, note why shifted)
- [ ] New pitfall encountered? → **add to recipe LIMIT/OPEN** or **create ar_ note for future recipe revision**
- [ ] Verification method needs refinement? → **update VERIFY section** (e.g. "API more reliable than UI polling")

**Before reuse (next day/next batch)**:
- [ ] Re-read recipe for any updates from prior run
- [ ] Verify coords still valid (screenshot recipe coords region, zoom-crop check)
- [ ] If major drift → halt, note in ar_, update recipe, retry

---

## Verification Method Priority (from recipe VERIFY)

1. **API response** (if available) — ground truth, no UI flake
2. **a11y queries** — element state, coords, detection
3. **zoom-crop screencapture** — visual verification of specific region (not VLM, human eye)
4. **Full screenshot** — overall flow verification (count items, check UI state)
5. **Static text/banner** — lowest priority, often misleading (use only after above confirm)

---

Basis: user "always check recipe first — app name or URL lookup, not guesswork". Prevents repeated mistakes, ensures consistency.
