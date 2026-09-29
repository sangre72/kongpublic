#!/bin/bash
# u_5748: speed-scheduled tau vs ema=0, 3 routes x 3 repeats, 300s. Judged on amp (primary).
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6 CU=CPU_AND_GPU
source ./chrome_guard.sh; chrome_guard "n3" || exit 9
source ./park_page.sh; trap park_page EXIT
source ./pagelock.sh; lock_page "n3" || { echo "PAGE BUSY"; exit 9; }; trap unlock_page EXIT
T=/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp; OUT=$T/stema_n3.jsonl; : > $OUT; SECS=${SECS:-300}; REPS=${REPS:-3}
python3 -c "import json;[print(p['class']+'|'+p['from']+'|'+p['to']) for p in json.load(open('data/stema3_pairs.json'))]" | while IFS='|' read -r cls f t; do
  for i in $(seq 1 $REPS); do
    for E in 0 auto; do
      n=$(pgrep -fl python3 | grep -Ec 'python3 (gpu_drive|train_|dagger)\.py'); [ "$n" -gt 0 ] && { echo "MPS_BUSY"; exit 2; }
      curl -s "http://localhost:8901/ctl?reset=1" -o /dev/null --max-time 5
      Q=""; [ "$E" != "0" ] && Q="&stema=$E"
      bash reload.sh "http://localhost:8901/index.html?go=1&from=$f&to=$t&jay=5$Q" 120 2>&1 | tail -1 >/dev/null
      wl=$(curl -s http://localhost:8901/tel | python3 -c "import sys,json;print(json.load(sys.stdin).get('wpLen') or 0)")
      [ "$wl" -gt 50 ] || { echo "route fail $f>$t"; continue; }
      echo "=== $cls rep$i ema=$E ($(date +%H:%M:%S)) ==="
      o=$(python3 gpu_drive.py --secs $SECS --speed $T/ode_v9.mlpackage --lp $T/ode_lp30cn.mlpackage --geo --lp-tier 2 --lp-vmax 8 2>&1 | grep -v -i 'warn\|scikit\|Torch' | tail -1)
      echo "{\"class\":\"$cls\",\"rep\":$i,\"stema\":\"$E\",\"res\":$o}" >> $OUT
      echo "done $cls rep$i ema=$E"
    done
  done
done
echo STEMA_N3_DONE
