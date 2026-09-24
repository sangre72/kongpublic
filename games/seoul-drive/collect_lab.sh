#!/bin/bash
# a_5612 D2 라벨 수집(2026-09-24): 무작위 구간(짝수)·'대로' 직접배치(홀수) 교대, ?lab=1 + LAB=1 → S.npy(픽셀 클래스, X 와 1:1). 홀드아웃 청크+이웃 제외, perturb=6.
# X/S 저장 384px(orch 2026-09-24: 해상도 축을 D2 에서 256 vs 384 로 검증), 학습기가 로드 시 축소.
# 사용: bash collect_lab.sh <시작라운드=2700> <에피소드수=60> [초=90]
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive; export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6 L12=1 M_EXT=1 ODE_ENV=0 LAB=1 STORE_RES=384
NT=/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/notify_telegram.py; r=${1:-2700}; N=${2:-60}; SECS=${3:-90}; done=0; tot=0; tries=0
while [ $done -lt $N ] && [ $tries -lt $((N*3)) ]; do tries=$((tries+1))
  [ "$(df -g / | tail -1 | awk '{print $4}')" -lt 30 ] && { echo "DISK<30GB stop"; python3 $NT "[오드 라벨 수집] 디스크 30GB 미만 → 정지" >/dev/null 2>&1; break; }
  n=$(pgrep -fl python3 | grep -Ec 'python3 (gpu_drive|offline_lp_eval|train_lp|train_geo|train_bev|train_seg|train_stage|dagger|offline_gate|offline_gate_bev|seg_gate)\.py'); [ "$n" -gt 0 ] && { echo "MPS_BUSY $n"; exit 2; }
  q=$(python3 - $((tries%2)) <<'PY'
import json,random,math,sys
av=int(sys.argv[1]); s=open('data/search.js').read(); rows=json.loads(s[s.index('=')+1:].rstrip().rstrip(';')); roads=[r for r in rows if r['k']=='road']
H=set(tuple(k) for k in json.load(open('data/holdout_chunks.json'))['chunks']); ck=lambda x,y:(math.floor(x/1000),math.floor(y/1000))
bad=lambda r: any(abs(ck(r['x'],r['y'])[0]-h[0])<=1 and abs(ck(r['x'],r['y'])[1]-h[1])<=1 for h in H)
ok=[r for r in roads if not bad(r)]; A=[r for r in ok if r['n'].endswith('대로')] if av else ok
for _ in range(500):
    a=random.choice(A); b=random.choice(ok); d=math.hypot(a['x']-b['x'],a['y']-b['y'])
    if 1500<=d<=5000: print('%d|%.1f|%.1f|%s|%s'%(av,a['x']*6,a['y']*6,b['n'],a['n'])); break
PY
); [ -n "$q" ] || continue; av=$(echo "$q"|cut -d'|' -f1); sx=$(echo "$q"|cut -d'|' -f2); sy=$(echo "$q"|cut -d'|' -f3); t=$(echo "$q"|cut -d'|' -f4); fn=$(echo "$q"|cut -d'|' -f5)
  if [ "$av" = 1 ]; then url="http://localhost:8901/index.html?go=1&lab=1&perturb=6&sx=$sx&sy=$sy&to=$t"; else url="http://localhost:8901/index.html?go=1&lab=1&perturb=6&from=$fn&to=$t"; fi
  bash reload.sh "$url" 60 2>&1 | tail -1 >/dev/null
  nl=$(python3 -c "import urllib.request,json;d=json.load(urllib.request.urlopen('http://localhost:8901/tel',timeout=5));g=d.get('geo') or {};print(g.get('nl') or 0, d.get('wpLen') or 0)"); nlv=${nl%% *}; wl=${nl##* }
  if [ "$wl" -lt 100 ] || { [ "$av" = 1 ] && [ "$nlv" -lt 3 ]; }; then echo "skip $fn nl=$nlv wp=$wl"; continue; fi
  echo "=== r$r av=$av $fn > $t nl=$nlv ($(date +%H:%M:%S)) ==="; rm -rf data/dagger_r$r
  python3 dagger.py --round $r --episodes 1 --secs $SECS --model none 2>&1 | grep -E '"ep"|"S"|Traceback|Error|Killed' | cut -c1-300
  if [ -f data/dagger_r$r/S.npy ]; then fr=$(python3 -c "import numpy as np;S=np.load('data/dagger_r$r/S.npy',mmap_mode='r');L=np.load('data/dagger_r$r/L.npy');print(S.shape[0],int((L[:,11]>0).sum()),int((L[L[:,11]>0,7]>=5).sum()))"); echo "frames/valid/wide $fr"; tot=$((tot+${fr%% *})); done=$((done+1)); r=$((r+1)); else echo "no S.npy r$r"; rm -rf data/dagger_r$r; fi
  [ $((done%10)) -eq 0 ] && [ $done -gt 0 ] && python3 $NT "[오드 a_5612 라벨 수집] $done 에피소드, 누적 $tot 프레임" >/dev/null 2>&1
done; echo "COLLECT_DONE episodes=$done frames=$tot last_r=$((r-1))"
