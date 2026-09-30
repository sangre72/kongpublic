#!/usr/bin/env bash
# u_5780: report frames / class mix / distinct roads / running ey gap every 20 episodes, unattended.
cd "$(dirname "${BASH_SOURCE[0]}")"
NT=/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/notify_telegram.py
LAST=0
while pgrep -f collect_onpolicy.sh >/dev/null; do
  N=$(ls -d data/dagger_r38*/S.npy 2>/dev/null | wc -l | tr -d ' ')
  if [ "$N" -ge $((LAST+20)) ]; then
    LAST=$N
    FR=$(python3 -c "
import numpy as np,glob
print(sum(np.load(d+'/L.npy',mmap_mode='r').shape[0] for d in sorted(glob.glob('data/dagger_r38*'))))" 2>/dev/null)
    CH=$(grep -E 'CLASS-HIST' /tmp/onpol_5780.log | tail -1)
    CV=$(python3 coverage.py 'data/dagger_r38*' 2>/dev/null | head -1)
    GAP=$(KSTACK=5 python3 geo_gap.py models/ode_geo_wide.pt 'data/dagger_r38*' 'data/dagger_r36*' 2>/dev/null \
          | grep ratio_model_over_rule | python3 -c "
import sys,json
try: print('ey ratio', json.loads(sys.stdin.read())['ratio_model_over_rule']['ey'])
except Exception: print('ey ratio n/a')")
    python3 $NT "[ODE onpolicy] $N eps / frames $FR | $CH | $CV | $GAP | df $(df -g / | awk 'NR==2{print $4}')GB" >/dev/null 2>&1 || true
    echo "PROGRESS $N eps frames=$FR $GAP" >> /tmp/onpol_progress.log
  fi
  sleep 120
done
echo "collector gone at $(ls -d data/dagger_r38*/S.npy 2>/dev/null | wc -l) eps" >> /tmp/onpol_progress.log
