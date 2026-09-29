#!/bin/bash
source /Users/bumsuklee/git/kong-bot/games/seoul-drive/park_page.sh; arm_park_trap   # u_5765: park on ANY exit
# 속도 DAgger (2026-09-22, 축소안 A): 조향=규칙 추종기, 라벨=규칙 목표속도(vmax, L.npy 3열).
#   0) 교사 라운드 3구간×600초(r850~852, vmax 라벨 포함) → ode_v2 학습(SPEED_LABEL=vmax) → 평가
#   k) 모델 주행 3구간×300초(r86k*, vmax 라벨 기록) → 재학습(r85*+r86*) → 평가. 사용: bash speed_loop.sh [회수=3]
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6 SPEED_LABEL=vmax
NT=/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/notify_telegram.py
N=${1:-3}
ROUTES=("사평대로|수정로35번길" "기아자동차강남지점|부림3길" "충정로7길|수정로35번길")
r=850
for pair in "${ROUTES[@]}"; do f="${pair%%|*}"; t="${pair##*|}"; echo "=== teacher $r $f ($(date +%H:%M:%S)) ==="
  bash reload.sh "http://localhost:8901/index.html?go=1&from=$f&to=$t" 120 2>&1 | tail -1 >/dev/null; rm -rf data/dagger_r$r
  python3 dagger.py --round $r --episodes 1 --secs 600 --model none 2>&1 | grep -E '"round"' | cut -c1-160; r=$((r+1)); done
prev=""
for ((k=0; k<=N; k++)); do
  if [ $k -gt 0 ]; then
    rb=$((860+k*10)); res=""
    for pair in "${ROUTES[@]}"; do f="${pair%%|*}"; t="${pair##*|}"
      bash reload.sh "http://localhost:8901/index.html?go=1&from=$f&to=$t" 60 2>&1 | tail -1 >/dev/null; rm -rf data/dagger_r$rb
      python3 dagger.py --round $rb --episodes 1 --secs 300 --model $prev 2>&1 | grep -E '"ep"' > /tmp/sp_$rb.log
      s=$(F="$f" python3 -c "
import json,os
try:
  e=json.loads(open('/tmp/sp_$rb.log').read().strip().splitlines()[-1]); ct=e['crash_types']; av=sum(v for kk,v in ct.items() if '불가항력' not in kk)
  print('%s %d/%s/%.0f%%' % (os.environ['F'][:4], av, e.get('tpN'), 100*e.get('prog_max',0)))
except Exception as x: print('%s ?' % os.environ['F'][:4])"); res="$res $s"; rb=$((rb+1)); done
    echo "eval $prev:$res"; python3 $NT "[속도 DAgger k=$k] $prev 3구간(회피가능사고/복귀/진행):$res" >/dev/null 2>&1
  fi
  out=ode_v$((k+2)).pt; echo "=== train $out ($(date +%H:%M:%S)) ==="
  python3 train_speed.py 'data/dagger_r85*,data/dagger_r86*' $out --epochs 10 ${prev:+--init $prev} 2>&1 | grep -E '"frames"|"done"|Error|error|vT_mae|skip' | cut -c1-200 | tail -4
  [ -f $out ] || { python3 $NT "[속도 DAgger] $out 학습 실패" >/dev/null 2>&1; break; }
  prev=$out
done
echo "=== speed loop done $(date +%H:%M:%S) last $prev ==="
