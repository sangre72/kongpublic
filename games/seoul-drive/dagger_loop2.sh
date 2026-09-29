#!/bin/bash
source /Users/bumsuklee/git/kong-bot/games/seoul-drive/park_page.sh; arm_park_trap   # u_5765: park on ANY exit
# DAgger 반복 v2 (2026-09-20 밤): 기반 = 카메라 고정 가상 샘플링(r41*), DAgger 라운드 라벨 = 그림자 경로추종(daShadow, 규칙 D-00).
#   k: dagger.py(모델 주행 2×300초, r5xx 저장) → train_stage straight 'data/dagger_r41*' --extra 'data/dagger_r5*' --init 이전 → 검증은 다음 k 의 수집이 겸함.
# 사용: bash dagger_loop2.sh <시작k=1> <회수=4> [초기모델=ode_s7.pt]
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6 EXTRA_W=2.0
NT=/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/notify_telegram.py
K=${1:-1}; N=${2:-4}; prev=${3:-ode_s7.pt}
for ((k=K; k<K+N; k++)); do
  r=$((500+k)); out=ode_s7_$k.pt
  echo "=== DAgger2 k=$k collect with $prev $(date +%H:%M:%S) ==="
  bash reload.sh "http://localhost:8901/index.html?go=1&from=사평대로&to=수정로35번길" 60 2>&1 | tail -1
  rm -rf data/dagger_r$r
  python3 dagger.py --round $r --episodes 2 --secs 300 --model $prev 2>&1 | grep -E '"ep"|"round"|Error|abort' | cut -c1-400 | tee /tmp/dagger2_val_$k.log
  s=$(grep '"ep"' /tmp/dagger2_val_$k.log | python3 -c "
import sys,json
out=[]
for l in sys.stdin:
  try: e=json.loads(l); out.append('진행 %.1f%% 사고 %d %s 순간이동 %s 라벨 %s' % (100*e.get('prog_max',0), e.get('crashes',0), e.get('crash_types',{}), e.get('tpN'), e.get('label_src')))
  except Exception: pass
print(' / '.join(out))")
  python3 $NT "[오드 DAgger2 k=$k] $prev 300초×2: $s" >/dev/null 2>&1
  echo "=== DAgger2 k=$k train $(date +%H:%M:%S) ==="
  python3 train_stage.py straight 'data/dagger_r41*' $out --extra 'data/dagger_r5*' --init $prev --epochs 8 --replay 0.2 2>&1 | grep -E '"stage": "straight"|"done"|"error"|warn' | cut -c1-260 | tee /tmp/dagger2_train_$k.log
  [ -f $out ] || { python3 $NT "[오드 DAgger2 k=$k] 학습 실패: $(tail -1 /tmp/dagger2_train_$k.log)" >/dev/null 2>&1; break; }
  prev=$out
done
echo "=== final validation $prev $(date +%H:%M:%S) ==="
bash reload.sh "http://localhost:8901/index.html?go=1&from=사평대로&to=수정로35번길" 60 2>&1 | tail -1
python3 dagger.py --round 599 --episodes 2 --secs 300 --model $prev 2>&1 | grep -E '"ep"|"round"' | cut -c1-400 | tee /tmp/dagger2_final.log
s=$(grep '"ep"' /tmp/dagger2_final.log | python3 -c "
import sys,json
out=[]
for l in sys.stdin:
  try: e=json.loads(l); out.append('진행 %.1f%% 사고 %d %s 순간이동 %s' % (100*e.get('prog_max',0), e.get('crashes',0), e.get('crash_types',{}), e.get('tpN')))
  except Exception: pass
print(' / '.join(out))")
python3 $NT "[오드 DAgger2 최종 $prev] 300초×2: $s" >/dev/null 2>&1
echo "=== DAgger2 done $(date +%H:%M:%S) ==="
