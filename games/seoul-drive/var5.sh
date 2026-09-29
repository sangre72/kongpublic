#!/bin/bash
# u_5747(a): noise floor. N repeats of ema=0 on ONE route, identical harness.
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6 CU=CPU_AND_GPU
source ./chrome_guard.sh; chrome_guard "var5" || exit 9
source ./park_page.sh; trap park_page EXIT
source ./pagelock.sh; lock_page "var5" || { echo "PAGE BUSY"; exit 9; }; trap unlock_page EXIT
T=/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp; OUT=$T/var5_600.jsonl; : > $OUT
F=${F:-형촌6길}; TO=${TO:-역삼로78길}; SECS=${SECS:-300}; N=${N:-5}
for i in $(seq 1 $N); do
  n=$(pgrep -fl python3 | grep -Ec 'python3 (gpu_drive|train_|dagger)\.py'); [ "$n" -gt 0 ] && { echo "MPS_BUSY"; exit 2; }
  curl -s "http://localhost:8901/ctl?reset=1" -o /dev/null --max-time 5
  bash reload.sh "http://localhost:8901/index.html?go=1&from=$F&to=$TO&jay=5" 120 2>&1 | tail -1 >/dev/null
  wl=$(curl -s http://localhost:8901/tel | python3 -c "import sys,json;print(json.load(sys.stdin).get('wpLen') or 0)")
  [ "$wl" -gt 50 ] || { echo "route fail rep$i"; continue; }
  echo "=== rep$i secs=$SECS ($(date +%H:%M:%S)) ==="
  o=$(python3 gpu_drive.py --secs $SECS --speed $T/ode_v9.mlpackage --lp $T/ode_lp30cn.mlpackage --geo --lp-tier 2 --lp-vmax 8 2>&1 | grep -v -i 'warn\|scikit\|Torch' | tail -1)
  echo "{\"rep\":$i,\"secs\":$SECS,\"res\":$o}" >> $OUT
  echo "done rep$i"
done
echo VAR5_DONE
