/* kong-upbit-helper — signal-triggered auto-execute (a_3649). ★REAL MONEY — highest caution.
 *
 * SPEC(user u_3646~3648):
 *  - BUY-signal → "즉시매수" 버튼 + KRW 금액입력(기본 5,100, configurable) → 클릭 = 금액세팅 +
 *    시장가 선택 + 실제 매수 submit 클릭(full-auto, u_3647).
 *  - SELL-signal → "즉시매도" + 모드(+1호가 / 시장가) → 클릭 = 세팅 + 실제 매도 submit.
 *  - 금액입력 + 잔액(주문가능) 비교 → 부족하면 버튼 disabled(silent-fail 금지).
 *
 * SAFETY(real-money 최소기준):
 *  1. amount-cap: MAX_PER_CLICK(기본 50,000원) 초과 = 차단(fat-finger/runaway guard).
 *  2. ★FIRST live-test(5,100원)= worker 는 submit 클릭 안 함(human-only, G6/security §3). 금액+주문유형만
 *     세팅하고 ready-state 로 둔다. window.KUH_ARM_SUBMIT===true 일 때만 실제 submit 클릭 활성(기본 false).
 *     유저가 첫 테스트 성공 확인 후에야 full-auto(arm) 허용.
 *  3. execute_log.jsonl 감사로그: 모든 시도(ts,coin,side,amount,signal,armed,submitted) 기록(localStorage
 *     + console, 파일쓰기는 확장에서 직접 불가 → localStorage 'kuh_exec_log' 누적 + 다운로드 헬퍼).
 *
 * DOM 안전: label-anchor(¬css-hash), native-setter+events(React), 클릭전 재검증.
 */
