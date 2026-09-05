/* kong-bit-helper v0.1 — content script.
 *
 * ar_3607/ar_3608 근거:
 *  - 매수가격/매도가격 = React controlled-input(free-decimal). 값 주입 = native-setter + input/change 이벤트 필수.
 *  - 앵커 = 텍스트라벨("매수가격"/"매도가격")로 input 을 찾음(css-XXXX emotion 해시는 빌드마다 변함 → 사용금지).
 *  - SPA(React) 재렌더 → MutationObserver 로 재주입.
 *  - Upbit 는 시세틱에 가격필드를 자동재작성하지 않음(a_3608 실측 12s 유지) → lock 은 사고성 변경만 방어(경량).
 *  - 현재가 = 주문폼 근처가 아닌 시세영역에서 읽되, 가장 견고한 소스 = 매수가격 인풋 placeholder/초기값이 아니라
 *    "현재가" 표기 요소. 폴백: 매수가격 input 의 현재 표시값(사용자 조작 전 = 시세).
 */
(() => {
  "use strict";

  // a_3789: %-preset 즐겨찾기 — buy/sell 각각 사용자 커스텀값을 chrome.storage.local 영속.
  //   기존 고정 PCTS = 기본값(첫 사용자·미저장시 폴백, 기존 동작 유지). 우클릭으로 개별 버튼 % 편집.
  const DEFAULT_PCTS = [-2, -1, -0.5, 0.5, 1, 2]; // 퍼센트 숫자(부호포함). buy/sell 공통 기본.
  // side별 현재 프리셋(퍼센트 숫자 배열). 로드 전엔 기본값.
  const _presets = { buy: DEFAULT_PCTS.slice(), sell: DEFAULT_PCTS.slice() };

  // 퍼센트 숫자 배열 → 버튼 스펙(label/d/cls)로 변환.
  function pctSpecs(side) {
    const arr = (_presets[side] && _presets[side].length ? _presets[side] : DEFAULT_PCTS);
    return arr.map((n) => ({
      label: (n > 0 ? "+" : "") + n + "%",
      d: n / 100,
      cls: n < 0 ? "kuh-down" : "kuh-up",
    }));
  }

  // storage에서 프리셋 로드(없으면 기본 유지). 로드 완료시 재주입.
  function loadPresets(cb) {
    try {
      chrome.storage?.local.get(["kbh_presets_buy", "kbh_presets_sell"], (r) => {
        if (r && Array.isArray(r.kbh_presets_buy) && r.kbh_presets_buy.length) _presets.buy = r.kbh_presets_buy;
        if (r && Array.isArray(r.kbh_presets_sell) && r.kbh_presets_sell.length) _presets.sell = r.kbh_presets_sell;
        cb && cb();
      });
    } catch (e) { cb && cb(); }
  }

  // 프리셋 저장(side별). 저장 후 재주입은 storage.onChanged가 처리.
  function savePresets(side) {
    try {
      const key = side === "sell" ? "kbh_presets_sell" : "kbh_presets_buy";
      chrome.storage?.local.set({ [key]: _presets[side] });
    } catch (e) {}
  }

  const nativeSetter = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype, "value"
  ).set;

  const parseNum = (s) => Number(String(s || "").replace(/[^0-9.]/g, "")) || 0;

  // BTC 가격대별 호가단위(대략) — 현재가 대비 %가격을 틱에 맞춰 반올림(제출 거부 방지).
  function tickSize(price) {
    if (price >= 2_000_000) return 1000;
    if (price >= 1_000_000) return 500;
    if (price >= 500_000) return 100;
    if (price >= 100_000) return 50;
    if (price >= 10_000) return 10;
    if (price >= 1_000) return 5;
    if (price >= 100) return 1;
    return 0.1;
  }
  const roundTick = (v) => {
    const t = tickSize(v);
    return Math.round(v / t) * t;
  };

  function setInputValue(input, value) {
    nativeSetter.call(input, String(value));
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
  }

  // 현재가 소스(a_3615 fix): document.title 이 라이브 시세를 담음(예 "▼ 110,844,000 BTC/KRW ...")
  //   → 가장 견고(항상 존재·실시간·미로그인 무관·매수/매도탭 무관). 폴백=현재가 라벨/인풋값.
  function getMarketPrice(priceInput) {
    // 시도1: document.title 의 첫 큰 숫자(코인 현재가).
    const mt = (document.title || "").match(/([\d,]{5,})\s*[A-Z]{2,5}\/KRW/);
    if (mt) {
      const v = parseNum(mt[1]);
      if (v > 0) return v;
    }
    // 시도2: '현재가' 라벨 근처 숫자.
    const nodes = document.querySelectorAll("span, strong, em, p");
    for (const n of nodes) {
      if (/현재가/.test((n.parentElement?.textContent) || "")) {
        const v = parseNum((n.textContent || "").trim());
        if (v > 0) return v;
      }
    }
    // 폴백: 인풋의 현재값(비어있으면 0 → 호출측에서 no-op).
    return parseNum(priceInput && priceInput.value);
  }

  // 현재 마켓의 코인 심볼(예 KRW-TRUMP → "TRUMP"). URL code 파라미터에서 추출.
  function currentCoinSymbol() {
    const m = (location.href.match(/KRW-([A-Z0-9]+)/) || [])[1];
    return m || null;
  }

  // 매수평균가(avg-buy-price) 읽기 — a_3636 재작성(컬럼-기반, 코인-매칭).
  //   ★ar_3635 버그: 구버전 라벨-형제 탐색이 엉뚱한 숫자(시세 근처)를 avg 로 오인 → silent-wrong.
  //   Upbit 보유(holdings) 테이블 구조: [코인심볼][보유수량/평가금][매수평균가][수익률].
  //   → '매수평균가' 헤더의 컬럼-인덱스를 구하고, 현재코인 row 의 그 컬럼 셀 값을 읽는다.
  //   보유 탭이 렌더돼 있어야 값 존재(¬있으면 null — silent-fallback 절대 금지).
  function getAvgBuyPrice() {
    const coin = currentCoinSymbol();
    if (!coin) return null;

    // ★Upbit 보유목록 = React div-grid(<table> 아님, role=table/cell). tag 비의존 + 기하정렬로 읽는다.
    //   전략: (1) '매수평균가' 헤더 요소 찾기(설정문구 제외) → 그 헤더의 화면 X좌표 = 컬럼 위치.
    //         (2) 현재코인 심볼을 가진 row(헤더와 다른 Y, 같은 표 컨테이너)의 셀들 중,
    //             헤더 X 와 가장 가까운 셀의 숫자 = 그 코인의 매수평균가.
    // a_3793 fix: 헤더는 텍스트-정확일치면 되고 childless 강제 불필요(래퍼요소도 허용).
    const headers = [...document.querySelectorAll("*")].filter((e) => {
      const t = (e.textContent || "").trim();
      if (t !== "매수평균가" && t !== "평균매수가") return false;
      // 자식 중에 같은 텍스트를 그대로 가진 게 있으면(즉 상위 래퍼면) 스킵 — 가장 안쪽 요소만.
      return ![...e.children].some((c) => (c.textContent || "").trim() === t);
    });
    // ★a_3793 fix3(devtools 실측 근거): 매수평균가 셀 = TD>EM 구조로 텍스트 "455.5 KRW"(숫자+단위 분리자식)
    //   → childless-leaf 필터로는 "455.5" 단독노드가 안 잡혔음(rowNums에 부재 확인).
    //   해결: "숫자 셀"을 childless 강제 없이, 텍스트가 [숫자(+KRW/콤마/소수)]로만 구성된 작은 요소로 판정.
    const NUM_CELL_RE = /^[\s]*[0-9][0-9,]*(\.[0-9]+)?\s*(KRW)?\s*$/;
    const numLeaves = [...document.querySelectorAll("td, em, span, div, p, b, strong")]
      .map((e) => ({ el: e, v: parseNum(e.textContent), r: e.getBoundingClientRect(), t: (e.textContent || "").trim() }))
      .filter((o) => o.v > 0 && o.r.width > 0 && o.r.width < 260 && NUM_CELL_RE.test(o.t));

    // ★a_3793 핵심수정: 코인심볼 요소 탐색시 childless 강제 제거.
    //   Upbit 보유행의 심볼은 [아이콘+텍스트] 래퍼(children>0)라 구버전 childless 필터가 전부 놓쳤음.
    //   → 텍스트에 coin이 정확 토큰으로 포함된 "가장 안쪽" 요소(자식이 같은 coin을 안 가진)만 후보.
    const coinRe = new RegExp("(^|[^A-Z0-9])" + coin + "([^A-Z0-9]|$)");
    const coinCandidates = [...document.querySelectorAll("*")].filter((e) => {
      const t = (e.textContent || "").trim();
      if (!coinRe.test(t)) return false;
      // 자식 중 같은 coin을 포함한 게 있으면 상위래퍼 → 스킵(가장 안쪽만).
      return ![...e.children].some((c) => coinRe.test((c.textContent || "").trim()));
    });

    // a_3793 fix2: 코인심볼이 차트헤더 등 표 밖에도 존재 → first-match-return시 엉뚱한 행 잡음("8" 오독).
    //   해결: 모든 (헤더×코인후보) 조합의 avg-컬럼 매칭 중 dx(컬럼정렬)가 가장 정확한 것을 선택.
    let bestV = null, bestScore = Infinity;
    for (const hd of headers) {
      const hr = hd.getBoundingClientRect();
      if (hr.width === 0) continue;
      const colX = hr.left + hr.width / 2;
      const coinEls = coinCandidates.filter((e) => {
        const r = e.getBoundingClientRect();
        // 반드시 헤더보다 아래(보유행) + 코인명이 avg컬럼 왼쪽.
        return r.width > 0 && r.top > hr.bottom - 2 && (r.left + r.width / 2) < colX;
      });
      for (const ce of coinEls) {
        const cr = ce.getBoundingClientRect();
        const rowY = cr.top + cr.height / 2;
        let best = null, bestDx = Infinity;
        for (const o of numLeaves) {
          if (Math.abs((o.r.top + o.r.height / 2) - rowY) > 26) continue; // 같은 행
          const dx = Math.abs((o.r.left + o.r.width / 2) - colX);
          if (dx < bestDx) { bestDx = dx; best = o; }
        }
        // 컬럼정렬 정확도(dx)로 최선후보 갱신. 헤더 바로아래 첫 행 우선(top 가까운).
        if (best && bestDx < 60) {
          const score = bestDx + (cr.top - hr.bottom) * 0.05; // dx 우선, 동률이면 위쪽 행.
          if (score < bestScore) { bestScore = score; bestV = best.v; }
        }
      }
    }
    return bestV; // ★못 찾으면 null — 절대 시세로 대체하지 않는다(a_3636 correctness).
  }

  // 라벨텍스트로 가격 input 을 찾는다(css-hash 비사용). 라벨워드가 조상 텍스트에 있는 decimal input.
  function findPriceInput(labelWord) {
    const decs = document.querySelectorAll('input[inputmode="decimal"]');
    for (const i of decs) {
      let p = i;
      for (let k = 0; k < 5 && p; k++) {
        p = p.parentElement;
        if (p && (p.textContent || "").includes(labelWord)) return i;
      }
    }
    return null;
  }

  const lockState = new WeakMap(); // input -> {locked:bool, value:string, handler:fn}

  function applyLock(input, on) {
    const st = lockState.get(input) || {};
    st.locked = on;
    if (on) {
      st.value = input.value;
      input.classList.add("kuh-locked-input");
      // 사고성 변경 방어: 값이 바뀌면 즉시 잠근값으로 복원(Upbit auto-rewrite 는 없지만 클릭/스크롤 실수 대비).
      st.handler = () => {
        if (st.locked && input.value !== st.value) {
          setInputValue(input, parseNum(st.value));
        }
      };
      input.addEventListener("input", st.handler, true);
      input.addEventListener("change", st.handler, true);
    } else {
      input.classList.remove("kuh-locked-input");
      if (st.handler) {
        input.removeEventListener("input", st.handler, true);
        input.removeEventListener("change", st.handler, true);
      }
    }
    lockState.set(input, st);
  }

  // side: 'buy' | 'sell'. sell 은 a_3615 로 기준(reference) 토글 추가: 시세 vs 매수평균가.
  function buildBar(input, side) {
    const bar = document.createElement("div");
    bar.className = "kuh-bar";
    bar.dataset.kuh = "1";

    // 기준모드 상태(a_3790: buy·sell 양쪽 노출). 'market'=현재가 대비, 'avg'=매수평균가 대비. 기본=market(기존유지).
    const refState = { mode: "market" };

    // ★a_3636 correctness: avg 모드는 절대 시세로 silent-대체하지 않는다.
    //   avg 모드 → getAvgBuyPrice() 만(null 이면 {ref:null,reason:'avg-unavail'} → no-op+badge).
    //   market 모드 → getMarketPrice().  두 소스가 섞이지 않도록 mode 로 완전 분기.
    // a_3790: buy 측도 avg 기준 지원(동일 안전-폴백). side 게이트 제거.
    function refPrice() {
      if (refState.mode === "avg") {
        const a = getAvgBuyPrice();
        return { ref: a && a > 0 ? a : null, mode: "avg" };
      }
      const m = getMarketPrice(input);
      return { ref: m && m > 0 ? m : null, mode: "market" };
    }

    function setRefUnavail(on) {
      const el = bar.querySelector(".kuh-ref");
      if (!el) return;
      el.classList.toggle("kuh-ref-unavail", on);
      if (on) el.title = "내 평균단가를 읽지 못했습니다(미보유·미로그인이거나 '보유' 탭 미확인) — 우측 '보유' 탭을 한 번 열어 값이 보이게 한 뒤 다시 시도하세요. 첫 매수라면 '현재가' 기준을 사용하세요(시세로 임의대체하지 않음).";
    }

    const specs = pctSpecs(side);
    specs.forEach((p, idx) => {
      const b = document.createElement("span");
      b.className = "kuh-btn " + p.cls;
      b.textContent = p.label;
      b.title = `${refState.mode === "avg" ? "내 평균단가" : "현재가"} 기준 ${p.label} (틱 정렬) · 우클릭=% 편집`;
      // a_3789: 우클릭 → 이 버튼 % 값 편집(영속 저장).
      b.addEventListener("contextmenu", (e) => {
        e.preventDefault();
        e.stopPropagation();
        const cur = _presets[side][idx];
        const raw = window.prompt(`${side === "sell" ? "매도" : "매수"} 버튼 % 값 (부호포함, 예: +3 또는 -5)`, String(cur));
        if (raw == null) return;
        const v = Number(String(raw).replace(/[^0-9.\-]/g, ""));
        if (!isFinite(v) || v === 0) return;
        _presets[side][idx] = v;
        savePresets(side);
        // a_3789: onChanged 의존 않고 즉시 재주입(확실한 버튼 갱신). storage는 영속용.
        try {
          document.querySelectorAll('[data-kuh="1"]').forEach((bb) => bb.remove());
          document.querySelectorAll('input[data-kuh-bound]').forEach((i) => { delete i.dataset.kuhBound; delete i.dataset.kuhBarId; });
          injectAll();
        } catch (err) {}
      });
      b.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        const r = refPrice();
        if (r.ref == null) {
          // ★avg 미가용 → 절대 시세로 대체 금지. no-op + 명확한 unavail 표식(avg 모드일 때).
          if (r.mode === "avg") setRefUnavail(true);
          return;
        }
        if (r.mode === "avg") setRefUnavail(false); // 값 정상 확인 → 배지 해제.
        const target = roundTick(r.ref * (1 + p.d));
        const st = lockState.get(input);
        if (st && st.locked) {
          st.value = String(target);
        }
        setInputValue(input, target);
      });
      bar.appendChild(b);
    });

    // 기준 토글(a_3615 sell → a_3790 buy·sell 양쪽): [현재가|매수가] 클릭 전환. 동일 안전-폴백.
    {
      const ref = document.createElement("span");
      ref.className = "kuh-ref";
      const render = () => {
        // a_3791: "매수가"는 매수체결가로 오인 소지 → "평균단가"로 명확화. side별 tooltip으로 용도 설명.
        ref.textContent = (refState.mode === "market" ? "기준:현재가" : "기준:평균단가");
        ref.title = side === "buy"
          ? "기준가 전환(현재가 ↔ 내 평균단가). '평균단가' 기준은 이미 보유중인 코인에 추가매수(물타기)할 때, 내 평균매수단가 대비 몇 %로 살지 계산합니다. 미보유·미로그인이면 사용불가(빨간표시)이며 가격을 임의로 만들지 않습니다 — 첫 매수라면 '현재가' 기준을 쓰세요."
          : "기준가 전환(현재가 ↔ 내 평균단가). '평균단가' 기준은 보유 포지션을 내 평균매수단가 대비 몇 %에 매도할지 계산합니다. 미보유·미로그인이면 사용불가(빨간표시).";
      };
      render();
      ref.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        refState.mode = refState.mode === "market" ? "avg" : "market";
        ref.classList.remove("kuh-ref-unavail");
        // avg 로 바꿨는데 값 없으면 즉시 미가용 표식(안내).
        if (refState.mode === "avg" && getAvgBuyPrice() == null) {
          ref.classList.add("kuh-ref-unavail");
          ref.title = "내 평균단가를 찾지 못함(로그인+해당코인 보유 필요). 첫 매수라면 '현재가' 기준을 사용하세요.";
        }
        render();
      });
      bar.appendChild(ref);
    }

    const lock = document.createElement("span");
    lock.className = "kuh-lock";
    lock.textContent = "🔓";
    lock.title = "가격 잠금(사고성 변경 방지)";
    lock.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const st = lockState.get(input) || {};
      const now = !st.locked;
      applyLock(input, now);
      lock.textContent = now ? "🔒" : "🔓";
      lock.classList.toggle("kuh-locked", now);
    });
    bar.appendChild(lock);

    return bar;
  }

  function injectFor(labelWord, side) {
    const input = findPriceInput(labelWord);
    if (!input) return false;
    // ★a_3635 fix: dedup 은 '이 input 에 이미 우리 바가 붙었나'로 판정(per-input marker),
    //   컨테이너-단위 [data-kuh] 검사(구버전)는 stale buy-bar 가 남아있으면 sell-bar 주입을 막아
    //   기준-토글이 안 붙는 버그가 있었다. 입력요소에 직접 표식.
    if (input.dataset.kuhBound === side) {
      // 같은 input 에 같은 side 바가 이미 붙음 → 살아있으면 유지.
      const prev = input.dataset.kuhBarId && document.getElementById(input.dataset.kuhBarId);
      if (prev) return true;
    }
    const host = input.closest("div") || input.parentElement;
    if (!host || !host.parentElement) return false;
    // 이 host 에 남아있는 우리 바(다른 side 포함) 제거 후 재주입(탭 전환 stale 방지).
    host.parentElement.querySelectorAll('[data-kuh="1"]').forEach((b) => b.remove());
    const bar = buildBar(input, side);
    const barId = "kuh-bar-" + side;
    bar.id = barId;
    input.dataset.kuhBound = side;
    input.dataset.kuhBarId = barId;
    host.parentElement.insertBefore(bar, host);
    return true;
  }

  function injectAll() {
    injectFor("매수가격", "buy");
    injectFor("매도가격", "sell");
  }

  // 최초 + SPA 재렌더 대응(MutationObserver, 디바운스).
  let pending = null;
  function scheduleInject() {
    if (pending) return;
    pending = setTimeout(() => {
      pending = null;
      try { injectAll(); } catch (e) { /* noop */ }
    }, 300);
  }

  // a_3789: 저장된 프리셋 먼저 로드 후 주입(첫 주입부터 커스텀값 반영). 로드 실패시에도 기본값으로 주입.
  loadPresets(() => { try { injectAll(); } catch (e) {} });
  injectAll(); // 즉시 1회(로드 콜백 지연 대비, 기본값). 로드 완료시 재주입으로 갱신.
  const mo = new MutationObserver(() => {
    // 우리 자신의 주입으로 인한 mutation 은 무시(data-kuh 만 추가된 경우).
    scheduleInject();
  });
  mo.observe(document.body, { childList: true, subtree: true });

  // a_3789: 프리셋 변경(우클릭 편집 저장) 실시간 반영 — 버튼 재생성 위해 강제 재주입.
  try {
    chrome.storage?.onChanged.addListener((ch, area) => {
      if (area !== "local") return;
      if (ch.kbh_presets_buy) _presets.buy = Array.isArray(ch.kbh_presets_buy.newValue) && ch.kbh_presets_buy.newValue.length ? ch.kbh_presets_buy.newValue : DEFAULT_PCTS.slice();
      if (ch.kbh_presets_sell) _presets.sell = Array.isArray(ch.kbh_presets_sell.newValue) && ch.kbh_presets_sell.newValue.length ? ch.kbh_presets_sell.newValue : DEFAULT_PCTS.slice();
      if (ch.kbh_presets_buy || ch.kbh_presets_sell) {
        // 기존 바 제거 후 재주입(버튼 라벨/값 갱신).
        document.querySelectorAll('[data-kuh="1"]').forEach((b) => b.remove());
        document.querySelectorAll('[data-kuh-bound]')?.forEach?.(() => {});
        document.querySelectorAll('input').forEach((i) => { delete i.dataset.kuhBound; delete i.dataset.kuhBarId; });
        injectAll();
      }
    });
  } catch (e) {}

  window.__kuh_loaded = "0.1.0";
  console.log("[kong-bit-helper] v0.1 loaded");
})();
