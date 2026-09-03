# Web accessibility guideline (MUST — user 2026-08-01 "a11y from the start")

> care-platform primary-users = elderly·disabled·low-vision. a11y = build-in-from-start, all-UI(KWCAG 2.2 / WCAG 2.2 AA).

★SCOPE-GATE(2026-09-03 generalized for reuse across any project): applies ONLY when the current repo has a web/UI surface(React/Next.js/HTML front-end) — kong-bot currently=NONE(bot+CLI+recipe-automation repo, cf code-structure.md §7). Content kept as reusable a11y pattern-library for whichever project next needs it. With design-guideline.

## Strength-tiering
- **Public-front(user-facing) = strict(AA-full)**: landing·signup·apply·search·reserve·FAQ·terms·user-portal. 12-reqs all-strict + axe=0.
- **Admin(/admin/*) = baseline**: semantic·keyboard·label·contrast basics kept, but front-level(axe=0·full-keyboard-E2E) unneeded(internal-expert-users·¬over-invest). caregiver/user-portal = front-level.

## 12 requirements
1. **Semantic markup**: header/nav/main/footer, heading-order(h1→h6), list/table semantic-tags.
2. **Keyboard-only**: all-interaction(menu·button·form·accordion·tab·modal) Tab/Enter/Esc/arrow. modal focus-trap·logical-tab-order.
3. **Focus visible**: focus-visible ring(contrast-met). ¬`outline:none`-only.
4. **Contrast**: text-AA(normal 4.5:1·large 3:1)·UI-component 3:1. **all theme/dark-preset AA**.
5. **Alt·label**: img `alt`·icon-button `aria-label`·form `<label for>`·decorative `aria-hidden`.
6. **ARIA proper**: native-first, role/aria-*(expanded·current·live) only-where-needed. ¬overuse.
7. **State**: ¬color-only(badge text/icon-together). error = aria-invalid + message.
8. **Dynamic alert**: toast·live-update `aria-live`(polite/assertive).
9. **Motion**: respect `prefers-reduced-motion`.
10. **Form a11y**: label·desc·error via aria-describedby·required-mark·auth-step screen-reader.
11. **Zoom/responsive**: 200%-zoom ¬content-loss·text-reflow.
12. **Lang**: `<html lang="ko">`.

## Verify
- Playwright + **axe-core**(@axe-core/playwright) scan(serious=0). keyboard-only key-flow(signup·reserve·search·menu) E2E. theme-preset contrast.

Basis: 장애인차별금지법(web-a11y duty)·KWCAG 2.2·WCAG 2.2 AA. user "a11y from-the-start before concrete-dev".
