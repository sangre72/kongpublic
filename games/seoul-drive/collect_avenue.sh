#!/bin/bash
# A' avenue collector v3(2026-09-24): search.js '대로' 도로점에 sx/sy 로 직접 배치(px=m×6), to=다른 대로(1.5~6km), 배치 직후 /tel geo.nl≥4 확인(아니면 즉시 스킵), 90초 규칙주행+perturb=6. 사용: bash collect_avenue.sh <시작라운드=2400> <목표에피소드=40>
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive; export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6 L12=1 M_EXT=1 ODE_ENV=0
NT=/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/notify_telegram.py; r=${1:-2400}; N=${2:-40}; done=0; tries=0
while [ $done -lt $N ] && [ $tries -lt $((N*4)) ]; do tries=$((tries+1))
  [ "$(df -g / | tail -1 | awk '{print $4}')" -lt 30 ] && { echo "DISK<30GB stop"; break; }
  n=$(pgrep -fl python3 | grep -Ec 'python3 (gpu_drive|offline_lp_eval|train_lp|train_geo|train_stage|dagger|offline_gate)\.py'); [ "$n" -gt 0 ] && { echo "MPS_BUSY $n"; exit 2; }
  q=$(python3 - <<'PY'
import json,random,math
s=open('data/search.js').read(); rows=json.loads(s[s.index('=')+1:].rstrip().rstrip(';')); av=[r for r in rows if r['k']=='road' and r['n'].endswith('대로')]
H=set(tuple(k) for k in json.load(open('data/holdout_chunks.json'))['chunks']); ck=lambda x,y:(math.floor(x/1000),math.floor(y/1000))
bad=lambda r: any(abs(ck(r['x'],r['y'])[0]-h[0])<=1 and abs(ck(r['x'],r['y'])[1]-h[1])<=1 for h in H)
ok=[r for r in av if not bad(r)]
for _ in range(500):
    a,b=random.sample(ok,2); d=math.hypot(a['x']-b['x'],a['y']-b['y'])
    if 1500<=d<=6000: print('%.1f|%.1f|%s|%s'%(a['x']*6,a['y']*6,b['n'],a['n'])); break
PY
); [ -n "$q" ] || continue; sx=$(echo "$q"|cut -d'|' -f1); sy=$(echo "$q"|cut -d'|' -f2); t=$(echo "$q"|cut -d'|' -f3); fn=$(echo "$q"|cut -d'|' -f4)
  bash reload.sh "http://localhost:8901/index.html?go=1&perturb=6&sx=$sx&sy=$sy&to=$t" 60 2>&1 | tail -1 >/dev/null
  nl=$(python3 -c "import urllib.request,json;d=json.load(urllib.request.urlopen('http://localhost:8901/tel',timeout=5));g=d.get('geo') or {};print(g.get('nl') or 0, d.get('wpLen') or 0)"); nlv=${nl%% *}; wl=${nl##* }
  if [ "$nlv" -lt 3 ] || [ "$wl" -lt 100 ]; then echo "skip $fn nl=$nlv wp=$wl"; continue; fi
  echo "=== r$r $fn(sx) > $t nl=$nlv ($(date +%H:%M:%S)) ==="; rm -rf data/dagger_r$r
  python3 dagger.py --round $r --episodes 1 --secs 90 --model none 2>&1 | grep -E '"ep"|Traceback|Error|Killed' | cut -c1-200
  if [ -f data/dagger_r$r/L.npy ]; then fr=$(python3 -c "import numpy as np;L=np.load('data/dagger_r$r/L.npy');v=L[:,11]>0;print(L.shape[0],int(v.sum()),int((L[v,7]>=3).sum()))"); echo "frames/valid/wide $fr"; done=$((done+1)); r=$((r+1)); fi
  [ $((done%10)) -eq 0 ] && [ $done -gt 0 ] && python3 $NT "[오드 A' 대로 수집] $done 에피소드" >/dev/null 2>&1
done; echo "COLLECT_DONE episodes=$done tries=$tries"
