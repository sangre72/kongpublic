#!/usr/bin/env bash
# play_minesweeper_pygame.sh — pygame 지뢰찾기 실마우스클릭 플레이 + 3스샷 (a_12, u_15).
# ★ORCH_DECISION#2: Tkinter 는 합성클릭 거부 → pygame(SDL2 네이티브 창, 합성클릭 수신)으로 교체.
#   오프닝무브(kongtrol decide)→locator 창탐지→실마우스클릭 폐루프→시작/도중/종료 3스샷.
#   preopen 금지(실클릭으로만 셀 열림 증명). HUMAN-ONLY-IO(pyobjc/osascript 금지).
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEMO="$ROOT/demo"
BIN="$ROOT/target/release/kongtrol"
SHOTDIR="${TMPDIR:-/tmp}/kongtrol_play_shots"
mkdir -p "$SHOTDIR"
[ -x "$BIN" ] || { echo "빌드 중..."; (cd "$ROOT" && cargo build --release -q); }

echo "== kongtrol pygame 지뢰찾기 실마우스클릭 플레이 =="

# 프리플라이트: 손쉬운 사용(클릭) 권한.
if "$BIN" --yes game minesweeper --win "0,0,80,80" --cell 40 --rows 1 --cols 1 --cycles 1 2>&1 | grep -q "권한 부족"; then
  echo "  ✗ Accessibility(손쉬운 사용) 미승인 → 실제 클릭 불가. 시스템 설정서 터미널 추가 후 재실행."
  exit 3
fi

# 앱 띄우기(pygame 네이티브). preopen 없음(빈 보드→오프닝무브가 첫 셀 실클릭).
GEOM="$SHOTDIR/app_geom.json"; rm -f "$GEOM"
MS_GEOM_FILE="$GEOM" python3 "$DEMO/minesweeper_pygame.py" >"$SHOTDIR/pygame_app.log" 2>&1 &
APP_PID=$!
# geom 폴링(최대 8s).
echo -n "[대기] pygame geometry 방출"
for _ in $(seq 1 40); do [ -f "$GEOM" ] && break; echo -n "."; sleep 0.2; done; echo
if [ ! -f "$GEOM" ]; then echo "  ✗ geom 방출 실패(로그: $SHOTDIR/pygame_app.log)"; kill $APP_PID 2>/dev/null; exit 4; fi
sleep 1  # 창 최전면 안정화

LOG=$(python3 -c "import json;g=json.load(open('$GEOM'));l=g['logical'];print('%d,%d,%d,%d'%(l[0],l[1],l[2],l[3]))")
SCALE=$(python3 -c "import json;print(json.load(open('$GEOM'))['scale'])")

# 시작 스샷(전부 닫힘, 클릭 전).
screencapture -x -R"$LOG" "$SHOTDIR/shot_1_start.png" 2>/dev/null && echo "[스샷1] shot_1_start(초기 닫힘)"

# ★locator 자동탐지 우선 시도(--win 없이). 실패 시(화면 회색 노이즈 등) geom 좌표 fallback.
echo "[탐지] locator 자동탐지 시도..."
LOC_OUT=$("$BIN" --yes game minesweeper --cycles 1 --sense-only 2>&1)
if echo "$LOC_OUT" | grep -q "locator"; then
  echo "  ✓ locator 자동탐지 성공(--win 없이 창 찾음)"
  USE_AUTO=1
else
  echo "  △ locator 자동탐지 실패(화면 회색 노이즈) → 앱 geom 좌표 fallback(앱 자기좌표 방출·하드코딩 아님)"
  USE_AUTO=0
  PX=$(python3 -c "import json;g=json.load(open('$GEOM'));print('%d,%d,%d,%d'%tuple(g['physical']))")
  CELLP=$(python3 -c "import json;g=json.load(open('$GEOM'));print(g['cell_physical'])")
fi

# 실마우스클릭 폐루프 — 2단계로 나눠 [도중] 스샷이 진행 중간을 포착하게:
#   ① 오프닝무브 1사이클(중앙 첫 실클릭→flood-fill) → shot_2_mid(일부 열림) → ② 나머지 확정룰.
run_loop() {  # $1=cycles
  if [ "$USE_AUTO" -eq 1 ]; then
    "$BIN" --yes game minesweeper --cycles "$1" --click-scale "$SCALE" 2>&1 | sed 's/^/  /'
  else
    "$BIN" --yes game minesweeper --win "$PX" --cell "$CELLP" --rows 5 --cols 5 --cycles "$1" --click-scale "$SCALE" 2>&1 | sed 's/^/  /'
  fi
}
echo "[플레이] ① 오프닝무브(중앙 첫 실클릭)..."
run_loop 1
sleep 0.5
screencapture -x -R"$LOG" "$SHOTDIR/shot_2_mid.png" 2>/dev/null && echo "[스샷2] shot_2_mid(오프닝 직후·일부 열림)"
echo "[플레이] ② 확정룰 폐루프(cycles=12)..."
run_loop 12
sleep 0.5
screencapture -x -R"$LOG" "$SHOTDIR/shot_3_end.png" 2>/dev/null && echo "[스샷3] shot_3_end(폐루프 종료 최종)"

# 앱이 받은 클릭 수(실클릭 증명).
CLICKS=$(grep -cE "LEFT|RIGHT" "$SHOTDIR/pygame_app.log" 2>/dev/null || echo 0)
echo "[실증] pygame 앱이 수신한 실마우스클릭 $CLICKS 개(preopen 아님)"
kill $APP_PID 2>/dev/null
echo "완료. 스샷: $SHOTDIR/shot_{1_start,2_mid,3_end}.png"
