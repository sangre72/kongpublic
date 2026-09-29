#!/bin/bash
# u_5770: RL lane-keeping on ONE straight scoped section. page lock + park trap per standing rules.
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6
source ./chrome_guard.sh; chrome_guard "rl_lat" || exit 9
source ./park_page.sh
source ./pagelock.sh; lock_page "rl_lat" || { echo "PAGE BUSY"; exit 9; }
trap 'park_page; unlock_page' EXIT INT TERM HUP
T=/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp
F=${F:-삼성로}; TO=${TO:-봉은사로}; W=${W:-0.5}; ITERS=${ITERS:-12}
curl -s "http://localhost:8901/ctl?reset=1" -o /dev/null --max-time 5
bash reload.sh "http://localhost:8901/index.html?go=1&lab=1&from=$F&to=$TO" 90 2>&1 | tail -1 >/dev/null
echo "=== RL w=$W $F>$TO $(date +%H:%M:%S) ==="
RL_FROM=$F RL_TO=$TO python3 ppo_lat.py --init $T/ode_geo_wide.pt --out $T/ode_rl_w$W.pt --iters $ITERS --steps 250 --w $W 2>&1 | grep -vE "warn|scikit|Torch version"
echo RL_DONE
