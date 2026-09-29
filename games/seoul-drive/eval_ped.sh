#!/bin/bash
source /Users/bumsuklee/git/kong-bot/games/seoul-drive/park_page.sh; arm_park_trap   # u_5765: park on ANY exit
# 보행자 회피 회귀(2026-09-22): 3구간×300초, 무단횡단 배율 ?jay=N. 사용: bash eval_ped.sh <model.pt> <round0> "<extra url params>" <tag>
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6
M=$1; R=$2; X=$3; TAG=$4; DA=$5; out=""   # DA = dagger 추가 인자(예: "--lp ode_lp5.pt")
for pair in "사평대로|수정로35번길" "기아자동차강남지점|부림3길" "충정로7길|수정로35번길"; do
  f="${pair%%|*}"; t="${pair##*|}"
  bash reload.sh "http://localhost:8901/index.html?go=1&from=$f&to=$t&$X" 60 2>&1 | tail -1 >/dev/null
  rm -rf data/dagger_r$R
  python3 dagger.py --round $R --episodes 1 --secs 300 --model $M $DA 2>&1 | grep -E '"ep"|Error|Traceback|Killed' > /tmp/evalped_$R.log
  pp=$(curl -s localhost:8901/tel | python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('pedPredN'),d.get('jayMult'))")
  s=$(F="$f" PP="$pp" python3 -c "
import json,os
try:
  e=json.loads([l for l in open('/tmp/evalped_$R.log') if '\"ep\"' in l][-1]); ct=e['crash_types']; av=sum(v for k,v in ct.items() if '불가항력' not in k)
  print('%s: 회피가능 %d(불가항력 %d) 복귀 %s 진행 %.1f%% pred/jay=%s lp/rule=%s/%s %s' % (os.environ['F'], av, e['crashes']-av, e.get('tpN'), 100*e.get('prog_max',0), os.environ['PP'], e.get('lp_frames'), e.get('rule_steer_frames'), ct))
except Exception as x: print('%s: no result %s' % (os.environ['F'], x))")
  echo "$s"; out="$out | $s"; R=$((R+1))
done
echo "EVALPED $TAG $M:$out"
