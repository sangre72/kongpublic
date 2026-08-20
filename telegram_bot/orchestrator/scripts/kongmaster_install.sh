#!/usr/bin/env bash
# Install kongmaster as launchd job. Idempotent — safe to re-run.
# a_946/ar_946(2026-08-19)
set -u
SELF="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR="$(cd "$(dirname "$SELF")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
UID_N="$(id -u)"
DOMAIN="gui/${UID_N}"
AGENTS="${HOME}/Library/LaunchAgents"
mkdir -p "$AGENTS" "$ROOT/logs"

PLIST_SRC="$SCRIPT_DIR/com.kongbot.kongmaster.plist"
PLIST_DST="$AGENTS/com.kongbot.kongmaster.plist"

cp "$PLIST_SRC" "$PLIST_DST"

if launchctl print "${DOMAIN}/com.kongbot.kongmaster" >/dev/null 2>&1; then
  echo "kongmaster_install: already loaded — bootout+bootstrap to pick up plist changes"
  launchctl bootout "$DOMAIN" "$PLIST_DST" 2>/dev/null || true
fi
launchctl bootstrap "$DOMAIN" "$PLIST_DST"
launchctl kickstart -k "${DOMAIN}/com.kongbot.kongmaster"

echo "kongmaster_install: done"
launchctl print "${DOMAIN}/com.kongbot.kongmaster" 2>&1 | grep -E "state|pid" || true
