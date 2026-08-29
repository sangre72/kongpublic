# cross-app menu patterns (2026-08-27, Finder+Safari, File+Edit)

## confirmed universal shortcuts(Edit menu, both apps)
- Copy = Cmd+C (Finder:"복사" / Safari:"복사하기" — label differs, function+shortcut identical)
- Paste = Cmd+V (label identical both apps: "붙여넣기")
- Select All = Cmd+A (label identical both apps: "전체 선택")
- Undo = Cmd+Z (label identical both apps: "실행 취소"/"실행 복귀" pairing)

## label-variance gotcha
- "복사"(Finder) vs "복사하기"(Safari) — same Copy function, cosmetic suffix diff. lookup should match on FUNCTION not exact string across apps.

## destructive-label pattern(observe-only, both apps had at least one)
- Finder: "휴지통으로 이동"/"즉시 삭제…" in File menu
- Safari: "삭제"(Edit menu, though context=content not app-level)/"탭 그룹 삭제"(File menu)
- pattern: any label containing 삭제/제거/이동(to trash)/즉시 = flag destructive, skip click-testing regardless of which menu(File OR Edit) it appears in.

## structural pattern
- both apps: File menu has New/Open/Close/Save-variant/Share/Print cluster in roughly same relative order.
- both apps: Edit menu has Undo/Redo/Cut/Copy/Paste/SelectAll/Find cluster in roughly same relative order.

---

## UPDATE(batch2: Keynote/Numbers/Pages/KakaoTalk added, 6 apps total)

## ★iWork-suite = near-identical menu structure(Keynote/Numbers/Pages)
- File menu: 신규…/열기…/닫기/저장/별도저장…/복제/이름변경…/공유…/암호설정…/프린트… all IDENTICAL across all 3 apps, only app-specific extras differ(Pages:메일병합/Apple Books발행, Keynote:테마변경, Numbers:템플릿으로저장).
- Edit menu: 실행취소/실행복귀/오려두기/복사/붙여넣기/삭제/모두지우기/전체선택/찾기 IDENTICAL across all 3.
- ★practical implication: learning ONE iWork app's menu-structure = near-complete transfer to the other 2(same vendor/framework, expected but now empirically confirmed 3/3).

## ★universal shortcuts NOW CONFIRMED 6/6 apps
Copy=Cmd+C, Paste=Cmd+V, SelectAll=Cmd+A, Undo=Cmd+Z — held across Finder/Safari/Keynote/Numbers/Pages/KakaoTalk without exception. high-confidence as a true macOS-wide convention, not just iWork-family coincidence.

## ★NEW gotcha: language-inconsistent app(KakaoTalk)
- KakaoTalk's Edit menu MIXES Korean(실행취소/실행복귀) and English(Cut/Copy/Paste/Delete/Select All/Find) labels in the SAME menu — non-Apple/non-iWork apps may not follow consistent-localization. lookup-by-label must handle BOTH language variants for this app, can't assume Korean-only.

## ★NEW pattern: not all apps have File menu
- KakaoTalk(chat-app) has NO File menu at all — only 편집(Edit)/창(Window)/도움말(Help). apps whose primary function isn't document-editing may lack File menu entirely — expect this for messaging/utility/media-player-type apps going forward, don't treat as an error.

## destructive-label pattern — UPDATED
- also seen: "지우기"(Clear, Keynote/Numbers/Pages "모두 지우기") as destructive-adjacent, "거부"(Reject, Pages "변경 내용 거부" discards tracked edits) as destructive-adjacent even though label itself isn't 삭제/제거.
- KakaoTalk confirms pattern applies regardless of language: "Delete"(English) = same skip-rule as "삭제"(Korean).
- NEW: session/account-level actions also count as destructive-adjacent even w/o delete/erase keyword — Telegram's "Log Out"(requires re-auth) flagged same as literal-delete items.

---

