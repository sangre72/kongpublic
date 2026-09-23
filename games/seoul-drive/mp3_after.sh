#!/bin/bash
# 8점 가상 재수집(r1300+) 종료 후: mp3(COND=9 차로의도) · mp3c8(COND=8) 동시 학습(u_5555 GPU 병행) → CoreML → GPU 파이프라인 T0 3구간×300초 평가 → 텔레그램. 대기는 파일 마커만(pgrep 자기매치 금지).
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6
NT=/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/notify_telegram.py
T=/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp; LOG=$T/chain5.log
until grep -q RECOLLECT_DONE $LOG; do sleep 30; done
n=$(ls -d data/dagger_r13[0-9][0-9] 2>/dev/null | wc -l | tr -d ' ')
python3 $NT "[mp3] 재수집 종료(라운드 $n개) → mp3(차로의도 O)·mp3c8(차로의도 X) 동시 학습 시작 $(date +%H:%M)" >/dev/null 2>&1
echo "=== train start $(date +%H:%M:%S) ==="
LP_MULTI=1 LP_MULTI8=1 LP_COND=9 LP_STRIDE=1 python3 train_lp.py 'data/dagger_r13*' ode_mp3.pt --epochs 10 --synth 'data/dagger_r13*' 2>&1 | grep --line-buffered -E '"done"|"frames"|epoch|Error|Killed|Traceback' | cut -c1-200 > $T/train_mp3.log &
LP_MULTI=1 LP_MULTI8=1 LP_COND=1 LP_STRIDE=1 python3 train_lp.py 'data/dagger_r13*' ode_mp3c8.pt --epochs 10 --synth 'data/dagger_r13*' 2>&1 | grep --line-buffered -E '"done"|"frames"|epoch|Error|Killed|Traceback' | cut -c1-200 > $T/train_mp3c8.log &
wait
echo "=== train end $(date +%H:%M:%S) ==="; tail -2 $T/train_mp3.log $T/train_mp3c8.log
for m in ode_mp3 ode_mp3c8; do [ -f $m.pt ] && python3 to_coreml.py $m.pt $T/$m.mlpackage 2>&1 | grep -v -i 'warn\|scikit\|Torch version' | tail -1; done
python3 $NT "[mp3] 학습 종료 $(date +%H:%M). mp3: $(tail -1 $T/train_mp3.log | cut -c1-120) / mp3c8: $(tail -1 $T/train_mp3c8.log | cut -c1-120). GPU T0 평가 시작(3구간×300초×2모델 ≈35분)" >/dev/null 2>&1
ROUTES=("사평대로|수정로35번길" "기아자동차강남지점|부림3길" "충정로7길|수정로35번길")
kill $(pgrep -f 'python3 serve.py') 2>/dev/null; sleep 1; nohup python3 serve.py > /tmp/serve.log 2>&1 & sleep 3
for m in ode_mp3 ode_mp3c8; do [ -d $T/$m.mlpackage ] || continue; res=""
  for pair in "${ROUTES[@]}"; do f="${pair%%|*}"; t="${pair##*|}"
    bash reload.sh "http://localhost:8901/index.html?go=1&from=$f&to=$t&jay=5" 120 2>&1 | tail -1 >/dev/null
    echo "=== eval $m T0 $f ($(date +%H:%M:%S)) ==="
    o=$(python3 gpu_drive.py --secs 300 --speed $T/ode_v9.mlpackage --lp $T/$m.mlpackage --lp-tier 0 2>&1 | grep -v -i 'warn\|scikit\|Torch version' | tail -1); echo "$o"
    res="$res | $f: $(echo "$o" | python3 -c "import json,sys
try:
  d=json.loads(sys.stdin.read()); print('prog %.0f%% crash %s tp %s lp %s hand %s'%(100*d.get('prog',0),d.get('crashes'),d.get('tpN'),d.get('lp_frames'),d.get('handovers')))
except Exception as e: print('parse-fail')")"
  done
  echo "EVALGPU $m T0:$res"; python3 $NT "[mp3 평가 T0·GPU] $m:$res" >/dev/null 2>&1
done
echo MP3_DONE
