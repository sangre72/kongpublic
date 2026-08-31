#!/usr/bin/env bash
# 오케 세션 10초 감시 (1틱). Monitor 루프에서 while 로 10초마다 호출.
# 제5원칙(유저 지시 2026-08-05): 세션 Monitor 1개 + 20분 자동 timeout 초기화.
# 방출(stdout 1줄=이벤트): 새 미처리 u_(NEW_USER_MSG) / 봇죽음(BOT_DOWN) /
#   needs-info ar_(NEEDS_INFO) / (240틱=20분마다) MONITOR_RESET_DUE.
# 매 틱 scheduler-status.txt 갱신 + logs/.orch_alive heartbeat 갱신(loop 생존신호).
set -u
# 프로젝트 루트를 스크립트 위치 기준으로 자동 해석(범용 — 어느 경로에 복사돼도 동작).
# 이 스크립트: <ROOT>/telegram_bot/orchestrator/scripts/orch_monitor_tick.sh → 3단계 상위가 ROOT.
# ★조용한 exit 0 금지(2026-08-07 사고 핵심): cd 실패 시 stderr 에 사유 남기고 exit 1(감시 죽음이 보이게).
SELF="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR="$(cd "$(dirname "$SELF")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$ROOT" 2>/dev/null || { echo "orch_monitor_tick: ROOT cd 실패($ROOT) — 감시 중단" >&2; exit 1; }
UD=telegram_bot/orchestrator/protocol/u
AD=telegram_bot/orchestrator/protocol/a
ARD=telegram_bot/orchestrator/protocol/ar
SEEN=logs/.orch_seen_u
ESEEN=logs/.orch_monitor_emitted   # 이벤트 중복방출 방지(노이즈 제거)
CTL=logs/monitor-control.txt
ST=logs/scheduler-status.txt
TICKF=logs/.orch_tick
ALIVE=logs/.orch_alive
touch "$SEEN" "$ESEEN"
tick=$(cat "$TICKF" 2>/dev/null || echo 0); tick=$((tick+1)); echo "$tick" > "$TICKF"

# heartbeat 갱신 (loop 생존신호 — 봇 check_orch_alive 가 관찰)
date > "$ALIVE"

# (a) 새 미처리 u_ = seen 에 없는 u_ (1회만 방출)
newu=""
for f in "$UD"/u_*.txt; do
  [ -e "$f" ] || continue
  b=$(basename "$f")
  grep -qx "$b" "$SEEN" && continue          # 이미 처리됨
  newu="$newu $b"
  if grep -qx "U:$b" "$ESEEN"; then
    # 1회 방출 후 세션이 놓치면 재방출 없음 = 접수 안 된 것처럼 보임.
    # 60s(6틱@10s)마다 미처리 u_ 재방출해서 세션을 다시 깨움.
    # ★즉시-깨움은 kong_orchestrator.py의 _wake_orch_self()가 u_ 저장 시점에 담당(u_2801) —
    #   여기서는 놓친 경우의 재방출(fallback)만, 중복 wake-self 호출 없음.
    if [ $((tick % 6)) -eq 0 ]; then
      echo "NEW_USER_MSG $b"
      bash "$SCRIPT_DIR/orch_wake_self.sh" "re-notify unprocessed u_: $b" >/dev/null 2>&1 &
    fi
    continue
  fi
  echo "NEW_USER_MSG $b"
  echo "U:$b" >> "$ESEEN"
done
# 처리 완료된 u_ 는 방출기록에서 정리(다음 동명 방지는 seq 유일이라 불필요, 누적만 정리)

# (b) 봇 생존 — start_orchestrator.sh status
if ! telegram_bot/orchestrator/scripts/start_orchestrator.sh status 2>/dev/null | grep -q '실행중'; then
  if ! grep -qx "BOTDOWN" "$ESEEN"; then echo "BOT_DOWN 봇 파이프 정지 감지 — start 필요"; echo "BOTDOWN" >> "$ESEEN"; fi
else
  grep -qx "BOTDOWN" "$ESEEN" && sed -i '' "/^BOTDOWN\$/d" "$ESEEN" 2>/dev/null
fi

# (c) needs-info ar_ (ANSWER 미부착만, 1회 방출) + (c-2) done/error/failed(워커 완료) 1회 방출
# ★유저 지적 2026-08-05 "종료 감지를 왜 못했나": 기존 tick 이 done 을 안 잡아 워커 완료를 못 깨웠다 → 추가.
ni=""
for ar in "$AD"/ar_*.txt "$ARD"/ar_*.txt; do
  [ -e "$ar" ] || continue
  st=$(grep -m1 -iE '\[STATUS\]|STATUS-line:' "$ar" 2>/dev/null | tr 'A-Z' 'a-z')
  arb=$(basename "$ar")
  # needs-info: 오케 개입 대기(ANSWER 미부착만)
  if echo "$st" | grep -q 'needs-info' && ! grep -qi '\[ANSWER\]' "$ar" 2>/dev/null; then
    ni="$ni $arb"
    grep -qx "NI:$arb" "$ESEEN" && continue
    echo "NEEDS_INFO $arb"; echo "NI:$arb" >> "$ESEEN"; continue
  fi
  # done/error/failed: 워커 완료 → 오케가 실측 검증·마감하도록 1회 방출
  if echo "$st" | grep -qE 'done|error|failed|blocked'; then
    grep -qx "WD:$arb" "$ESEEN" && continue
    echo "WORKER_DONE $arb ($st) — 오케 실측 검증 후 마감(§11.5 A-3: 실제 화면 확인)"; echo "WD:$arb" >> "$ESEEN"
  fi
done

# (d) 20분(240틱) 자동 timeout 리셋
if [ $((tick % 240)) -eq 0 ] && grep -q 'RESET_MONITOR' "$CTL" 2>/dev/null; then
  echo "MONITOR_RESET_DUE tick=$tick (20min) — 세션은 이 Monitor TaskStop 후 재arm"
fi

# scheduler-status 갱신 (statusLine·유저 확인용)
ts=$(date '+%H:%M:%S')
rem=$(( (240 - tick % 240) * 10 / 60 ))
bot=$(telegram_bot/orchestrator/scripts/start_orchestrator.sh status 2>/dev/null | grep -q '실행중' && echo '살아있음' || echo '죽음')
printf '세션유지 스케줄러 · %s · 다음 timeout초기화까지 %s분 · 봇=%s · 대기u_=[%s]\n' \
  "$ts" "$rem" "$bot" "${newu# }" > "$ST"
