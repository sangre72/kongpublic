# Code Structure Rules (MUST — user 2026-08-01)

Always applies to all code work in this repo(work root = repo root, any project).

> **Also required**: feature consistency · per-role feature matrix → [feature-consistency-guideline.md](./feature-consistency-guideline.md)


## 1. Isolate mock data in a separate dir (user: "later just delete the dir")

> Goal: **when removing mocks / swapping to real API, deleting the mock dir alone suffices.**

- **All fake data · fake stores · mock values** → isolate under a dedicated mock dir as per-domain files.
- **Real logic never imports mocks directly.** Data-access layer·services·handlers don't scatter-reference mocks — inject only at a **single boundary**(data-access module references only mocks, or mock barrel).
- No inline hardcoded mock data in modules/functions → move to mock dir.
- Real backend·real API: delete mock dir + swap only data boundary to real calls. Rest of code unchanged.
- Each mock file top comment: `# MOCK — 실서버 연동 시 제거`.

## 2. Libraryize (extract reusable common)

- Reusable **pure logic**(calc·date·format·status-map·config etc.) → common lib module, side-effect-free.
- No hardcoded domain logic in logic consumers(handlers·workers·components) — call lib fn.
- Separate common primitives(shared utils·UI primitives) from per-domain modules.
- Shared types → common types module. No duplicate defs.

## 3. Data-screen common standard (user 2026-08-01, applies on web UI work)

> Applies if a data-handling web UI exists. Not applicable to pure pipeline/bot code.

All data screens (list·search·history·admin) provide via reusable `DataView` pattern:
- **View toggle**: table ↔ gallery(card grid).
- **Paging**: pagination/load-more + page size(10/20/50) + total count.
- **Basics**: search·filter(per-domain)·sort·count summary·empty/skeleton/error·(if applicable) bulk-select·export·refresh.
- **URL sync**: filter·sort·page in querystring.
- **A11y**: semantic table/list, aria-sort, keyboard.
- Don't reimplement per screen → **libraryize as common component**.

## 3-1. File line-count cap (user 2026-08-03 "files too long" · 2026-08-05 u_146 "modularize → right line count")

> **Too-long file hurts maintenance·modularity·review·portability.** Line count = mgmt metric.

> ### ★ Goal = "modularize to reach right line count" (user 2026-08-05 u_146)
> **Line count = outcome metric, modularization = means.** Don't force-cut/paste; **split modules by responsibility·domain boundary → each file lands at right count (rec ~300, cap 800).**
> - Not "over 800 → cut anywhere" but **"how many responsibilities does this file hold → split per-responsibility via §4 modularization·§2 libraryization"** → line count naturally right.
> - Split = **behavior-preserving pure refactor**. Barrel(`index.ts`) keeps public API so **external import paths don't break**(if must change → update all + regression test).
>
> ### ★★ Consider line count from the start (user 2026-08-05 — "doing it later means re-running all tests")
> **New files·features designed·built under 400 lines from the start.** Post-hoc split = re-run all regression → expensive.
> - Before start(§A checklist): "how many responsibilities → if likely >400, split files/modules from the start".
> - Goal: each file **under 400**(ideal ~200, rec ~300). If trending over → split per-responsibility right there(no bulk split later).
> - Big modules → sub-fns·pure fns; data-access → per-responsibility files; specs/definitions → per-domain files, **from the start**.
> - Why: post-completion split needs tsc + full E2E/regression re-verify(cost·time). Split at dev time → only that feature's tests.

### Recommended thresholds (differentiated by nature)
| Range | Verdict | Action |
|------|------|------|
| **~200 lines** | ideal | — |
| **~300 lines** | rec cap | keep |
| **300~500 lines** | caution | check cohesion, split if growing |
| **500~800 lines** | warning | **plan a split**(domain·responsibility unit) |
| **>800 lines** | ★violation | **split required**(sign of many domains/responsibilities in one file) |

### Exceptions by nature (cap relaxed)
- **Spec/definition files**(openapi spec·type dict·codes·naming dict·route registration): data listings can be long → >800 allowed but **per-domain file split** recommended(e.g. openapi/ per-domain).
- **Generated artifacts**(code-generator output etc.): out of scope.
- Else **logic/module/data-access files = strict cap**.

### Split method
- **Central data-access/util holding many domains** → extract via §4 per-business modularization(`features/<업무>/`).
- **Big module/component** → split sub-units·pure fns(lib).
- **A fn over 100 lines** → split into helpers.

### ★ Split-target registry (category·description·plan — user 2026-08-05)

> Violation/warning files' **list·category·split plan·progress = single-managed in one ledger**. (If a split-ledger doc exists, manage there and don't hardcode in body.)

- Categorize nature → **apply different split method**: `LOGIC`(logic/lib)·`MODULE`(general source module)·`DATA`(data-access) = strict cap / `SPEC`(spec·code dict·route reg)·`TYPES`(type defs) = relaxed(>800 allowed, per-domain split recommended) / `GENERATED`(generated artifact) = out of scope.
- **New/modified file >800** → add registry row(file·lines·category·**description**·verdict·priority·split plan). If can't split now, at least priority(P).
  - **Description** column(what responsibility) required — basis for which boundary to split(user 2026-08-05: "need file with category and description").
