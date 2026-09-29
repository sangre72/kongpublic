#!/bin/bash
source /Users/bumsuklee/git/kong-bot/games/seoul-drive/park_page.sh; arm_park_trap   # u_5765: park on ANY exit
# a_5598 COMMON collector(2026-09-23): 전 지도 무작위 구간(search.js road 이름 쌍, 1.5~5km, 홀드아웃 청크+이웃 제외) + ?perturb=6 조향 교란 → 규칙 주행(dagger --model none) L12 라벨.
# 사용: bash collect_random.sh <시작라운드=2000> <에피소드수=60> [초=90]   → data/dagger_r<r>/ (X Y W M P Q L T + L.npy 12열)
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive; export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6 L12=1 M_EXT=1 ODE_ENV=0
NT=/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/notify_telegram.py; r=${1:-2000}; N=${2:-60}; SECS=${3:-90}; done=0; tot=0
for i in $(seq 1 $N); do
  [ "$(df -g / | tail -1 | awk '{print $4}')" -lt 30 ] && { echo "DISK<30GB stop"; python3 $NT "[오드 수집] 디스크 30GB 미만 → 정지" >/dev/null 2>&1; break; }
  n=$(pgrep -fl python3 | grep -Ec 'python3 (gpu_drive|offline_lp_eval|train_lp|train_geo|train_stage|dagger)\.py'); [ "$n" -gt 0 ] && { echo "MPS_BUSY $n"; exit 2; }
  pair=$(python3 - <<'PY'
import json,random,math,collections
s=open('data/search.js').read(); rows=json.loads(s[s.index('=')+1:].rstrip().rstrip(';')); roads=[r for r in rows if r['k']=='road']
H=set(tuple(k) for k in json.load(open('data/holdout_chunks.json'))['chunks']); ck=lambda x,y:(math.floor(x/1000),math.floor(y/1000))
def bad(r):
    c=ck(r['x'],r['y']); return any(abs(c[0]-h[0])<=1 and abs(c[1]-h[1])<=1 for h in H)
ok=[r for r in roads if not bad(r)]
for _ in range(500):
    a,b=random.sample(ok,2); d=math.hypot(a['x']-b['x'],a['y']-b['y'])
    if 1500<=d<=5000: print(a['n']+'|'+b['n']); break
PY
); f="${pair%%|*}"; t="${pair##*|}"; [ -n "$f" ] || continue
  bash reload.sh "http://localhost:8901/index.html?go=1&perturb=6&from=$f&to=$t" 90 2>&1 | tail -1 >/dev/null
  if ! python3 -c "import urllib.request,json,sys;d=json.load(urllib.request.urlopen('http://localhost:8901/tel',timeout=5));sys.exit(0 if (d.get('wpLen') or 0)>100 and (d.get('perturbS') or 0)>0 else 1)"; then echo "route fail $f>$t skip"; continue; fi
  echo "=== r$r $f > $t ($(date +%H:%M:%S)) ==="; rm -rf data/dagger_r$r
  python3 dagger.py --round $r --episodes 1 --secs $SECS --model none 2>&1 | grep -E '"ep"|Traceback|Error|Killed' | cut -c1-300
  if [ -f data/dagger_r$r/L.npy ]; then fr=$(python3 -c "import numpy as np;L=np.load('data/dagger_r$r/L.npy');print(L.shape[0],int((L[:,11]>0).sum()))"); echo "frames/valid $fr"; tot=$((tot+${fr%% *})); done=$((done+1)); r=$((r+1)); else echo "no L.npy r$r"; fi
  [ $((done%10)) -eq 0 ] && [ $done -gt 0 ] && python3 $NT "[오드 수집 a_5598] 무작위 구간 $done 에피소드, 누적 $tot 프레임 (목표 15만)" >/dev/null 2>&1
done
echo "COLLECT_DONE episodes=$done frames=$tot last_r=$((r-1))"
