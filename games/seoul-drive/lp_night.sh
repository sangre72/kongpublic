#!/bin/bash
source /Users/bumsuklee/git/kong-bot/games/seoul-drive/park_page.sh; arm_park_trap   # u_5765: park on ANY exit
# 밤샘 조향 이양 DAgger(2026-09-22 u_5516): 사이클 k = ①모델조향(T0·T1) 3구간×300초 수집(라벨=규칙 앞점) ②lp 재학습(직전 모델 init, 전 데이터+교란) ③평가 T0(3구간) ④평가 T1(3구간).
#   합격 기준: T0 회피가능 0·복귀 0 유지, T1 회피가능 0·복귀 합계 감소. 07:00 정지. 사용: bash lp_night.sh <시작라운드=960> <시작lp=ode_lp7.pt>
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6 LP_STRIDE=2
NT=/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/notify_telegram.py
r=${1:-960}; prev=${2:-ode_lp7.pt}; k=$(( (r-960)/10 + 8 )); BEST_T1=${3:-7}
ROUTES=("사평대로|수정로35번길" "기아자동차강남지점|부림3길" "충정로7길|수정로35번길")
while [ "$(date +%H)" -lt 7 ] || [ "$(date +%H)" -ge 19 ]; do
  [ "$(df -g / | tail -1 | awk '{print $4}')" -lt 20 ] && { python3 $NT "[밤샘 조향] 디스크 20GB 미만 → 정지"; break; }
  echo "=== cycle lp$k collect r$r ($(date +%H:%M:%S)) ==="
  rc=$r; for pair in "${ROUTES[@]}"; do f="${pair%%|*}"; t="${pair##*|}"
    bash reload.sh "http://localhost:8901/index.html?go=1&from=$f&to=$t" 60 2>&1 | tail -1 >/dev/null; rm -rf data/dagger_r$rc
    python3 dagger.py --round $rc --episodes 1 --secs 300 --model ode_v2.pt --lp $prev --lp-tier 1 2>&1 | grep -E '"ep"|Traceback|Error|Killed' | cut -c1-300 > /tmp/lpn_$rc.log; rc=$((rc+1)); done
  pkill -x "Google Chrome"; sleep 3
  out=ode_lp$k.pt; echo "=== train $out ($(date +%H:%M:%S)) ==="
  python3 train_lp.py 'data/dagger_r85*,data/dagger_r87*,data/dagger_r88*,data/dagger_r89*,data/dagger_r91*,data/dagger_r96*,data/dagger_r97*,data/dagger_r98*,data/dagger_r99*' $out --epochs 6 --init $prev --synth 'data/dagger_r93*' 2>&1 | grep -E '"done"|"frames"|Error|Killed|Traceback' | cut -c1-200
  [ -f $out ] || { python3 $NT "[밤샘 조향] $out 학습 실패 → 정지"; break; }
  e0=$(bash eval_ped.sh ode_v2.pt $((r+3)) 'jay=5' T0 "--lp $out" 2>&1 | grep "^EVALPED" | cut -c1-400)
  e1=$(bash eval_ped.sh ode_v2.pt $((r+6)) 'jay=5' T1 "--lp $out --lp-tier 1" 2>&1 | grep "^EVALPED" | cut -c1-400)
  echo "$e0"; echo "$e1"
  # ★채택 판정(2026-09-22 lp8 회귀 후): T0 회피가능 0·복귀 합계 ≤1 이고 T1 회피가능 0·복귀 합계 < 직전 채택 모델 값이면 채택, 아니면 직전 모델 유지(데이터는 누적).
  a0=$(echo "$e0" | grep -oE "회피가능 [0-9]+" | awk '{s+=$2} END{print s+0}'); t0=$(echo "$e0" | grep -oE "복귀 [0-9]+" | awk '{s+=$2} END{print s+0}')
  a1=$(echo "$e1" | grep -oE "회피가능 [0-9]+" | awk '{s+=$2} END{print s+0}'); t1=$(echo "$e1" | grep -oE "복귀 [0-9]+" | awk '{s+=$2} END{print s+0}')
  if [ "$a0" = 0 ] && [ "$t0" -le 1 ] && [ "$a1" = 0 ] && [ "$t1" -lt "${BEST_T1:-7}" ]; then verdict="채택(T1 복귀 ${BEST_T1:-7}→$t1)"; prev=$out; BEST_T1=$t1; else verdict="기각(직전 $prev 유지; T0 $a0/$t0, T1 $a1/$t1)"; fi
  python3 $NT "[밤샘 조향 lp$k] T0: $(echo "$e0" | sed 's/EVALPED T0 ode_v2.pt://') | T1: $(echo "$e1" | sed 's/EVALPED T1 ode_v2.pt://') → $verdict" >/dev/null 2>&1
  echo "verdict lp$k: $verdict"; r=$((r+10)); k=$((k+1))
done
pkill -x "Google Chrome"; echo "=== night loop end $(date +%H:%M:%S) last $prev ==="; python3 $NT "[밤샘 조향] 종료. 마지막 모델 $prev" >/dev/null 2>&1
