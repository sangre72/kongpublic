#!/bin/bash
source /Users/bumsuklee/git/kong-bot/games/seoul-drive/park_page.sh; arm_park_trap   # u_5765: park on ANY exit
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
T=/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp
for LAM in 0.1 1 10 100; do
  n=$(pgrep -fl python3 | grep -Ec 'python3 (gpu_drive|train_|dagger)\.py'); while [ "$n" -gt 0 ]; do sleep 20; n=$(pgrep -fl python3 | grep -Ec 'python3 (gpu_drive|train_|dagger)\.py'); done
  echo "=== lambda=$LAM $(date +%H:%M:%S) ==="
  python3 train_cmd_tc.py 'data/dagger_r3[56]*' $T/ode_cmd_tc_$LAM.pt --lam $LAM --epochs 6 --seq 32 --k 5 --init models/ode_lp30cn.pt 2>&1 | grep -E '"ep"|"lam"|"done"|Error|Traceback'
done
echo TC_SWEEP_DONE
