#!/bin/bash
source /Users/bumsuklee/git/kong-bot/games/seoul-drive/park_page.sh; arm_park_trap   # u_5765: park on ANY exit
# DAgger v3 (2026-09-21 밤, 앞점 인터페이스): k회차 = 모델 주행 3구간×300초(앞점 라벨 L.npy 기록, r9xx) → train_lp(초기화=직전, 6 epoch) → eval_lp(3구간).
# 사용: bash dagger_loop3.sh <시작k=1> <회수=6> [초기모델=ode_lp4.pt]
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6 XT_MAX=0.6
NT=/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/notify_telegram.py
K=${1:-1}; N=${2:-6}; prev=${3:-ode_lp4.pt}
for ((k=K; k<K+N; k++)); do
  echo "=== DAgger3 k=$k collect with $prev $(date +%H:%M:%S) ==="
  r=$((900+k*10)); res=""
  for pair in "사평대로|수정로35번길" "기아자동차강남지점|부림3길" "충정로7길|수정로35번길"; do
    f="${pair%%|*}"; t="${pair##*|}"
    bash reload.sh "http://localhost:8901/index.html?go=1&from=$f&to=$t" 60 2>&1 | tail -1 >/dev/null
    rm -rf data/dagger_r$r
    python3 dagger.py --round $r --episodes 1 --secs 300 --model $prev 2>&1 | grep -E '"ep"' > /tmp/d3_$r.log
    s=$(F="$f" python3 -c "
import json,os
try:
  e=json.loads(open('/tmp/d3_$r.log').read().strip().splitlines()[-1]); ct=e['crash_types']; av=sum(v for k,v in ct.items() if '불가항력' not in k)
  print('%s %d/%s/%.0f%%' % (os.environ['F'][:4], av, e.get('tpN'), 100*e.get('prog_max',0)))
except Exception as x: print('%s ?' % os.environ['F'][:4])")
    res="$res $s"; r=$((r+1))
  done
  echo "collect(=eval of $prev): $res"
  python3 $NT "[DAgger3 k=$k] $prev 3구간(회피가능사고/복귀/진행):$res" >/dev/null 2>&1
  out=ode_lp4_$k.pt
  echo "=== DAgger3 k=$k train $(date +%H:%M:%S) ==="
  python3 train_lp.py 'data/dagger_r81*,data/dagger_r9*' $out --synth 'data/dagger_r80*,data/dagger_r82*' --init $prev --epochs 6 2>&1 | grep -E '"frames"|"done"|error|lp_mae' | cut -c1-200 | tail -3
  [ -f $out ] || { python3 $NT "[DAgger3 k=$k] 학습 실패" >/dev/null 2>&1; break; }
  prev=$out
done
echo "=== DAgger3 done $(date +%H:%M:%S) (last $prev) ==="
python3 $NT "[DAgger3 종료 $(date +%H:%M)] 마지막 모델 $prev — 아침에 최종 평가 보고" >/dev/null 2>&1
