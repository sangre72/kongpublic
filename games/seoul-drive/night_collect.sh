#!/bin/bash
# 새 화면(카메라 리드 25m) 기준 새 데이터셋 수집(u_5548, 2026-09-22 밤): 규칙 주행 600초 + 교란(?perturb=6) 복귀 600초를 구간마다 번갈아. 라벨 = 조향·속도·vmax·10/20/40/80m 앞점(L.npy 7열)·M(의도). 07:00 정지.
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6 M_EXT=1 ODE_ENV=0
NT=/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/notify_telegram.py
r=${1:-1100}; n=0
python3 $NT "[새 데이터 수집] 시작 $(date +%H:%M) 카메라 리드 25m, 규칙 600초 + 교란 600초 교대, 07:00 까지" >/dev/null 2>&1
while [ "$(date +%H)" -ge 19 ] || [ "$(date +%H)" -lt 7 ]; do
  [ "$(df -g / | tail -1 | awk '{print $4}')" -lt 25 ] && { python3 $NT "[새 데이터 수집] 디스크 25GB 미만 → 정지"; break; }
  pair=$(python3 -c "import json; p=json.load(open('pairs30.json')); q=p[$n%len(p)]; print(q['from']+'|'+q['to'])"); f="${pair%%|*}"; t="${pair##*|}"
  for mode in plain perturb; do
    extra=""; [ $mode = perturb ] && extra="&perturb=6"
    echo "=== r$r $mode $f > $t ($(date +%H:%M:%S)) ==="
    bash reload.sh "http://localhost:8901/index.html?go=1&from=$f&to=$t$extra" 120 2>&1 | tail -1
    python3 -c "
import json,urllib.request,sys
d=json.load(urllib.request.urlopen('http://localhost:8901/tel',timeout=5)); sys.exit(0 if (d.get('wpLen') or 0)>100 else 1)" || { echo "route fail"; r=$((r+1)); continue; }
    rm -rf data/dagger_r$r
    python3 dagger.py --round $r --episodes 1 --secs 600 --model none 2>&1 | grep -E '"ep"|Traceback|Error|Killed' | cut -c1-240
    r=$((r+1))
  done
  n=$((n+1))
  [ $((n % 3)) = 0 ] && python3 $NT "[새 데이터 수집] $n 구간 완료(라운드 r$r 까지), $(date +%H:%M)" >/dev/null 2>&1
done
pkill -x "Google Chrome"; echo "=== collect end $(date +%H:%M:%S) r=$r ==="; python3 $NT "[새 데이터 수집] 종료 $(date +%H:%M), 마지막 라운드 r$((r-1))" >/dev/null 2>&1
