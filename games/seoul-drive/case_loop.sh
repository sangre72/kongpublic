#!/bin/bash
# a_5588 addendum3: regression case 사평대로 oscillation section, sx/sy = 60m before, ×N, model T1, attribution trace
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive; export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6 CU=CPU_AND_GPU
T=/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp; N=${N:-5}; TAG=${TAG:-case_b}; SECS=${SECS:-90}
URL="http://localhost:8901/index.html?go=1&sx=-2928.7&sy=-3860.6&to=수정로35번길&jay=5"
for i in $(seq 1 $N); do n=$(pgrep -fl python3 | grep -Ec 'gpu_drive|offline_|train_|dagger'); [ "$n" -gt 0 ] && { echo "MPS_BUSY $n"; exit 2; }
  bash reload.sh "$URL" 120 2>&1 | tail -1 >/dev/null; sx=$(curl -s http://localhost:8901/tel | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('sxDbg'),'wpLen',d.get('wpLen'))"); echo "=== $TAG run$i ($(date +%H:%M:%S)) $sx ==="
  o=$(LP_TRACE=$T/tr/${TAG}_$i python3 gpu_drive.py --secs $SECS --speed $T/ode_v9.mlpackage $( [ "${M:-ode_mp3c8}" = none ] || echo "--lp $T/${M:-ode_mp3c8}.mlpackage" ) --lp-tier 1 2>&1 | grep -v -i 'warn\|scikit\|Torch version' | tail -1); echo "$o"
  echo "{\"tag\":\"$TAG\",\"run\":$i,\"res\":$o}" >> $T/case_results.jsonl
done; echo "${TAG}_DONE"
