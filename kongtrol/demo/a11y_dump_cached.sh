#!/usr/bin/env bash
# a11y_dump_cached.sh <pid>  → stdout JSON dump. TTL=${A11Y_CACHE_TTL:-5}s (a_66).
#   Cuts repeated ground.sh AX-walk (Chrome ~0.57s) when worker still calls per-label.
#   Prefer `kongtrol input run` (1 dump in-process). This cache = ground.sh fallback.
set -u
PID="${1:?pid}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="$ROOT/target/release/kongtrol"
TTL="${A11Y_CACHE_TTL:-5}"
CACHE="${TMPDIR:-/tmp}/kongtrol_a11y_${PID}.json"
NOW=$(date +%s)
if [ -f "$CACHE" ]; then
  AGE=$((NOW - $(stat -f %m "$CACHE")))
  if [ "$AGE" -ge 0 ] && [ "$AGE" -lt "$TTL" ]; then
    cat "$CACHE"
    exit 0
  fi
fi
JSON=$("$BIN" --json see --a11y --pid "$PID" 2>/dev/null) || exit 1
printf '%s' "$JSON" > "$CACHE"
printf '%s' "$JSON"
