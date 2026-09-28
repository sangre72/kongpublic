#!/bin/bash
# a_5598 eval20 harness: 미학습 20구간 × 300초, 모델 T1 조향(--geo), 무단횡단 5, v9 속도. 사용: M=<mlpackage basename> TAG=<tag> [GEO=1] bash eval20.sh → $T/eval20_<tag>.jsonl ; 요약 python3 eval20_sum.py <tag>
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive; export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6 CU=CPU_AND_GPU
source "$(dirname "$0")/chrome_guard.sh"; chrome_guard "$(basename "$0")" || exit 9
source "$(dirname "$0")/park_page.sh"; trap park_page EXIT
source "$(dirname "$0")/pagelock.sh"; lock_page "$(basename "$0")" || { echo "PAGE BUSY - abort (see PLAN_ODE standing rule)"; exit 9; }; trap unlock_page EXIT
T=/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp; M=${M:-none}; TAG=${TAG:-e20}; GEO=${GEO:-1}; OUT=$T/eval20_$TAG.jsonl; SECS=${SECS:-300}
python3 -c "import json;[print(p['from']+'|'+p['to']) for p in json.load(open('data/eval20_scope_pairs.json'))]" | while IFS='|' read -r f t; do
  n=$(pgrep -fl python3 | grep -Ec 'python3 (gpu_drive|offline_lp_eval|train_lp|train_geo|train_bev|train_seg|train_stage|dagger|offline_gate|seg_gate)\.py'); [ "$n" -gt 0 ] && { echo "MPS_BUSY $n"; exit 2; }
  bash reload.sh "http://localhost:8901/index.html?go=1&from=$f&to=$t&jay=5${HUD:+&hud=$HUD}${EXTRA_Q}" 120 2>&1 | tail -1 >/dev/null
  wl=$(curl -s http://localhost:8901/tel | python3 -c "import sys,json;print(json.load(sys.stdin).get('wpLen') or 0)"); [ "$wl" -gt 50 ] || { echo "route fail $f>$t"; echo "{\"tag\":\"$TAG\",\"route\":\"$f>$t\",\"res\":null}" >> $OUT; continue; }
  echo "=== $TAG $f > $t ($(date +%H:%M:%S)) wpLen $wl ==="
  o=$(LP_TRACE=$T/tr/${TAG} python3 gpu_drive.py --secs $SECS --speed $T/ode_v9.mlpackage $( [ "$M" = none ] || echo "--lp $T/$M.mlpackage" ) $( [ "$GEO" = 1 ] && [ "$M" != none ] && echo "--geo" ) --lp-tier ${LPT:-2} ${VMAX:+--lp-vmax $VMAX} 2>&1 | grep -v -i 'warn\|scikit\|Torch version' | tail -1); echo "$o" | cut -c1-200
  echo "{\"tag\":\"$TAG\",\"route\":\"$f>$t\",\"res\":$o}" >> $OUT
done; echo "EVAL20_${TAG}_DONE"
