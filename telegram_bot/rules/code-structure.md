# Code Structure Rules — kong-bot real layout (MUST — rewritten 2026-08-27 a_2740, was sky Next.js doc)

∀ code-work ∈ this repo(`telegram_bot/`, `kongtrol/`, scripts).

## 1. Package layout (actual, ¬aspirational)
```
telegram_bot/
  handlers/            telegram command/event handlers
  services/            business-logic(called by handlers)
  orchestrator/
    orchestrator.py(→kong_orchestrator.py, a_2737) main-loop: u_→a_ convert+worker-spawn+ar_ detect-reply
    protocol_store.py  protocol/ file-IO(status normalize etc)
    telegram_io.py      telegram send/receive wrapper
    worker.py           claude -p worker spawn
    protocol/{u,a,ar,archive}/  u_/a_/ar_ file-store(cf §3)
    scripts/            ops scripts(start_orchestrator.sh·worker1_*.sh etc)
  rules/                .claude/rules/ mirror(full-copy, cf §5 — always-sync, file-count=.claude/rules/ always-match)
  guides/                ops guide docs
kongtrol/
  src/{main.rs,sys.rs,process.rs,service.rs,input.rs}  physical-IO CLI(Rust)
  target/release/kongtrol  built-binary(absolute-path-ref, ¬PATH-registered)
kaymaps/<app-or-domain>/RECIPE_*.txt   per-app operation-recipe(compressed-EN, cf recipe-lookup-guideline.md)
jobs/<job-name>/         job-output(video·image·mapping_*.json etc, per-job-dir)
docs/appkb/               app first-run/onboarding screen-catalog(first-run-screens.md)
```

## 2. Libraryize (extract reusable common)
- Reusable **pure logic**(code-parse·time-format·coord-transform etc = computable, cf [[compute-vs-ar-split]]) → shared module(`services/` or dedicated `lib`), ¬copy-paste-per-handler.
- No hardcoded per-recipe coordinate/timing logic scattered across handlers — kongtrol coords live in `kaymaps/**/RECIPE_*.txt`(data), ¬hardcoded in `.py`.
- Common protocol-file helpers(status-parse·seen-dedup·file-naming) → `protocol_store.py`, ¬reimplement-per-script.

## 3. protocol/u·a·ar file-naming convention (cross-ref och.txt COMMS section — ¬duplicate detail)
- `u_{NN}_{topic}.txt`(telegram user-request, bot-written) → `a_{NN}_{topic}.txt`(orch instruction) → `ar_{NN}_{topic}.txt`(worker reply). same NN pairs across the three.
- Terminal-states(done/error/blocked/needs-info/failed) → archived to `protocol/archive/{a,ar}/` by bot; `in-progress` never archived.
- Full lifecycle/state-machine detail = `telegram_bot/orchestrator/och.txt`(authoritative), this file states naming-shape only.

## 4. File line-count cap (same spirit as sky, right-sized for this repo's languages)
- Python/shell files: same modularization-principle — **ideal~200, rec-cap~300, warning 500-800, violation>800**. split by responsibility(handler vs service vs protocol-IO), ¬arbitrary-cut.
- Exception: `kaymaps/**/RECIPE_*.txt`(data/spec-like, per-app recipe-listings can run long — split per-app-dir instead, ¬per-line-count).
- Rust(`kongtrol/src/*.rs`): same cap-principle, split by command-group(`sys`/`process`/`service`/`input`) as already-structured.
- No formal split-registry doc exists for this repo(sky's was Next.js-app-scale) — if a file crosses 800, flag in relevant ar_/handoff-note instead, propose-split, ¬force unless asked.

## 5. ★ Two rule-dir sync (`~.claude/rules/` ⟷ `telegram_bot/rules/`, MUST — cf worker_1.txt L43)
- This project has a **full-mirror**(count grows as rules added, was miscounted "8-file" — fixed 2026-09-03 after real 8-vs-10 drift found: kongtrol-base-reference.md+recipe-lookup-guideline.md were missing from telegram_bot/rules/): `.claude/rules/*.md` ⟷ `telegram_bot/rules/*.md` MUST stay content-equivalent(both loaded per diff-context — session vs worker). on any edit to one, **update-other SAME-task**, ¬leave-drifting.
- Before any rules-touching task: `diff <(ls .claude/rules/*.md|xargs -n1 basename) <(ls telegram_bot/rules/*.md|xargs -n1 basename)` → check file-SET parity first(¬just per-file content-diff — missing/extra FILE = more-common drift), then per-file-diff for content.

## 6. Recipe-first for kongtrol UI automation (cross-ref recipe-lookup-guideline.md — ¬duplicate)
- Any new app/screen kongtrol interacts w/ = check `kaymaps/<app>/RECIPE_*.txt` first, follow exact STEPS(¬invented coords/keys). new/undocumented UI-element = max-2-attempts(diff-methods) then escalate, never loop-retry-same-method(cf pre-development-checklist.md-adjacent gate in worker_1.txt §NEW-UI-ELEMENT-GATE).
- After successful new-flow, extract → recipe-file(compressed-EN K7-format) — ¬leave tribal-knowledge only in a_/ar_ history.

## 7. No role/RBAC/tenant/i18n scaffolding here
- kong-bot ¬multi-user-role, ¬multi-tenant, ¬i18n-surface(single-operator telegram-bot + local macOS-automation) — old-sky §6-8(role-array-compare, tenant/region/language context) ¬apply. IF this project ever grows multi-user/multi-tenant surface → re-derive fresh, ¬revive sky-specific ones(diff domain-shape).

Basis: user 2026-08-27(u_2740) — prior version was sky's Next.js app/features/DAL/RBAC/tenant doc, entirely inapplicable to this Python-bot+Rust-CLI+recipe-automation project, caused confusion loaded into every kong-bot session.
