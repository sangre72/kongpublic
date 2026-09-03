#!/usr/bin/env bash
# Claude + Grok SessionStart/P0. Never stop a healthy watch. Dup-prevent only.
# stdout is injected into the session (Claude SessionStart hook / worker ON LOAD).
set -u
SELF="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR="$(cd "$(dirname "$SELF")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$ROOT" || exit 1
# ★AUTO-TTY-REGISTER(u_2026-09-03): SessionStart 훅에서 이 워커 세션 tty를 자동 등록 →
#   껐다 켤 때 수동 session_register_tty.sh 불필요(orch↔worker wake가 tty로 창 매칭).
bash "$SCRIPT_DIR/session_register_tty.sh" worker1 2>&1 || echo "WARN: tty auto-register failed(fallback=title-phrase match)"
bash "$SCRIPT_DIR/worker1_ensure_tick.sh" || true
ST=logs/worker1_status.txt
age=999
[ -f "$ST" ] && age=$(( $(date +%s) - $(stat -f %m "$ST") ))
echo "WORKER1_P0 tick_age=${age}s"
[ -f "$ST" ] && cat "$ST"
echo "KEEP-ON: do not kill launchd tick/watch2. Dup-prevent: do not start a 2nd of the same job."
echo "RECOGNIZE: if status pending=[…] nonempty → pickup those a_ NOW (do not wait for PENDING_A event)."
echo "SESSION ARM (Claude Monitor tool OR Grok monitor tool — same cmds). Skip if this session already has them."
echo "ARM_M1 persistent=true desc='kong worker Monitor 1 = a_ 5s intake (u_308 5s SLA, no 1h timeout)'"
echo "ARM_M1_CMD: cd \"$ROOT\" || exit 1; setopt NULL_GLOB 2>/dev/null; shopt -s nullglob 2>/dev/null; while true; do KONG_WORKER_MON1=1 bash telegram_bot/orchestrator/scripts/worker1_monitor_tick.sh || echo TICK_ERROR exit=\$?; sleep 5; done"
echo "ARM_1M: scheduler_create interval=60s ONE only (Grok min · KEEP 60s · never stretch 5m · never delete live). prompt=bash worker1_watch2.sh + pickup pending from logs/worker1_status.txt. 1m never-die with launchd watch2."
echo "ARM_M2 persistent=true desc='kong worker Monitor 2 = watch2 TUI stream (no 30min timeout)'"
echo "ARM_M2_CMD: cd \"$ROOT\" || exit 1; while true; do KONG_WORKER_MON2=1 bash telegram_bot/orchestrator/scripts/worker1_watch2.sh; sleep 15; done"
echo "NOTE: 1m never-die owners = launchd com.kongbot.worker1-watch2 + ONE 60s scheduler. Session M2 badge expire ≠ 1m role dead."
