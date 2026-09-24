#!/bin/bash
# A' wide-road set(2026-09-24): pairs30(장거리 간선 위주) 30구간 × 300초 규칙주행 + perturb=6, L12 라벨. 홀드아웃 청크 프레임은 학습기가 제외. 사용: bash collect_pairs30.sh <시작라운드=2300> [초=300]
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive; export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6 L12=1 M_EXT=1 ODE_ENV=0
NT=/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/notify_telegram.py; r=${1:-2300}; SECS=${2:-300}; done=0; tot=0; wide=0
python3 -c "import json;[print(p['from']+'|'+p['to']) for p in json.load(open('pairs30.json'))]" | while IFS='|' read -r f t; do
  [ "$(df -g / | tail -1 | awk '{print $4}')" -lt 30 ] && { echo "DISK<30GB stop"; break; }
  n=$(pgrep -fl python3 | grep -Ec 'python3 (gpu_drive|offline_lp_eval|train_lp|train_geo|train_stage|dagger|offline_gate)\.py'); [ "$n" -gt 0 ] && { echo "MPS_BUSY $n"; exit 2; }
  bash reload.sh "http://localhost:8901/index.html?go=1&perturb=6&from=$f&to=$t" 120 2>&1 | tail -1 >/dev/null
  python3 -c "import urllib.request,json,sys;d=json.load(urllib.request.urlopen('http://localhost:8901/tel',timeout=5));sys.exit(0 if (d.get('wpLen') or 0)>100 and (d.get('perturbS') or 0)>0 else 1)" || { echo "route fail $f>$t skip"; continue; }
  echo "=== r$r $f > $t ($(date +%H:%M:%S)) ==="; rm -rf data/dagger_r$r
  python3 dagger.py --round $r --episodes 1 --secs $SECS --model none 2>&1 | grep -E '"ep"|Traceback|Error|Killed' | cut -c1-200
  if [ -f data/dagger_r$r/L.npy ]; then fr=$(python3 -c "import numpy as np;L=np.load('data/dagger_r$r/L.npy');v=L[:,11]>0;print(L.shape[0],int(v.sum()),int((L[v,7]>=4).sum()))"); echo "frames/valid/wide $fr"; r=$((r+1)); fi
done; echo "COLLECT_DONE"
