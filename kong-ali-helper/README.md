# AliKong (v0.5.0)

Chrome MV3 extension for AliExpress (renamed from "Kong AliExpress Helper" at a_3753).
Icon: gorilla-mascot-with-price-tag, generated via Krea2 Turbo (ComfyUI), `icons/icon{16,48,128}.png`.
Store package: `alikong_v0.5.0.zip` (runtime files only — README/screenshots/tests excluded).

## Features (v0.1)
- **가격안전 신호등 (price-safety traffic-light)** — product page badge, single glanceable
  초록(안전)/노랑(주의)/빨강(위험) verdict combining 3 signals into ONE score:
  - **discount-inflation heuristic** — AliExpress does NOT expose price history in the DOM
    (verified via CDP: no 90일/최저가/price-history), so very high discount% (≥80 red, ≥60 yellow)
    is used as an original-price-inflation proxy.
  - **rating** (≥4.5 good, <4.0 penalized).
  - **review count** (sample-size trust: ≥100 solid, <10 sparse-warning).
  Transparent reasons shown; footer states "가격이력 미제공→할인율 휴리스틱 · 참고용".
- **쿠폰 자동적용 (coupon auto-apply)** — cart/checkout: lists page coupon-apply buttons + one-click
  delegation, and anchors the coupon-code input (label/placeholder, not css-hash). Foundation baseline.

## Reused from kong-upbit-helper
label-anchor (not css-hash), native-setter + input/change events (React/Vue controlled inputs),
MutationObserver + interval for SPA re-render / lazy-load, floating badge pattern.

## Verified (live, real AliExpress product page)
Badge renders live: e.g. USB-C cable item → **주의** (고할인 62% · 평점 5.0 · 리뷰 2개 표본희박).
Screenshot: `ali_badge_live.png`. Coupon helper activates on cart/checkout pages.

## Scope note
STEP1 only. Cross-platform price-compare, shipment-tracking, price-watchlist = separate future steps.

## Install
chrome://extensions → Developer mode → Load unpacked → this folder.
(After code changes: quit+relaunch Chrome to bust content-script cache — Chrome 152 caching.)

## Files
`manifest.json` (MV3), `content.js` (badge + coupon), `helper.css` (kah- prefixed).

## Coupon auto-discovery + auto-apply pipeline (v0.3, a_3737~3741)
- **Discover**: on the coupon-center (`/ssr/*/glo-coupon-center*`), auto-scroll to load all cards, scrape
  each coupon's discount + condition + **typeable CODE** (e.g. WKBQF6IS2GI9, 5YQ7MN) — AliExpress does
  publish real codes here (contrary to the my-coupons store-view).
- **Handoff**: codes saved to `chrome.storage.local` (subdomain-agnostic — coupon-center is `ko.` and
  checkout is `www.`, so localStorage/cookies don't carry across; chrome.storage does).
- **Auto-apply**: on the checkout page (`/p/trade/confirm*`), "수집 코드 자동 시도 (N)" tries each collected
  code into the native 프로모션 코드 field + clicks 적용, and判定s success by the **총합계 actually dropping**
  (ground-truth), stopping on the first that works. Manual paste is also available.
- Verified E2E: 6 codes carried ko.→www., auto-try ran all 6, correctly reported none applied because the
  order total was below every coupon's minimum threshold (correct behavior, not a bug).

## Landing shipment-status card (v0.4, a_3750)
- **Trigger**: on the AliExpress landing/home (`www.aliexpress.com/`, `/gcp/*`, `/home*`), if there are
  active in-transit orders, a **dismissible designed card** appears top-right (NOT an auto-fading toast —
  the user has multiple orders + detail to read).
- **Data source (same-origin, read-only)**: AliExpress order list is JS-rendered (not in fetched HTML,
  same constraint as coupon-center), so it reuses the coupon-center pattern — when the user visits
  **My Orders** (`/p/order*`), `scrapeOrders()` reads the in-transit orders (status keyword match:
  배송 중/발송됨/운송 중/In transit/Shipped…, excluding 배송완료/Delivered) and caches them to
  `chrome.storage.local`. The landing reads that cache (subdomain/page-agnostic) and renders the card.
  The footer honestly states "최근 '내 주문' 방문 시점 기준 · 실시간 아님".
- **Card**: each order shows a thumbnail + product name + a **status badge (color+text, a11y-safe)** +
  est-delivery if available. A visible **X close button** dismisses the current instance immediately.
  Empty in-transit list → renders nothing (no empty card).
- **Once-per-calendar-day gate (a_3751)**: re-appearance is throttled to once per calendar day via a
  `chrome.storage.local` key `kah_ship_lastshown` (YYYY-MM-DD). On landing load the card renders + chimes
  only if in-transit orders exist AND the stored date ≠ today; it then writes today's date. Same-day repeat
  homepage visits skip entirely (no re-render, no re-chime), whether or not the user dismissed it. It shows
  again the next calendar day without needing a page close. The X button is independent of this gate —
  the gate controls re-appearance timing, X controls dismissing the current instance.
- **Chime**: on first card appearance, a short clean **WebAudio bell chime** plays (2-note A5→E6
  arpeggio, sine fundamental + soft triangle octave overtone, gentle attack + natural decay, low gain =
  pleasant, not jarring). Synth chosen over an external file: zero-dependency, no license/CSP/CDN concerns,
  and MV3 extensions can't easily load external audio. Fails silently under browser autoplay policy.
- **Verified E2E (Playwright)**: card renders with real order data + status badges, chime fires
  (AudioContext invoked once), X dismiss removes card, and empty-orders → no card. Screenshot:
  `kah_ship_card.png`. Once-per-day gate tested with cross-load `chrome.storage` persistence: day1 →
  render+chime, same-day repeat → skip (no card, no chime), next-day → render+chime again.
