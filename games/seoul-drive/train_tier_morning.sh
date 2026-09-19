#!/bin/bash
# train_morning.sh 뒤: 관제(등급) 모델 학습 → 텔레그램 (u_5443)
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8
NT=/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/notify_telegram.py
while pgrep -f "collect_overnight.sh|train_morning.sh" >/dev/null; do sleep 60; done
echo "=== tier training $(date +%H:%M:%S) ==="
python3 train_tier.py 'data/dagger_r1*' tier_net.pt --epochs 15 2>&1 | tee /tmp/train_tier.log | grep -E '"frames"|"done"|"error"' | cut -c1-260
d=$(grep '"frames"' /tmp/train_tier.log | head -1 | cut -c1-160); r=$(grep '"ep"' /tmp/train_tier.log | tail -1 | cut -c1-260); s=$(grep -E '"done"|"error"' /tmp/train_tier.log | tail -1 | cut -c1-120)
python3 $NT "[오드 관제모델] $d / 마지막 epoch: $r / $s" >/dev/null 2>&1
echo "=== tier done $(date +%H:%M:%S) ==="
