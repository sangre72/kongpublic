#!/bin/bash
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6 CU=CPU_AND_GPU
source ./chrome_guard.sh; chrome_guard "rec_cmd" || exit 9
source ./park_page.sh; arm_park_trap   # u_5765: EXIT+INT+TERM+HUP
source ./pagelock.sh; lock_page "rec_cmd" || { echo "PAGE BUSY"; exit 9; }; trap 'park_page; unlock_page' EXIT INT TERM HUP   # u_5765 fix3: one trap does BOTH (a second trap ... EXIT was silently replacing the park trap)
T=/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp
curl -s "http://localhost:8901/ctl?reset=1" -o /dev/null --max-time 5
bash reload.sh "http://localhost:8901/index.html?go=1&from=강동대로&to=삼학사로14길&jay=5" 120 2>&1 | tail -1 >/dev/null
echo "=== rec ($(date +%H:%M:%S)) ==="
LP_TRACE=$T/cmdtr K_XT=1.0 python3 gpu_drive.py --secs 300 --speed $T/ode_v9.mlpackage --lp $T/ode_lp30cn.mlpackage --geo --lp-tier 2 --lp-vmax 8 2>&1 | grep -v -i 'warn\|scikit\|Torch' | tail -1
echo REC_DONE
