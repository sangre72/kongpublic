#!/bin/bash
# orch 2026-09-27 코너 가중 수집: 회전이 많은 구간에서 lp 라벨 수집, 정점 통과 후 3초 프레임 W=2.0.
# 사용: bash collect_corner.sh [시작라운드=3300] [에피소드=40] [초=90]
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
source "$(dirname "$0")/chrome_guard.sh"; chrome_guard "$(basename "$0")" || exit 9
source "$(dirname "$0")/park_page.sh"; arm_park_trap   # u_5765: EXIT+INT+TERM+HUP
source "$(dirname "$0")/pagelock.sh"; lock_page "collect_corner" || { echo "PAGE BUSY - abort"; exit 9; }; trap 'park_page; unlock_page' EXIT INT TERM HUP   # u_5765 fix3: one trap does BOTH (a second trap ... EXIT was silently replacing the park trap)
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6 L12=1 M_EXT=1 ODE_ENV=0 LAB=1 STORE_RES=256 CORNER_W=2.0 CORNER_W_SEC=3
NT=/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/notify_telegram.py
r=${1:-3300}; N=${2:-40}; SECS=${3:-90}; done=0; tot=0; tries=0; boost=0
RECENT=""; RECENTCK=""; SEEN=""; STALL=0   # u_5742: last-10 pair ring + last-6 start-chunk ring
while [ $done -lt $N ] && [ $tries -lt $((N*12)) ]; do tries=$((tries+1))
  [ "$(df -g / | tail -1 | awk '{print $4}')" -lt 30 ] && { echo "DISK<30GB stop"; break; }
  n=$(pgrep -fl python3 | grep -Ec 'python3 (gpu_drive|train_|dagger|offline_gate|seg_gate)\.py' || true); [ "$n" -gt 0 ] && { sleep 30; continue; }
  # u_5741(b): class-aware picking. DEF = class furthest below the holdout mix (35/35/30).
  # u_5751: deficit by DISTINCT ROADS, not frames (frames already 60.8k vs 40k target; only
  #   diversity is worth buying now, and the frame quota stalled arterial at 4 of its 24-road pool).
  DEFLINE=$(COVLOG=$COVLOG python3 road_deficit.py 2>/dev/null || echo "arterial")
  DEF=${DEFLINE%% *}
  ART=$(echo "$DEFLINE" | sed -E 's/.*arterial=([0-9]+).*/\1/')
  if [ "${ART:-0}" -ge 12 ]; then echo "ARTERIAL_TARGET_MET $DEFLINE"; break; fi
  if [ "${STALL:-0}" -ge 3 ]; then echo "ARTERIAL_STALL $DEFLINE"; break; fi
  if [ $((tries % 10)) -eq 1 ]; then echo "CLASS-HIST $DEFLINE"; echo "COVERAGE $(python3 coverage.py 'data/dagger_r3[56]*' 2>/dev/null)"; fi
  q=$(DEF=$DEF RECENT="$RECENT" RECENTCK="$RECENTCK" python3 - <<'PY'
import json,random,math
s=open('data/search.js').read(); rows=json.loads(s[s.index('=')+1:].rstrip().rstrip(';')); roads=[r for r in rows if r['k']=='road']
# u_5750: +/-1 chunk buffer replaced by a 1000m distance buffer + name guard.
#   old rule excluded a 3x3km neighbourhood per holdout cell = 70% of in-scope roads
#   (two 103->10, arterial 30->10). New rule: two 55, arterial 24, alley 594. Test set unchanged.
from holdout_buffer import train_eligible, holdout_names
_hn = holdout_names([r for r in roads if r.get('n')])
ok=[r for r in roads if train_eligible(r, _hn)]
# ★u_5705 2026-09-28: 무작위 추첨은 범위 내 다차로 도로가 151/1126 뿐이라 92연속 MIX-SKIP 으로 수집이 멈췄다.
#   출발지를 **범위 내 arterial/two 목록에서 직접** 뽑는다(도착지는 범위 내 아무 도로).
import sys; sys.path.insert(0,'.')
from scope import in_scope
cls=json.load(open('data/scope_road_class.json'))
byn={r['n']:r for r in ok if r.get('n')}
import os
_def=os.environ.get('DEF','alley')
# u_5741 fix2: label is per-road, measured nl is per-start-point, so widen the pool to the label
# plus its neighbours and let the measured-nl gate decide. Pure label matching starved 'two'.
# u_5741 fix6: a plain union pool is ~87% alley (975/1126 in-scope roads), so "preference" did nothing
#   (10 rounds, deficit=two: alley +1660 vs two +212). Draw the deficit class FIRST and only fall
#   back to the union when that class has no usable start, so the deficit actually steers the draw.
# u_5759 STAGE 1: alley + two only (the classes with most eligible roads).
_prim=[byn[n] for n,c in cls.items() if c==_def and c in ('alley','two') and n in byn]
_all=[byn[n] for n,c in cls.items() if c in ('alley','two') and n in byn]
starts=_prim if _prim else _all
if not starts: starts=_all
# u_5741 fix7: MEASURED - a two-lane START still yields ~all-alley frames (r3516: nl1 1297 vs nl2 35),
#   because the destination is any in-scope road (87% alley) so the router routes THROUGH alleys.
#   Both endpoints must be in the deficit class for the PATH to stay on that class.
# u_5742(a): constrain only ONE endpoint to the deficit class; the other is any in-scope road.
#   fix7 (both endpoints) gave the right class mix but collapsed route space to 10 pairs / 4% of scope.
dests=[r for r in ok if r.get('n') and in_scope(r['x'], r['y'])]
# u_5742(ii) diversity guard: refuse a pair used in the last 10 rounds, and require the start chunk
#   to differ from the previous round's start chunk.
import os as _os
_recent=set(filter(None,(_os.environ.get('RECENT','') or '').split('\n')))
_recentck=set(filter(None,(_os.environ.get('RECENTCK','') or '').split('\n')))
def _ck(r): return '%d,%d'%(r['x']//1000, r['y']//1000)
for _ in range(400):
    if not starts or not dests: break
    a=random.choice(starts); b=random.choice(dests)
    d=math.hypot(a['x']-b['x'],a['y']-b['y'])
    if a['n']==b['n'] or not (1200<=d<=3500): continue
    if ('%s > %s'%(a['n'],b['n'])) in _recent: continue          # u_5742: no repeat within 10 rounds
    if _ck(a) in _recentck: continue                               # u_5742 fix2: start chunk unused in last 6 rounds
                                                                   #   (prev-round-only guard let 4 starts alternate: 자곡로 x5 of 12 rounds, chunks stuck at 13)
    print('%s|%s'%(a['n'],b['n'])); break
PY
); [ -n "$q" ] || continue; f=${q%%|*}; t=${q##*|}
  bash reload.sh "http://localhost:8901/index.html?go=1&lab=1&asym=1&pgrid=2&pgey=0.6,1.2&pgep=10,20&from=$f&to=$t" 60 2>&1 | tail -1 >/dev/null
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
  # u_5741 fix8: MEASURED - arterial candidates never reach 6 turns (best 5 over 20 draws: 2x5,3x7,4x5,5x3),
  #   because arterials are long and straight and the in-scope pool is only 40 roads. A fixed >=6 gate makes
  #   the arterial deficit unreachable and the loop spins until the try budget dies. Threshold by class.
  # u_5741 fix9: same unreachable-threshold stall now on two-lane. With BOTH endpoints class-constrained
  #   the two pool is 111 roads, so surviving pairs are short: best 5 turns over 29 draws (16x2, 11x3, 1x5).
  #   Only alley (975 roads) can sustain >=6. Threshold: alley 6, two/arterial 4.
  MINT=6; case "$DEF" in arterial|two) MINT=4 ;; esac
  if [ "${nt:-0}" -lt "$MINT" ] || [ "${wl:-0}" -lt 100 ]; then echo "skip $f>$t turns=$nt wp=$wl (need>=$MINT $DEF)"; continue; fi
  # u_5741 fix2: gate on the MEASURED nl (frames are binned by nl, not by the road-class label).
  #   scope_road_class labels a whole road, but nl is measured at the start point - 중대로27길 is labelled "two"
  #   yet starts nl=1, so a label-based draw + nl>=2 gate rejected every two-lane candidate (10 rounds, two +0).
  # u_5741 fix4 (final): do NOT gate the start on class at all.
  #   Measured over 11 rounds: a single route already yields frames of every class (nl 1..5 present),
  #   and the in-scope start pool is 87% alley - so ANY start-class gate starves the picker
  #   (deficit-gate: 3 rejects/2.5min 0 rounds; surplus-gate: 10 rejects/3min 0 rounds).
  #   Balancing is done where the frames are actually binned: per-frame nl. The picker keeps the
  #   deficit class only as a PREFERENCE for the start draw (see DEF above), never as a hard reject.
  :
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
    # u_5742: remember this pair (ring of 10) and its start chunk
    case "$SEEN" in *"|$f|"*) STALL=$((STALL+1));; *) STALL=0; SEEN="$SEEN|$f|";; esac
    RECENT=$(printf '%s\n%s' "$f > $t" "$RECENT" | head -10)
    RECENTCK=$(printf '%s\n%s' "$(python3 -c "
import json,sys
s=open('data/search.js').read(); rows=json.loads(s[s.index('=')+1:].rstrip().rstrip(';'))
for r in rows:
    if r.get('k')=='road' and r.get('n')=='$f': print('%d,%d'%(r['x']//1000, r['y']//1000)); break
" 2>/dev/null)" "$RECENTCK" | head -6)
  else rm -rf data/dagger_r$r; fi
  # u_5741 fix5: this was the loop's LAST command; when done%10 != 0 the compound returns non-zero
  #   and the while-loop exits silently after a single successful round (observed: r3511 ok, then stop).
  if [ $((done%10)) -eq 0 ] && [ $done -gt 0 ]; then
    python3 $NT "[오드 코너수집] $done 에피소드, 누적 $tot 프레임(코너 가중 $boost)" >/dev/null 2>&1 || true
  fi
  true
done
echo "CORNER_COLLECT_DONE episodes=$done frames=$tot boosted=$boost last_r=$((r-1))"
