#!/bin/bash
source /Users/bumsuklee/git/kong-bot/games/seoul-drive/park_page.sh; arm_park_trap   # u_5765: park on ANY exit
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
T=/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp
for W in 3 5 10; do
  n=$(pgrep -fl python3 | grep -Ec 'python3 (gpu_drive|train_|dagger)\.py'); while [ "$n" -gt 0 ]; do sleep 20; n=$(pgrep -fl python3 | grep -Ec 'python3 (gpu_drive|train_|dagger)\.py'); done
  echo "=== ONPOL_W=$W $(date +%H:%M:%S) ==="
  # u_5762: write the full log to a file; grep in a pipe buffers and hid all epoch output.
  GEO_GRU=0 ONPOL_W=$W python3 train_geo.py 'data/dagger_r3[567]*' $T/ode_geo_w$W.pt --epochs 8 --k 5 --init models/ode_lp30cn.pt > $T/onpw_$W.log 2>&1
  grep -E '"ep"|"done"' $T/onpw_$W.log | tail -9
done
echo ONPW_DONE
