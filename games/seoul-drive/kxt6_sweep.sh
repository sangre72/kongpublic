#!/bin/bash
# u_5740 (1): k_xt in {1.0, 0.0} x 6 scoped routes (2 alley / 2 two / 2 arterial), 300s each, prog-parity checked after.
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6 CU=CPU_AND_GPU
source ./chrome_guard.sh; chrome_guard "kxt6" || exit 9
source ./park_page.sh; arm_park_trap   # u_5765: EXIT+INT+TERM+HUP
source ./pagelock.sh; lock_page "kxt6" || { echo "PAGE BUSY"; exit 9; }; trap 'park_page; unlock_page' EXIT INT TERM HUP   # u_5765 fix3: one trap does BOTH (a second trap ... EXIT was silently replacing the park trap)
T=/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp; OUT=$T/kxt6.jsonl; : > $OUT; SECS=${SECS:-300}; VMAX=8
python3 -c "import json;[print(p['class']+'|'+p['from']+'|'+p['to']) for p in json.load(open('data/kxt6_pairs.json'))]" | while IFS='|' read -r cls f t; do
  for K in 1.0 0.0; do
    n=$(pgrep -fl python3 | grep -Ec 'python3 (gpu_drive|train_|dagger)\.py'); [ "$n" -gt 0 ] && { echo "MPS_BUSY $n"; exit 2; }
    curl -s "http://localhost:8901/ctl?reset=1" -o /dev/null --max-time 5
    bash reload.sh "http://localhost:8901/index.html?go=1&from=$f&to=$t&jay=5" 120 2>&1 | tail -1 >/dev/null
    wl=$(curl -s http://localhost:8901/tel | python3 -c "import sys,json;print(json.load(sys.stdin).get('wpLen') or 0)")
    [ "$wl" -gt 50 ] || { echo "route fail $f>$t"; continue; }
    echo "=== $cls $f>$t K=$K ($(date +%H:%M:%S)) wpLen $wl ==="
    o=$(K_XT=$K python3 gpu_drive.py --secs $SECS --speed $T/ode_v9.mlpackage --lp $T/ode_lp30cn.mlpackage --geo --lp-tier 2 --lp-vmax $VMAX 2>&1 | grep -v -i 'warn\|scikit\|Torch version' | tail -1)
    echo "{\"class\":\"$cls\",\"route\":\"$f>$t\",\"k_xt\":$K,\"res\":$o}" >> $OUT
    echo "done $cls K=$K"
  done
done
echo KXT6_DONE
