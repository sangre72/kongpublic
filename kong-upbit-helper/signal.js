/* kong-upbit-helper — buy/sell signal chart-overlay (a_3640, display-only).
 *
 * 방법론(fork-verified 실무문헌 재사용, ¬재설계):
 *  - confluence = RSI + MACD + Volume 가중(단일지표 금지 — 각 ~50-55%, 조합 ~73-77% backtest).
 *  - multi-TF alignment gate: 상위TF(1h) 추세방향 확인 + 하위TF(15m) 진입타이밍(Elder, ~4x).
 *    두 TF 동의해야 발화 → 신호 적음이 정상(전문가 규율, ¬버그).
 *  - 정직 라벨: "모멘텀 지표"(¬"예측"). 횡보장(ranging) 감지시 별도 표기(추세장과 구분).
 *
 * 데이터: Upbit Quotation API(candle OHLCV, no-auth) — DOM-scrape ¬사용(UI-fragile 회피).
 * 표시전용: 자동주문 절대 없음. price-helper(content.js)와 같은 안전패턴(label-anchor, MutationObserver).
 */
(() => {
  "use strict";

  const API = "https://api.upbit.com/v1/candles/minutes";
  const HTF_UNIT = 60;   // 상위TF = 1시간(추세방향)
  const LTF_UNIT = 15;   // 하위TF = 15분(진입타이밍) — ~4x ratio(Elder)
  const POLL_MS = 60_000; // 1분마다 갱신(API rate 여유, 캔들틱 대응)

  const num = (s) => Number(String(s).replace(/[^0-9.\-]/g, "")) || 0;

  function currentMarket() {
    const m = (location.href.match(/KRW-([A-Z0-9]+)/) || [])[1];
    return m ? "KRW-" + m : null;
  }

  // ★CORS: content-script 직접 fetch(api.upbit.com)는 차단됨('Failed to fetch' 실증).
  //   → background service-worker 에 message 로 요청(host_permissions 로 SW 는 cross-origin 허용).
  function fetchCandles(market, unit, count) {
    return new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(
        { type: "kuh-candles", market, unit, count },
        (resp) => {
          if (chrome.runtime.lastError) return reject(new Error(chrome.runtime.lastError.message));
          if (!resp || !resp.ok) return reject(new Error(resp && resp.error ? resp.error : "no-resp"));
          // 최신→과거 로 오므로 뒤집어 과거→최신.
          resolve(resp.data.slice().reverse());
        }
      );
    });
  }

  // ---- 지표(python 프로토타입과 동일 검증됨) ----
  function rsi(closes, n = 14) {
    if (closes.length < n + 1) return null;
    let g = 0, l = 0;
    for (let i = 1; i <= n; i++) {
      const ch = closes[i] - closes[i - 1];
      g += Math.max(ch, 0); l += Math.max(-ch, 0);
    }
    let ag = g / n, al = l / n;
    for (let i = n + 1; i < closes.length; i++) {
      const ch = closes[i] - closes[i - 1];
      ag = (ag * (n - 1) + Math.max(ch, 0)) / n;
      al = (al * (n - 1) + Math.max(-ch, 0)) / n;
    }
    if (al === 0) return 100;
    return 100 - 100 / (1 + ag / al);
  }
  function emaSeries(vals, n) {
    const k = 2 / (n + 1); const out = [vals[0]];
    for (let i = 1; i < vals.length; i++) out.push(vals[i] * k + out[i - 1] * (1 - k));
    return out;
  }
  function macd(closes) {
    if (closes.length < 35) return null;
    const e12 = emaSeries(closes, 12), e26 = emaSeries(closes, 26);
    const line = e12.map((v, i) => v - e26[i]);
    const sig = emaSeries(line, 9);
    return { line: line[line.length - 1], signal: sig[sig.length - 1], hist: line[line.length - 1] - sig[sig.length - 1] };
  }
  // 횡보 감지: 최근 ATR-유사 변동폭 대비 방향성 약하면 ranging.
  function isRanging(closes, n = 20) {
    if (closes.length < n) return false;
    const recent = closes.slice(-n);
    const hi = Math.max(...recent), lo = Math.min(...recent);
    const range = (hi - lo) / lo;
    // 최근 net 이동 / 총 변동폭 비율이 낮으면 방향성 약함(횡보).
    const net = Math.abs(recent[recent.length - 1] - recent[0]) / lo;
    return range > 0 && net / range < 0.35; // 넷무브가 레인지의 35% 미만 = 횡보
  }

  // ---- confluence 점수(가중) ----
  // RSI(방향+과매수/도), MACD(hist 부호+기울기), Volume(현재>평균 확인). -100..+100.
  function confluence(closes, vols) {
    const r = rsi(closes);
    const m = macd(closes);
    if (r == null || m == null) return null;
    let score = 0;
    // RSI 기여(±40): 50 기준 편차, 극단(>70/<30)은 과매수/도로 역가중 살짝.
    let rsiPart = ((r - 50) / 50) * 40;
    if (r > 72) rsiPart *= 0.5;   // 과매수 → 매수신호 약화
    if (r < 28) rsiPart *= 0.5;   // 과매도 → 매도신호 약화
    score += rsiPart;
    // MACD 기여(±40): hist 부호. 정규화(가격대별 스케일 → tanh 유사).
    const macdPart = Math.max(-40, Math.min(40, (m.hist / (Math.abs(closes[closes.length - 1]) * 0.002)) * 40));
    score += macdPart;
    // Volume 확인(±20): 현재봉 거래량이 최근평균 초과면 신호 신뢰 가중(방향은 RSI/MACD 따름).
    const vAvg = vols.slice(-21, -1).reduce((a, b) => a + b, 0) / 20;
    const vNow = vols[vols.length - 1];
    const volConfirm = vAvg > 0 ? vNow / vAvg : 0;
    const dir = Math.sign(rsiPart + macdPart);
    score += dir * Math.max(0, Math.min(20, (volConfirm - 1) * 20));
    return { score: Math.max(-100, Math.min(100, score)), rsi: r, macdHist: m.hist, volRatio: volConfirm };
  }

  // ---- multi-TF gate ----
  function tfDirection(c) { return c.score >= 15 ? 1 : c.score <= -15 ? -1 : 0; }

  // a_3673/a_3675: IQR 중간범위 진폭%(캔들별 (high-low)/low×100 → 정렬 → 상하 25% 이상치 제외 →
  //   중간 50%(Q1..Q3) 평균). 급등락 스파이크·무변동 캔들 배제한 "보통 캔들" 대표 진폭. 이미 fetch한 캔들 재사용.
  function iqrAmplitude(candles) {
    const amp = candles
      .map((c) => (c.low_price ? (c.high_price - c.low_price) / c.low_price * 100 : 0))
      .filter((a) => a >= 0);
    const n = amp.length;
    if (n < 8) return null;
    const s = amp.slice().sort((a, b) => a - b);
    const q1 = s[Math.floor(n / 4)], q3 = s[Math.floor((3 * n) / 4)];
    const mid = s.filter((a) => a >= q1 && a <= q3);
    if (!mid.length) return null;
    const avg = mid.reduce((x, y) => x + y, 0) / mid.length;
    return { avg, q1, q3, n, midN: mid.length }; // a_3677: breakdown 노출(투명성)
  }

  async function computeSignal(market) {
    const [htf, ltf] = await Promise.all([
      fetchCandles(market, HTF_UNIT, 200),
      fetchCandles(market, LTF_UNIT, 200),
    ]);
    const hc = htf.map((c) => c.trade_price), hv = htf.map((c) => c.candle_acc_trade_volume);
    const lc = ltf.map((c) => c.trade_price), lv = ltf.map((c) => c.candle_acc_trade_volume);
    const H = confluence(hc, hv), L = confluence(lc, lv);
    if (!H || !L) return { state: "no-data" };
    const ranging = isRanging(hc);
    const dH = tfDirection(H), dL = tfDirection(L);
    // gate: 두 TF 방향 동의 + 둘 다 non-zero → 신호. 아니면 관망.
    let signal = "관망"; // neutral / wait
    if (dH !== 0 && dH === dL) signal = dH > 0 ? "매수" : "매도";
    return {
      state: "ok", signal, ranging,
      htf: H, ltf: L, dH, dL,
      amp1h: iqrAmplitude(htf), // a_3675: 1h IQR 중간범위 진폭%(same htf fetch 재사용)
      // 표시 점수 = 두 TF 평균(정렬시), 아니면 상위TF.
      shown: dH === dL ? Math.round((H.score + L.score) / 2) : Math.round(H.score),
    };
  }

  // ---- overlay UI ----
  // a_3645: 배지를 TradingView 차트 컨테이너(#tv_chart_container, stable id) 안 우상단에
  //   absolute 배치 → 차트 위에 얹혀 보이고 window-resize 에도 차트 따라감(하드코딩 픽셀 X).
  function chartContainer() {
    // 여러 후보 + 가장 큰(실제 차트) 컨테이너 선택. TradingView 지연마운트 대비 크기검증.
    const cands = [
      document.getElementById("tv_chart_container"),
      document.querySelector(".TVChartContainer"),
      document.querySelector('[id^="tradingview_"]'),
      document.querySelector('[id^="tradingview_"]')?.parentElement,
      document.querySelector('iframe[id*="tradingview" i]')?.parentElement,
      document.querySelector('[class*="TVChart" i]'),
    ].filter(Boolean);
    for (const c of cands) {
      const r = c.getBoundingClientRect();
      if (r.width > 400 && r.height > 250) return c; // 실제 차트 크기여야 채택
    }
    return null;
  }
  function ensureBadge() {
    let el = document.getElementById("kuh-signal");
    const chart = chartContainer();
    if (el) {
      // 차트가 (지연로드/재렌더로) 이제 존재하고 배지가 아직 그 안이 아니면 → 안으로 이동 + onchart 클래스.
      if (chart && el.parentElement !== chart) {
        if (getComputedStyle(chart).position === "static") chart.style.position = "relative";
        el.classList.add("kuh-signal-onchart"); // ★이동 시 onchart 클래스 부여(안 하면 fixed 유지 버그)
        chart.appendChild(el);
      }
      return el;
    }
    el = document.createElement("div");
    el.id = "kuh-signal";
    el.className = "kuh-signal";
    if (chart) {
      // 컨테이너 기준 absolute 배치 위해 relative 보장.
      if (getComputedStyle(chart).position === "static") chart.style.position = "relative";
      el.classList.add("kuh-signal-onchart");
      chart.appendChild(el);
    } else {
      // 차트 못 찾으면 종전 fixed 폴백.
      document.body.appendChild(el);
    }
    return el;
  }

  function render(sig, market) {
    const el = ensureBadge();
    // ★render 시 className 을 통째 재설정하면 kuh-signal-onchart(위치클래스)가 지워진다 →
    //   onchart 여부를 보존해 재적용(a_3645 위치버그 방지).
    const onchart = el.classList.contains("kuh-signal-onchart") ? " kuh-signal-onchart" : "";
    if (!sig || sig.state !== "ok") {
      el.innerHTML = `<div class="kuh-sig-head">모멘텀 지표</div><div class="kuh-sig-body">데이터 대기…</div>`;
      el.className = "kuh-signal kuh-sig-wait" + onchart;
      return;
    }
    const cls = sig.signal === "매수" ? "kuh-sig-buy" : sig.signal === "매도" ? "kuh-sig-sell" : "kuh-sig-wait";
    el.className = "kuh-signal " + cls + onchart;
    const rangeTag = sig.ranging ? ' <span class="kuh-sig-range">횡보장(신뢰↓)</span>' : "";
    el.innerHTML = `
      <div class="kuh-sig-head">모멘텀 지표 · ${market.replace("KRW-", "")}${rangeTag}</div>
      <div class="kuh-sig-main">${sig.signal} <span class="kuh-sig-score">(${sig.shown > 0 ? "+" : ""}${sig.shown})</span></div>
      <div class="kuh-sig-detail">
        1h: RSI ${sig.htf.rsi.toFixed(0)} · MACD ${sig.htf.macdHist > 0 ? "▲" : "▼"} · Vol×${sig.htf.volRatio.toFixed(1)}<br>
        15m: RSI ${sig.ltf.rsi.toFixed(0)} · MACD ${sig.ltf.macdHist > 0 ? "▲" : "▼"} · Vol×${sig.ltf.volRatio.toFixed(1)}<br>
        TF정렬: ${sig.dH === sig.dL && sig.dH !== 0 ? "일치 ✓" : "불일치 → 관망"}<br>
        진폭(1h중간): ${sig.amp1h ? sig.amp1h.avg.toFixed(1) + "%" : "-"}
      </div>
      <div class="kuh-sig-foot">예측 아님 · 모멘텀 참고용 · 자동주문 없음</div>`;
  }

  let timer = null, lastMarket = null;
  async function tick() {
    const market = currentMarket();
    if (!market) return;
    lastMarket = market;
    try {
      const sig = await computeSignal(market);
      // 시장이 그 사이 바뀌었으면 stale 표시 방지.
      if (currentMarket() === market) {
        render(sig, market);
        // a_3677: execute.js 가 amplitude breakdown 을 읽어 추천매도가 계산에 재사용.
        window.__kuh_amp = sig.amp1h ? { ...sig.amp1h, market } : null;
      }
    } catch (e) {
      render(null, market);
    }
  }

  function start() {
    tick();
    if (timer) clearInterval(timer);
    timer = setInterval(tick, POLL_MS);
    // 마켓 전환(SPA URL 변경) 감지 → 즉시 갱신.
    let href = location.href;
    setInterval(() => {
      if (location.href !== href) { href = location.href; tick(); }
    }, 1500);
    // ★a_3645: TradingView 차트가 지연-마운트되므로, 배지가 아직 차트 밖(body)이면
    //   차트 나타날 때까지 짧게 폴링해 안으로 재배치(ensureBadge 의 move-branch 트리거).
    let tries = 0;
    const reposition = setInterval(() => {
      tries++;
      const el = document.getElementById("kuh-signal");
      const chart = chartContainer();
      if (el && chart && el.parentElement !== chart) ensureBadge();
      if (tries > 40 || (el && chart && el.parentElement === chart)) clearInterval(reposition);
    }, 500); // 최대 20초
  }

  // 차트 로드 후 시작(MutationObserver로 배지 유지).
  start();
  new MutationObserver(() => {
    if (!document.getElementById("kuh-signal") && currentMarket()) tick();
  }).observe(document.body, { childList: true, subtree: true });

  console.log("[kong-upbit-helper] signal overlay loaded");
})();
