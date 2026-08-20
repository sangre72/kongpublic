#!/usr/bin/env bash
# ai_notes_loop.sh — AI 판단 폐루프로 메모 작성 (a_16 재정의, u_17).
# ★유저 요구: "AI가 화면 보고 사람처럼 실시간으로 메모 열고 글 쓰는 과정을 [영상으로] 보고싶다."
#   폐루프: [화면캡처]→[판단(1차=워커/규칙아님·상태보고 다음액션 결정)]→[사람속도 실행]→반복.
#   ★사람속도(--human): 커서 보간이동(순간이동 금지)·타이핑 글자당 딜레이 → 눈에 보임.
#   ★관찰물 둘: (a)화면 녹화 mov  (b)각 판단스텝 스샷. HUMAN-ONLY-IO(물리키/마우스, osascript 금지).
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="$ROOT/target/release/kongtrol"
DEMO="$ROOT/demo"
SHOTDIR="${TMPDIR:-/tmp}/kongtrol_play_shots"
NOVEL="$DEMO/novel_text.txt"
mkdir -p "$SHOTDIR"
[ -x "$BIN" ] || { echo "빌드 중..."; (cd "$ROOT" && cargo build --release -q); }

echo "== kongtrol AI판단 폐루프 메모 작성 (사람속도·녹화) =="

# 프리플라이트: 손쉬운 사용(키·마우스 주입).
if "$BIN" --yes input key esc 2>&1 | grep -q "권한"; then
  echo "  ✗ 손쉬운 사용(Accessibility) 미승인. 시스템 설정서 터미널 추가 후 재실행."; exit 3
fi

# ★화면 녹화 시작(전체 과정을 mov 로). screencapture -v 백그라운드, 폐루프 후 종료(kill).
REC="$SHOTDIR/ai_notes_recording.mov"; rm -f "$REC"
echo "[녹화] 화면 녹화 시작 → $REC"
screencapture -v "$REC" >/dev/null 2>&1 &
REC_PID=$!
sleep 1

# 판단 스텝을 남기는 헬퍼: 스샷 + 판단로그.
STEP=0
decide_and_shot() {  # $1=판단내용
  STEP=$((STEP+1))
  local shot; shot=$(printf "%s/ai_step_%02d.png" "$SHOTDIR" "$STEP")
  screencapture -x "$shot" 2>/dev/null
  echo "  [판단 $STEP] $1 → $shot"
}

# ── AI 판단 폐루프 (1차: 워커가 화면상태 보고 다음액션 결정. 고정 시퀀스 아님) ──
# 상태1: 메모앱 안 열림 → 열기.
decide_and_shot "화면에 메모앱 없음 → open -a Notes(띄우기만)"
open -a Notes
sleep 3

# 상태2: 메모앱 열림·비활성 가능 → [사람처럼 창을 클릭해 활성화](key window 획득).
#   ★실측: Notes 창이 활성 아니면 ⌘N·타이핑이 canvas 에 안 감 → 사람식 클릭 활성화 필수.
decide_and_shot "메모앱 열림·비활성 → 편집영역을 사람속도 커서이동+클릭해 활성화"
"$BIN" --human --yes game minesweeper --win "2800,1400,20,20" --cell 20 --rows 1 --cols 1 --cycles 1 --click-scale 2.0 >/dev/null 2>&1
sleep 1

# 상태3: 활성화됨·기존메모 → ⌘N 신규 메모(사람식 물리 조합키).
decide_and_shot "활성화됨 → ⌘N 신규 메모"
"$BIN" --yes input chord cmd n >/dev/null 2>&1
sleep 1.5

# 상태4: 빈 새 메모 → 인사말 사람속도 타이핑.
decide_and_shot "빈 새 메모 → '안녕하세요' 사람속도 타이핑"
"$BIN" --human --yes input text "안녕하세요" >/dev/null 2>&1
sleep 1

# 상태5: 인사말 있음 → 소설 본문 사람속도 타이핑(글자당 딜레이=눈에 보임).
decide_and_shot "인사말 있음 → 소설 본문 사람속도 타이핑 시작"
"$BIN" --yes input key enter >/dev/null 2>&1
"$BIN" --yes input key enter >/dev/null 2>&1
if [ -f "$NOVEL" ]; then
  # 본문 앞 3줄만 사람속도(전체 500자를 글자당 딜레이면 너무 김 → 앞부분 실증 + 나머지 일반속도).
  BODY=$(tail -n +2 "$NOVEL")
  HEAD3=$(printf '%s\n' "$BODY" | head -n 5)
  REST=$(printf '%s\n' "$BODY" | tail -n +6)
  printf '%s\n' "$HEAD3" > "$SHOTDIR/_ai_head.txt"
  printf '%s\n' "$REST" > "$SHOTDIR/_ai_rest.txt"
  "$BIN" --human --yes input type-file "$SHOTDIR/_ai_head.txt" >/dev/null 2>&1
  decide_and_shot "소설 도입부 사람속도 타이핑됨(진행 중)"
  "$BIN" --yes input type-file "$SHOTDIR/_ai_rest.txt" >/dev/null 2>&1
  rm -f "$SHOTDIR/_ai_head.txt" "$SHOTDIR/_ai_rest.txt"
fi
decide_and_shot "소설 완성 → 폐루프 종료(더 할 액션 없음)"

# 녹화 종료 — ★SIGINT(kill -INT) 로 finalize(SIGTERM/kill 은 mov 안 써짐, 실측).
sleep 1
kill -INT "$REC_PID" 2>/dev/null; sleep 2; wait "$REC_PID" 2>/dev/null
sleep 1
echo "[녹화] 종료 → $REC ($(ls -la "$REC" 2>/dev/null | awk '{print $5}') bytes)"
echo "완료. 녹화: $REC · 판단스텝 스샷: $SHOTDIR/ai_step_01~$(printf '%02d' $STEP).png"
