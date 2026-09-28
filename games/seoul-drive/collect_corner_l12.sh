#!/bin/bash
# orch 2026-09-27 코너 가중 수집: 회전이 많은 구간에서 lp 라벨 수집, 정점 통과 후 3초 프레임 W=2.0.
# 사용: bash collect_corner.sh [시작라운드=3300] [에피소드=40] [초=90]
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
source "$(dirname "$0")/chrome_guard.sh"; chrome_guard "$(basename "$0")" || exit 9
source "$(dirname "$0")/park_page.sh"; trap park_page EXIT
source "$(dirname "$0")/pagelock.sh"; lock_page "collect_corner" || { echo "PAGE BUSY - abort"; exit 9; }; trap unlock_page EXIT
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6 L12=1 M_EXT=1 ODE_ENV=0 LAB=1 STORE_RES=256 CORNER_W=2.0 CORNER_W_SEC=3
NT=/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/notify_telegram.py
r=${1:-3300}; N=${2:-40}; SECS=${3:-90}; done=0; tot=0; tries=0; boost=0
while [ $done -lt $N ] && [ $tries -lt $((N*3)) ]; do tries=$((tries+1))
  [ "$(df -g / | tail -1 | awk '{print $4}')" -lt 30 ] && { echo "DISK<30GB stop"; break; }
  n=$(pgrep -fl python3 | grep -Ec 'python3 (gpu_drive|train_|dagger|offline_gate|seg_gate)\.py' || true); [ "$n" -gt 0 ] && { sleep 30; continue; }
  # u_5741(b): class-aware picking. DEF = class furthest below the holdout mix (35/35/30).
  DEFLINE=$(python3 class_deficit.py 'data/dagger_r35*' 2>/dev/null || echo "alley")
  DEF=${DEFLINE%% *}
  if [ $((tries % 10)) -eq 1 ]; then echo "CLASS-HIST $DEFLINE"; fi
  q=$(DEF=$DEF python3 - <<'PY'
import json,random,math
s=open('data/search.js').read(); rows=json.loads(s[s.index('=')+1:].rstrip().rstrip(';')); roads=[r for r in rows if r['k']=='road']
H=set(tuple(k) for k in json.load(open('data/holdout_chunks.json'))['chunks']); ck=lambda x,y:(math.floor(x/1000),math.floor(y/1000))
bad=lambda r: any(abs(ck(r['x'],r['y'])[0]-h[0])<=1 and abs(ck(r['x'],r['y'])[1]-h[1])<=1 for h in H)
ok=[r for r in roads if not bad(r)]
# ★u_5705 2026-09-28: 무작위 추첨은 범위 내 다차로 도로가 151/1126 뿐이라 92연속 MIX-SKIP 으로 수집이 멈췄다.
#   출발지를 **범위 내 arterial/two 목록에서 직접** 뽑는다(도착지는 범위 내 아무 도로).
import sys; sys.path.insert(0,'.')
from scope import in_scope
cls=json.load(open('data/scope_road_class.json'))
byn={r['n']:r for r in ok if r.get('n')}
import os
_def=os.environ.get('DEF','alley')
_want = ('alley',) if _def=='alley' else (('two',) if _def=='two' else ('arterial',))
starts=[byn[n] for n,c in cls.items() if c in _want and n in byn]
if not starts: starts=[byn[n] for n,c in cls.items() if c in ('arterial','two') and n in byn]
dests=[r for r in ok if r.get('n') and in_scope(r['x'], r['y'])]
for _ in range(400):
    if not starts or not dests: break
    a=random.choice(starts); b=random.choice(dests)
    d=math.hypot(a['x']-b['x'],a['y']-b['y'])
    if a['n']!=b['n'] and 1200<=d<=3500: print('%s|%s'%(a['n'],b['n'])); break
PY
); [ -n "$q" ] || continue; f=${q%%|*}; t=${q##*|}
  bash reload.sh "http://localhost:8901/index.html?go=1&lab=1&asym=1&perturb=6&from=$f&to=$t" 60 2>&1 | tail -1 >/dev/null
  # 회전이 많은 구간만: turnRuns >= 6
  tr=$(python3 -c "
import urllib.request,json
try:
    d=json.load(urllib.request.urlopen('http://localhost:8901/tel',timeout=5)); w=d.get('wpDbg') or {}
    print(len(w.get('turnRuns') or []), d.get('wpLen') or 0)
except Exception: print(0,0)")
  nt=${tr%% *}; wl=${tr##* }
  # ★2026-09-27 orch(3): 도로유형 혼합 강제. 이전 수집은 무작위라 가중 프레임의 80.8%가 1차로 골목으로 쏠렸고
  #   그 결과 간선 다차로 구간(eval20 대부분)으로 일반화되지 않았다. nl(방향당 차로수) >= 2 인 구간만 받는다.
  nlv=$(python3 -c "
import urllib.request,json
try:
    d=json.load(urllib.request.urlopen('http://localhost:8901/tel',timeout=5)); g=d.get('geo') or {}
    print(int(g.get('nl') or 0))
except Exception: print(0)")
  if [ "${nt:-0}" -lt 6 ] || [ "${wl:-0}" -lt 100 ]; then echo "skip $f>$t turns=$nt wp=$wl"; continue; fi
  MINNL=2; [ "$DEF" = "alley" ] && MINNL=1
  if [ "${nlv:-0}" -lt "$MINNL" ]; then echo "MIX-SKIP $f>$t nl=$nlv (need >=$MINNL, def=$DEF)"; continue; fi
  # ★u_5705 SCOPE: 강남구+송파구 안의 구간만 수집한다.
  insc=$(python3 -c "
import urllib.request,json,sys
sys.path.insert(0,'.')
from scope import in_scope
try:
    d=json.load(urllib.request.urlopen('http://localhost:8901/tel',timeout=5)); p=d.get('pos') or []
    print(1 if (p and in_scope(p[0]/6.0, p[1]/6.0)) else 0)
except Exception: print(0)")
  if [ "${insc:-0}" != "1" ]; then echo "SCOPE-SKIP $f>$t"; continue; fi
  # ★u_5683 데이터 게이트: 경로 자체가 불량(오프셋 점프>1.5m·도로폭 이탈·같은 이름 차로수 2↑ 변화)이면 수집하지 않는다.
  pa=$(python3 path_audit.py 2>/dev/null)
  if [ "$(echo "$pa" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("ok"))' 2>/dev/null)" != "True" ]; then
    echo "GATE-SKIP $f>$t $(echo "$pa" | cut -c1-160)"; continue
  fi
  echo "=== r$r $f > $t turns=$nt ($(date +%H:%M:%S)) ==="; rm -rf data/dagger_r$r
  python3 dagger.py --round $r --episodes 1 --secs $SECS --model none 2>&1 | grep -E '"ep"|"S"|corner_boost|Traceback|Error|Killed' | cut -c1-260
  if [ -f data/dagger_r$r/S.npy ]; then
    fr=$(python3 -c "
import numpy as np
S=np.load('data/dagger_r$r/S.npy',mmap_mode='r'); W=np.load('data/dagger_r$r/W.npy')
print(S.shape[0], int((W>1).sum()))")
    tot=$((tot+${fr%% *})); boost=$((boost+${fr##* })); done=$((done+1)); r=$((r+1))
  else rm -rf data/dagger_r$r; fi
  [ $((done%10)) -eq 0 ] && [ $done -gt 0 ] && python3 $NT "[오드 코너수집] $done 에피소드, 누적 $tot 프레임(코너 가중 $boost)" >/dev/null 2>&1
done
echo "CORNER_COLLECT_DONE episodes=$done frames=$tot boosted=$boost last_r=$((r-1))"