- **On split start/progress** → verdict → 🔀 in-progress, note how far(1st helper extraction etc.) in plan column.
- **On split done** → verdict → ✅ + result·final line count. Regression test pass required.
- **Procedure**: ① find >800 → register(category·description·plan) → ② at refactor split per that plan via §4/§2 → ③ build/lint pass + regression pass → ④ update registry ✅.

### Verification
- At review/done, new/modified file **>800 → register + split plan**.
- Actual split work delegated per-domain unit, **P1(violation) first** — not all at once, per-domain unit with regression tests.

Basis: user "files too long, put recommended line count in standard" / "add split-target split work + need file with category·description"(2026-08-05). Central module bloat → resolved via features modularization.

## 4. Per-business modularization (user 2026-08-01 — call it "업무별 모듈화")

> **Independent, large business features** cohere **self-contained** in `features/<업무>/`(under this project's source tree). Goal: **portability where copying the dir alone lets another project use it almost as-is.**

- Target: independent system-grade business(e.g. orchestrator·worker pipeline unit, notifications, collectors — migrate when they grow). Small domain modules(a few files) stay in place — no over-splitting.
- Module internal standard layout(rename to fit stack):
  ```
  features/<업무>/
    ├─ lib/         순수 로직·설정·타입 (덩치 있는 것은 여기)
    ├─ handlers/    그 업무 전용 진입점/핸들러
    ├─ services/    그 업무 서비스 로직
    ├─ mocks/       그 업무 mock (# MOCK 주석, 삭제 가능)
    ├─ data.py|ts   그 업무 데이터 접근 경계
    └─ index         공개 API 배럴 (외부는 여기서만 import)
  ```
- **Declare external deps**: list project-common the module uses(shared utils·config·session) as "external deps" in the public API entry top comment → what's needed at port time, at a glance.
- **Self-contained·single boundary**: external(central module etc.) doesn't reference module internals directly, only public API. No circular ref, keep server/client boundary.

## 5. Current structure (maintenance baseline)

> Below = example skeleton. Apply names·layers to the real stack(python pipeline/bot), but keep **responsibility separation·data boundary·mock isolation·libraryization** principles.
```
<진입점>/                  실행 진입점/라우팅은 얇게, features/<업무> 만 호출
<도메인>/ (또는 features/) 기능별 모듈 (+ 공통 프리미티브)
services/ (또는 actions/)  업무 로직 (도메인별)
data/ (DAL)               데이터 접근 경계 (인가·서버전용) — mock 주입 지점
lib/                      순수 로직·타입·유틸 (라이브러리화 대상)
mocks/                    ★ 모든 mock 격리 (삭제 가능 단위)
```

Basis: user "libraryization matters too", "make per-applied subdir individually for mock data — later just delete the dir".

## 6. Compare roles as arrays (user 2026-08-03 — "may have duplicate roles")

> For projects with roles/permissions: **all role/permission comparison = array-includes(`['X'].includes(role)`), not direct string(`role === 'X'`).** A user may hold duplicate roles, and multi allowed-roles is common.

- Menu/button/screen gate: `roles?: string[]` + `roles.includes(viewer.role)`.
- Data-access/server authz: `requireRole([...])` array. Single also `['X']`.
- New = array from start. Existing `role === 'X'` → migrate to array at refactor.

Basis: user "all role comparison as array. Duplicate roles may exist."

## 7. Common functions — catalog first (user 2026-08-03)

> **Before writing new logic, check the common function catalog(if any).** Exists → import & use it(no re-implement). Missing → make in lib/features & **add 1 line to catalog**.
> Background: re-implementing existing common fns everywhere collapses the standard. Catalog forces reuse instead of grep every time.

- Check catalog before start. Find common modules by nature(authz·calc·session·naming·code value etc.) first.
- ★Role comparison via common rbac fn — no direct `role === 'X'`(with §6 array compare).
- New common fn = register in catalog. Same logic 2nd time = promote to lib + register. No re-invention.
- On finding direct compare·inline logic → migrate to catalog fn(at refactor).

Basis: user "make a common function list doc, use if exists·make & add doc if not."

## 8. Request-context standard — tenant·region·language (user 2026-08-03)

> **Prep future expansion(multi-tenant·multi-region·i18n).** Don't fully implement now; new code = **context-propagatable structure**.

- **Tenant**(per host/server): reserve tenant identifier in context. Data query via tenant-boundary fn habit(no-op ok now). No hardcoded specific tenant.
- **Region**: region-dependent logic via common lib. Multi-region = infra level.
- **Language**(i18n): even if single locale fixed now, date·currency·sort via lib(date·format·compare) as locale injection points. New bulk copy = constants for future i18n. Avoid direct locale hardcode.
- On activation(multi-tenant·i18n), routing via these already makes filling values work.

Basis: user "tenant·server(region)·language(i18n) standard into guideline".
