#!/usr/bin/env bash
# wake_verify_submit.sh <tty> — u_5819/u_5823: after a wake inject, confirm the Claude Code input box
# is empty. A long inject can land as "[Pasted text #N]" and the Enter keystrokes get absorbed, so the
# message sits unsent (observed 2026-09-30, a_5818 PRIORITY msg). Re-send Enter up to 3x until the
# prompt line is empty or shows the queued-message hint. Prints VERIFY_OK / VERIFY_STUCK.
TTY="$1"; [[ -z "$TTY" ]] && { echo "VERIFY_SKIP(no tty)"; exit 0; }
prompt_line() {
  # The live input box = the line(s) between the LAST two '────' border rules. A bare "last ❯ line"
  # matched an already-submitted prompt in scrollback (22:06 false STUCK on u_5829). No box found
  # → print __NOBOX__ (caller treats as unknown, never spams Enter).
  osascript <<EOF2 2>/dev/null | python3 -c '
import sys
L=sys.stdin.read().split("\n")
r=[k for k,x in enumerate(L) if x.startswith("\u2500\u2500\u2500\u2500")]
if len(r)<2: print("__NOBOX__"); sys.exit()
a,b=r[-2],r[-1]
box=" ".join(x.strip() for x in L[a+1:b]).strip()
print(box if box else "\u276f")'
tell application "Terminal"
  repeat with w in windows
    repeat with t in tabs of w
      if (tty of t) is "$TTY" then return (history of t)
    end repeat
  end repeat
end tell
EOF2
}
# u_5826: a single empty read at 1.5s is not proof — the TUI can render the inject late. Require two
# consecutive empty reads; every non-empty read re-sends Enter. All outcomes logged for diagnosis.
LOG="$(cd "$(dirname "$0")/../../.." && pwd)/logs/wake_verify.log"
empty=0; sent=0; qflush=0
for i in 1 2 3 4 5; do
  sleep 1.5
  L=$(prompt_line)
  if [[ "$L" == "__NOBOX__" ]]; then echo "$(date '+%F %T') $TTY NOBOX" >> "$LOG"; echo "VERIFY_NOBOX"; exit 0; fi
  body=$(printf '%s' "${L#❯}" | sed 's/[[:space:]]*$//; s/^[[:space:]]*//')
  # queued hint = message parked in the TUI queue; observed 22:04 it was NOT flushed when the session
  # went idle (delivered only with the next submit). One extra Enter flushes it; harmless if busy.
  if [[ "$body" == "Press up to edit queued messages"* && $qflush -eq 0 ]]; then
    qflush=1; body="QUEUED"
  fi
  if [[ -z "$body" || "$body" == "Press up to edit queued messages"* ]]; then
    empty=$((empty+1))
    if [[ $empty -ge 2 ]]; then
      echo "$(date '+%F %T') $TTY OK try=$i resent=$sent" >> "$LOG"; echo "VERIFY_OK(try=$i,resent=$sent)"; exit 0
    fi
    continue
  fi
  empty=0; sent=$((sent+1))
  osascript <<EOF3 >/dev/null 2>&1
tell application "Terminal"
  repeat with w in windows
    repeat with t in tabs of w
      if (tty of t) is "$TTY" then do script "" in t
    end repeat
  end repeat
end tell
EOF3
done
echo "$(date '+%F %T') $TTY STUCK resent=$sent prompt=${body:0:80}" >> "$LOG"
echo "VERIFY_STUCK(resent=$sent,prompt='${body:0:60}')"; exit 1
