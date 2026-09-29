#!/bin/bash
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
T=/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp
for W in 0.1 0.5 2.0; do
  n=$(pgrep -fl python3 | grep -Ec 'python3 (gpu_drive|train_|dagger|ppo_lat)\.py'); while [ "$n" -gt 0 ]; do sleep 20; n=$(pgrep -fl python3 | grep -Ec 'python3 (gpu_drive|train_|dagger|ppo_lat)\.py'); done
  echo "=== W=$W $(date +%H:%M:%S) ==="
  ITERS=15 W=$W bash ./rl_lat.sh 2>&1 | grep -E '"iter"|"done"|"init"|RL_DONE'
done
echo RL_SWEEP_DONE
