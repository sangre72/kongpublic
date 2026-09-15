#!/bin/bash
# 오드 v2 커리큘럼 수집 (u_5144)
# 오너: "회피 추월 정지 각도별 회전 등등 필요하겠내"
#
# ★왜 커리큘럼인가: 그냥 달리면 좌회전·정지·추월이 거의 안 나온다.
#   실측(기존 고유 21,677): 좌회전 108 / 우회전 10,142 / 정지 71 / 이탈 68 / 사고 3.
#   교사에게 '이 상황을 하라'고 시켜야 그 라벨이 생긴다.
#
# 각 단계는 빌드 플래그·교사 모드를 바꿔 그 상황만 집중 수집한다.
set -e
ROOT=/Users/bumsuklee/git/kong-bot
cd "$ROOT"
SECS=${1:-300}

run() {  # run <이름> <빌드옵션> <교사모드> <초>
  local name=$1 opts=$2 mode=$3 secs=$4
  echo "=== $name (${secs}s) opts='$opts' mode=$mode ==="
  python3 games/seoul-drive/build.py --traffic heavy --speed 65 $opts >/dev/null
  bash games/seoul-drive/reload.sh
  open -a "Google Chrome" >/dev/null; sleep 3
  # 교사 모드 지정(localStorage 를 통해 300ms 내 반영됨)
  curl -s -X POST -d "{\"on\":1,\"force\":1,\"teach\":\"$mode\"}" http://localhost:8901/ctl >/dev/null || true
  sleep 2
  python3 games/seoul-drive/collect_avoid.py "games/seoul-drive/data/ode_$name" "$secs" || true
}

run straight ""                  fwd   "$SECS"   # 직진 기준
run left     ""                  left  "$SECS"   # ★좌회전 — 현재 108장뿐
run right    ""                  right "$SECS"   # 우회전 균형
run lanechg  "--lanedemo"        fwd   "$SECS"   # 차로변경
run overtake "--collect-ot"      fwd   "$SECS"   # ★추월
run stopgo   "--sigdemo"         fwd   "$SECS"   # ★정지→출발
run recover  "--collect-recover" fwd   "$SECS"   # ★이탈 복구

echo "=== 수집 완료 ==="
du -sh games/seoul-drive/data/ode_* 2>/dev/null
