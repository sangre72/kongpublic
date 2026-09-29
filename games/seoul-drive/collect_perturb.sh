#!/bin/bash
source /Users/bumsuklee/git/kong-bot/games/seoul-drive/park_page.sh; arm_park_trap   # u_5765: park on ANY exit
# 이탈→복귀 시연 수집(2026-09-20 u_5455). 교사 주행 + ?perturb=6 (6초마다 0.6~1.2초 조향 교란) + 프레임 푸시 13fps.
# 사용: bash collect_perturb.sh <시작라운드=300> <라운드수=3>   → data/dagger_r<r>/ (X,Y,W,M,P)
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8
NT=/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/notify_telegram.py
r=${1:-300}; N=${2:-3}; end=$((r+N))
while pgrep -f "dagger_loop.sh|dagger.py|stall_probe|run_regression|exp_speed60" >/dev/null; do sleep 30; done
while [ $r -lt $end ]; do
  pair=$(python3 -c "import json; p=json.load(open('pairs30.json')); q=p[($r-300)%len(p)]; print(q['from']+'|'+q['to'])")
  f="${pair%%|*}"; t="${pair##*|}"
  echo "=== perturb round $r : $f > $t ($(date +%H:%M:%S)) ==="
  bash reload.sh "http://localhost:8901/index.html?go=1&perturb=6&from=$f&to=$t" 120 2>&1 | tail -1
  if ! python3 -c "
import json,urllib.request,sys
d=json.load(urllib.request.urlopen('http://localhost:8901/tel',timeout=5)); sys.exit(0 if (d.get('wpLen') or 0)>100 and (d.get('perturbS') or 0)>0 else 1)"; then echo "route/perturb fail, skip"; r=$((r+1)); continue; fi
  rm -rf data/dagger_r$r
  python3 dagger.py --round $r --episodes 2 --secs 600 --model none 2>&1 | grep -E '"ep"|"round"|err|abort' | cut -c1-300 | tee /tmp/dagger_r$r.log
  pn=$(curl -s localhost:8901/tel | python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('perturbN'))")
  # ★한글을 -c 인자에 넣으면 nohup 환경에서 'surrogates not allowed'(2026-09-20 r301/302 보고 누락). 환경변수로 넘긴다.
  s=$(R=$r F="$f" T="$t" PN="$pn" python3 -c "
import json,os
r=os.environ['R']
try:
  st=json.load(open('data/dagger_r%s/episodes.json' % r)); fr=sum(e.get('frames',0) for e in st); cr=sum(e.get('crashes',0) for e in st)
  print('%s %s %s > %s: %s %d, %s %d, %s %s, %s %s' % ('\uad50\ub780 \ub77c\uc6b4\ub4dc', r, os.environ['F'], os.environ['T'], '\ud504\ub808\uc784', fr, '\uc0ac\uace0', cr, '\uad50\ub780', os.environ['PN'], '\uc9c4\ud589', [e.get('prog_max') for e in st]))
except Exception as e: print('round %s: no result (%s)' % (r, e))")
  echo "$s"; python3 $NT "[오드 수집·이탈복귀] $s" >/dev/null 2>&1
  r=$((r+1))
done
echo "=== perturb collection done $(date +%H:%M:%S) ==="
