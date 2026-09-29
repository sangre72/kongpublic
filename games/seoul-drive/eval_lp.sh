#!/bin/bash
source /Users/bumsuklee/git/kong-bot/games/seoul-drive/park_page.sh; arm_park_trap   # u_5765: park on ANY exit
# 앞점 모델 공정 비교(2026-09-21): 3구간×300초, 사고(회피가능)·순간이동·진행률. 사용: bash eval_lp.sh <model.pt> [round0=650]
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6
M=$1; R=${2:-650}; out=""
for pair in "사평대로|수정로35번길" "기아자동차강남지점|부림3길" "충정로7길|수정로35번길"; do
  f="${pair%%|*}"; t="${pair##*|}"
  bash reload.sh "http://localhost:8901/index.html?go=1&from=$f&to=$t" 60 2>&1 | tail -1 >/dev/null
  rm -rf data/dagger_r$R
  python3 dagger.py --round $R --episodes 1 --secs 300 --model $M 2>&1 | grep -E '"ep"' > /tmp/eval_$R.log
  s=$(F="$f" python3 -c "
import json,os
try:
  e=json.loads(open('/tmp/eval_$R.log').read().strip().splitlines()[-1]); ct=e['crash_types']; av=sum(v for k,v in ct.items() if '불가항력' not in k)
  print('%s: 회피가능사고 %d(불가항력 %d) 복귀 %s 진행 %.1f%%' % (os.environ['F'], av, e['crashes']-av, e.get('tpN'), 100*e.get('prog_max',0)))
except Exception as x: print('%s: no result %s' % (os.environ['F'], x))")
  echo "$s"; out="$out | $s"; R=$((R+1))
done
echo "EVAL $M:$out"
