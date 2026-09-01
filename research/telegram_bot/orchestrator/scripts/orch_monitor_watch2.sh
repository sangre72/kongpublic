#!/usr/bin/env bash
# 오케 Monitor 2 = 감시자의 감시자 (watchdog v2 + launchd revive, a_292).
# 유저 지시 2026-08-10: "모니터 사망 시 발생 현상 확인할 다른 모니터링 하나 더 띄워라 / 이상동작·사망하면 다시 살려라".
#
# ★v1(orch_monitor_watchdog.sh) 결함: pkill+nohup 직접 부활 → 진동(2026-08-10).
# ★v2: 감지·알림만 → 세션 죽으면 부활 주체도 사라짐 → 155min death-alert (2026-08-15).
# ★v3(a_292): dead 시 launchctl kickstart com.kongbot.orch-tick (worker1_watch2 동일 패턴).
#   NEVER ensure_tick from here (kickstart -k BOTH). NEVER nohup/pkill peer tick loop.
#   세션 Monitor 재무장도 병행 가능(stdout MONITOR1_DOWN) — 하트비트 소유는 launchd.
#
# 판정(둘 중 하나면 dead):
#   - heartbeat(logs/.orch_alive) 나이 > STALE_SEC(기본 30초) → tick 루프 멈춤.
#   - tick(logs/.orch_tick) 값이 이전 관측 대비 미증가(정지) — 프로세스는 떠도 hang 인 경우.
# 방출: MONITOR1_DOWN <사유> (dead 일 때만·연속 중복 억제) / 정상은 무음.
set -uo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$REPO_ROOT" || { echo "MONITOR1_DOWN watch2 ROOT cd 실패"; exit 0; }

ALIVE="logs/.orch_alive"
TICKF="logs/.orch_tick"
STATE="logs/.orch_watch2_state"   # 이전 tick·중복억제 상태
STALE_SEC="${ORCH_STALE_SEC:-30}"
now=$(date +%s)

# heartbeat 나이
age=999999
[ -f "$ALIVE" ] && age=$(( now - $(stat -f %m "$ALIVE" 2>/dev/null || echo 0) ))

# tick 증가 여부(이전 관측과 비교)
cur_tick=$(cat "$TICKF" 2>/dev/null || echo 0)
prev_tick=0; prev_emit=0
[ -f "$STATE" ] && { read -r prev_tick prev_emit < "$STATE" 2>/dev/null || true; }
: "${prev_tick:=0}"; : "${prev_emit:=0}"

dead=0; reason=""
if [ "$age" -gt "$STALE_SEC" ]; then dead=1; reason="heartbeat stale(${age}s>${STALE_SEC}s)"; fi
# tick 정지: 이전에 관측한 값과 동일하고, heartbeat 도 안 신선하면 hang (stale 조건과 중복 시 stale 우선)
if [ "$dead" -eq 0 ] && [ "$cur_tick" = "$prev_tick" ] && [ "$age" -gt 25 ]; then
  dead=1; reason="tick 정지($cur_tick 고정·heartbeat ${age}s)"
fi

if [ "$dead" -eq 1 ]; then
  # 연속 중복 방출 억제: 직전에 이미 방출(prev_emit=1)했으면 무음
  if [ "$prev_emit" != "1" ]; then
    echo "MONITOR1_DOWN $reason — revive launchd orch-tick (no -k unless hung)"
  fi
  echo "$cur_tick 1" > "$STATE"
  # Revive launchd tick only. NEVER call orch_ensure_tick here (could -k both).
  # NEVER nohup a peer tick loop (oscillation lesson).
  uidn=$(id -u)
  job="gui/${uidn}/com.kongbot.orch-tick"
  if launchctl print "$job" 2>/dev/null | grep -q 'state = running'; then
    # process alive but tick frozen → hung; then -k
    launchctl kickstart -k "$job" 2>/dev/null || true
  else
    launchctl kickstart "$job" 2>/dev/null || true
  fi
else
  echo "$cur_tick 0" > "$STATE"   # 정상: emit 플래그 해제(다음 사망 시 재방출)
fi
exit 0
