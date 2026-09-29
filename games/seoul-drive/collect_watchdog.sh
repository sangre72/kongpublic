#!/bin/bash
source /Users/bumsuklee/git/kong-bot/games/seoul-drive/park_page.sh; arm_park_trap   # u_5765: park on ANY exit
# 밤 수집 감시견(2026-09-20 00:2x): 라운드 시작 90초 뒤에도 doneM<30 이면 그 dagger 라운드를 죽인다(정차 데이터 방지). 루프는 다음 구간으로 넘어간다.
while pgrep -f collect_overnight.sh >/dev/null; do
  pid=$(pgrep -f "dagger.py --round" | head -1)
  if [ -n "$pid" ]; then
    sleep 90
    et=$(ps -o etime= -p "$pid" 2>/dev/null | tr -d ' '); age=$(python3 -c "
import sys; t='$et'
try:
    d=0
    if '-' in t: d,t=t.split('-')
    p=[int(x) for x in t.split(':')]
    while len(p)<3: p=[0]+p
    print(int(d)*86400+p[0]*3600+p[1]*60+p[2])
except Exception: print(0)")
    if pgrep -f "dagger.py --round" >/dev/null && [ "$age" -lt 200 ]; then   # 첫 에피소드에서만(늦게 죽이면 앞 에피소드 데이터도 잃는다)
      m=$(python3 -c "
import json,urllib.request
try: d=json.load(urllib.request.urlopen('http://localhost:8901/tel',timeout=5)); print(int(d.get('doneM') or 0))
except Exception: print(999)")
      if [ "$m" -lt 30 ]; then r=$(pgrep -fl "dagger.py --round" | head -1 | grep -o "round [0-9]*"); echo "$(date +%H:%M:%S) watchdog: $r doneM=$m → kill"; pkill -f "dagger.py --round"; fi
    fi
  fi
  sleep 30
done
echo "watchdog exit $(date +%H:%M:%S)"
