#!/usr/bin/env bash
# Install launchd tick+M2. Idempotent. ★Do NOT kill a healthy job.
# 2026-08-14: old version always `kickstart -k` → murdered both monitors on every ensure.
set -u
SELF="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR="$(cd "$(dirname "$SELF")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
UID_N="$(id -u)"
DOMAIN="gui/${UID_N}"
AGENTS="${HOME}/Library/LaunchAgents"
mkdir -p "$AGENTS" "$ROOT/logs"

job_running() {
  launchctl print "${DOMAIN}/$1" 2>/dev/null | grep -q 'state = running'
}

tick_fresh() {
  local st="$ROOT/logs/worker1_status.txt"
  [ -f "$st" ] || return 1
  local age=$(( $(date +%s) - $(stat -f %m "$st") ))
  [ "$age" -le 20 ]
}

# Same interpreter as Claude/Grok shells. Never pin /usr/bin/python3 (Xcode 3.9 stub).
resolve_py() {
  local py
  py="$(command -v python3 2>/dev/null || true)"
  if [ -x "${HOME}/miniconda3/bin/python3" ]; then
    case "$py" in
      /usr/bin/python3|"") py="${HOME}/miniconda3/bin/python3" ;;
    esac
  fi
  [ -n "$py" ] || py="/usr/bin/python3"
  printf '%s' "$py"
}

ensure_one() {
  local label="$1" src="$2"
  local dest="${AGENTS}/${label}.plist"
  cp "$src" "$dest"
  if [ "$label" = "com.kongbot.worker1-tick" ]; then
    local py; py="$(resolve_py)"
    # rewrite ProgramArguments[0] so Claude PATH python == launchd python
    /usr/bin/sed -i '' "s#<string>/usr/bin/python3</string>#<string>${py}</string>#g; s#<string>/Users/bumsuklee/miniconda3/bin/python3</string>#<string>${py}</string>#g" "$dest"
    echo "worker1_ensure_tick: tick python=${py}"
  fi
  if ! launchctl print "${DOMAIN}/${label}" >/dev/null 2>&1; then
    launchctl bootstrap "$DOMAIN" "$dest" 2>/dev/null \
      || launchctl load -w "$dest" 2>/dev/null || true
    launchctl enable "${DOMAIN}/${label}" 2>/dev/null || true
    launchctl kickstart "${DOMAIN}/${label}" 2>/dev/null || true
    echo "worker1_ensure_tick: bootstrapped $label"
    return
  fi
  if job_running "$label"; then
    if [ "$label" = "com.kongbot.worker1-tick" ] && tick_fresh; then
      echo "worker1_ensure_tick: $label running + tick fresh — no kick"
      return
    fi
    if [ "$label" = "com.kongbot.worker1-watch2" ]; then
      echo "worker1_ensure_tick: $label running — no kick"
      return
    fi
  fi
  # tick loaded but stale/not running → restart that job only
  echo "worker1_ensure_tick: restart $label (not running or tick stale)"
  launchctl kickstart -k "${DOMAIN}/${label}" 2>/dev/null \
    || launchctl kickstart "${DOMAIN}/${label}" 2>/dev/null || true
}

ensure_one com.kongbot.worker1-tick "$SCRIPT_DIR/com.kongbot.worker1-tick.plist"
ensure_one com.kongbot.worker1-watch2 "$SCRIPT_DIR/com.kongbot.worker1-watch2.plist"

sleep 2
ST="$ROOT/logs/worker1_status.txt"
if [ -f "$ST" ]; then
  age=$(( $(date +%s) - $(stat -f %m "$ST") ))
  echo "worker1_ensure_tick: tick_age=${age}s status=$(cat "$ST")"
else
  echo "worker1_ensure_tick: status missing after bootstrap" >&2
  exit 1
fi
[ "$age" -le 20 ] || { echo "worker1_ensure_tick: status still stale ${age}s" >&2; exit 1; }
