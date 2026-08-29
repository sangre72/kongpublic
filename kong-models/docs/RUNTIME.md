# kong-models tier-1 runtime flow (lookup-table, no training)

## step-0: FOREGROUND CHECK (★MANDATORY, never skip) — ★CORRECTED 2026-08-27(a_2553)
Before ANY menu-lookup/click, verify target app is frontmost.
- background app = silent input-fail(kongtrol sends input but nothing happens, no error thrown) — per kongtrol-base-reference.md Focus-Management.
- ★★★CRITICAL(a_2553 incident): `see --a11y --pid <PID>` succeeding(non-trivial element-count) does NOT prove clicks will land correctly. a11y reads a PROCESS's element-tree regardless of visual z-order/occlusion. Physical clicks go to whatever window is TRULY topmost on-screen at that coordinate, independent of the a11y-queried pid. **a11y-success ≠ click-safety** — these are two separate checks.
- correct check: `open -a "<App>"` + `sleep 2` → THEN take a screenshot and visually confirm(via Read-tool inspection, not just element-count) the target app's actual window/content is visible and not occluded by another window/dialog at the intended click-region.
- if visual-frontmost-check fails(something else covering it, e.g. a lingering dialog from a prior step): do NOT click blind. Close/dismiss the blocker first(verify via fresh screenshot it's gone), or report blocked.
- fix: pure physical `open -a`/click-based activation only, NOT `osascript`/System Events(pure-io-no-system-events rule).

## step-1: drift-check
Compare live `see --a11y` label-set for the target menu vs stored kong-models/<menu-type>/<app>.json label-set.
- match → proceed to step-2(fast-path lookup).
- mismatch → flag "stale, app-updated-since-last-learn" → re-run capture-flow for this app, don't trust old JSON blindly.

## step-2: lookup(fast-path, no full-tree-scan)
Use stored JSON's item-label+path as a target-hint — query a11y for that SPECIFIC path directly(e.g. jump straight to `AXMenuBarItem[File] > AXMenuItem[Save]`) rather than enumerating the entire menu tree fresh each time.
- resolve the item's LIVE coord on THIS session's screen(a11y always gives current real coords — the JSON stores role+label PATH only, never cached pixel values, per LEARNING.md's resolution-independence mandate).
- click resolved coord.

## step-3: safety-gate(always active, not optional)
Before clicking ANY resolved item: check its `safe_to_click` field from the JSON.
- `false` → do not click, this is destructive/unverified — observe-only.
- `true` → proceed.
- item not in stored JSON at all(drift/new-item) → treat as unverified, skip-and-flag rather than guessing.

Basis: a_2542(safety-caution) + a_2549(no-vision-redirect, tier-1 lookup design) + a_2550(explicit foreground-check-as-step-0).
