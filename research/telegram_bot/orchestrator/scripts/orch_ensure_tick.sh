#!/usr/bin/env bash
# Install launchd orch tick+M2. Idempotent. ★Do NOT kill a healthy job.
# Mirrors worker1_ensure_tick.sh. Root-fix for session-bound .orch_alive death (a_292).
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
  local st="$ROOT/logs/.orch_alive"
  [ -f "$st" ] || return 1
  local age=$(( $(date +%s) - $(stat -f %m "$st") ))
  [ "$age" -le 20 ]
}

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
  if [ "$label" = "com.kongbot.orch-tick" ]; then
    local py; py="$(resolve_py)"
    /usr/bin/sed -i '' "s#<string>/usr/bin/python3</string>#<string>${py}</string>#g; s#<string>/Users/bumsuklee/miniconda3/bin/python3</string>#<string>${py}</string>#g" "$dest"
    echo "orch_ensure_tick: tick python=${py}"
  fi
  if ! launchctl print "${DOMAIN}/${label}" >/dev/null 2>&1; then
    launchctl bootstrap "$DOMAIN" "$dest" 2>/dev/null \
      || launchctl load -w "$dest" 2>/dev/null || true
    launchctl enable "${DOMAIN}/${label}" 2>/dev/null || true
    launchctl kickstart "${DOMAIN}/${label}" 2>/dev/null || true
    echo "orch_ensure_tick: bootstrapped $label"
    return
  fi
  if job_running "$label"; then
    if [ "$label" = "com.kongbot.orch-tick" ] && tick_fresh; then
      echo "orch_ensure_tick: $label running + alive fresh — no kick"
      return
    fi
    if [ "$label" = "com.kongbot.orch-watch2" ]; then
      echo "orch_ensure_tick: $label running — no kick"
      return
    fi
  fi
  echo "orch_ensure_tick: restart $label (not running or alive stale)"
  launchctl kickstart -k "${DOMAIN}/${label}" 2>/dev/null \
    || launchctl kickstart "${DOMAIN}/${label}" 2>/dev/null || true
}

ensure_one com.kongbot.orch-tick "$SCRIPT_DIR/com.kongbot.orch-tick.plist"
ensure_one com.kongbot.orch-watch2 "$SCRIPT_DIR/com.kongbot.orch-watch2.plist"

sleep 2
ALIVE="$ROOT/logs/.orch_alive"
if [ -f "$ALIVE" ]; then
  age=$(( $(date +%s) - $(stat -f %m "$ALIVE") ))
  echo "orch_ensure_tick: alive_age=${age}s tick=$(cat "$ROOT/logs/.orch_tick" 2>/dev/null || echo '?')"
else
  echo "orch_ensure_tick: .orch_alive missing after bootstrap" >&2
  exit 1
fi
[ "$age" -le 20 ] || { echo "orch_ensure_tick: alive still stale ${age}s" >&2; exit 1; }
