#!/usr/bin/env bash
# 워커 Monitor 2 = 워커 감시자의 감시자 (worker watchdog v2, non-invasive).
# 유저 지시 2026-08-10: "같은 작업(오케 dual-watch)을 워커에게도 정의 — 문제 발생시 대처".
#
# ★orch orch_monitor_watch2.sh 의 워커판. 판정 대상 = worker Monitor 1 (a_ 10s 감시).
# dead → stdout WORKER_MON1_DOWN + launchctl kickstart tick (no -k unless hung).
# NEVER ensure_tick from here (old ensure -k both jobs). NEVER nohup a peer tick.
#
# 판정(worker1_status.txt mtime + .worker1_tick):
#   - status.txt 나이 > STALE_SEC(기본 40초·10s poll + fork작업 지연 여유) → tick 루프 멈춤.
#   - .worker1_tick 값이 이전 관측 대비 미증가 & status age>25s → hang.
# 방출: WORKER_MON1_DOWN <사유> (dead 일 때만·연속 중복 억제) / 정상 무음.
set -uo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$REPO_ROOT" || { echo "WORKER_MON1_DOWN watch2 ROOT cd 실패"; exit 0; }

ST="logs/worker1_status.txt"
TICKF="logs/.worker1_tick"
STATE="logs/.worker1_watch2_state"
STALE_SEC="${WORKER1_STALE_SEC:-40}"
now=$(date +%s)

age=999999
[ -f "$ST" ] && age=$(( now - $(stat -f %m "$ST" 2>/dev/null || echo 0) ))

cur_tick=$(cat "$TICKF" 2>/dev/null || echo 0)
prev_tick=0; prev_emit=0
[ -f "$STATE" ] && { read -r prev_tick prev_emit < "$STATE" 2>/dev/null || true; }
: "${prev_tick:=0}"; : "${prev_emit:=0}"

dead=0; reason=""
if [ "$age" -gt "$STALE_SEC" ]; then dead=1; reason="worker1_status stale(${age}s>${STALE_SEC}s)"; fi
if [ "$dead" -eq 0 ] && [ "$cur_tick" = "$prev_tick" ] && [ "$age" -gt 25 ]; then
  dead=1; reason="worker tick 정지($cur_tick 고정·status ${age}s)"
fi

if [ "$dead" -eq 1 ]; then
  if [ "$prev_emit" != "1" ]; then
    echo "WORKER_MON1_DOWN $reason — revive launchd tick (no -k unless hung)"
  fi
  echo "$cur_tick 1" > "$STATE"
  # Revive launchd tick only. NEVER call ensure_tick here (old ensure did
  # kickstart -k on BOTH jobs → M1+M2 died together). NEVER nohup a peer loop.
  uidn=$(id -u)
  job="gui/${uidn}/com.kongbot.worker1-tick"
  if launchctl print "$job" 2>/dev/null | grep -q 'state = running'; then
    # process alive but tick frozen → hung; then -k
    launchctl kickstart -k "$job" 2>/dev/null || true
  else
    launchctl kickstart "$job" 2>/dev/null || true
  fi
else
  echo "$cur_tick 0" > "$STATE"
fi
exit 0
