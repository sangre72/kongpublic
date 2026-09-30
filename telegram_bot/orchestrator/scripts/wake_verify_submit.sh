#!/usr/bin/env bash
# wake_verify_submit.sh <tty> — u_5819/u_5823: after a wake inject, confirm the Claude Code input box
# is empty. A long inject can land as "[Pasted text #N]" and the Enter keystrokes get absorbed, so the
# message sits unsent (observed 2026-09-30, a_5818 PRIORITY msg). Re-send Enter up to 3x until the
# prompt line is empty or shows the queued-message hint. Prints VERIFY_OK / VERIFY_STUCK.
TTY="$1"; [[ -z "$TTY" ]] && { echo "VERIFY_SKIP(no tty)"; exit 0; }
prompt_line() {
  osascript <<EOF2 2>/dev/null | grep -E '^❯' | tail -1
tell application "Terminal"
  repeat with w in windows
    repeat with t in tabs of w
      if (tty of t) is "$TTY" then return (contents of t)
    end repeat
  end repeat
end tell
EOF2
}
for i in 1 2 3; do
  sleep 1.5
  L=$(prompt_line)
  body=$(printf '%s' "${L#❯}" | sed 's/[[:space:]]*$//; s/^[[:space:]]*//')
  if [[ -z "$body" || "$body" == "Press up to edit queued messages"* ]]; then echo "VERIFY_OK(try=$i)"; exit 0; fi
  osascript <<EOF3 >/dev/null 2>&1
tell application "Terminal"
  repeat with w in windows
    repeat with t in tabs of w
      if (tty of t) is "$TTY" then do script (return & "") in t
    end repeat
  end repeat
end tell
EOF3
done
echo "VERIFY_STUCK(prompt='${body:0:60}')"; exit 1
