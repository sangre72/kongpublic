#!/usr/bin/env bash
# 오케 모니터링 워치독 (유저 지시 2026-08-06: "20분마다 세션 유지하면서 모니터링도 죽어있으면 살려라")
#
# 역할: heartbeat(logs/.orch_alive)가 stale 하거나 monitor loop 프로세스가 없으면
#        → monitor loop 를 백그라운드로 재기동한다. 살아있으면 아무것도 안 함(idempotent).
# 호출: 오케 세션이 20분 주기(ScheduleWakeup)로 이 스크립트를 실행 → 세션 유지 + 모니터링 자동복구.
#
# 판정 기준:
#   - .orch_alive 나이 > STALE_SEC(기본 30초) → tick loop 가 멈춤(heartbeat 안 뜀) → 죽음으로 간주.
#   - orch_monitor_tick.sh 를 도는 loop 프로세스(pgrep) 부재 → 죽음.
# 방출(stdout 1줄): ALIVE / REVIVED(재기동함) / 상세.
set -uo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$REPO_ROOT"

ALIVE="logs/.orch_alive"
STALE_SEC="${ORCH_STALE_SEC:-30}"
LOG="logs/orch_monitor.log"
mkdir -p logs

now=$(date +%s)

# (1) loop 프로세스 존재? (tick 을 도는 while 루프)
loop_running=0
if pgrep -f "orch_monitor_tick.sh" >/dev/null 2>&1; then loop_running=1; fi

# (2) heartbeat 신선도
age=999999
if [ -f "$ALIVE" ]; then age=$(( now - $(stat -f %m "$ALIVE" 2>/dev/null || echo 0) )); fi

dead=0
reason=""
if [ "$loop_running" -eq 0 ]; then dead=1; reason="loop 프로세스 없음"; fi
if [ "$age" -gt "$STALE_SEC" ]; then dead=1; reason="${reason:+$reason·}heartbeat stale(${age}s>${STALE_SEC}s)"; fi

if [ "$dead" -eq 0 ]; then
  echo "ALIVE monitor loop 정상(heartbeat ${age}s)"
  exit 0
fi

# 재기동: 기존 잔여 loop 정리 후 새 loop 를 nohup 백그라운드로 기동.
pkill -f "orch_monitor_tick.sh" 2>/dev/null || true
sleep 1
nohup bash -c 'cd '"$REPO_ROOT"'; while true; do bash telegram_bot/orchestrator/scripts/orch_monitor_tick.sh >> logs/orch_monitor.log 2>&1; sleep 5; done' >/dev/null 2>&1 &
newpid=$!
echo "$(date '+%Y-%m-%d %H:%M:%S') REVIVED monitor loop 재기동(pid=$newpid) — 사유: $reason" | tee -a "$LOG"
echo "REVIVED monitor loop 재기동됨(pid=$newpid) — 사유: $reason"
