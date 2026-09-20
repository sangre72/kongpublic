#!/bin/bash
# 수집 관문(오너 u_5476, 2026-09-20): 교사(GEOM) 주행이 대표 3구간×300초에서 사고 0·순간이동 0 이어야 수집 가능.
#   (a) GEOM 직접 주행  (b) --model pipe (모델 파이프 경유, 13fps). 둘 다 통과해야 함. 사용: bash teacher_gate.sh [초=300]
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6
NT=/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/notify_telegram.py
SECS=${1:-300}; R=600; out=""
for pair in "사평대로|수정로35번길" "기아자동차강남지점|부림3길" "충정로7길|수정로35번길"; do
  f="${pair%%|*}"; t="${pair##*|}"
  for mode in none pipe; do
    bash reload.sh "http://localhost:8901/index.html?go=1&from=$f&to=$t" 60 2>&1 | tail -1 >/dev/null
    rm -rf data/dagger_r$R
    python3 dagger.py --round $R --episodes 1 --secs $SECS --model $mode 2>&1 | grep -E '"ep"' | cut -c1-400 > /tmp/gate_$R.log
    s=$(python3 -c "
import json
try:
  e=json.loads(open('/tmp/gate_$R.log').read().strip().splitlines()[-1]); print('%s %s: 사고 %d %s 순간이동 %s 진행 %.1f%%' % ('$f', 'GEOM' if '$mode'=='none' else 'PIPE', e['crashes'], e['crash_types'], e.get('tpN'), 100*e.get('prog_max',0)))
except Exception as x: print('$f $mode: no result', x)")
    echo "$s"; out="$out
$s"; R=$((R+1))
  done
done
python3 $NT "[교사 관문 ${SECS}초] $out" >/dev/null 2>&1
echo "GATE_DONE"
