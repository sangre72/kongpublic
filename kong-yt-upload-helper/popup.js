/* popup.js — CSV 로드+검증(a_3761 amend) + 진행표시 + popup UI i18n(a_3763 amend). */
(() => {
  "use strict";
  const REQUIRED = ["filename", "title", "playlist", "scheduleDate"];

  // ---------- popup UI i18n(a_3763): UI 언어=로케일 드롭다운과 동일 설정에 연동 ----------
  //   (auto = navigator.language 기반, 미지원시 en). 정적요소=data-i18n, 동적메시지=T(key,..).
  const I18N = {
    ko: {
      sub: "CSV로 YouTube Studio 업로드의 제목·재생목록·예약일을 자동 채웁니다.",
      guideH: "CSV 형식 (헤더 1줄 + 영상별 1줄)",
      guideNote: "· 필수 열 4개: <b>filename, title, playlist, scheduleDate</b><br>· scheduleDate = YYYY-MM-DD · 제목에 쉼표 있으면 \"큰따옴표\"로 감싸기",
      localeLbl: "YT Studio UI 언어", localeAuto: "자동 감지",
      pickBtn: "📄 설정 CSV 파일 선택",
      donate: "☕ 개발자에게 커피 한 잔",

      foot: "제목·재생목록·예약일까지 자동채움. <b>최종 '예약' 버튼은 직접 검토 후 클릭</b>(오발행 방지).",
      loaded: (n, f) => `✅ ${n}개 행 로드됨 (${f})`, existing: (n, d) => `기존 로드: ${n}개 행 · 완료 ${d}`,
      warnDup: "중복 filename", errRead: "파일을 읽지 못했습니다", errSave: "저장 실패",
      errEmpty: "빈 파일입니다.", errMissing: (c, h) => `헤더에 필수 열 누락: [${c}]. 첫 줄 헤더 = ${REQUIRED.join(",")} 이어야 합니다. (현재 헤더: ${h || "(없음)"})`,
      errNoRows: "데이터 행이 없습니다(헤더만 있음). 영상별로 1줄씩 추가하세요.",
      errCell: (ln, col, line) => `${ln}행 '${col}' 칸이 비었습니다. (해당 행: ${line})`,
      errDate: (ln, v) => `${ln}행 scheduleDate '${v}' 형식 오류 — YYYY-MM-DD 여야 합니다(예: 2026-09-05).`,
      errExt: (ln, v) => `${ln}행 filename '${v}' 확장자 없음 — scene_01.mp4 처럼 파일명 전체를 넣으세요.`,
    },
    en: {
      sub: "Auto-fills title, playlist, and schedule date on YouTube Studio uploads from a CSV.",
      guideH: "CSV format (1 header row + 1 row per video)",
      guideNote: "· Required columns: <b>filename, title, playlist, scheduleDate</b><br>· scheduleDate = YYYY-MM-DD · wrap titles containing commas in \"double quotes\"",
      localeLbl: "YT Studio UI language", localeAuto: "Auto-detect",
      pickBtn: "📄 Choose CSV config file",
      donate: "☕ Buy the developer a coffee",

      foot: "Auto-fills title, playlist, and schedule date. <b>Click the final Schedule button yourself after reviewing</b> (prevents mis-publishing).",
      loaded: (n, f) => `✅ Loaded ${n} rows (${f})`, existing: (n, d) => `Loaded: ${n} rows · done ${d}`,
      warnDup: "duplicate filename", errRead: "Could not read file", errSave: "Save failed",
      errEmpty: "Empty file.", errMissing: (c, h) => `Missing required column(s) in header: [${c}]. Header must be ${REQUIRED.join(",")}. (current: ${h || "(none)"})`,
      errNoRows: "No data rows (header only). Add one row per video.",
      errCell: (ln, col, line) => `Row ${ln}: '${col}' cell is empty. (row: ${line})`,
      errDate: (ln, v) => `Row ${ln}: scheduleDate '${v}' invalid — must be YYYY-MM-DD (e.g. 2026-09-05).`,
      errExt: (ln, v) => `Row ${ln}: filename '${v}' has no extension — use the full name like scene_01.mp4.`,
    },
    ja: {
      sub: "CSVからYouTube Studioアップロードのタイトル・再生リスト・予約日を自動入力します。",
      guideH: "CSV形式(ヘッダー1行 + 動画ごとに1行)",
      guideNote: "· 必須列4つ: <b>filename, title, playlist, scheduleDate</b><br>· scheduleDate = YYYY-MM-DD · タイトルにカンマがある場合は\"ダブルクォート\"で囲む",
      localeLbl: "YT Studio UI 言語", localeAuto: "自動検出",
      pickBtn: "📄 設定CSVファイルを選択",
      donate: "☕ 開発者にコーヒーを一杯",

      foot: "タイトル・再生リスト・予約日まで自動入力。<b>最終の「予約」ボタンは確認後ご自身でクリック</b>(誤公開防止)。",
      loaded: (n, f) => `✅ ${n}行 読み込み (${f})`, existing: (n, d) => `読み込み済: ${n}行 · 完了 ${d}`,
      warnDup: "重複filename", errRead: "ファイルを読み込めません", errSave: "保存失敗",
      errEmpty: "空のファイルです。", errMissing: (c, h) => `ヘッダーに必須列がありません: [${c}]。ヘッダーは ${REQUIRED.join(",")} である必要があります。(現在: ${h || "(なし)"})`,
      errNoRows: "データ行がありません(ヘッダーのみ)。動画ごとに1行追加してください。",
      errCell: (ln, col, line) => `${ln}行目 '${col}' が空です。(該当行: ${line})`,
      errDate: (ln, v) => `${ln}行目 scheduleDate '${v}' 形式エラー — YYYY-MM-DD が必要です(例: 2026-09-05)。`,
      errExt: (ln, v) => `${ln}行目 filename '${v}' に拡張子がありません — scene_01.mp4 のようにフルネームを入力。`,
    },
    es: {
      sub: "Autocompleta título, lista de reproducción y fecha de programación en subidas de YouTube Studio desde un CSV.",
      guideH: "Formato CSV (1 fila de encabezado + 1 fila por video)",
      guideNote: "· Columnas obligatorias: <b>filename, title, playlist, scheduleDate</b><br>· scheduleDate = YYYY-MM-DD · pon los títulos con comas entre \"comillas dobles\"",
      localeLbl: "Idioma de la interfaz de YT Studio", localeAuto: "Detección automática",
      pickBtn: "📄 Elegir archivo CSV",
      donate: "☕ Invita un café al desarrollador",

      foot: "Autocompleta título, lista y fecha. <b>Haz clic tú mismo en el botón Programar tras revisar</b> (evita publicaciones erróneas).",
      loaded: (n, f) => `✅ ${n} filas cargadas (${f})`, existing: (n, d) => `Cargado: ${n} filas · hechas ${d}`,
      warnDup: "filename duplicado", errRead: "No se pudo leer el archivo", errSave: "Error al guardar",
      errEmpty: "Archivo vacío.", errMissing: (c, h) => `Faltan columnas obligatorias en el encabezado: [${c}]. El encabezado debe ser ${REQUIRED.join(",")}. (actual: ${h || "(ninguno)"})`,
      errNoRows: "Sin filas de datos (solo encabezado). Añade una fila por video.",
      errCell: (ln, col, line) => `Fila ${ln}: la celda '${col}' está vacía. (fila: ${line})`,
      errDate: (ln, v) => `Fila ${ln}: scheduleDate '${v}' inválido — debe ser YYYY-MM-DD (ej. 2026-09-05).`,
      errExt: (ln, v) => `Fila ${ln}: filename '${v}' sin extensión — usa el nombre completo como scene_01.mp4.`,
    },
  };
  let _uiLoc = "en";
  const T = (k, ...a) => { const s = (I18N[_uiLoc] || I18N.en)[k]; return typeof s === "function" ? s(...a) : s; };
  function resolveUiLocale(override) {
    if (override && override !== "auto" && I18N[override]) return override;
    const nav = (navigator.language || "en").slice(0, 2).toLowerCase();
    return I18N[nav] ? nav : "en";
  }
  function applyStaticI18n() {
    document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = T(el.getAttribute("data-i18n")); });
    document.querySelectorAll("[data-i18n-html]").forEach((el) => { el.innerHTML = T(el.getAttribute("data-i18n-html")); });
  }
  const $ = (id) => document.getElementById(id);
  const errEl = $("kyt-error"), statusEl = $("kyt-status"), listEl = $("kyt-list");

  // --- 간단 CSV 파서(따옴표·이스케이프 대응, 쉼표 포함 필드 지원) ---
  function parseCSV(text) {
    const rows = [];
    let row = [], field = "", inQ = false;
    text = text.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (inQ) {
        if (c === '"') { if (text[i + 1] === '"') { field += '"'; i++; } else inQ = false; }
        else field += c;
      } else {
        if (c === '"') inQ = true;
        else if (c === ",") { row.push(field); field = ""; }
        else if (c === "\n") { row.push(field); rows.push(row); row = []; field = ""; }
        else field += c;
      }
    }
    if (field.length || row.length) { row.push(field); rows.push(row); }
    // 완전 빈 줄 제거.
    return rows.filter((r) => r.some((c) => (c || "").trim() !== ""));
  }

  const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

  // --- 검증 + 파싱 → {ok, rows, error}(i18n 메시지) ---
  function validate(text) {
    const grid = parseCSV(text);
    if (!grid.length) return { ok: false, error: T("errEmpty") };
    const header = grid[0].map((h) => (h || "").trim());
    const missing = REQUIRED.filter((c) => !header.includes(c));
    if (missing.length) return { ok: false, error: T("errMissing", missing.join(", "), header.join(",")) };
    const idx = {}; REQUIRED.forEach((c) => (idx[c] = header.indexOf(c)));
    const dataRows = grid.slice(1);
    if (!dataRows.length) return { ok: false, error: T("errNoRows") };
    const out = [];
    for (let r = 0; r < dataRows.length; r++) {
      const line = dataRows[r]; const lineNo = r + 2; // 1-based, +헤더
      const rec = {};
      for (const col of REQUIRED) {
        const v = (line[idx[col]] || "").trim();
        if (!v) return { ok: false, error: T("errCell", lineNo, col, line.join(",")) };
        rec[col] = v;
      }
      if (!DATE_RE.test(rec.scheduleDate)) return { ok: false, error: T("errDate", lineNo, rec.scheduleDate) };
      if (!/\.[A-Za-z0-9]+$/.test(rec.filename)) return { ok: false, error: T("errExt", lineNo, rec.filename) };
      out.push(rec);
    }
    const dup = out.map((r) => r.filename).filter((f, i, a) => a.indexOf(f) !== i);
    return { ok: true, rows: out, warn: dup.length ? `${T("warnDup")}: ${[...new Set(dup)].join(", ")}` : null };
  }

  function showError(msg) { errEl.textContent = "❌ " + msg; errEl.style.display = "block"; statusEl.textContent = ""; listEl.innerHTML = ""; }
  function clearError() { errEl.textContent = ""; errEl.style.display = "none"; }

  function renderList(rows, done) {
    const d = new Set(done || []);
    listEl.innerHTML = rows.map((r) =>
      `<div class="kyt-row ${d.has(r.filename) ? "kyt-row-done" : ""}">
         <span class="kyt-row-f">${d.has(r.filename) ? "✅" : "◻︎"} ${esc(r.filename)}</span>
         <span class="kyt-row-t">${esc(r.title)}</span>
         <span class="kyt-row-m">${esc(r.playlist)} · ${esc(r.scheduleDate)}</span>
       </div>`).join("");
  }
  const esc = (s) => String(s || "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  // --- 파일 선택 ---
  $("kyt-pick").addEventListener("click", () => $("kyt-file").click());
  $("kyt-file").addEventListener("change", async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    clearError();
    let text;
    try { text = await f.text(); } catch (err) { showError(T("errRead") + ": " + err.message); return; }
    const v = validate(text);
    if (!v.ok) { showError(v.error); return; }
    try {
      chrome.storage.local.set({ kyt_rows: v.rows, kyt_done: [] }, () => {
        statusEl.textContent = T("loaded", v.rows.length, f.name) + (v.warn ? " · ⚠ " + v.warn : "");
        renderList(v.rows, []);
      });
    } catch (err) { showError(T("errSave") + ": " + err.message); }
  });

  // --- 로케일 선택(a_3762) + popup UI 언어 연동(a_3763): auto-detect 기본 + 수동 override + 영속 ---
  const localeSel = $("kyt-locale");
  function applyLocale(v) {
    _uiLoc = resolveUiLocale(v);
    applyStaticI18n();
  }
  // 저장값 복원(없으면 auto) → 드롭다운 + popup UI 언어 반영.
  try {
    chrome.storage.local.get(["kyt_locale"], (r) => {
      const v = r && r.kyt_locale ? r.kyt_locale : "auto";
      localeSel.value = ["auto", "ko", "en", "ja", "es"].includes(v) ? v : "auto";
      applyLocale(localeSel.value);
    });
  } catch (e) { applyLocale("auto"); }
  // 변경 즉시 저장(content.js DOM-label + popup UI 둘 다 이 로케일 사용). auto=자동감지.
  localeSel.addEventListener("change", () => {
    const v = localeSel.value;
    try { chrome.storage.local.set({ kyt_locale: v }); } catch (e) {}
    applyLocale(v);
  });

  // --- 로드시 기존 상태 복원 ---
  try {
    chrome.storage.local.get(["kyt_rows", "kyt_done"], (r) => {
      if (r && Array.isArray(r.kyt_rows) && r.kyt_rows.length) {
        statusEl.textContent = T("existing", r.kyt_rows.length, (r.kyt_done || []).length);
        renderList(r.kyt_rows, r.kyt_done || []);
      }
    });
  } catch (e) {}
})();
