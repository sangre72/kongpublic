#!/usr/bin/env bash
# verify_locator.sh — a_15 화면 시각탐지 locator 실증(EXPECTED 3).
# ★네이티브 지뢰찾기 앱을 [화면 3위치]에 옮겨 띄우고, 각 위치에서 kongtrol locator 자동탐지
#   (--win 없이 전체화면 캡처→탐지)가 성공하는지 + 탐지 Region 을 전체화면 스샷에 빨간 박스로
#   오버레이해 "제대로 찾았음"을 증명한다. 좌표 받아쓰기 폐기(u_15) — 화면만 보고 창을 찾음.
#
# 사용: bash demo/verify_locator.sh
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEMO="$ROOT/demo"
BIN="$ROOT/target/release/kongtrol"
SHOTDIR="${TMPDIR:-/tmp}/kongtrol_play_shots"
mkdir -p "$SHOTDIR"

[ -x "$BIN" ] || { echo "✗ 바이너리 없음: $BIN (cargo build --release 필요)"; exit 1; }

# 창을 옮길 3위치(논리좌표). 창 400x400 논리 → 화면(논리 2056x1329) 안에 들도록.
POSITIONS=("80,80" "800,450" "1500,850")
LABELS=("좌상" "중앙" "우하")

cleanup() { pkill -f "demo/minesweeper_app.py" 2>/dev/null || true; }
trap cleanup EXIT

ok=0
declare -a SUMMARY

for i in "${!POSITIONS[@]}"; do
  pos="${POSITIONS[$i]}"
  label="${LABELS[$i]}"
  echo "== [$((i+1))/3] $label 위치 $pos =="

  cleanup; sleep 1
  MS_WINPOS="$pos" MS_GEOM_FILE="$SHOTDIR/geom_$i.json" \
    python3 "$DEMO/minesweeper_app.py" >"$SHOTDIR/app_verify_$i.log" 2>&1 &
  sleep 4  # 창 렌더 + 최전면

  # kongtrol 자동탐지(--win 없이 → locator). stderr 의 [locator] region 파싱.
  det_line=$("$BIN" --yes game minesweeper --cycles 1 --sense-only 2>&1 \
    | grep -m1 "\[locator\] 자동탐지" || true)

  full="$SHOTDIR/locator_verify_$i.png"
  if [ -z "$det_line" ]; then
    echo "  ✗ 탐지 실패(locator None). 앱로그: $SHOTDIR/app_verify_$i.log"
    SUMMARY+=("$label $pos: 탐지실패")
    cleanup
    continue
  fi

  # region=(x,y,w,h) 추출.
  region=$(echo "$det_line" | sed -E 's/.*region=\(([0-9]+),([0-9]+),([0-9]+),([0-9]+)\).*/\1 \2 \3 \4/')
  read -r rx ry rw rh <<<"$region"
  echo "  ✓ 탐지: region=($rx,$ry,$rw,$rh) — $det_line"

  # 전체화면 스샷(물리) → 탐지 region(물리좌표)에 빨간 박스 오버레이.
  raw="$SHOTDIR/_full_$i.png"
  screencapture -x "$raw" 2>/dev/null
  MS_BOX="$rx,$ry,$rw,$rh" MS_IN="$raw" MS_OUT="$full" MS_LABEL="$label $pos" \
    python3 "$DEMO/overlay_box.py" \
    && echo "  [스샷] 박스 오버레이: $full" \
    || echo "  [스샷] 오버레이 실패(원본: $raw)"
  rm -f "$raw"

  # 실제 앱 논리좌표(geom)와 비교(오차 참고).
  if [ -f "$SHOTDIR/geom_$i.json" ]; then
    phys=$(python3 -c "import json;g=json.load(open('$SHOTDIR/geom_$i.json'));print('%d,%d,%d,%d'%tuple(g['physical']))" 2>/dev/null || echo "?")
    echo "  실제 앱 물리좌표(geom)=$phys vs 탐지=($rx,$ry,$rw,$rh)"
    SUMMARY+=("$label $pos: 탐지성공 region=($rx,$ry,$rw,$rh) 실제=$phys")
  else
    SUMMARY+=("$label $pos: 탐지성공 region=($rx,$ry,$rw,$rh)")
  fi
  ok=$((ok+1))
  cleanup
done

echo
echo "===== 요약: 3위치 중 $ok 개 탐지 성공 ====="
for s in "${SUMMARY[@]}"; do echo " - $s"; done
echo "스샷 디렉토리: $SHOTDIR/ (locator_verify_0~2.png)"
