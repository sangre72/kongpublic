# Code Structure Rules — kong-bot real layout (MUST — rewritten 2026-08-27 a_2740, was sky Next.js doc)

Always applies to all code work in this repo(`telegram_bot/`, `kongtrol/`, scripts).

## 1. Package layout (actual, not aspirational)
```
telegram_bot/
  handlers/            텔레그램 명령/이벤트 핸들러
  services/            비즈니스 로직(핸들러가 호출)
  orchestrator/
    orchestrator.py(→kong_orchestrator.py, a_2737) 메인 루프: u_→a_ 변환+워커 spawn+ar_ 감지 회신
    protocol_store.py  protocol/ 파일 IO(status normalize 등)
    telegram_io.py      텔레그램 send/receive 래퍼
    worker.py           claude -p 워커 spawn
    protocol/{u,a,ar,archive}/  u_/a_/ar_ 파일 저장소(cf §3)
    scripts/            운영 스크립트(start_orchestrator.sh·worker1_*.sh 등)
  rules/                .claude/rules/ 미러(전체-copy, cf §5 — 항상 동기화, 파일개수=.claude/rules/ 와 항상 일치)
  guides/                운영 가이드 문서
kongtrol/
  src/{main.rs,sys.rs,process.rs,service.rs,input.rs}  물리 IO CLI(Rust)
  target/release/kongtrol  빌드된 바이너리(절대경로 참조, PATH 미등록)
kaymaps/<app-or-domain>/RECIPE_*.txt   앱별 조작 레시피(compressed-EN, cf recipe-lookup-guideline.md)
jobs/<job-name>/         작업 산출물(영상·이미지·mapping_*.json 등, job별 디렉토리)
docs/appkb/               앱 첫실행/온보딩 화면 카탈로그(first-run-screens.md)
```

## 2. Libraryize (extract reusable common)
- Reusable **pure logic**(코드 파싱·시간 포맷·좌표 변환 등 계산 가능한 것, cf [[compute-vs-ar-split]]) → shared module(`services/` or a dedicated `lib`), not copy-pasted per handler.
- No hardcoded per-recipe coordinate/timing logic scattered across handlers — kongtrol coordinates live in `kaymaps/**/RECIPE_*.txt`(data), not hardcoded in `.py`.
- Common protocol-file helpers(status parse·seen-dedup·file naming) → `protocol_store.py`, don't reimplement per script.

## 3. protocol/u·a·ar file-naming convention (cross-ref och.txt COMMS section — don't duplicate detail)
- `u_{NN}_{topic}.txt`(telegram user request, bot-written) → `a_{NN}_{topic}.txt`(orch instruction) → `ar_{NN}_{topic}.txt`(worker reply). Same NN pairs across the three.
- Terminal states(done/error/blocked/needs-info/failed) → archived to `protocol/archive/{a,ar}/` by bot; `in-progress` never archived.
- Full lifecycle/state-machine detail = `telegram_bot/orchestrator/och.txt`(authoritative), this file only states the naming shape.

## 4. File line-count cap (same spirit as sky, right-sized for this repo's languages)
- Python/shell files: same modularization principle — **ideal ~200, rec cap ~300, warning 500-800, violation >800**. Split by responsibility(handler vs service vs protocol-IO), not arbitrary cut.
- Exception: `kaymaps/**/RECIPE_*.txt`(data/spec-like, per-app recipe listings can run long — split per-app dir instead, not per-line-count).
- Rust(`kongtrol/src/*.rs`): same cap principle, split by command-group(`sys`/`process`/`service`/`input`) as already structured.
- No formal split-registry doc exists for this repo(sky's was Next.js-app-scale) — if a file crosses 800, flag in the relevant ar_/handoff note instead, propose split, don't force unless asked.

## 5. ★ Two rule-dir sync (`~.claude/rules/` ⟷ `telegram_bot/rules/`, MUST — cf worker_1.txt L43)
- This project has a **full-mirror**(count grows as rules are added, was miscounted "8-file" — fixed 2026-09-03 after a real 8-vs-10 drift found: kongtrol-base-reference.md+recipe-lookup-guideline.md were missing from telegram_bot/rules/): `.claude/rules/*.md` and `telegram_bot/rules/*.md` must stay content-equivalent (both loaded per different contexts — session vs worker). On any edit to one, **update the other in the same task**, don't leave them drifting.
- Before any rules-touching task: `diff <(ls .claude/rules/*.md|xargs -n1 basename) <(ls telegram_bot/rules/*.md|xargs -n1 basename)` to check file-SET parity first(not just per-file content diff — a missing/extra FILE is the more common drift), then per-file diff for content.

## 6. Recipe-first for kongtrol UI automation (cross-ref recipe-lookup-guideline.md — don't duplicate)
- Any new app/screen kongtrol interacts with = check `kaymaps/<app>/RECIPE_*.txt` first, follow exact STEPS(no invented coords/keys). New/undocumented UI element = max 2 attempts(different methods) then escalate, never loop-retry same method (cf pre-development-checklist.md-adjacent gate in worker_1.txt §NEW-UI-ELEMENT GATE).
- After a successful new flow, extract it into a recipe file(compressed-EN K7 format) — don't leave tribal knowledge only in a_/ar_ history.

## 7. No role/RBAC/tenant/i18n scaffolding here
- Kong-bot has no multi-user-role, multi-tenant, or i18n surface(single-operator telegram bot + local macOS automation) — §6-8 of the old sky version(role-array-compare, tenant/region/language context) do not apply. If this project ever grows a multi-user/multi-tenant surface, re-derive those sections fresh rather than reviving the sky-specific ones(different domain shape).

Basis: user 2026-08-27(u_2740) — prior version was sky's Next.js app/features/DAL/RBAC/tenant doc, entirely inapplicable to this Python-bot+Rust-CLI+recipe-automation project, causing confusion loaded into every kong-bot session.
