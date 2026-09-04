# Kong Upbit Price Helper (v0.1)

Chrome MV3 extension — adds **±% quick-price buttons** and a **price-lock toggle** to Upbit's
매수가격/매도가격 (buy/sell limit-price) inputs on `upbit.com/exchange`.

## Features (v0.1 — price-helper only)

- **±% quick buttons** (`-2% -1% -0.5% +0.5% +1% +2%`) beside the price input. Each sets the price
  to **current market price × (1 ± pct)**, tick-size-rounded so the exchange won't reject it.
- **Price lock 🔒** — click to freeze the price field; any accidental change (click/scroll) is
  reverted to the locked value. An intentional ±% button press while locked updates the lock target.

- **Sell-side reference toggle** (`기준:현재가` ↔ `기준:매수가`, v0.1.1 / a_3615) — the sell form's
  ±% buttons can compute off either the **current market price** or the user's **average-buy-price**
  (매수평균가, for profit-target selling). Avg-buy-price is read live from the page by label anchor;
  it is only available when **logged in with an actual holding** — otherwise the toggle shows a red
  "unavailable" state and avg-mode buttons no-op (never fabricates a price). Buy-side is unchanged
  (market-only); it could gain the same toggle later if wanted.

> Signal-overlay (RSI/MACD/volume) is a **separate** future feature — not in v0.1.

## Install (user)

Chrome → `chrome://extensions` → enable **Developer mode** → **Load unpacked** → select this folder.
Then open an Upbit exchange page; the buttons appear above the 매수가격/매도가격 input.

> Note: launching Chrome with `--load-extension` on the CLI is blocked in recent Chrome builds
> (152+). Use the Load-unpacked UI above — that is the normal path.

## How it works (per ar_3607/ar_3608 live findings)

- Price inputs are **React controlled-inputs** — values are injected with the native value setter
  plus dispatched `input`+`change` events (a plain `.value =` is ignored by React).
- The input is located by **label text** ("매수가격"/"매도가격") climbed to the nearest
  `input[inputmode=decimal]` — **not** by Upbit's `css-XXXX` emotion classes (those are hashed and
  change every build).
- A **MutationObserver** (debounced 300ms) re-injects the bar after React re-renders.
- **Upbit does NOT auto-rewrite the price field on market ticks** (verified: a set value held for
  12s across many ticks). So the lock only needs to guard against accidental user changes — done via
  an `input`/`change` listener that restores the locked value.

## Verified (live, CDP, read-only — no order submitted)

- Bar injects with all 6 buttons + lock icon.
- **+1%**: `110,796,000 → 111,904,000` (= ×1.01, tick-rounded to 1,000 KRW). ✓
- **Lock**: locked `111,904,000`, attempted change to `12,345,000` → reverted to `111,904,000`. ✓
- **MutationObserver**: bar removed → re-injected within 300ms. ✓
- Screenshot: `/tmp/upbit_helper_final.png`.

## Files

| file | role |
|------|------|
| `manifest.json` | MV3, content_script on `*.upbit.com/exchange*` |
| `content.js` | injection, ±% logic, native-setter value set, lock, MutationObserver |
| `helper.css` | `kuh-` prefixed styles (no clash with Upbit's css-XXXX) |

## Signal overlay (v0.2 / a_3640) — momentum indicator, display-only

A chart-anchored badge (top-right) showing a **BUY/SELL/WAIT momentum read** for the
currently-viewed market, computed from real Upbit Quotation API candle data.

- **Confluence**: RSI + MACD + Volume-confirmation, weighted (single-indicator banned —
  each ~50-55% alone, combo ~73-77% backtested). Score −100..+100.
- **Multi-timeframe gate**: 1h (trend) + 15m (timing, ~4× ratio, Elder). A signal fires **only
  when both timeframes agree** — fewer signals, higher quality. TF disagreement → 관망 (wait).
  "Most of the time: wait" is intended discipline, not a bug.
- **Ranging detection**: flags sideways markets (신뢰↓) where momentum signals are less reliable.
- **Honest labeling**: "모멘텀 지표" (momentum indicator), footer "예측 아님 · 자동주문 없음"
  (not a prediction · no auto-order). Display-only — never places an order.

**Data via background service worker**: content-script `fetch` to `api.upbit.com` is CORS-blocked
(verified "Failed to fetch"); the fetch runs in `background.js` (host_permissions grant it) and is
relayed to the content script. Updates every 60s and on market switch (SPA URL change).

### Verified (live, real API, no order)
- BTC: 1h RSI 64 / 15m RSI 47 → TF **disagree** → **관망** ✓
- TRUMP: 1h RSI 51 ▼ / 15m RSI 39 ▼ → TF **aligned bearish** → **매도** ✓ (python cross-check RSI 1h=51, 15m=39 — exact match)
- Auto-updates on market switch. Screenshots: `upbit_signal_live.png`, `upbit_signal_trump.png`.

### Files added
`signal.js` (indicators + overlay), `background.js` (CORS-safe candle fetch), signal styles in `helper.css`.
