#!/usr/bin/env bash
# Session M1 5s a_* intake (a_308). Does not replace launchd 10s tick.
set -u
SELF="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR="$(cd "$(dirname "$SELF")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
[ -d "$ROOT/telegram_bot/orchestrator/protocol/a" ] || { echo "worker1_session_m1_5s: ROOT verify 실패($ROOT)" >&2; exit 1; }
cd "$ROOT" || exit 1
while true; do
  KONG_WORKER_MON1=1 bash "$ROOT/telegram_bot/orchestrator/scripts/worker1_monitor_tick.sh" || true
  sleep 5
done
