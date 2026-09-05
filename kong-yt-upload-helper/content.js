/* kong-yt-upload-helper v0.1 — YouTube Studio 업로드 CSV 자동채움 (DOM 자동화, NO YouTube Data API).
 *
 * 설계원칙(★a_3749 postmortem 반영, RECIPE_scheduled_upload_VERIFIED.txt):
 *  - LABEL/TEXT 기반 DOM 조회 우선(aria-label·텍스트 매칭) — 좌표 하드코딩·재사용 금지(z-order/stale-coord 버그 회피).
 *  - React-controlled input = native-setter + input/change 이벤트(값 바인딩 반영).
 *  - MutationObserver + interval = SPA 재렌더·모달 등장 대응.
 *  - 파일선택 2경로(native picker click / 드롭존 drop-event) 모두 filename→CSV row 매칭으로 수렴.
 *  - ★안전: 최종 "예약/게시" 클릭은 자동 안 함(실제 업로드=비가역). 제목·재생목록·예약일까지 자동채움 후
 *    사용자가 검토→직접 예약버튼 누름. (자동채움=편의, 최종 발행=사람 확정.)
 */
(() => {
  "use strict";
  const LOG = (...a) => console.log("[kong-yt]", ...a);

  // ---------- CSV 세션 상태 ----------
  // rows: [{filename, title, playlist, scheduleDate}], done: Set(filename)
  let _rows = [];
  let _done = new Set();
  let _busy = false;

  function loadState() {
    try {
      chrome.storage?.local.get(["kyt_rows", "kyt_done"], (r) => {
        if (r && Array.isArray(r.kyt_rows)) _rows = r.kyt_rows;
        if (r && Array.isArray(r.kyt_done)) _done = new Set(r.kyt_done);
        LOG("loaded rows:", _rows.length, "done:", _done.size);
      });
    } catch (e) {}
  }
  function saveDone() {
    try { chrome.storage?.local.set({ kyt_done: [...done()] }); } catch (e) {}
  }
  function done() { return _done; }

  // storage 변경(popup에서 CSV 로드) 실시간 반영.
  try {
    chrome.storage?.onChanged.addListener((ch, area) => {
      if (area !== "local") return;
      if (ch.kyt_rows) _rows = Array.isArray(ch.kyt_rows.newValue) ? ch.kyt_rows.newValue : [];
      if (ch.kyt_done) _done = new Set(Array.isArray(ch.kyt_done.newValue) ? ch.kyt_done.newValue : []);
      if (ch.kyt_locale) _localeOverride = ch.kyt_locale.newValue || "auto"; // a_3762 수동 override 실시간반영
      // a_3787: CSV가 팝업에서 뒤늦게 로드된 경우(다이얼로그 이미 열림) — DOM 변경/interval 대기 없이 즉시 채움.
      //   renderBadge()는 배지만 그림 → 실제 채움은 tick()이 담당하므로 tick()을 직접 호출.
      if (ch.kyt_rows && _rows.length) {
        try { tick(); } catch (e) {}
      }
    });
  } catch (e) {}
  loadState();

  // ---------- 유틸: React-controlled input 값 설정 ----------
  const nativeInputSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value")?.set;
  const nativeTextareaSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value")?.set;
  function setNativeValue(el, value) {
    const proto = el instanceof HTMLTextAreaElement ? nativeTextareaSetter : nativeInputSetter;
    if (proto) proto.call(el, String(value)); else el.value = String(value);
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
  }

  // contenteditable(YT 제목/설명은 실제로 contenteditable div일 수 있음) 처리.
  // execCommand("insertText")를 우선 시도(실 브라우저 React-editable에 가장 자연스러움), 실패시
  // textContent 직접설정 + input 이벤트로 fallback(headless/execCommand 미지원 대응).
  function setEditableText(el, text) {
    el.focus();
    let ok = false;
    try {
      document.execCommand?.("selectAll", false, null);
      ok = document.execCommand?.("insertText", false, text);
    } catch (e) { ok = false; }
    if (!ok || (el.textContent || "").trim() !== text.trim()) {
      // fallback: 직접 세팅 + beforeinput/input 이벤트(React onInput 트리거).
      el.textContent = text;
      el.dispatchEvent(new InputEvent("input", { bubbles: true, data: text, inputType: "insertText" }));
    } else {
      el.dispatchEvent(new InputEvent("input", { bubbles: true, data: text, inputType: "insertText" }));
    }
  }

  // ---------- ★멀티로케일 라벨맵(a_3761 amend: distributable) ----------
  // YT Studio UI 언어별 필드/버튼 라벨. 새 로케일 추가 = 아래 객체에 한 블록만 추가하면 됨(구조 고정).
  //   각 값 = 정규식(부분매칭). ko/en 필수, ja/es 포함. 미지원 언어 = en fallback.
  const LOCALE_LABELS = {
    ko: {
      title: /제목/, playlistOpen: /재생목록 선택|재생목록에 추가/, done: /^완료$/,
      scheduleOpt: /^예약$/, dateField: /날짜/, next: /^다음$/,
      audienceNo: /아니요.*아동용이 아닙니다/, publishStep: /저장 또는 게시|공개 상태/,
    },
    en: {
      title: /title/i, playlistOpen: /select playlist|add to playlist/i, done: /^done$/i,
      scheduleOpt: /^schedule$/i, dateField: /date/i, next: /^next$/i,
      audienceNo: /no,?\s*it'?s not made for kids/i, publishStep: /save or publish|visibility/i,
    },
    ja: {
      title: /タイトル/, playlistOpen: /再生リストを選択|再生リストに追加/, done: /^完了$/,
      scheduleOpt: /^スケジュール設定$|^予約$/, dateField: /日付/, next: /^次へ$/,
      audienceNo: /いいえ.*子ども向けではありません/, publishStep: /保存または公開|公開設定/,
    },
    es: {
      title: /título/i, playlistOpen: /seleccionar lista|añadir a lista/i, done: /^listo$|^hecho$/i,
      scheduleOpt: /^programar$/i, dateField: /fecha/i, next: /^siguiente$/i,
      audienceNo: /no,?\s*no es contenido para ni.os/i, publishStep: /guardar o publicar|visibilidad/i,
    },
  };
  // 현재 YT Studio UI 언어 감지: <html lang> 우선, 없으면 본문 키워드 스니핑, 최종 en fallback.
  function detectLocale() {
    const htmlLang = (document.documentElement.getAttribute("lang") || "").slice(0, 2).toLowerCase();
    if (LOCALE_LABELS[htmlLang]) return htmlLang;
    const t = document.body.innerText || "";
    if (/제목|재생목록|공개 상태/.test(t)) return "ko";
    if (/タイトル|再生リスト|公開設定/.test(t)) return "ja";
    if (/título|lista de reproducción|visibilidad/i.test(t)) return "es";
    return "en";
  }
  let _locale = "en";
  let _localeOverride = "auto"; // a_3762: 사용자 수동선택(auto=자동감지). chrome.storage에서 로드/변경반영.
  const L = () => LOCALE_LABELS[_locale] || LOCALE_LABELS.en;
  // 저장된 수동 override 로드 + 실시간 변경반영.
  function loadLocaleOverride() {
    try { chrome.storage?.local.get(["kyt_locale"], (r) => { _localeOverride = (r && r.kyt_locale) || "auto"; }); } catch (e) {}
  }
  loadLocaleOverride();
  // resolveLocale: override가 명시언어면 그것, auto면 detectLocale().
  function resolveLocale() {
    return (_localeOverride && _localeOverride !== "auto" && LOCALE_LABELS[_localeOverride]) ? _localeOverride : detectLocale();
  }

  // ---------- LABEL/TEXT 기반 DOM 조회(★좌표금지) ----------
  // visible: 렌더된 요소만(숨김 제외). offsetParent는 position:fixed·일부 contenteditable서 null일 수
  //   있어(그래도 보임) 단독기준 금지 → clientRects 또는 offset 크기로 판정.
  const visible = (el) => {
    if (!el) return false;
    const st = el.ownerDocument?.defaultView?.getComputedStyle?.(el);
    if (st && (st.display === "none" || st.visibility === "hidden")) return false;
    return el.getClientRects().length > 0 || el.offsetWidth > 0 || el.offsetHeight > 0 || el.getAttribute("contenteditable") === "true";
  };
  function byLabelInput(re) {
    // aria-label / placeholder / 근처 라벨텍스트로 input·textarea·contenteditable 찾기.
    const cands = [...document.querySelectorAll('input, textarea, [contenteditable="true"], [role="textbox"]')];
    return cands.find((el) => {
      if (!visible(el)) return false;
      const s = (el.getAttribute("aria-label") || "") + " " + (el.getAttribute("placeholder") || "");
      return re.test(s);
    });
  }
  function byText(selector, re) {
    return [...document.querySelectorAll(selector)].find((el) => visible(el) && re.test((el.textContent || "").trim()));
  }
  function clickByText(selector, re) {
    const el = byText(selector, re);
    if (el) { const c = el.closest('button,[role="button"],ytcp-button,a') || el; c.click(); return true; }
    return false;
  }

  // ---------- 업로드 단계 감지(로케일맵 기반) ----------
  const stepTitleField = () => byLabelInput(L().title);
  const isDetailsStep = () => !!stepTitleField();
  const isPublishStep = () => L().publishStep.test(document.body.innerText) && L().scheduleOpt.test(document.body.innerText);

  // ---------- 파일명 → CSV row 매칭 ----------
  function rowForFilename(fname) {
    if (!fname) return null;
    const base = fname.replace(/\.[^.]+$/, "").toLowerCase();
    return _rows.find((r) => {
      const rb = String(r.filename || "").replace(/\.[^.]+$/, "").toLowerCase();
      return rb === base || rb === fname.toLowerCase() || base.includes(rb) || rb.includes(base);
    }) || null;
  }
  // 현재 업로드중 파일명 추출(details 화면에 '파일 이름: scene_NN.mp4' 노출).
  function currentUploadFilename() {
    const m = (document.body.innerText || "").match(/([A-Za-z0-9_\-]+\.mp4)/i);
    return m ? m[1] : null;
  }

  // ---------- 자동채움 스텝들 ----------
  function fillTitle(row) {
    const el = stepTitleField();
    if (!el || !row.title) return false;
    if ((el.textContent || el.value || "").trim() === row.title.trim()) return true; // 이미 됨
    if (el.isContentEditable) setEditableText(el, row.title);
    else setNativeValue(el, row.title);
    LOG("title set:", row.title);
    return true;
  }
  function selectPlaylist(row) {
    if (!row.playlist) return true;
    // 재생목록 드롭다운 버튼(로케일 라벨 매칭) 클릭 → 항목 체크 → 완료.
    const openBtn = byText('ytcp-text-dropdown-trigger, tp-yt-paper-button, button', L().playlistOpen);
    if (openBtn) (openBtn.closest('[role="button"],button,ytcp-text-dropdown-trigger') || openBtn).click();
    // 드롭다운 렌더 후 항목 체크(다음 tick에서 처리하도록 신호만).
    return true;
  }
  function checkPlaylistItem(row) {
    if (!row.playlist) return false;
    // 열린 드롭다운서 playlist 라벨 매칭 체크박스 클릭.
    const item = [...document.querySelectorAll('ytcp-checkbox-lit, ytcp-ve, li, div[role="option"], span')]
      .find((el) => visible(el) && (el.textContent || "").trim() === row.playlist.trim());
    if (item) {
      const cb = item.closest('[role="option"],li,ytcp-checkbox-lit') || item;
      cb.click();
      // 완료 버튼(로케일).
      setTimeout(() => clickByText('button, ytcp-button, tp-yt-paper-button', L().done), 300);
      LOG("playlist checked:", row.playlist);
      return true;
    }
    return false;
  }
  function setSchedule(row) {
    if (!row.scheduleDate) return true;
    // '예약' 옵션 선택(로케일 라벨).
    clickByText('tp-yt-paper-radio-button, ytcp-ve, span, div', L().scheduleOpt);
    // 날짜필드(있으면) 값 세팅 — YT는 date-picker input.
    const dateEl = byLabelInput(L().dateField);
    if (dateEl) setNativeValue(dateEl, row.scheduleDate);
    LOG("schedule set(예약 선택):", row.scheduleDate);
    return true;
  }

  // ---------- 드롭존 파일 이벤트 감지(경로 b) ----------
  // 확장은 OS 드래그 자체 못 가로챔 → 결과 native drop/change 이벤트로 File.name 읽어 매칭.
  function wireDropAndPickerListeners() {
    if (window.__kytWired) return; window.__kytWired = true;
    document.addEventListener("drop", (e) => {
      try {
        const f = e.dataTransfer?.files?.[0];
        if (f) { window.__kytLastFile = f.name; LOG("drop file:", f.name); }
      } catch (err) {}
    }, true);
    document.addEventListener("change", (e) => {
      try {
        const t = e.target;
        if (t && t.type === "file" && t.files?.[0]) { window.__kytLastFile = t.files[0].name; LOG("picker file:", t.files[0].name); }
      } catch (err) {}
    }, true);
  }

  // ---------- 배지(진행표시) ----------
  function renderBadge() {
    if (!_rows.length) { document.getElementById("kyt-badge")?.remove(); return; }
    let el = document.getElementById("kyt-badge");
    if (!el) { el = document.createElement("div"); el.id = "kyt-badge"; el.className = "kyt-badge"; document.body.appendChild(el); }
    const cur = currentUploadFilename();
    const row = rowForFilename(cur) || rowForFilename(window.__kytLastFile);
    el.innerHTML =
      `<div class="kyt-head">🎬 YT 업로드 도우미 <span class="kyt-cnt">${_done.size}/${_rows.length}</span> <span class="kyt-loc">${_locale.toUpperCase()}</span></div>
       <div class="kyt-detail">${cur ? "현재: " + cur : "업로드 파일 대기 중"}${row ? "<br>→ " + esc(row.title) : (cur ? "<br>⚠ CSV에 매칭 행 없음" : "")}</div>
       <div class="kyt-foot">제목·재생목록·예약일 자동채움 · 최종 예약버튼은 직접 확인 후 클릭</div>`;
  }
  const esc = (s) => String(s || "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  // ---------- 메인 루프 ----------
  function tick() {
    try {
      _locale = resolveLocale(); // a_3762: 수동 override 우선, 없으면 자동감지.
      wireDropAndPickerListeners();
      renderBadge();
      if (!_rows.length || _busy) return;
      if (!isDetailsStep()) return;
      const fname = currentUploadFilename() || window.__kytLastFile;
      const row = rowForFilename(fname);
      if (!row) return;
      if (_done.has(row.filename)) return;
      _busy = true;
      // 자동채움 시퀀스(각 스텝 label기반). 최종 예약클릭은 안 함(사람 확정).
      fillTitle(row);
      selectPlaylist(row);
      setTimeout(() => { checkPlaylistItem(row); }, 600);
      setTimeout(() => { setSchedule(row); _busy = false; }, 1400);
    } catch (e) { _busy = false; }
  }

  tick();
  setInterval(tick, 2500);
  new MutationObserver(() => { if (_rows.length && isDetailsStep()) renderBadge(); })
    .observe(document.body, { childList: true, subtree: true });

  // popup → content: 특정 파일 처리완료 표시 요청(사용자가 '이 행 완료' 누를 때) 및 상태조회.
  try {
    chrome.runtime?.onMessage.addListener((msg, _s, reply) => {
      if (msg?.type === "kyt-mark-done" && msg.filename) { _done.add(msg.filename); saveDone(); reply?.({ ok: true, done: _done.size }); }
      if (msg?.type === "kyt-status") reply?.({ rows: _rows.length, done: _done.size, current: currentUploadFilename() });
      return true;
    });
  } catch (e) {}

  LOG("v0.1 loaded");
})();
