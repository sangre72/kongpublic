#!/bin/bash
# u_5771 long unattended RL run: 150 episodes, checkpoint + curve every 10.
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6
source ./chrome_guard.sh; chrome_guard "rl_blend" || exit 9
source ./park_page.sh
source ./pagelock.sh; lock_page "rl_blend" || { echo "PAGE BUSY"; exit 9; }
trap 'park_page; unlock_page' EXIT INT TERM HUP
T=/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp
F=${F:-삼성로}; TO=${TO:-봉은사로}
echo "=== RL BLEND w=0.5 ent=0.05 std_lr=1e-2 clip=0.3 $(date +%H:%M:%S) ==="
RL_FROM=$F RL_TO=$TO W=0.5 ENT_C=0.05 STD_LR=1e-2 STD_MAX=0.5 STD_TGT=0.35 \
  python3 ppo_lat.py --init $T/ode_geo_wide.pt --out $T/ode_rl_blend.pt --iters 200 --steps 250 --w 0.5 2>&1 \
  | grep -vE "warn|scikit|Torch version"
echo RL_LONG_DONE
