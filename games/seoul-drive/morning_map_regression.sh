#!/bin/bash
# 아침 2단계: train_morning.sh 끝난 뒤 새 지도(oneway 연속성·왕복 짝수 기본값) 빌드 → 회귀 9구간 → 충정로7길 서소문로 캡처 → 텔레그램
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8
NT=/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/notify_telegram.py
while pgrep -f "collect_overnight.sh|train_morning.sh" >/dev/null; do sleep 60; done
echo "=== map build $(date +%H:%M:%S) ==="
(python3 build.py 2>&1 | tail -1)
echo "=== regression ==="; bash run_regression.sh 2>&1 | grep -E "EVT|result|PASS|REGRESSION|FAIL|불가항력" | cut -c1-230 | tee /tmp/reg_morning.log
s=$(grep -E "ALL PASS|REGRESSION\(S\)" /tmp/reg_morning.log | tail -1)
python3 $NT "[오드 아침] 새 지도 빌드 후 회귀 9구간: $s" >/dev/null 2>&1
echo "=== 서소문로 capture ==="
bash reload.sh "http://localhost:8901/index.html?go=1&from=충정로7길&to=수정로35번길" 60 2>&1 | tail -1
until python3 -c "
import json,urllib.request,sys
d=json.load(urllib.request.urlopen('http://localhost:8901/tel',timeout=5)); sys.exit(0 if (d.get('doneM') or 0)>=1840 or (d.get('tpN') or 0)>2 else 1)"; do sleep 2; done
screencapture -x -R0,130,470,600 /tmp/seosomun_morning.png
python3 -c "
import json,urllib.request
d=json.load(urllib.request.urlopen('http://localhost:8901/tel',timeout=5)); t=d.get('tch') or {}; g=t.get('g2') or {}
print('doneM',d.get('doneM'),'lat',g.get('lat'),'rw',g.get('roadW'),'nl',g.get('nl'),'o',g.get('o'),'cr',d.get('cr'),'tpN',d.get('tpN'))"
echo "=== morning map done $(date +%H:%M:%S) ==="