## UPDATE(batch2: Chrome/Telegram/Word added, 9 apps total)

## ★★★ VENDOR-CLUSTER label-variance(major finding)
Korean menu-labels for the SAME function differ by VENDOR, not randomly — each vendor is internally consistent but differs from others:
| function | Apple(Finder/iWork) | Google(Chrome) | Microsoft(Word) |
|---|---|---|---|
| Edit(menu itself) | 편집 | 수정 | 편집 |
| Cut | 오려두기 | 잘라내기 | 잘라내기 |
| Copy | 복사(iWork/Finder) | 복사 | 복사하기 |
| Redo | 실행 복귀 | 다시실행 | 실행 복귀 |
| Select All | 전체 선택 | 모두 선택 | 모두 선택 |
| Print | 프린트 | 인쇄 | 인쇄... |
→ practical implication: lookup-by-exact-label WILL FAIL cross-vendor even for identical functions. must either (a) maintain a per-vendor label-alias table, or (b) prefer shortcut-key lookup(Cmd+X/C/V/A/Z are 100% consistent) over label-text when shortcut exists.

## ★localization-consistency pattern
- Apple-native apps(Finder/Keynote/Numbers/Pages) + Google(Chrome) = fully Korean-localized.
- Telegram = fully English(zero Korean labels).
- KakaoTalk = MIXED Korean+English within same menu(inconsistent even internally).
→ can't assume any single language per-locale-setting; must read actual label text each time, not assume from OS-locale.

## ★app-launch-state gotcha(Microsoft Word)
- Word opens a template-picker/start-screen window FIRST — NO menu-bar visible until "새 문서"(New Document) is clicked to reach the real editor. Any app with a startup/welcome-screen may have this same gotcha — check `see --a11y` element-count before assuming menu-bar is ready; if the window looks like a picker/gallery(many AXButton template-thumbnails), navigate past it first.

## ★a11y-empty-fix(RESOLVED, was environment-limitation note, now solved)
- Arc + VSCode both initially returned empty a11y(0 AXMenuBarItem) despite process running+menu-bar visually present. ★FIX: click into the app's own window FIRST(establishes real focus) THEN query `see --a11y --pid <pid>` — worked immediately after. Also for Electron apps(VSCode): use the pid-matching pattern `pgrep -f "<App>.app/Contents/MacOS"` NOT generic `pgrep -x "<App>"`(the latter can match a Helper-process w/ 0 a11y elements instead of the real main window process).
- standing rule going forward: if `see --a11y --pid X` returns 0/empty elements despite the process existing, click into the window once before retrying — don't conclude "no menu bar" without this step first.

---

## UPDATE(batch3: Arc+VSCode added per explicit request, 11 apps total)

## ★"Open Recent"/"최근 사용한 파일" submenu pattern(cross-app, per a_2546)
Structure(confirmed via VSCode, expect similar in other multi-doc apps): recent-items-list(paths/files) THEN management-action-items(Reopen-Closed/More.../Clear-Recently-Opened). 
★the "Clear"/"지우기" action-item within this submenu = DESTRUCTIVE-ADJACENT(wipes history-list, not actual files, but irreversible) — flag same as top-level destructive items even though it's nested in an otherwise-safe "Open Recent" parent.

## ★browser-category has no Open/Recent-Files pattern
Arc(browser) confirmed: File menu has zero "Open File"/"Recent Files" concept — browsers use tab/history navigation instead. Don't expect this submenu-pattern for browser-category apps(Chrome/Safari/Arc), only for document-editor-category(Word/VSCode/iWork).

## ★code-editor category has no Delete/Clear item in Edit menu
VSCode's Edit menu lacks any Delete/Clear-All item(unlike every other app-category tested) — text-deletion happens via keyboard Delete-key directly, not a menu command. don't expect a destructive-item-to-flag in this specific app-category's Edit menu; absence itself is the notable pattern.
