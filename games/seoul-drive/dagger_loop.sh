#!/bin/bash
# DAgger 반복(2026-09-20, PLAN_ODE §9). 회귀(run_regression)가 페이지를 쓰는 동안 기다렸다가 시작(크롬·GPU 동시실행 금지).
#   k 회차: train_stage straight (밤 교사 수집 r1* + DAgger r2* 전 프레임 --extra, --init 직전 모델) → ode_s1_k.pt
#           → dagger.py --round 20k --model ode_s1_k.pt 120초(사평대로) → 텔레그램. 도착·무사고면 종료.
# 사용: bash dagger_loop.sh [시작k=2] [회수=4] [초기모델=ode_s1.pt]
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8
NT=/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/notify_telegram.py
K=${1:-2}; N=${2:-4}; prev=${3:-ode_s1.pt}
while pgrep -f "run_regression.sh|route_test.py|dagger.py" >/dev/null; do sleep 30; done
for ((k=K; k<K+N; k++)); do
  out=ode_s1_$k.pt; r=$((200+k)); log=/tmp/dagger_train_$k.log
  echo "=== DAgger k=$k train $(date +%H:%M:%S) ==="
  python3 train_stage.py straight 'data/dagger_r1*' $out --extra 'data/dagger_r2*' --init $prev --epochs 12 --replay 0.2 2>&1 | grep -E '"stage": "straight"|"done"|"error"|warn' | cut -c1-260 | tee $log
  [ -f $out ] || { python3 $NT "[오드 DAgger k=$k] 학습 실패: $(tail -1 $log)" >/dev/null 2>&1; break; }
  bash reload.sh "http://localhost:8901/index.html?go=1&from=사평대로&to=수정로35번길" 60 2>&1 | tail -1
  python3 dagger.py --round $r --episodes 1 --secs 120 --model $out 2>&1 | grep -E '"ep"|"round"|Error|abort' | cut -c1-300 | tee /tmp/dagger_val_$k.log
  s=$(grep '"ep"' /tmp/dagger_val_$k.log | tail -1 | python3 -c "
import sys,json
try:
  e=json.loads(sys.stdin.read()); print('진행 %.1f%% 사고 %d %s 프레임 %d 가중치0 %d 도착 %s' % (100*e.get('prog_max',0), e.get('crashes',0), e.get('crash_types',{}), e.get('frames',0), e.get('w0_frames',0), e.get('arrived')))
except Exception as x: print('결과 없음', x)")
  python3 $NT "[오드 DAgger k=$k] $(grep '\"done\"' $log | tail -1 | cut -c1-80) → 120초 실주행: $s" >/dev/null 2>&1
  prev=$out
  grep -q '"arrived": true' /tmp/dagger_val_$k.log && grep -q '"crashes": 0' /tmp/dagger_val_$k.log && break
done
echo "=== DAgger loop done $(date +%H:%M:%S) ==="
