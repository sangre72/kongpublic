# Design guideline (MUST — user 2026-08-01)

> **All design = stylish, beautiful color.** ¬plain default mockup. **High-quality visual ∈ pass-bar.**

★SCOPE-GATE(2026-09-03 generalized for reuse across any project): applies ONLY when the current repo has a web/UI surface — kong-bot currently=NONE(cf code-structure.md §7). Content kept as reusable design pattern-library for whichever project next needs it.

## Tone & mood
- **trust·care(bright·warm)** — care-platform warmth. ¬cold-gray-only, warm-neutral + vivid-accent.

## Requirements
1. **Beautiful palette**: brand-color + semantic(success/warn/danger/info). ¬black-white+gray-border-only.
2. **Design tokens**: color·typo·spacing·radius·shadow·motion tokenized(Tailwind theme/CSS-vars) consistent.
3. **Typo hierarchy**: title/body/caption scale clear·readable font.
4. **Spacing·rhythm**: generous whitespace·aligned grid. ¬cramped.
5. **Component polish**: card·button·badge·table·tab = radius·shadow·hover·focus·transition. status-badge=semantic-color.
6. **Dark mode**(if possible): light/dark token-pair.
7. **A11y**: contrast-AA·focus-ring·keyboard.
8. **Docs(/docs)**: ¬raw-markdown-dump. render as TOC+pages.

## Forbidden (anti-pattern)
- white-bg+gray-1px-border card-list "mockup"-level / raw-markdown pipe-table·codefence exposed / no-color·no-shadow/radius/hover plain-elements.

---

## ★ UI robustness checklist (MUST — user 2026-08-08 u_141/u_142)

> WHY: 2026-08-08 recurring UI-bugs(dropdown-overflow·A4-mobile-clip·body-menu-dup·box-content-overflow) → invariant-rule to prevent recurrence. all UI-work(with design·a11y rules).

### 1. Box/container no-overflow (★highest-freq bug)
- **flex-child = `min-w-0` MUST** — absent → child-content(preview+long-text) expands beyond cell→overflow·clip.
  (incident: theme-dropdown preset-button lacked `w-full min-w-0` → content=393px > panel=359px.)
- **long-text = `truncate`**(1-line) or `break-words`(multi) — name·desc·URL.
- container overflow explicit(`overflow-x-auto` scroll or `hidden`). **fixed-width = `max-w-*` + responsive**.

### 2. Layout×2 (desktop·mobile)
- **desktop = sidebar(`lg:`)**, **mobile = hamburger overlay-drawer**(¬push-body).
- **¬main-nav-dup-in-body**: mobile inline-sidebar `hidden lg:block`. mypage-etc = content-only(¬main-menu, top/hamburger unified).

### 3. Header dropdown common-pattern (theme·notif etc header-right)
- **mobile = `fixed` viewport-basis**(`right-4 top-14`), **desktop = `sm:absolute right-0 top-full`**.
- ★ancestor `backdrop-blur`/`transform`/`filter` = fixed-containing-block contamination(fixed-basis≠viewport→that-ancestor) → verify-measured(header backdrop-blur present-case).
- width `w-[min(100vw-2rem,20rem)]`, **inner-content `min-w-0`**(§1).

### 4. Responsive MUST (375px verify)
- **fixed-width(A4-210mm etc) = mobile [scale-down](container-query cqw) or [container horiz-scroll]** — forced `max-width:100%` = table-label-clip(incident: A4-canvas). **body horiz-scroll always=0**. all-UI **375px L/R-clip=0**.

### 5. Verify discipline (★lesson)
- clip-verify = **[container-rect + inner-content-maxRight] BOTH** — panel∈viewport-safe ≠ child-safe(incident: panel-rect-only-check missed content=393px overflow).
- **375px E2E** real-rect(`getBoundingClientRect`) measured. "measure-rect, ¬guess"(user).

### 6. Input UI
- ¬`inputMode`/`type` misuse(e.g. email-dual-purpose-field ¬`tel`) — match-actual-purpose.

### 7. No system-internal exposure
- poller-status·heartbeat·queue-count etc = ¬general-screen. **ADMIN_SUPER-gate or hidden**(audit·health-endpoint = internal-path-only).

> With: [accessibility-guideline.md](./accessibility-guideline.md)·[code-structure.md](./code-structure.md). per-element detail-catalog = deferred(¬over-invest).

Basis: user "admin mockup beautiful", "all design stylish·beautiful color". UI-robustness: u_141/u_142(2026-08-08) — recurring UI-bugs(u_124~140: dropdown-overflow·A4-clip·menu-dup·poller-exposure) → invariant-rule.
