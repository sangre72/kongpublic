# Design guideline (필수 준수 — user 2026-08-01)

> **All design = stylish, beautiful color.** No plain default mockup. **High-quality visual = part of pass bar.**

Applies: this project all UI output(web screen·doc render 등).

## Tone & mood
- consistent mood per service (예: 신뢰감 있고 따뜻한 톤). no cold gray-only, warm neutral + vivid accent.

## Requirements
1. **Beautiful palette**: brand color + semantic(success/warn/danger/info). no black-white+gray-border only.
2. **Design tokens**: color·typo·spacing·radius·shadow·motion tokenized(Tailwind theme/CSS vars) consistent.
3. **Typo hierarchy**: title/body/caption scale clear·readable font.
4. **Spacing·rhythm**: generous whitespace·aligned grid. no cramped.
5. **Component polish**: card·button·badge·table·tab = radius·shadow·hover·focus·transition. status badge = semantic color.
6. **Dark mode**(if possible): light/dark token pair.
7. **A11y**: contrast AA·focus ring·keyboard.
8. **Docs(/docs)**: no raw markdown dump. render as TOC+pages.

## Forbidden (anti-pattern)
- white bg+gray 1px border card list "mockup" level / raw markdown pipe-table·codefence exposed / no-color·no shadow/radius/hover plain elements.

---

## ★ UI robustness checklist (필수 준수 — user 2026-08-08)

> 반복 UI 버그(dropdown 넘침·fixed-width mobile 잘림·본문 메뉴 중복·box content 넘침) → **불변 규칙** 재발 방지. all UI work(with design·a11y rules).

### 1. Box/container no-overflow
- **flex child = `min-w-0` 필수** — 없으면 child content(icon+long text)가 cell 밖 확장→넘침·잘림.
- **long text = `truncate`(1줄) or `break-words`(multi)**.
- container overflow 명시. **fixed-width = `max-w-*` + 화면 대응**.

### 2. Layout 2종 (desktop·mobile)
- **desktop = sidebar**, **mobile = hamburger overlay drawer**(no push body).
- **no 주 nav dup in body**: mobile inline-sidebar hidden. 특정 화면(마이페이지 등) = content-only(주 메뉴 X, 상단/hamburger 일원화).

### 3. Header dropdown 공통 패턴
- **mobile = `fixed` viewport 기준**, **desktop = `absolute` 부모 기준**.
- ★ancestor `backdrop-blur`/`transform`/`filter` = fixed containing-block 오염 → 실측 확인.
- width = viewport 대응(`min(100vw-여백, 상한)`), **inner content `min-w-0`**.

### 4. Responsive 필수 (mobile 375px 검증)
- **fixed-width = mobile scale down or container 가로스크롤** — 억지 `max-width:100%` = inner 잘림. **body 가로스크롤 always 0**. all UI 좌우 잘림 0.

### 5. Verify 규율
- 잘림 검증 = **[container rect + inner content maxRight] 둘 다** — panel 이 viewport 안이어도 child 넘칠 수 있음. 실 rect(getBoundingClientRect) 측정("추측 말고 실측").

### 6. Input UI
- no `inputMode`/`type` misuse(성격 맞게).

### 7. No system-internal 노출
- status·heartbeat·queue count 등 = no 일반 화면(권한 gate or hidden).

근거: user "관리자 목업 아름답게", "모든 디자인 스타일리시·아름다운 색". UI robustness: 반복 UI 버그 불변 규칙화(넘침·잘림·메뉴 중복·internal 노출).
