#!/bin/bash
# 가상 상태 샘플링 수집(오너 u_5467, 2026-09-20). ?synth=1: 150ms 마다 경로 위 임의 상태 → 프레임+라벨(X-Lbl) 푸시. 주행·교란·진행 판정 없음.
# 사용: bash collect_synth.sh <시작라운드=400> <라운드수=6> [초=600]  → data/dagger_r<r>/
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=${ODE_CROP:-0.6}
NT=/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/notify_telegram.py
r=${1:-400}; N=${2:-6}; SECS=${3:-600}; end=$((r+N))
while [ $r -lt $end ]; do
  pair=$(python3 -c "import json; p=json.load(open('pairs30.json')); q=p[($r-400)%len(p)]; print(q['from']+'|'+q['to'])")
  f="${pair%%|*}"; t="${pair##*|}"
  echo "=== synth round $r : $f > $t ($(date +%H:%M:%S)) ==="
  bash reload.sh "http://localhost:8901/index.html?go=1&synth=1&from=$f&to=$t" 120 2>&1 | tail -1
  if ! python3 -c "
import json,urllib.request,sys
d=json.load(urllib.request.urlopen('http://localhost:8901/tel',timeout=5)); sys.exit(0 if (d.get('wpLen') or 0)>100 and d.get('synth') else 1)"; then echo "route/synth fail, skip"; r=$((r+1)); continue; fi
  rm -rf data/dagger_r$r
  python3 dagger.py --round $r --episodes 1 --secs $SECS --model none 2>&1 | grep -E '"ep"|"round"|err|abort' | cut -c1-300 | tee /tmp/dagger_r$r.log
  s=$(R=$r F="$f" T="$t" python3 -c "
import json,os
r=os.environ['R']
try:
  st=json.load(open('data/dagger_r%s/episodes.json' % r)); fr=sum(e.get('frames',0) for e in st)
  print('synth round %s %s > %s: frames %d, label_src %s' % (r, os.environ['F'], os.environ['T'], fr, st[0].get('label_src')))
except Exception as e: print('round %s: no result (%s)' % (r, e))")
  echo "$s"; python3 $NT "[오드 가상수집] $s" >/dev/null 2>&1
  r=$((r+1))
done
echo "=== synth collection done $(date +%H:%M:%S) ==="