(() => {
  "use strict";

  const DEFAULT_AMOUNT = 5100;      // 첫 테스트 금액(u_3648)
  const MAX_PER_CLICK = 50000;      // safety#1 amount-cap(원)
  const num = (s) => Number(String(s || "").replace(/[^0-9.]/g, "")) || 0;

  const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
  function setInputValue(input, value) {
    nativeSetter.call(input, String(value));
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
  }
  function currentCoin() { return (location.href.match(/KRW-([A-Z0-9]+)/) || [])[1] || null; }

  // ---- audit log(localStorage 누적; 확장은 파일직접쓰기 불가) ----
  function logExec(entry) {
    try {
      const key = "kuh_exec_log";
      const arr = JSON.parse(localStorage.getItem(key) || "[]");
      arr.push(entry);
      localStorage.setItem(key, JSON.stringify(arr.slice(-500)));
      console.log("[kuh-exec-log]", JSON.stringify(entry));
    } catch (e) { /* noop */ }
  }
  // 다운로드 헬퍼(콘솔에서 __kuhDownloadLog() 호출 → execute_log.jsonl).
  window.__kuhDownloadLog = () => {
    const arr = JSON.parse(localStorage.getItem("kuh_exec_log") || "[]");
    const blob = new Blob([arr.map((e) => JSON.stringify(e)).join("\n")], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = "execute_log.jsonl"; a.click();
  };

  // ---- a_3653: 거래지원 종료예정(delisting) 경고팝업 auto-dismiss ----
  //   flagged 코인 주문폼 열면 "거래지원 종료 예정 안내" 모달이 확인버튼으로 order-flow 를 막는다.
  //   text-anchor 로 모달 감지 → 확인 클릭 → execute_log 에 기록(silent 금지). 주문 CONTENT 불변(정보게이트만 해제).
  let _lastDismiss = 0;
  function dismissDelistingWarning() {
    // 모달 제목 텍스트로 감지(css-hash 비사용).
    const title = [...document.querySelectorAll("*")].find(
      (e) => e.children.length === 0 && /거래지원 종료 예정 안내|거래지원 종료 안내|유의 종목 안내/.test((e.textContent || "").trim())
    );
    if (!title) return false;
    // 모달 컨테이너 안의 '확인' 버튼/링크 클릭.
    let modal = title;
    for (let k = 0; k < 6 && modal.parentElement; k++) modal = modal.parentElement;
    const ok = [...modal.querySelectorAll("button, a")].find((e) => (e.textContent || "").trim() === "확인");
    if (!ok) return false;
    const now = Date.now();
    if (now - _lastDismiss < 3000) return true; // 중복클릭 방지
    _lastDismiss = now;
    ok.click();
    logExec({ ts: new Date().toISOString(), coin: currentCoin(), event: "delisting_warning_dismissed" });
    // 배지에도 표식(유저 가시성 — real-time push 대안, 아래 notify-note 참조).
    const badge = document.getElementById("kuh-signal");
    if (badge && !badge.querySelector(".kuh-delist-note")) {
      const n = document.createElement("div");
      n.className = "kuh-delist-note";
      n.textContent = "⚠ 거래지원 종료예정 경고 자동확인됨";
      badge.appendChild(n);
      setTimeout(() => n.remove(), 15000);
    }
    return true;
  }
  // 상시 감시(팝업이 order-form 열 때 뜨므로): 1.5s 폴링 + execute 직전에도 호출.
  setInterval(dismissDelistingWarning, 1500);

  // ---- DOM readers(label-anchor) ----
  function orderTab() {
    // 현재 활성 매수/매도 탭 판정(주문폼). 활성표시가 애매하면 존재하는 가격라벨로 추론.
    if ([...document.querySelectorAll("*")].some((e) => e.children.length === 0 && (e.textContent || "").trim() === "매도가격")) return "sell";
    return "buy";
  }
  function priceInput(side) {
    const label = side === "sell" ? "매도가격" : "매수가격";
    for (const i of document.querySelectorAll('input[inputmode="decimal"]')) {
      let p = i; for (let k = 0; k < 5 && p; k++) { p = p.parentElement; if (p && (p.textContent || "").includes(label)) return i; }
    }
    return null;
  }
  function totalInput() {
    for (const i of document.querySelectorAll('input[inputmode="decimal"]')) {
      let p = i; for (let k = 0; k < 5 && p; k++) { p = p.parentElement; if (p && (p.textContent || "").includes("주문총액")) return i; }
    }
    return null;
  }
  // ★real-money: 잔액 0 을 null(못읽음)과 구분해야 한다 — 구버전은 v>0 만 반환해 잔액0이 null 로
  //   빠져 disable 이 안 걸리는 안전구멍이 있었다(a_3649 실측: 주문가능=0인데 버튼 활성). 수정: KRW/원
  //   토큰 근처 숫자를 찾으면 0 이라도 반환.
  function availableBalance() {
    const l = [...document.querySelectorAll("*")].find((e) => e.children.length === 0 && (e.textContent || "").trim() === "주문가능");
    if (!l) return null;
    let p = l;
    for (let k = 0; k < 5 && p; k++) {
      p = p.parentElement;
      if (p) {
        const t = (p.textContent || "").replace("주문가능", "");
        // KRW/원 표기가 있는 잔액행이면 숫자 파싱(0 포함). ¬있으면 계속 위로.
        if (/KRW|원/.test(t) && /\d/.test(t)) return num(t);
      }
    }
    return null;
  }
  function orderTypeTab(name) {
    return [...document.querySelectorAll("*")].find((e) => e.children.length === 0 && (e.textContent || "").trim() === name) || null;
  }
  // 실제 매수/매도 submit 버튼: 주문폼 하단의 큰 컬러 버튼(텍스트 정확히 '매수'/'매도', <button> or <a>).
  //   ★real-money: 가장 아래(y 최대) + 폼 안 것만. 탭('매수'/'매도' 상단 탭)과 구분 위해 y-position 사용.
  function submitButton(side) {
    const label = side === "sell" ? "매도" : "매수";
    const cands = [...document.querySelectorAll("button, a")].filter((e) => (e.textContent || "").trim() === label);
    if (!cands.length) return null;
    // 가장 아래쪽(주문폼 제출버튼이 탭보다 아래) 채택.
    return cands.sort((a, b) => b.getBoundingClientRect().top - a.getBoundingClientRect().top)[0];
  }

  // ---- execute ----
  // armed=false(기본): 금액+주문유형만 세팅, submit 클릭 안 함(첫 테스트 human-only). armed=true: 실제 클릭.
  function execute(side, amountKRW, sellMode) {
    const coin = currentCoin();
    dismissDelistingWarning(); // a_3653: 정보게이트 먼저 해제(막힘 방지). 주문 CONTENT 불변.
    const armed = window.KUH_ARM_SUBMIT === true;
    const bal = availableBalance();
    const base = { ts: new Date().toISOString(), coin, side, amount: amountKRW, sellMode: sellMode || null, balance: bal, armed };

    // safety#1: amount-cap
    if (amountKRW > MAX_PER_CLICK) {
      logExec({ ...base, result: "blocked-amount-cap", cap: MAX_PER_CLICK });
      alert(`[안전차단] 1회 금액 ${amountKRW.toLocaleString()}원 > 상한 ${MAX_PER_CLICK.toLocaleString()}원. 실행 안 함.`);
      return { ok: false, reason: "amount-cap" };
    }
    // 잔액 검증(매수만; 매도는 수량기반이라 별도).
    if (side === "buy" && bal != null && amountKRW > bal) {
      logExec({ ...base, result: "blocked-insufficient-balance" });
      alert(`[잔액부족] 주문가능 ${bal.toLocaleString()}원 < 주문 ${amountKRW.toLocaleString()}원.`);
      return { ok: false, reason: "insufficient" };
    }
    // 주문유형 = 시장가. ★click 시 폼이 re-render 되므로 총액 입력은 다음 tick 에 재조회 후(a_3655 fix:
    //   구버전은 click 직후 동기 fill → 재렌더 전 stale field 라 5100 미반영, 총액=0 사고).
    const typeTab = orderTypeTab("시장가");
    if (typeTab) typeTab.click();

    // 금액/가격 세팅(매수=총액). re-render 대기 후 재조회 + 검증-재시도.
    if (side === "buy") {
      let attempts = 0;
      const fill = () => {
        attempts++;
        const tot = totalInput();
        if (tot) {
          setInputValue(tot, amountKRW);
          // 반영 확인(React 컨트롤드 — 값이 안 붙으면 재시도). 반영완료 후에만(armed) submit.
          setTimeout(() => {
            const cur = num(tot.value);
            if (cur !== amountKRW && attempts < 5) { fill(); return; }
            logExec({ ...base, result: armed ? "SUBMITTED" : "ready-not-submitted(human-first-test)", filled: cur });
            if (armed) { const b = submitButton("buy"); if (b) b.click(); } // ★fill 반영 후에만 submit
          }, 120);
        } else if (attempts < 5) {
          setTimeout(fill, 150);
        }
      };
      setTimeout(fill, 150); // 시장가 전환 re-render 후.
      // buy 는 fill 콜백에서 (armed 시) submit 하므로 아래 동기 submit 경로는 buy 건너뜀.
      if (!armed) logExec({ ...base, result: "ready-not-submitted(human-first-test)" });
      return { ok: true, reason: armed ? "submitting-async" : "ready-human-submit", balance: bal };
    }

    if (!armed) {
      logExec({ ...base, result: "ready-not-submitted(human-first-test)" });
      return { ok: true, reason: "ready-human-submit", balance: bal };
    }
    // armed=true → 실제 submit 클릭.
    const btn = submitButton(side);
    if (!btn) { logExec({ ...base, result: "no-submit-button" }); return { ok: false, reason: "no-submit-btn" }; }
    btn.click();
    logExec({ ...base, result: "SUBMITTED" });
    return { ok: true, reason: "submitted" };
  }

  // ---- UI: 즉시매수/매도 버튼 + 금액입력 (signal 배지 근처에 부착) ----
  function buildExecUI(side) {
    const wrap = document.createElement("div");
    wrap.className = "kuh-exec";
    wrap.dataset.kuhExec = side;
    const amt = document.createElement("input");
    amt.type = "text"; amt.inputMode = "numeric"; amt.className = "kuh-exec-amt";
    amt.value = String(DEFAULT_AMOUNT); amt.title = "주문금액(KRW)";
    const btn = document.createElement("button");
    btn.className = "kuh-exec-btn " + (side === "buy" ? "kuh-exec-buy" : "kuh-exec-sell");
    btn.textContent = side === "buy" ? "즉시매수" : "즉시매도";
    // 잔액 검증 → 부족시 disable.
    function refresh() {
      const a = num(amt.value); const bal = availableBalance();
      const bad = a <= 0 || a > MAX_PER_CLICK || (side === "buy" && bal != null && a > bal);
      btn.disabled = bad;
      btn.title = a > MAX_PER_CLICK ? `상한 ${MAX_PER_CLICK}원 초과` : (side === "buy" && bal != null && a > bal) ? `잔액부족(가능 ${bal})` : "";
    }
    amt.addEventListener("input", refresh);
    setInterval(refresh, 2000); refresh();
    btn.addEventListener("click", (e) => {
      e.preventDefault(); e.stopPropagation();
      execute(side, num(amt.value));
    });
    wrap.appendChild(amt); wrap.appendChild(btn);

    // a_3677: SELL 측 = 진폭기반 추천매도가 섹션(계산 breakdown 투명공개 + 실행버튼).
    if (side === "sell") wrap.appendChild(buildRecoSell());
    return wrap;
  }

  // 매도 탭 활성화(non-destructive UI nav). 이미 활성이면 no-op. 원래 탭 복원은 하지 않음(읽기 목적상
  //   매도탭 유지가 자연스러움 — reco-sell 은 매도 컨텍스트). a_3681.
  function ensureSellTab() {
    // 매도가격 라벨이 보이면 이미 매도탭.
    const onSell = [...document.querySelectorAll("*")].some((e) => e.children.length === 0 && (e.textContent || "").trim() === "매도가격");
    if (onSell) return;
    // 주문폼의 매도 탭(링크/버튼 text=매도, 상단탭). 사이드바 아닌 order-form 쪽(x<1050).
    const tab = [...document.querySelectorAll("a,button,span,li")].find((e) => {
      if ((e.textContent || "").trim() !== "매도") return false;
      const r = e.getBoundingClientRect();
      return r.width > 0 && r.left < 1050 && r.top < 1000; // order-form 상단 탭 영역
    });
    if (tab) tab.click();
  }

  // ★a_3681: avg-buy(매수평균가)는 매도탭 활성 후 SELL-FORM 하단에 나타남(user clue u_3680) —
  //   보유 사이드바(ar_3636)가 아니라. 매도탭 보장 → sell-form 하단 라벨-앵커로 읽는다.
  function readAvgBuy() {
    ensureSellTab(); // 읽기 전 매도탭 활성(non-destructive)
    // (1) SELL-FORM 하단: '매수평균가'/'평균매수가' 라벨(order-form 열, x<1100) → 근처(같은행/다음형제) 숫자.
    const labels = [...document.querySelectorAll("*")].filter((e) => {
      const t = (e.textContent || "").trim();
      if (!(t === "매수평균가" || t === "평균매수가" || t === "매수평균")) return false;
      const r = e.getBoundingClientRect();
      return r.width > 0 && r.left < 1100 && !/노출|기준선|설정/.test(t); // order-form 영역, 설정문구 제외
    });
    for (const lab of labels) {
      const lr = lab.getBoundingClientRect();
      const rowY = lr.top + lr.height / 2;
      // 같은 행(Y근접)에서 라벨 오른쪽의 숫자.
      const leaves = [...document.querySelectorAll("*")].filter((e) => e.children.length === 0);
      let best = null, bx = Infinity;
      for (const e of leaves) {
        const v = num(e.textContent); if (!(v > 0)) continue;
        const r = e.getBoundingClientRect();
        if (Math.abs((r.top + r.height / 2) - rowY) > 16) continue; // 같은 행
        if (r.left <= lr.right) continue;                            // 라벨 오른쪽만
        if (r.left - lr.right < bx) { bx = r.left - lr.right; best = v; }
      }
      if (best != null) return best;
    }
    // (2) 폴백: 보유 사이드바 컬럼-geometry(ar_3636, 매도탭 무관 항상 시도).
    const coin = currentCoin(); if (!coin) return null;
    const heads = [...document.querySelectorAll("*")].filter((e) => e.children.length === 0 && (e.textContent || "").trim() === "매수평균가");
    const leaves = [...document.querySelectorAll("*")].filter((e) => e.children.length === 0);
    const nums = leaves.map((e) => ({ v: num(e.textContent), r: e.getBoundingClientRect() })).filter((o) => o.v > 0 && o.r.width > 0);
    for (const hd of heads) {
      const hr = hd.getBoundingClientRect(); if (!hr.width) continue;
      const colX = hr.left + hr.width / 2;
      const coinEls = leaves.filter((e) => (e.textContent || "").trim() === coin && e.getBoundingClientRect().top > hr.top - 5);
      for (const ce of coinEls) {
        const y = ce.getBoundingClientRect(); const rowY = y.top + y.height / 2;
        let best = null, bd = Infinity;
        for (const o of nums) { if (Math.abs((o.r.top + o.r.height / 2) - rowY) > 26) continue; const dx = Math.abs((o.r.left + o.r.width / 2) - colX); if (dx < bd) { bd = dx; best = o; } }
        if (best && bd < 90) return best.v;
      }
    }
    return null;
  }

  // 첫 사용 human-first: 이 새 execute-path 는 최초 1회는 클릭만·submit 안 함(a_3671 패턴). 승인후 auto.
  let recoArmed = false; // window.KUH_ARM_RECO_SELL===true 또는 유저 승인 후 true.

  function buildRecoSell() {
    const box = document.createElement("div");
    box.className = "kuh-reco";
    function render() {
      const amp = window.__kuh_amp;               // {avg,q1,q3,n,midN} from signal.js
      const avg = readAvgBuy();                     // 매수평균가(보유)
      if (!amp || avg == null) {
        box.innerHTML = `<div class="kuh-reco-head">추천 매도가(진폭기반)</div><div class="kuh-reco-na">${!amp ? "진폭 계산중…" : "매수평균가 필요(보유 탭 열기)"}</div>`;
        return;
      }
      const pct = amp.avg;                          // 목표% = IQR 중간범위 진폭
      const target = avg * (1 + pct / 100);         // 추천매도가 = 매수평균가 × (1+진폭%) (익절 목표, 원가 위)
      box.innerHTML =
        `<div class="kuh-reco-head">추천 매도가(진폭기반)</div>
         <div class="kuh-reco-calc">
           IQR 중간50%(${amp.midN}/${amp.n}캔들) Q1=${amp.q1.toFixed(1)}% Q3=${amp.q3.toFixed(1)}%<br>
           목표진폭 = ${pct.toFixed(2)}%<br>
           매수평균가 ${avg.toLocaleString()} × (1+${pct.toFixed(2)}%)</div>
         <div class="kuh-reco-target">→ ${target.toLocaleString(undefined,{maximumFractionDigits:8})} KRW</div>`;
      const rbtn = document.createElement("button");
      rbtn.className = "kuh-exec-btn kuh-exec-sell";
      rbtn.textContent = "이 가격에 매도";
      rbtn.addEventListener("click", (e) => {
        e.preventDefault(); e.stopPropagation();
        executeRecoSell(target, avg, pct, amp);
      });
      box.appendChild(rbtn);
    }
    render();
    setInterval(render, 2500);
    return box;
  }

  // 추천매도가로 지정가 매도 세팅 + (armed 시)제출. 첫 사용=ready만(human-first, a_3671 패턴).
  function executeRecoSell(target, avg, pct, amp) {
    dismissDelistingWarning();
    const armed = recoArmed || window.KUH_ARM_RECO_SELL === true;
    const base = { ts: new Date().toISOString(), coin: currentCoin(), side: "sell", type: "reco-amplitude", target, avgBuy: avg, ampPct: pct, armed };
    // 지정가 매도 선택 + 매도가격 = target.
    const t = orderTypeTab("지정가"); if (t) t.click();
    setTimeout(() => {
      const pin = priceInput("sell");
      if (pin) setInputValue(pin, Math.round(target * 1e8) / 1e8);
      if (!armed) {
        logExec({ ...base, result: "reco-ready-not-submitted(human-first)" });
        alert(`추천매도가 ${target.toLocaleString(undefined,{maximumFractionDigits:8})} 세팅됨. 첫 사용은 직접 [매도] 버튼을 눌러 확인해 주세요(이 버튼 최초1회 human-first).`);
        return;
      }
      const b = submitButton("sell"); if (b) b.click();
      logExec({ ...base, result: "reco-SUBMITTED" });
    }, 180);
  }

  // signal 배지에 exec-UI 를 signal 방향에 맞춰 부착(BUY→즉시매수, SELL→즉시매도).
  function attachToBadge() {
    const badge = document.getElementById("kuh-signal");
    if (!badge) return;
    // signal 텍스트에서 방향 읽기.
    const main = badge.querySelector(".kuh-sig-main");
    const txt = (main && main.textContent) || "";
    let side = null;
    if (/매수/.test(txt)) side = "buy"; else if (/매도/.test(txt)) side = "sell";
    let ex = badge.querySelector(".kuh-exec");
    if (!side) { if (ex) ex.remove(); return; } // 관망 → exec-UI 없음
    if (ex && ex.dataset.kuhExec === side) return; // 이미 맞는 것 있음
    if (ex) ex.remove();
    badge.appendChild(buildExecUI(side));
  }

  // 배지 갱신 주기에 맞춰 exec-UI 동기화.
  setInterval(attachToBadge, 2000);
  console.log("[kong-upbit-helper] execute module loaded (armed=" + (window.KUH_ARM_SUBMIT === true) + ")");
})();
