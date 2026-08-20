#!/usr/bin/env bash
# play_notes.sh — macOS 메모(Notes) 자동 타이핑 + 단계별 과정 스샷 (a_14·a_16, u_15·u_17).
# ★osascript/앱API 금지 → open -a(띄우기만) + enigo 물리키(⌘N·타이핑)로만 조작.
#   키보드 입력은 앱에 정상 전달됨(마우스클릭 canvas 벽과 무관 — 실측 확인).
# 흐름: Notes 열기 → ⌘N 신규메모 → "안녕하세요" → 500자 소설 → 완성.
# ★a_16: [과정 단계별] 스샷 — 여는순간·⌘N순간·타이핑 각 단계 촘촘히 캡처(결과 아닌 진행).
#   step_01_before(열기전) → 02_opened(앱뜸) → 03_newnote(⌘N) → 04_hello → 05_typing → 06_done.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEMO="$ROOT/demo"
BIN="$ROOT/target/release/kongtrol"
SHOTDIR="${TMPDIR:-/tmp}/kongtrol_play_shots"
NOVEL="$DEMO/novel_text.txt"
mkdir -p "$SHOTDIR"
[ -x "$BIN" ] || { echo "빌드 중..."; (cd "$ROOT" && cargo build --release -q); }

echo "== kongtrol 메모 자동 타이핑 =="

# 프리플라이트: 키 주입 권한(손쉬운 사용) — 무해한 esc 1회.
if "$BIN" --yes input key esc 2>&1 | grep -q "권한"; then
  echo "  ✗ 손쉬운 사용(Accessibility) 미승인 → 키 주입 불가. 시스템 설정서 터미널 추가 후 재실행."
  exit 3
fi

# ★step_01: 열기 전 바탕화면(과정 시작 — 아직 Notes 안 뜬 상태).
screencapture -x "$SHOTDIR/step_01_before.png" 2>/dev/null && echo "[스샷 01] step_01_before(열기 전 바탕화면)"

# 1) Notes 열기(띄우기만 — 권한 불요). 파일다이얼로그 없음(TextEdit 과 달리 안정).
echo "[1] 메모 앱 열기(open -a Notes)..."
open -a Notes
sleep 3
# ★step_02: open -a 직후 앱 뜬 순간.
screencapture -x "$SHOTDIR/step_02_opened.png" 2>/dev/null && echo "[스샷 02] step_02_opened(Notes 앱 뜬 순간)"

# 2) ⌘N 신규 메모 (osascript 금지 — enigo 물리 조합키).
echo "[2] ⌘N 신규 메모(물리 조합키)..."
"$BIN" --yes input chord cmd n >/dev/null 2>&1
sleep 1.5
# ★step_03: ⌘N 으로 신규 메모 만들어진 순간(빈 새 메모).
screencapture -x "$SHOTDIR/step_03_newnote.png" 2>/dev/null && echo "[스샷 03] step_03_newnote(⌘N 신규 메모 생성 순간)"

# 3) "안녕하세요" 타이핑 → step_04.
echo "[3] '안녕하세요' 타이핑(물리키)..."
"$BIN" --yes input text "안녕하세요" >/dev/null 2>&1
sleep 1
screencapture -x "$SHOTDIR/step_04_hello.png" 2>/dev/null && echo "[스샷 04] step_04_hello('안녕하세요' 타이핑된 순간)"
cp "$SHOTDIR/step_04_hello.png" "$SHOTDIR/notes_1_hello.png" 2>/dev/null  # a_14 호환

# 4) 소설 타이핑 (전반부 → step_05, 후반부 → step_06).
"$BIN" --yes input key enter >/dev/null 2>&1
"$BIN" --yes input key enter >/dev/null 2>&1
if [ -f "$NOVEL" ]; then
  BODY=$(tail -n +2 "$NOVEL")
  HALF_LINES=$(printf '%s\n' "$BODY" | wc -l | awk '{print int($1/2)}')
  printf '%s\n' "$BODY" | head -n "$HALF_LINES" > "$SHOTDIR/_novel_half1.txt"
  printf '%s\n' "$BODY" | tail -n +"$((HALF_LINES+1))" > "$SHOTDIR/_novel_half2.txt"
  echo "[4] 소설 전반부 타이핑 중..."
  "$BIN" --yes input type-file "$SHOTDIR/_novel_half1.txt" >/dev/null 2>&1
  sleep 1
  screencapture -x "$SHOTDIR/step_05_typing.png" 2>/dev/null && echo "[스샷 05] step_05_typing(소설 타이핑 중간)"
  cp "$SHOTDIR/step_05_typing.png" "$SHOTDIR/notes_2_mid.png" 2>/dev/null  # a_14 호환
  echo "[5] 소설 후반부 타이핑..."
  "$BIN" --yes input type-file "$SHOTDIR/_novel_half2.txt" >/dev/null 2>&1
  sleep 1
  screencapture -x "$SHOTDIR/step_06_done.png" 2>/dev/null && echo "[스샷 06] step_06_done(소설 완성)"
  cp "$SHOTDIR/step_06_done.png" "$SHOTDIR/notes_3_done.png" 2>/dev/null  # a_14 호환
  rm -f "$SHOTDIR/_novel_half1.txt" "$SHOTDIR/_novel_half2.txt"
else
  echo "  (소설 파일 없음: $NOVEL)"
fi
echo "완료. 과정 스샷: $SHOTDIR/step_01_before ~ step_06_done.png (순서대로)"
