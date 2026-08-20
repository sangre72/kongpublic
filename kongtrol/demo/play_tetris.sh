#!/usr/bin/env bash
# play_tetris.sh — 테트리스 키보드 자동조작 + 5레벨 플레이 스샷 (a_13, u_15).
# ★키보드 입력은 Tkinter canvas 에 정상 전달됨(마우스클릭과 경로 다름 — 실측 확인).
#   각 레벨: 앱 기동 → 창 포커스 → 물리키 시퀀스(좌우·회전·드롭) 주입 → 플레이 스샷 저장.
#
# 사용: ./play_tetris.sh            # 5레벨 각 플레이·스샷
#       ./play_tetris.sh 3          # 특정 레벨만
# ★권한: 손쉬운 사용(Accessibility) 승인됨 전제(키 주입). 화면기록(스샷).
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEMO="$ROOT/demo"
BIN="$ROOT/target/release/kongtrol"
SHOTDIR="${TMPDIR:-/tmp}/kongtrol_play_shots"
mkdir -p "$SHOTDIR"
[ -x "$BIN" ] || { echo "빌드 중..."; (cd "$ROOT" && cargo build --release -q); }

echo "== kongtrol 테트리스 키보드 플레이 (5레벨) =="

# 프리플라이트: 키 주입 권한(손쉬운 사용) 확인 — 무해한 esc 1회.
if "$BIN" --yes input key esc 2>&1 | grep -q "권한"; then
  echo "  ✗ 손쉬운 사용(Accessibility) 미승인 → 키 주입 불가. 시스템 설정서 터미널 추가 후 재실행."
  exit 3
fi

LEVELS="${1:-1 2 3 4 5}"
for L in $LEVELS; do
  echo "── 레벨 $L ──"
  pkill -f "demo/tetris_app.py" 2>/dev/null; sleep 1
  GEOM="$SHOTDIR/tetris_geom_$L.json"; rm -f "$GEOM"
  MS_GEOM_FILE="$GEOM" python3 "$DEMO/tetris_app.py" --level "$L" >"$SHOTDIR/tetris_app_$L.log" 2>&1 &
  APP_PID=$!
  # geom 폴링(최대 8s)
  for _ in $(seq 1 40); do [ -f "$GEOM" ] && break; sleep 0.2; done
  if [ ! -f "$GEOM" ]; then echo "  ✗ 앱 geom 방출 실패(로그: $SHOTDIR/tetris_app_$L.log)"; kill $APP_PID 2>/dev/null; continue; fi
  LOG=$(python3 -c "import json;g=json.load(open('$GEOM'));l=g['logical'];print('%d,%d,%d,%d'%(l[0],l[1],l[2],l[3]))")

  # 시작 스샷(플레이 전)
  screencapture -x -R"$LOG" "$SHOTDIR/tetris_L${L}_start.png" 2>/dev/null

  # 키 시퀀스: 좌우 이동 + 회전 + 소프트/하드 드롭 반복(블록 여러 개 배치 = 플레이 진행).
  echo "  [키] 좌우·회전·드롭 시퀀스 주입..."
  for round in 1 2 3 4 5; do
    "$BIN" --yes input key left --repeat 2 >/dev/null 2>&1
    "$BIN" --yes input key up >/dev/null 2>&1       # 회전
    "$BIN" --yes input key right >/dev/null 2>&1
    "$BIN" --yes input key space >/dev/null 2>&1    # 하드드롭
    sleep 0.3
  done
  sleep 0.5

  # 플레이 후 스샷(블록 쌓인 상태)
  SHOT="$SHOTDIR/tetris_L${L}.png"
  screencapture -x -R"$LOG" "$SHOT" 2>/dev/null && echo "  [스샷] 레벨$L 플레이: $SHOT"
  # 앱이 받은 키 로그 요약
  KEYS=$(grep -cE "MOVE|ROTATE|DROP" "$SHOTDIR/tetris_app_$L.log" 2>/dev/null || echo 0)
  echo "  [실증] 앱이 수신한 키액션 $KEYS 개"
  kill $APP_PID 2>/dev/null
done
pkill -f "demo/tetris_app.py" 2>/dev/null
echo "완료. 스크린샷: $SHOTDIR/tetris_L*.png"
