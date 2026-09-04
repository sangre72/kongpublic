/* kong-ali-helper v0.1 (STEP1) — AliExpress 가격안전 신호등 배지 + 쿠폰 자동적용.
 *
 * kong-upbit-helper 패턴 재사용: label-anchor(¬css-hash), native-setter+events(React/Vue controlled input),
 *   MutationObserver(SPA 재렌더), floating 배지.
 *
 * 실측(a_3706 CDP 조사): AliExpress 는 price-history(90일/최저가) DOM 미노출 → 실이력 불가 →
 *   discount-inflation 휴리스틱 사용(초고할인%=조작의심). rating·seller-rating 은 DOM 존재.
 *   photo-review 비율은 리뷰영역 lazy-load → review-count+rating 을 authenticity proxy 로.
 */
(() => {
  "use strict";

  // ★a_3741 fix: coupon-center(ko.)↔checkout(www.) subdomain 격리 → chrome.storage.local(subdomain-무관,
  //   확장 전역 저장소)로 코드캐시 공유. 비동기라 로드시 1회 읽어 _cacheMem 에 보관(동기접근용).
  let _cacheMem = [];
  function kahSetCache(obj) {
    _cacheMem = obj;
    try { chrome.storage?.local.set({ kah_codes: obj }); } catch (e) {}
  }
  function kahGetCache() { return _cacheMem; }
  // 시작 시 storage 에서 로드(비동기) → _cacheMem 채움.
  try { chrome.storage?.local.get("kah_codes", (r) => { if (r && Array.isArray(r.kah_codes)) _cacheMem = r.kah_codes; }); } catch (e) {}
  // ★a_3741 cleanup: a_3740 이 심은 과대 kah_codes 쿠키가 "400 Request Header Too Large" 유발 → 삭제.
  try {
    ["/", "/p/", "/ssr/"].forEach((pth) => {
      document.cookie = "kah_codes=;domain=.aliexpress.com;path=" + pth + ";expires=Thu, 01 Jan 1970 00:00:00 GMT";
      document.cookie = "kah_codes=;path=" + pth + ";expires=Thu, 01 Jan 1970 00:00:00 GMT";
    });
  } catch (e) {}

  const parseNum = (s) => Number(String(s || "").replace(/[^0-9.]/g, "")) || 0;

  const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
  function setInputValue(input, value) {
    nativeSetter.call(input, String(value));
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
  }

  const isCartPage = () => /cart|order|checkout/i.test(location.href);
  // ★product page = /item/ 만(‑ /p/shoppingcart 등 cart 는 제외). cart 면 product 아님.
  const isProductPage = () => !isCartPage() && /\/item\/\d+/.test(location.href);

  // ---------- 가격안전 신호등 (product page) ----------
  // 신호 3종 → 단일 색: 초록(안전)/노랑(주의)/빨강(위험).
  function collectSignals() {
    const bodyText = document.body.innerText || "";
    const sig = { discountPct: null, rating: null, reviewCount: null };

    // (a) discount% — 페이지에 표시된 할인율(최댓값 채택, 초고할인=inflation 의심).
    const discs = (bodyText.match(/-?\s?(\d{1,2})\s?%/g) || [])
      .map((s) => parseNum(s)).filter((v) => v > 0 && v <= 99);
    if (discs.length) sig.discountPct = Math.max(...discs);

    // (b) rating — 별점(0~5). '4.7' 형태 leaf 중 rating 문맥.
    const rEl = [...document.querySelectorAll("*")].find((e) => {
      if (e.children.length) return false;
      const t = (e.textContent || "").trim();
      if (!/^[0-5]\.[0-9]$/.test(t)) return false;
      const ctx = (e.parentElement?.textContent || "") + (e.getAttribute?.("aria-label") || "");
      return /점|star|rating|평|리뷰|review/i.test(ctx) || !!e.closest('[class*="rating" i],[class*="star" i],[class*="review" i]');
    });
    if (rEl) sig.rating = parseNum(rEl.textContent);
    else {
      const anyR = (bodyText.match(/\b[0-5]\.[0-9]\b/g) || []).map(parseNum).filter((v) => v >= 3 && v <= 5);
      if (anyR.length) sig.rating = anyR.sort((a, b) => a - b)[Math.floor(anyR.length / 2)]; // median
    }

    // (c) review-count — 'N개 리뷰'/'N Reviews'/'(N)'.
    const rc = bodyText.match(/([\d,]+)\s*(개?\s*리뷰|reviews?|평가|후기)/i);
    if (rc) sig.reviewCount = parseNum(rc[1]);

    return sig;
  }

  // 종합 스코어 → 색. 각 신호 감점/가점.
  function verdict(sig) {
    let score = 100; const reasons = [];
    // 할인 조작 휴리스틱: 초고할인은 원가 부풀리기 의심.
    if (sig.discountPct != null) {
      if (sig.discountPct >= 80) { score -= 35; reasons.push(`초고할인 ${sig.discountPct}%(원가 부풀림 의심)`); }
      else if (sig.discountPct >= 60) { score -= 15; reasons.push(`고할인 ${sig.discountPct}%(주의)`); }
      else reasons.push(`할인 ${sig.discountPct}%(정상범위)`);
    }
    // 평점.
    if (sig.rating != null) {
      if (sig.rating >= 4.5) { reasons.push(`평점 ${sig.rating}(우수)`); }
      else if (sig.rating >= 4.0) { score -= 10; reasons.push(`평점 ${sig.rating}(보통)`); }
      else { score -= 30; reasons.push(`평점 ${sig.rating}(낮음)`); }
    } else reasons.push("평점 정보 없음");
    // 리뷰 수(신뢰 표본).
    if (sig.reviewCount != null) {
      if (sig.reviewCount >= 100) { reasons.push(`리뷰 ${sig.reviewCount.toLocaleString()}개(표본충분)`); }
      else if (sig.reviewCount >= 10) { score -= 10; reasons.push(`리뷰 ${sig.reviewCount}개(표본적음)`); }
      else { score -= 20; reasons.push(`리뷰 ${sig.reviewCount}개(표본희박·주의)`); }
    } else reasons.push("리뷰 수 미확인");

    const color = score >= 75 ? "green" : score >= 50 ? "yellow" : "red";
    const label = color === "green" ? "안전" : color === "yellow" ? "주의" : "위험";
    return { color, label, score, reasons };
  }

  function renderBadge() {
    let el = document.getElementById("kah-badge");
    if (!el) {
      el = document.createElement("div");
      el.id = "kah-badge";
      el.className = "kah-badge";
      document.body.appendChild(el);
    }
    const sig = collectSignals();
    const v = verdict(sig);
    el.className = "kah-badge kah-" + v.color;
    el.innerHTML =
      `<div class="kah-head">가격안전 신호등</div>
       <div class="kah-main"><span class="kah-dot"></span>${v.label} <span class="kah-score">(${v.score})</span></div>
       <div class="kah-detail">${v.reasons.map((r) => "· " + r).join("<br>")}</div>
       <div class="kah-foot">가격이력 미제공→할인율 휴리스틱 · 참고용, 최종판단은 본인</div>`;
  }
  // (a_3716: STEP2 가격비교(Coupang/Naver) 기능 전체 제거 — 유료백엔드 필요·실시간 불가로 유저가 드롭.
  //  comparePriceSection/wireCompare/productTitle/aliPrice/searchKeywords 및 관련 CSS 모두 삭제. dead-code 없음.)

  // ---------- 쿠폰 자동적용 (cart/checkout) ----------
  // ★a_3719 fix: 구버전은 "쿠폰 적용 가능" 라벨만 반복표시(어떤 쿠폰인지 구분 안 됨). →
  //   각 쿠폰마커별로 CONTEXT(스토어명 + 근처 할인금액 '등록 후 ₩N 할인'/'₩N'/'N%')를 읽어
  //   구분되는 실목록으로 렌더. 클릭=해당 마커의 clickable 조상 위임(쿠폰선택 UI 열림).
  // ★a_3721: 해당 쿠폰의 '자기 값'만 정확히(오귀속 방지). 가격인하(price-drop)·상품가격은 배제.
  //   반환 {text, type:'amount'|'percent'|null}. 값이 모달에만 있으면 null(honest).
  function nearbyDiscount(el) {
    // 좁게(3단계) 스코프 — 같은 쿠폰항목 블록만. 넓히면 옆 아이템 숫자 오귀속.
    let scope = el;
    for (let k = 0; k < 3 && scope.parentElement; k++) scope = scope.parentElement;
    const txt = (scope.textContent || "");
    // %할인 우선.
    const pm = txt.match(/([\d.]+)\s?%\s*(추가)?할인/);
    if (pm) return { text: pm[1] + "% 할인", type: "percent" };
    // 금액할인: '등록 후 ₩N 할인' 또는 '₩N 할인쿠폰'(가격인하 제외).
    const am = txt.match(/등록\s*후\s*(₩[\d,]+)\s*할인|(₩[\d,]+)\s*할인\s*쿠폰/);
    if (am) return { text: (am[1] || am[2]) + " 할인", type: "amount" };
    // '이상 구매 시 ₩N' 조건형.
    const cm = txt.match(/(₩[\d,]+)\s*이상[^₩]*?(₩[\d,]+)\s*할인/);
    if (cm) return { text: cm[2] + " 할인(조건)", type: "amount" };
    return null; // 값이 select-modal 에만 → honest null
  }
  function nearbyStore(el) {
    // 같은 블록 내 스토어링크(…Store/스토어) 텍스트.
    let scope = el;
    for (let k = 0; k < 6 && scope.parentElement; k++) scope = scope.parentElement;
    const s = [...scope.querySelectorAll("a, span")].find((a) => /Store|스토어|Shop/i.test(a.textContent || "") && (a.textContent || "").length < 50);
    return s ? (s.textContent || "").trim().slice(0, 24) : null;
  }
  // ★a_3723: 이 쿠폰이 적용되는 상품(이름+썸네일). 같은 블록 내 상품링크(/item/)+상품이미지.
  function nearbyProducts(el) {
    let scope = el;
    for (let k = 0; k < 6 && scope.parentElement; k++) scope = scope.parentElement;
    // 상품명: /item/ 링크 텍스트(스토어링크 제외, 긴 상품명).
    const names = [...scope.querySelectorAll('a[href*="/item/"]')]
      .map((a) => (a.textContent || "").trim()).filter((t) => t.length > 8 && !/Store|스토어/i.test(t));
    // 썸네일: 상품 이미지(aliexpress-media/알리 CDN).
    const imgs = [...scope.querySelectorAll("img")]
      .map((i) => i.src).filter((s) => /ae0[0-9]|alicdn|aliexpress-media/i.test(s));
    const uniq = [...new Set(names)];
    return { names: uniq.slice(0, 3), thumb: imgs[0] || null, multi: uniq.length > 1 };
  }
  // a_3726: 계정쿠폰(my-coupons) same-origin fetch + parse. 같은 aliexpress.com → CORS 없음.
  let _acctCoupons = [];
  let _acctCouponsLoaded = false;
  // ★a_3737 ground-truth fix: /p/my-coupons = 스토어쿠폰 뷰(claimed 계정쿠폰 없음). 실제 claimed 쿠폰은
  //   coupon-center(/ssr/*/glo-coupon-center*)에 있고 JS-rendered → 단순 fetch 로 DOM 안 옴.
  //   → coupon-center 페이지 방문시 그 페이지서 스크랩→localStorage 캐시. cart 는 캐시 읽음.
  const isCouponCenter = () => /glo-coupon-center|coupon-center|calp/i.test(location.href);
  // ★a_3739: lazy-load 대응 — coupon-center 는 스크롤해야 카드가 렌더됨. 1회 자동 하단스크롤로 로드유도.
  let _ccScrolled = false;
  function primeCouponCenter() {
    if (_ccScrolled) return;
    _ccScrolled = true;
    // 점진 스크롤(가상리스트/lazy img 로드 유도) 후 top 복귀.
    let y = 0; const step = () => { y += 800; window.scrollTo(0, y); if (y < document.body.scrollHeight && y < 8000) setTimeout(step, 250); else setTimeout(() => window.scrollTo(0, 0), 300); };
    step();
  }
  function scrapeCouponCenter() {
    const found = [];
    // 쿠폰카드: ₩할인 or %할인 leaf + 근처 조건/코드. 카드컨테이너(작은 블록) 단위.
    [...document.querySelectorAll("*")].forEach((e) => {
      if (e.children.length !== 0) return;
      const t = (e.textContent || "").trim();
      const dm = t.match(/^(₩\s?[\d,]+)\s*할인$/) || t.match(/^([\d.]+)%\s*할인$/);
      if (!dm) return;
      let scope = e; for (let k = 0; k < 5 && scope.parentElement; k++) scope = scope.parentElement;
      const bt = (scope.textContent || "").replace(/\s+/g, " ");
      const cond = bt.match(/₩\s?[\d,]+\s*이상[^₩]*?주문/);
      // 코드: 대문자+숫자 혼합 5~14자(예 WKBQF6IS2GI9, RJT2SC, M69T5CNQ9P0O). 순수단어 제외(숫자 포함 필수).
      const codes = (bt.match(/\b(?=[A-Z0-9]*[0-9])[A-Z0-9]{5,14}\b/g) || []).filter((c) => !/^\d+$/.test(c) && !/^[A-Z]+$/.test(c));
      const code = codes[0] || null;
      const pct = /%/.test(t);
      found.push({ source: "acct",
        disc: { text: t, type: pct ? "percent" : "amount" },
        store: null, prod: { names: [], thumb: null, multi: false },
        title: t + (code ? " · 코드 " + code : ""),
        cond: cond ? cond[0] : null, exp: null, code: code });
    });
    const seen = new Set();
    const uniq = found.filter((c) => { const k = c.disc.text + (c.code || ""); if (seen.has(k)) return false; seen.add(k); return true; }).slice(0, 12);
    kahSetCache(uniq); try { localStorage.setItem("kah_acct_coupons", JSON.stringify(uniq)); } catch (e) {}
    return uniq;
  }
  function fetchAcctCoupons() {
    _acctCouponsLoaded = true;
    // 캐시(coupon-center 방문시 저장됨) 읽기.
    _acctCoupons = kahGetCache(); if (!_acctCoupons.length) { try { _acctCoupons = JSON.parse(localStorage.getItem("kah_acct_coupons") || "[]"); } catch (e) { _acctCoupons = []; } }
  }

  function renderCouponHelper() {
    const input = [...document.querySelectorAll('input[type="text"], input:not([type])')].find((i) => {
      const ctx = (i.placeholder || "") + (i.getAttribute("aria-label") || "") + (i.name || "");
      return /쿠폰|coupon|프로모|promo|code|코드/i.test(ctx);
    });
    // 쿠폰 마커(말단 라벨). 각각을 CONTEXT 로 구분.
    const markers = [...document.querySelectorAll("button, a, div[role='button'], span, div")].filter((b) => {
      const t = (b.textContent || "").trim();
      if (b.closest("#kah-coupon, #kah-badge")) return false;
      if (!(/쿠폰|coupon/i.test(t) && /적용|사용|apply|받기|get|가능/i.test(t))) return false;
      if (t.length > 24) return false;
      if (b.querySelector("*")) return false;
      return true;
    });
    // 각 마커 → 리치 엔트리(store · discount(type) · product name/thumb · store-wide여부).
    const esc = (s) => String(s || "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
    const coupons = markers.map((el) => ({
      source: "cart", el, disc: nearbyDiscount(el), store: nearbyStore(el), prod: nearbyProducts(el),
    }));
    // a_3726: 계정쿠폰(my-coupons) 병합(비동기, 캐시). 카트에 없는 미사용 계정쿠폰만.
    coupons.push(..._acctCoupons);
    if (!input && !coupons.length && !_acctCouponsLoaded) { fetchAcctCoupons(); return; }
    if (!input && !coupons.length) return;

    let panel = document.getElementById("kah-coupon");
    if (!panel) {
      panel = document.createElement("div");
      panel.id = "kah-coupon"; panel.className = "kah-badge kah-coupon";
      document.body.appendChild(panel);
    }
    // a_3721 polish + a_3723 product + a_3726 descriptive/account: 카드형(썸네일·상품·설명·할인·출처).
    const rows = coupons.slice(0, 14).map((c, i) => {
      const dcls = c.disc?.type === "percent" ? "kah-dc-pct" : c.disc?.type === "amount" ? "kah-dc-amt" : "kah-dc-na";
      const dtxt = c.disc ? c.disc.text : (c.source === "acct" ? "쿠폰" : "선택창서 확인");
      const acct = c.source === "acct";
      // 제목(무엇인가): 상품명 or 계정쿠폰제목 or 스토어.
      const title = acct ? (c.title || "계정 쿠폰") : (c.prod.multi ? "스토어 전체 쿠폰" : (c.prod.names[0] || c.store || "쿠폰"));
      // 설명줄(a_3726: 너무 terse → 조건/기한/출처 명시).
      const bits = [];
      if (c.store) bits.push(c.store);
      if (c.cond) bits.push("조건 " + c.cond);
      if (c.exp) bits.push("기한 " + c.exp);
      const meta = bits.join(" · ") || (acct ? "내 계정 보유 쿠폰" : "장바구니 상품 쿠폰");
      const srcBadge = acct ? `<span class="kah-src kah-src-acct">계정쿠폰</span>` : `<span class="kah-src kah-src-cart">장바구니</span>`;
      const thumb = c.prod.thumb ? `<img class="kah-cthumb" src="${esc(c.prod.thumb)}" alt="">` : `<div class="kah-cthumb kah-cthumb-x">🎟</div>`;
      return `<button class="kah-ccard" data-i="${i}">
        ${thumb}
        <div class="kah-cinfo">
          <div class="kah-cprod">${srcBadge}${esc(title)}</div>
          <div class="kah-cmeta">${esc(meta)}</div>
          <div class="kah-cact">${acct ? "클릭 → 내 쿠폰 페이지 열기" : "클릭 → 이 상품으로 이동(적용은 결제화면서)"}</div>
        </div>
        <div class="kah-cdisc ${dcls}">${esc(dtxt)}</div>
      </button>`;
    }).join("");
    const nAcct = coupons.filter((c) => c.source === "acct").length;
    // ★a_3731 정직 re-scope: 카트에는 실제 apply-target 없음(ar_3730 실증). = 안내(informational)만.
    //   실적용은 결제(checkout)페이지 프로모션코드 or 스토어 쿠폰받기. 카드=해당 위치로 안내/이동.
    panel.innerHTML =
      `<div class="kah-head">🎟 쿠폰 안내 <span class="kah-cnt">${coupons.length}</span></div>
       <div class="kah-detail">이 상품들에 쓸 수 있는 쿠폰 목록입니다. 실제 적용은 결제화면 '프로모션 코드'/스토어에서 됩니다(카트선 자동적용 아님).</div>
       <div class="kah-clist">${rows || '<div class="kah-cmp-na">표시할 쿠폰 없음</div>'}</div>`;
    panel.querySelectorAll(".kah-ccard").forEach((cb) => {
      cb.addEventListener("click", (e) => {
        e.preventDefault(); e.stopPropagation();
        const c = coupons[+cb.dataset.i];
        if (!c) return;
        if (c.source === "acct") { window.open("https://ko.aliexpress.com/p/my-coupons/index.html", "_blank", "noopener"); return; }
        if (c.el) {
          const clickable = c.el.closest('button, a, [role="button"], [onclick]') || c.el;
          clickable.scrollIntoView({ block: "center" });
          clickable.click();
        }
      });
    });
  }

  // ---------- 결제(checkout)페이지 프로모션코드 적용 도우미 (a_3731) ----------
  // ★ar_3730/3731: 카트엔 apply-target 없음. 실제 apply = /trade/confirm(결제)페이지 '프로모션 코드'
  //   입력+적용 → 총합계 변동(ground-truth). 이건 automatable → 코드 넣고 적용 클릭. 실가격 바뀜.
  const isCheckoutPage = () => /\/trade\/(confirm|order)|placeOrder|order[_-]?confirm/i.test(location.href);
  function findPromoInput() {
    // '프로모션 코드' 라벨 근처 입력창 or placeholder '여기에 코드'.
    const byPh = [...document.querySelectorAll("input")].find((i) => /코드를 입력|promo|coupon code/i.test((i.placeholder || "")));
    if (byPh) return byPh;
    const lab = [...document.querySelectorAll("*")].find((e) => e.children.length === 0 && /프로모션 코드/.test(e.textContent || ""));
    if (lab) { let p = lab; for (let k = 0; k < 5 && p; k++) { p = p.parentElement; const i = p?.querySelector("input"); if (i) return i; } }
    return null;
  }
  function renderCheckoutPromo() {
    const input = findPromoInput();
    if (!input) return;
    let panel = document.getElementById("kah-promo");
    if (!panel) {
      panel = document.createElement("div");
      panel.id = "kah-promo"; panel.className = "kah-badge kah-coupon";
      document.body.appendChild(panel);
    }
    // 총합계 읽기(적용 전후 비교=ground-truth).
    function readTotal() {
      const el = [...document.querySelectorAll("*")].find((e) => e.children.length === 0 && /총\s*합계/.test((e.parentElement?.textContent) || (e.previousElementSibling?.textContent) || ""));
      // 총합계 라벨 근처 ₩숫자.
      let scope = el; for (let k = 0; k < 4 && scope?.parentElement; k++) scope = scope.parentElement;
      const m = (scope?.textContent || document.body.textContent).match(/총\s*합계[^\d]*(₩\s?[\d,]+)/);
      return m ? parseNum(m[1]) : null;
    }
    // 캐시된 coupon-center 코드(a_3739 발견: 코드 실재, a_3741 chrome.storage 로 cross-subdomain 공유).
    let codes = [...new Set(kahGetCache().map((c) => c.code).filter(Boolean))].slice(0, 6);
    // storage 비동기 로드가 아직이면(0) 직접 재조회 후 코드 생기면 패널 재렌더.
    if (!codes.length) { try { chrome.storage?.local.get("kah_codes", (r) => { if (r && Array.isArray(r.kah_codes) && r.kah_codes.length) { _cacheMem = r.kah_codes; renderCheckoutPromo(); } }); } catch (e) {} }

    // ★a_3740 정직 apply: input+native [적용] 클릭. 성공판정 = 총합계 감소.
    function tryCode(code) {
      return new Promise((resolve) => {
        const before = readTotal();
        setInputValue(input, code);
        const apply = [...document.querySelectorAll("button, a, [role='button']")].find((b) => (b.textContent || "").trim() === "적용");
        if (apply) apply.click(); else input.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
        setTimeout(() => { const after = readTotal(); resolve({ code, before, after, ok: after != null && before != null && after < before }); }, 1600);
      });
    }

    panel.innerHTML =
      `<div class="kah-head">🎟 프로모션 코드 자동적용</div>
       <div class="kah-detail">쿠폰센터에서 수집한 코드 ${codes.length}개를 자동으로 하나씩 넣어보고 총합계가 줄면 채택. (수동 붙여넣기도 가능)</div>
       <button class="kah-exec-btn kah-promo-auto">수집 코드 자동 시도 (${codes.length})</button>
       <input class="kah-promo-in" type="text" placeholder="직접 코드 붙여넣기(선택)">
       <button class="kah-exec-btn kah-promo-go">이 코드 적용</button>
       <div class="kah-promo-msg"></div>`;
    const pin = panel.querySelector(".kah-promo-in");
    const msg = panel.querySelector(".kah-promo-msg");
    panel.querySelector(".kah-promo-go").addEventListener("click", async (e) => {
      e.preventDefault(); e.stopPropagation();
      const code = (pin.value || "").trim();
      if (!code) { msg.textContent = "코드를 입력하세요."; return; }
      msg.textContent = `'${code}' 적용 중…`;
      const r = await tryCode(code);
      msg.textContent = r.ok ? `✅ 적용됨! 총합계 ${r.before?.toLocaleString()}→${r.after?.toLocaleString()}` : `❌ '${code}' 적용 안 됨(무효/조건미달).`;
    });
    panel.querySelector(".kah-promo-auto").addEventListener("click", async (e) => {
      e.preventDefault(); e.stopPropagation();
      if (!codes.length) { msg.textContent = "수집된 코드 없음 — 쿠폰센터를 먼저 방문하세요."; return; }
      for (let i = 0; i < codes.length; i++) {
        msg.textContent = `자동 시도 ${i + 1}/${codes.length}: ${codes[i]} …`;
        const r = await tryCode(codes[i]);
        if (r.ok) { msg.textContent = `✅ ${codes[i]} 적용 성공! 총합계 ${r.before?.toLocaleString()}→${r.after?.toLocaleString()}`; return; }
      }
      msg.textContent = "시도한 코드 모두 적용 안 됨(조건미달/무효). 장바구니 상품·금액 확인.";
    });
  }

  // ---------- 랜딩 배송현황 카드 (a_3750) ----------
  // ★데이터 접근 approach(a_3750 step3 검증): 최신 AliExpress 주문목록은 JS-rendered(초기 HTML fetch 로 안 옴,
  //   coupon-center 와 동일 제약). same-origin 제약+read-only → coupon-center 와 동일 패턴 채택:
  //   유저가 My Orders 페이지(/p/order/*) 방문시 그 페이지서 in-transit 주문 스크랩→chrome.storage.local 캐시.
  //   랜딩(www root)은 캐시를 읽어 카드 렌더(cross-page 는 chrome.storage 로 subdomain/page 무관 공유, a_3741 검증됨).
  const isOrdersPage = () => /\/p\/order|order-list|orderlist|\/p\/mydo/i.test(location.href);
  const isLandingPage = () =>
    /^https:\/\/[^/]*aliexpress\.com\/(\?|$|gcp\/|home|index)/i.test(location.href) &&
    !/\/item\/|cart|order|trade|confirm|checkout|coupon|ssr|calp|my-/i.test(location.href);

  // in-transit 판정 키워드(한/영). '배송중/발송됨/이동중/In transit/Shipped/On the way' 등, '배송완료/Delivered' 제외.
  const IN_TRANSIT_RE = /배송\s*중|발송(됨|완료)|운송\s*중|이동\s*중|출고|in\s*transit|shipped|on\s*(its|the)\s*way|dispatched|out\s*for\s*delivery/i;
  const DELIVERED_RE = /배송\s*완료|수령\s*완료|delivered|완료됨|거래\s*완료/i;

  function scrapeOrders() {
    const orders = [];
    // 주문카드: /item/ 상품링크 + 이미지 + 상태텍스트가 같은 블록. 상태 leaf 를 앵커로 블록 스코프.
    [...document.querySelectorAll("*")].forEach((e) => {
      if (e.children.length !== 0) return;
      const t = (e.textContent || "").trim();
      if (!t || t.length > 40) return;
      if (!IN_TRANSIT_RE.test(t) || DELIVERED_RE.test(t)) return;
      // 상태 leaf 발견 → 주문블록 스코프(위로 6단계).
      let scope = e;
      for (let k = 0; k < 6 && scope.parentElement; k++) scope = scope.parentElement;
      if (DELIVERED_RE.test(scope.textContent || "")) return; // 블록 전체가 완료면 제외
      // 상품명(/item/ 링크, 긴 텍스트).
      const nameEl = [...scope.querySelectorAll('a[href*="/item/"], a[href*="/i/"]')]
        .map((a) => (a.textContent || "").trim()).find((s) => s.length > 8);
      // 썸네일(알리 CDN).
      const img = [...scope.querySelectorAll("img")].map((i) => i.src).find((s) => /ae0[0-9]|alicdn|aliexpress-media/i.test(s));
      // 예상배송/도착일(있으면).
      const em = (scope.textContent || "").match(/(예상\s*(도착|배송)[^\d]*([\d]{1,2}[\/월.\-][\d]{1,2}[일]?|[A-Z][a-z]{2}\s*\d{1,2}))|estimated\s*delivery[^\d]*([A-Za-z0-9 ,\/\-]{3,16})/i);
      orders.push({
        name: nameEl || "주문 상품",
        status: t,
        eta: em ? (em[0] || "").replace(/\s+/g, " ").slice(0, 40) : null,
        thumb: img || null,
      });
    });
    // 중복(상품명+상태) 제거.
    const seen = new Set();
    const uniq = orders.filter((o) => { const k = o.name + o.status; if (seen.has(k)) return false; seen.add(k); return true; }).slice(0, 8);
    try { chrome.storage?.local.set({ kah_orders: uniq, kah_orders_ts: Date.now() }); } catch (e) {}
    return uniq;
  }

  // 짧고 깨끗한 벨 차임(WebAudio, a_3750 amend + relax: synth 채택 — clean·무의존·무라이선스·무CSP문제).
  //   맑은 벨 = 각 음 sine(기음)+triangle 배음(약하게)로 배음 살짝, 부드러운 attack + 긴 자연감쇠(벨 여운).
  let _chimePlayed = false;
  function playChime() {
    if (_chimePlayed) return; _chimePlayed = true;
    try {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return;
      const ac = new Ctx();
      const master = ac.createGain(); master.gain.value = 0.9; master.connect(ac.destination);
      const now = ac.currentTime;
      // 2음 상행 아르페지오(맑고 밝은 벨): A5(880) → E6(1319). 살짝 겹치게(0.12s) → 여운 어울림.
      const note = (f, dt, peak, dur) => {
        // 기음(sine) + 옥타브 배음(triangle, 낮은 게인)로 벨 특유의 반짝임.
        [["sine", f, peak], ["triangle", f * 2, peak * 0.18]].forEach(([type, freq, pk]) => {
          const o = ac.createOscillator(), g = ac.createGain();
          o.type = type; o.frequency.value = freq;
          g.gain.setValueAtTime(0.0001, now + dt);
          g.gain.exponentialRampToValueAtTime(pk, now + dt + 0.015); // 부드러운 attack
          g.gain.exponentialRampToValueAtTime(0.0001, now + dt + dur); // 자연 감쇠(벨 여운)
          o.connect(g); g.connect(master);
          o.start(now + dt); o.stop(now + dt + dur + 0.05);
        });
      };
      note(880, 0, 0.16, 0.7);
      note(1318.5, 0.12, 0.15, 0.9);
      setTimeout(() => { try { ac.close(); } catch (e) {} }, 1600);
    } catch (e) { /* 자동재생 정책 등 실패 무시 */ }
  }

  // ★a_3751: dismiss-지속성 = 세션→달력일(once-per-calendar-day). 하루 첫 표시 후엔 닫든 안닫든
  //   같은 날엔 재표시·재차임 안 함(페이지 재방문·재로드해도). 다음 날엔 페이지 안 닫아도 다시 표시.
  //   저장 = chrome.storage.local key "kah_ship_lastshown"=오늘날짜(YYYY-MM-DD). X close = 현재 인스턴스
  //   즉시 제거(게이트와 독립 — 게이트는 재등장 타이밍, X는 현재표시 닫기. 렌더시 날짜 이미 기록됨).
  const todayStr = () => {
    const d = new Date();
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  };
  function renderShipmentCard() {
    const esc = (s) => String(s || "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
    chrome.storage?.local.get(["kah_orders", "kah_ship_lastshown"], (r) => {
      const orders = (r && Array.isArray(r.kah_orders)) ? r.kah_orders : [];
      if (!orders.length) { document.getElementById("kah-ship")?.remove(); return; } // in-transit 없음 → 아무것도 안 그림
      // once-per-day 게이트: 오늘 이미 표시했으면 skip(재렌더·재차임 안 함).
      if (r && r.kah_ship_lastshown === todayStr()) return;
      // 이미 이 로드에서 그려져 있으면(중복 tick) 재차임 방지 — 패널 존재시 skip.
      if (document.getElementById("kah-ship")) return;
      const panel = document.createElement("div");
      panel.id = "kah-ship"; panel.className = "kah-badge kah-ship";
      document.body.appendChild(panel);
      const rows = orders.map((o) => {
        const thumb = o.thumb ? `<img class="kah-cthumb" src="${esc(o.thumb)}" alt="">` : `<div class="kah-cthumb kah-cthumb-x">📦</div>`;
        return `<div class="kah-ccard">
          ${thumb}
          <div class="kah-cinfo">
            <div class="kah-cprod">${esc(o.name)}</div>
            <div class="kah-cmeta"><span class="kah-ship-st">${esc(o.status)}</span>${o.eta ? " · " + esc(o.eta) : ""}</div>
          </div>
        </div>`;
      }).join("");
      panel.innerHTML =
        `<button class="kah-ship-x" aria-label="닫기" title="닫기">✕</button>
         <div class="kah-head">📦 배송 중인 주문 <span class="kah-cnt">${orders.length}</span></div>
         <div class="kah-clist">${rows}</div>
         <div class="kah-foot">최근 '내 주문' 방문 시점 기준 · 실시간 아님
           <a class="kah-donate" href="https://buymeacoffee.com/panichill" target="_blank" rel="noopener noreferrer">☕ 후원</a>
         </div>`;
      panel.querySelector(".kah-ship-x").addEventListener("click", (e) => {
        e.preventDefault(); e.stopPropagation();
        panel.remove(); // 현재 인스턴스 즉시 닫기(오늘날짜는 이미 기록됨 → 오늘 재등장 안 함).
      });
      // 오늘 표시함 기록(닫든 안닫든 오늘은 재등장 안 함).
      try { chrome.storage?.local.set({ kah_ship_lastshown: todayStr() }); } catch (e) {}
      playChime(); // 카드 최초(하루 1회) 등장시 차임.
    });
  }

  // ---------- loop ----------
  function tick() {
    try {
      if (isProductPage()) renderBadge();
      else document.getElementById("kah-badge")?.remove();
      if (isCartPage()) renderCouponHelper();
      if (isCheckoutPage()) renderCheckoutPromo();
      else document.getElementById("kah-promo")?.remove();
      if (isCouponCenter()) { primeCouponCenter(); _acctCoupons = scrapeCouponCenter(); _acctCouponsLoaded = true; renderCouponHelper(); } // a_3737/3739: lazy-load 유도 후 scrape+cache + 여기서도 패널 렌더(직접검증)
      // a_3750: 주문페이지 방문시 in-transit 스크랩→캐시 / 랜딩에서 카드 렌더.
      if (isOrdersPage()) scrapeOrders();
      if (isLandingPage()) renderShipmentCard();
      else document.getElementById("kah-ship")?.remove();
    } catch (e) { /* noop */ }
  }

  tick();
  setInterval(tick, 3000); // SPA 재렌더·lazy-load 대응(주기 갱신)
  new MutationObserver(() => {
    if (isProductPage() && !document.getElementById("kah-badge")) tick();
  }).observe(document.body, { childList: true, subtree: true });

  console.log("[kong-ali-helper] v0.1 loaded");
})();
