#!/usr/bin/env bash
# play_minesweeper.sh — kongtrol M7 지뢰찾기 원클릭 데모 (ADR 0007 폐루프).
# ★대상=네이티브 앱(브라우저 아님). 권한 프리플라이트 → 앱 구동 → 폐루프(인식→클릭) → 스크린샷.
#
# 사용:
#   ./play_minesweeper.sh              # 실화면 클릭 모드(화면기록+Accessibility 권한 필요, 실제 클릭)
#   ./play_minesweeper.sh --sense      # 실앱 캡처+인식만(화면기록 권한만, 클릭 없음)
#   ./play_minesweeper.sh --image      # 파일 이미지 모드(권한 불요, 인식·판단 파이프라인 실증)
#
# ★권한(macOS): 실화면+클릭 모드는 아래 2개 TCC 승인 필요(우회 금지 0004):
#   - 화면 기록: 시스템 설정 > 개인정보 보호 및 보안 > 화면 기록  → 터미널(또는 kongtrol) 추가
#   - 손쉬운 사용(Accessibility): 시스템 설정 > 개인정보 보호 및 보안 > 손쉬운 사용 → 터미널 추가
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEMO="$ROOT/demo"
BIN="$ROOT/target/release/kongtrol"
SHOTDIR="${TMPDIR:-/tmp}/kongtrol_play_shots"
mkdir -p "$SHOTDIR"

echo "== kongtrol 지뢰찾기 원클릭 데모 =="

# 0) 바이너리 준비
[ -x "$BIN" ] || { echo "빌드 중..."; (cd "$ROOT" && cargo build --release -q); }

MODE="${1:-screen}"

if [ "$MODE" = "--image" ]; then
  # ── 파일 이미지 모드: 권한 불요. 실제 격자 이미지로 인식→판단 실증 ──
  echo "[모드] 이미지 파일 (권한 불요, 인식·판단 파이프라인 실증)"
  IMG="$SHOTDIR/board_00.png"
  python3 "$DEMO/render_board.py" "$IMG" >/dev/null
  echo "[1] 실제 지뢰찾기 보드 렌더: $IMG"
  echo "[2] kongtrol 폐루프(인식→판단):"
  "$BIN" --yes game minesweeper --image "$IMG" --cell 80 --rows 5 --cols 5 --cycles 5 --sense-only
  echo "[3] 스크린샷(보드 이미지) = $IMG"
  echo "완료. 인식된 격자상태+판단좌표는 위 로그. 보드 이미지: $IMG"
  exit 0
fi

# ── 실앱 캡처 모드 결정 ──
# MODE=--sense : 화면기록 권한만으로 [실제 앱 창 캡처 + 인식(sense-only)] 완주(클릭 없음).
# MODE=screen  : 전체(Accessibility 필요 — 실제 클릭까지). 프리플라이트에서 미승인이면 안내·중단.
SENSE_ONLY=0
if [ "$MODE" = "--sense" ]; then SENSE_ONLY=1; fi

echo "[프리플라이트] 권한 체크..."
# 화면기록: kongtrol xcap 캡처가 실제 픽셀 얻는지(전부 검정이면 미승인)
CAP_OK=$("$BIN" --json --yes game minesweeper --win "0,0,80,80" --cell 40 --rows 1 --cols 1 --cycles 1 --sense-only 2>&1 | grep -c "사이클 완료\|numberCells\|cycle" || true)
if [ "$SENSE_ONLY" -eq 0 ]; then
  # Accessibility: enigo 실제 클릭 시도 → PermissionDenied면 미승인
  ACC_OUT=$("$BIN" --yes game minesweeper --win "0,0,80,80" --cell 40 --rows 1 --cols 1 --cycles 1 2>&1 || true)
  if echo "$ACC_OUT" | grep -q "권한 부족"; then
    echo "  ✗ Accessibility(손쉬운 사용) 미승인 → 실제 클릭 불가."
    echo "    승인: 시스템 설정 > 개인정보 보호 및 보안 > 손쉬운 사용 → 터미널 추가 후 재실행."
    echo "    (우회 안 함 — 0004 보안 원칙). 클릭 없이 실앱 캡처+인식만: $0 --sense · 순수 파이프라인: $0 --image"
    exit 3
  fi
fi
echo "  ✓ 권한 OK($([ "$SENSE_ONLY" -eq 1 ] && echo '화면기록만·인식모드' || echo '화면기록+손쉬운사용·클릭모드')). 앱 구동..."

