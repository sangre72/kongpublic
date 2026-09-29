#!/bin/bash
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6 CU=CPU_AND_GPU
source ./chrome_guard.sh; chrome_guard "rec_cmd" || exit 9
source ./park_page.sh; trap park_page EXIT
source ./pagelock.sh; lock_page "rec_cmd" || { echo "PAGE BUSY"; exit 9; }; trap unlock_page EXIT
T=/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp
curl -s "http://localhost:8901/ctl?reset=1" -o /dev/null --max-time 5
bash reload.sh "http://localhost:8901/index.html?go=1&from=강동대로&to=삼학사로14길&jay=5" 120 2>&1 | tail -1 >/dev/null
echo "=== rec ($(date +%H:%M:%S)) ==="
LP_TRACE=$T/cmdtr K_XT=1.0 python3 gpu_drive.py --secs 300 --speed $T/ode_v9.mlpackage --lp $T/ode_lp30cn.mlpackage --geo --lp-tier 2 --lp-vmax 8 2>&1 | grep -v -i 'warn\|scikit\|Torch' | tail -1
echo REC_DONE
