#!/usr/bin/env bash
# orch_stop_worker.sh — IMMEDIATE worker interrupt (u_3472+): ESC-inject cuts in-flight turn,
#   then wake follow-up asks worker to report ABORTED right away.
# Rationale: normal wake queues behind worker's current turn(LLM turn not interruptible).
#   ESC(key code 53) is a HARD interrupt to the worker TUI → stops current turn on the spot.
# Flow: focus worker tty window → System Events ESC → short delay → wake "report ABORTED".
# usage: bash orch_stop_worker.sh ["reason"]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TTY_FILE="$REPO_ROOT/logs/.orch_tty_worker1"
REASON="${1:-orch STOP}"

TARGET_TTY=""
[ -f "$TTY_FILE" ] && TARGET_TTY="$(tr -d '[:space:]' < "$TTY_FILE")"

# 1) focus worker window + ESC(key code 53) = immediate turn-interrupt.
osascript <<EOF >/dev/null 2>&1 || true
tell application "Terminal"
  set targetTty to "$TARGET_TTY"
  if targetTty is not "" then
    repeat with w in windows
      if (tty of w) is targetTty then
        set frontmost of w to true
        set index of w to 1
        exit repeat
      end if
    end repeat
  end if
  activate
end tell
delay 0.2
tell application "System Events" to key code 53
delay 0.1
tell application "System Events" to key code 53
EOF

# 2) wake follow-up: worker report ABORTED immediately (payload-in-wake).
sleep 0.4
bash "$SCRIPT_DIR/orch_wake_worker.sh" "INTERRUPTED(ESC) reason=$REASON. abort current task NOW, reply via wake 'ABORTED: <task> state=<partial>' immediately, then idle. ¬retry ¬resume-unless-told." 2>&1 | tail -1
echo "STOP-SENT: ESC+wake to worker($TARGET_TTY)"
