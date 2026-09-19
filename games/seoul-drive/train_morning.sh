#!/bin/bash
# 밤샘 수집이 끝나면 1단계(직진) 학습 → 새 모델로 120초 실주행 검증 → 텔레그램 보고 (2026-09-19 u_5431/u_5432)
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8
NT=/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/notify_telegram.py
while pgrep -f collect_overnight.sh >/dev/null; do sleep 60; done
echo "=== training start $(date +%H:%M:%S) ==="
n=$(python3 -c "
import glob,json; t=0
for p in glob.glob('data/dagger_r1*/episodes.json'): t+=sum(e['frames'] for e in json.load(open(p)))
print(t)")
python3 $NT "[오드 학습] 수집 종료. 총 프레임 $n. 1단계(직진) 학습 시작." >/dev/null 2>&1
python3 train_stage.py straight 'data/dagger_r1*' ode_s1.pt --epochs 20 --replay 0.2 2>&1 | tee /tmp/train_s1.log | grep -E '"stage"|"warn"|"error"|"done"' | cut -c1-260
s=$(grep -E '"done"|"error"' /tmp/train_s1.log | tail -1 | cut -c1-200); f=$(grep '"stage"' /tmp/train_s1.log | head -1 | cut -c1-200)
python3 $NT "[오드 학습] 1단계 결과: $f / $s" >/dev/null 2>&1
if [ -f ode_s1.pt ]; then
  echo "=== validation (model drives) ==="
  bash reload.sh "http://localhost:8901/index.html?go=1&from=사평대로&to=수정로35번길" 60 2>&1 | tail -1
  python3 dagger.py --round 200 --episodes 1 --secs 120 --model ode_s1.pt 2>&1 | grep -E '"ep"|"round"|Error|abort' | cut -c1-300 | tee /tmp/val_s1.log
  v=$(grep '"ep"' /tmp/val_s1.log | tail -1 | cut -c1-260)
  python3 $NT "[오드 검증] ode_s1 모델 주행 120초(사평대로): $v" >/dev/null 2>&1
fi
echo "=== morning done $(date +%H:%M:%S) ==="
