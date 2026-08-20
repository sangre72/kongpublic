#!/usr/bin/env bash
# M2 loop for launchd. Calls worker1_watch2.sh every 15s. No inline match logic.
# Absolute kong-bot root (never git rev-parse / sky cwd).
set -u
SELF="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR="$(cd "$(dirname "$SELF")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
[ -d "$ROOT/telegram_bot/orchestrator/scripts" ] || { echo "worker1_watch2_loop: ROOT verify 실패($ROOT)" >&2; exit 1; }
cd "$ROOT" || exit 1
export KONG_WORKER_ROOT="$ROOT"
while true; do
  KONG_WORKER_MON2=1 bash "$SCRIPT_DIR/worker1_watch2.sh" || true
  sleep 15
done
