#!/usr/bin/env bash
# Orch SessionStart/P0. Never stop a healthy watch. Dup-prevent only.
# Heartbeat owner = launchd com.kongbot.orch-tick (a_292). Session Monitor = TUI badge + re-arm path.
set -u
SELF="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR="$(cd "$(dirname "$SELF")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$ROOT" || exit 1
# ★AUTO-TTY-REGISTER(u_2026-09-03): SessionStart 훅에서 이 세션 tty를 자동 등록 →
#   껐다 켤 때 수동 session_register_tty.sh 불필요(wake 스크립트가 tty로 창 매칭).
bash "$SCRIPT_DIR/session_register_tty.sh" orch 2>&1 || echo "WARN: tty auto-register failed(fallback=title-phrase match)"
bash "$SCRIPT_DIR/orch_ensure_tick.sh" || true
ALIVE=logs/.orch_alive
age=999
[ -f "$ALIVE" ] && age=$(( $(date +%s) - $(stat -f %m "$ALIVE") ))
echo "ORCH_P0 alive_age=${age}s tick=$(cat logs/.orch_tick 2>/dev/null || echo '?')"
[ -f logs/scheduler-status.txt ] && cat logs/scheduler-status.txt
echo "KEEP-ON: do not kill launchd orch-tick/orch-watch2. Dup-prevent: do not start a 2nd of the same job."
echo "SESSION ARM (Claude/Grok Monitor — ★persistent=true · BAN timeout_ms 1h/30m). Skip if already armed this session."
echo "ARM_M1 persistent=true desc='telegram u_ user-request 5s watch (orch Monitor 1, no 1h timeout)'"
echo "ARM_M1_CMD: cd \"$ROOT\" || exit 1; while true; do bash telegram_bot/orchestrator/scripts/orch_monitor_tick.sh; sleep 5; done"
echo "ARM_1M: scheduler_create interval=60s foreground=true ONE only (KEEP 60s · never stretch 5m · never delete live). prompt=bash orch_rearm_check.sh → REARM_* = Monitor tool now."
echo "ARM_M2 persistent=true desc='orch Monitor 2 = watchdog v2 (no 30min timeout)'"
echo "ARM_M2_CMD: cd \"$ROOT\" || exit 1; while true; do bash telegram_bot/orchestrator/scripts/orch_monitor_watch2.sh; sleep 15; done"
echo "NOTE: heartbeat never-die = launchd com.kongbot.orch-tick (+ watch2 kickstart). Session M1 timeout ≠ allowed."
