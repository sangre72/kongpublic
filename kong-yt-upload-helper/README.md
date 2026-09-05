# KongTube Upload Helper (v0.2.0)

Chrome MV3 extension. CSV-driven auto-fill for YouTube Studio uploads — **DOM automation only, no YouTube Data API**.

## What it does
Load a CSV (one row per video: `filename,title,playlist,scheduleDate`), and on the YouTube Studio upload
flow the extension auto-fills the **title**, selects the matching **playlist**, and sets the **schedule date**
for each uploaded file (matched by filename). You still click the final 예약/Schedule button yourself
(safety — real scheduled uploads are irreversible; auto-fill is a convenience, human confirms publish).

## CSV format
```
filename,title,playlist,scheduleDate
scene_01.mp4,2026년 9월 5일 쥐띠 🐭 오늘의 운세,오늘의 운세,2026-09-05
scene_02.mp4,"소띠, 운세",오늘의 운세,2026-09-05
```
- Required columns: `filename, title, playlist, scheduleDate`. `scheduleDate` = `YYYY-MM-DD`.
- Titles with commas → wrap in `"quotes"`. Loader validates header, required columns, empty cells, and date
  format, and reports the exact **row/column** on error.

## File selection (both paths supported)
1. **Native picker** — click the page's file-select button (Finder dialog), pick the mp4.
2. **Drag-drop** — drag the file from Finder onto the page's dropzone (as done manually before).
The extension can't intercept the OS-level drag itself, but listens for the resulting native `drop`/`change`
event, reads the dropped `File.name`, and matches it against the CSV row — both paths converge to the same
auto-fill.

## Multi-locale (distributable, a_3761 amend)
YouTube Studio UI label lookup uses a **locale-label-map** (`LOCALE_LABELS` in content.js) covering
**Korean / English / Japanese / Spanish** for title, playlist, schedule, done, next, audience, and
publish-step labels. UI language is auto-detected (`<html lang>` → body keyword sniff → `en` fallback).
Adding a new locale = add one block to `LOCALE_LABELS` (structure fixed for easy extension).

### Locale setting (a_3762)
The popup has a **"YT Studio UI 언어" dropdown**: `자동 감지` (default) + explicit ko/en/ja/es. The choice
is saved to `chrome.storage.local` (`kyt_locale`) and **persists across popup opens**. content.js resolves
the locale as: **manual override if set** (skip auto-detect), else `detectLocale()`. Set back to `자동 감지`
to resume auto-detection. Changes apply live (storage.onChanged).

## Design (reused conventions)
- **Label/text-based DOM query** (aria-label / visible text) as the primary lookup — **not** blind
  coordinate reuse (avoids the z-order / stale-coordinate bugs recorded in the a_3749 postmortem of
  `RECIPE_scheduled_upload_VERIFIED.txt`).
- **native-setter + input/change events** for React-controlled inputs; `execCommand("insertText")` with a
  `textContent`+input fallback for contenteditable title fields.
- **MutationObserver + interval** for SPA re-render / modal-appearance survival.
- No YouTube Data API anywhere; content-script DOM automation only.

## Files
`manifest.json` (MV3), `content.js` (locale-map + auto-fill), `helper.css` (kyt- badge),
`popup.html`/`popup.js`/`popup.css` (CSV load + validation + progress + format guide).

## Verified (Playwright, component-level)
- CSV validation: valid load, missing-column, empty-cell (reports row+column), bad-date, missing-extension
  — all pass.
- `byLabelInput` label matching, `setEditableText` contenteditable fill, locale auto-detect (ko/en/ja/es),
  and the in-page progress badge — all pass in isolation.
- Popup renders the format guide + loads a 3-row CSV showing per-row title/playlist/date (`popup_shot.png`).
- NOTE: live YouTube Studio was not repeat-automated (real scheduled uploads have real consequences); the
  logic is validated against a mock Studio DOM. Full end-to-end Playwright launch is slow in this env — the
  component tests above cover the logic.

## Install
chrome://extensions → Developer mode → Load unpacked → this folder.
