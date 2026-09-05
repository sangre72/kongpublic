/* kong-upbit-helper v0.1 — content script.
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

  const PCTS = [
    { label: "-2%", d: -0.02, cls: "kuh-down" },
    { label: "-1%", d: -0.01, cls: "kuh-down" },
    { label: "-0.5%", d: -0.005, cls: "kuh-down" },
    { label: "+0.5%", d: 0.005, cls: "kuh-up" },
    { label: "+1%", d: 0.01, cls: "kuh-up" },
    { label: "+2%", d: 0.02, cls: "kuh-up" },
  ];

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
    const headers = [...document.querySelectorAll("*")].filter((e) => {
      const t = (e.textContent || "").trim();
      return (t === "매수평균가" || t === "평균매수가") && e.children.length === 0;
    });
    // 문서 전체의 말단 숫자요소 캐시(geometry 매칭용).
    const allLeaves = [...document.querySelectorAll("*")].filter((e) => e.children.length === 0);
    const numLeaves = allLeaves
      .map((e) => ({ el: e, v: parseNum(e.textContent), r: e.getBoundingClientRect() }))
      .filter((o) => o.v > 0 && o.r.width > 0);

    for (const hd of headers) {
      const hr = hd.getBoundingClientRect();
      if (hr.width === 0) continue;
      const colX = hr.left + hr.width / 2;
      // 현재 코인 심볼을 가진 말단요소들(문서 전체 — 사이드바 div-grid 가 헤더와 sibling 일 수 있음).
      //   헤더보다 X 가 왼쪽(코인명이 avg컬럼 왼쪽) + 헤더보다 아래(row 는 헤더 아래) 인 것만 후보.
      const coinEls = allLeaves.filter((e) => {
        if ((e.textContent || "").trim() !== coin) return false;
        const r = e.getBoundingClientRect();
        return r.width > 0 && r.top > hr.top - 5 && (r.left + r.width / 2) < colX;
      });
      for (const ce of coinEls) {
        const cr = ce.getBoundingClientRect();
        const rowY = cr.top + cr.height / 2;
        // 같은 행(Y 근접) + 헤더 X 에 가장 가까운 숫자셀.
        let best = null, bestDx = Infinity;
        for (const o of numLeaves) {
          if (Math.abs((o.r.top + o.r.height / 2) - rowY) > 26) continue; // 같은 행
          const dx = Math.abs((o.r.left + o.r.width / 2) - colX);
          if (dx < bestDx) { bestDx = dx; best = o; }
        }
        if (best && bestDx < 90) return best.v;
      }
    }
    return null; // ★못 찾으면 null — 절대 시세로 대체하지 않는다(a_3636 correctness).
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

    // 기준모드 상태(sell 만 노출). 'market'=현재가 대비, 'avg'=매수평균가 대비. 기본=market(기존유지).
    const refState = { mode: "market" };

    // ★a_3636 correctness: avg 모드는 절대 시세로 silent-대체하지 않는다.
    //   avg 모드 → getAvgBuyPrice() 만(null 이면 {ref:null,reason:'avg-unavail'} → no-op+badge).
    //   market 모드 → getMarketPrice().  두 소스가 섞이지 않도록 mode 로 완전 분기.
    function refPrice() {
      if (side === "sell" && refState.mode === "avg") {
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
      if (on) el.title = "매수평균가를 읽지 못했습니다 — 우측 '보유' 탭을 한 번 열어 값이 보이게 한 뒤 다시 시도하세요(시세로 대체하지 않음).";
    }

    for (const p of PCTS) {
      const b = document.createElement("span");
      b.className = "kuh-btn " + p.cls;
      b.textContent = p.label;
      b.title = `${side === "sell" && refState.mode === "avg" ? "매수평균가" : "현재가"} ${p.label} (틱 정렬)`;
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
    }

    // sell-side 기준 토글(a_3615): [현재가|매수가] 클릭 전환.
    if (side === "sell") {
      const ref = document.createElement("span");
      ref.className = "kuh-ref";
      const render = () => {
        ref.textContent = (refState.mode === "market" ? "기준:현재가" : "기준:매수가");
        ref.title = "기준가 전환(현재가 ↔ 매수평균가). 매수평균가는 로그인+보유 시에만 사용가능.";
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
          ref.title = "매수평균가를 페이지에서 찾지 못함(로그인+보유 필요). 현재가 기준으로 사용하세요.";
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

  injectAll();
  const mo = new MutationObserver(() => {
    // 우리 자신의 주입으로 인한 mutation 은 무시(data-kuh 만 추가된 경우).
    scheduleInject();
  });
  mo.observe(document.body, { childList: true, subtree: true });

  window.__kuh_loaded = "0.1.0";
  console.log("[kong-upbit-helper] v0.1 loaded");
})();