# 앱 띄우기(네이티브 Tkinter). 앱이 [실제 창 물리좌표 + backing scale] 을 app_geom.json 으로 방출.
# ★모드별 초기 보드:
#   screen(실클릭) = --preopen 없음(전부 닫힘) → kongtrol 오프닝무브가 실제 첫 셀을 클릭해 게임 시작.
#   --sense(클릭없음) = --preopen 으로 숫자 열린 플레이 화면 재현(클릭 못 하므로 상태 시드).
GEOM="$SHOTDIR/app_geom.json"
rm -f "$GEOM"  # 이전 실행 잔재 제거(폴링이 옛 좌표 오독 방지)
if [ "$SENSE_ONLY" -eq 1 ]; then
  PREOPEN_ARGS=(--preopen "0,0;1,0;1,1;0,2;1,2;2,0;2,1;2,2;3,0")
else
  PREOPEN_ARGS=()  # 실클릭 모드: 빈 보드에서 오프닝무브가 실제로 열어감
fi
MS_GEOM_FILE="$GEOM" \
  python3 "$DEMO/minesweeper_app.py" "${PREOPEN_ARGS[@]+"${PREOPEN_ARGS[@]}"}" \
  >"$SHOTDIR/app.log" 2>&1 &
APP_PID=$!

# ★geometry 파일 폴링 대기(최대 8s) — 고정 sleep 대신 실제 방출 시점까지 대기(근본).
#   앱이 원자적 rename 으로 쓰므로 파일 존재=완전한 JSON.
echo -n "[대기] geometry 방출"
for _ in $(seq 1 40); do
  [ -f "$GEOM" ] && break
  echo -n "."; sleep 0.2
done
echo
if [ ! -f "$GEOM" ]; then echo "  ✗ geometry 방출 실패(8s 초과·앱 로그: $SHOTDIR/app.log)"; kill $APP_PID 2>/dev/null; exit 4; fi
PX=$(python3 -c "import json;g=json.load(open('$GEOM'));print('%d,%d,%d,%d'%tuple(g['physical']))")
CELLP=$(python3 -c "import json;g=json.load(open('$GEOM'));print(g['cell_physical'])")
LOG=$(python3 -c "import json;g=json.load(open('$GEOM'));l=g['logical'];print('%d,%d,%d,%d'%(l[0],l[1],l[2],l[3]))")
# ★scale = 캡처(물리)↔클릭(논리) 변환 배수. 클릭 좌표는 물리÷scale 로 논리화(enigo 는 논리pt).
SCALE=$(python3 -c "import json;print(json.load(open('$GEOM'))['scale'])")
echo "[좌표] 실물리=$PX cell=$CELLP scale=$SCALE (논리=$LOG)"

# ★앱 창만 캡처: screencapture -R 논리영역 crop(Z-order 무관하게 해당 사각영역).
#   [이상적]으로는 `screencapture -l <CGWindowID>` 가 창만 정확 캡처(데스크톱 잡음 0)이나,
#   Tkinter 는 CGWindowID 를 직접 노출하지 않음 → -R 창영역 crop 로 차선(현실적 최선).
SHOT="$SHOTDIR/live_play.png"
screencapture -x -R"$LOG" "$SHOT" 2>/dev/null && echo "[스샷] 실제 플레이 앱 창: $SHOT" || echo "[스샷] 실패(화면기록 권한 확인)"
if [ "$SENSE_ONLY" -eq 1 ]; then
  echo "[인식] kongtrol 실앱 캡처→인식(클릭 없음, 화면기록 권한만):"
  "$BIN" --yes game minesweeper --win "$PX" --cell "$CELLP" --rows 5 --cols 5 --cycles 3 --sense-only
else
  echo "[플레이] kongtrol 폐루프 실행(캡처→인식→오프닝무브→실제 클릭, cycles=12):"
  "$BIN" --yes game minesweeper --win "$PX" --cell "$CELLP" --rows 5 --cols 5 \
    --cycles 12 --click-scale "$SCALE"
  # 클릭 후 최종 스샷(셀 열려 숫자 드러난 상태 포착)
  screencapture -x -R"$LOG" "$SHOTDIR/live_play_final.png" 2>/dev/null && echo "[스샷] 클릭 후(숫자 열림): $SHOTDIR/live_play_final.png"
fi
kill $APP_PID 2>/dev/null
echo "완료. 스크린샷: $SHOTDIR/"
