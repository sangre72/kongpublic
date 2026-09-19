#!/bin/bash
# 밤샘 수집(u_5431 2026-09-19): 라운드마다 다른 스윕 구간(pairs30.json)을 로드 → dagger 3에피소드×600초(W/M 저장) → 라운드 통계 텔레그램. 07:00 또는 30라운드까지.
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
# (원본은 검증 배치 뒤에 시작하도록 대기했다 — 레포 판은 즉시 시작. 사용: bash collect_overnight.sh [시작라운드])
echo "=== collection start $(date +%H:%M:%S) ==="
python3 /Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/notify_telegram.py "[오드 수집] 시작 $(date +%H:%M). 라운드=구간 하나, 3에피소드×600초, W/M 저장. 라운드마다 보고." >/dev/null 2>&1
r=${1:-100}
while [ "$(date +%H)" != "07" ] && [ $r -lt 130 ]; do
  pair=$(python3 -c "import json; p=json.load(open('pairs30.json')); q=p[($r-100)%len(p)]; print(q['from']+'|'+q['to'])")
  f="${pair%%|*}"; t="${pair##*|}"
  echo "=== round $r : $f > $t ($(date +%H:%M:%S)) ==="
  bash reload.sh "http://localhost:8901/index.html?go=1&from=$f&to=$t" 120 2>&1 | tail -1
  if ! python3 -c "
import json,urllib.request,sys
d=json.load(urllib.request.urlopen('http://localhost:8901/tel',timeout=5)); sys.exit(0 if (d.get('wpLen') or 0)>100 else 1)"; then echo "route fail, skip"; r=$((r+1)); continue; fi
  python3 dagger.py --round $r --episodes 3 --secs 600 --model bc_final.pt 2>&1 | grep -E '"ep"|"round"|err|abort' | cut -c1-260 | tee /tmp/dagger_r$r.log
  s=$(python3 -c "
import json,glob
try:
  st=json.load(open('data/dagger_r$r/episodes.json')); fr=sum(e.get('frames',0) for e in st); cr=sum(e.get('crashes',0) for e in st); w0=sum(e.get('w0_frames',0) for e in st)
  print(f'라운드 $r $f→$t: 프레임 {fr}, 사고 {cr}(가중치0 프레임 {w0}), 모델주행 {[e.get(\"model_pct\") for e in st]}%, 진행 {[e.get(\"prog_max\") for e in st]}')
except Exception as e: print(f'라운드 $r: 결과 없음 ({e})')")
  echo "$s"; python3 /Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/notify_telegram.py "[오드 수집] $s" >/dev/null 2>&1
  r=$((r+1))
done
echo "=== collection done $(date +%H:%M:%S) ==="
