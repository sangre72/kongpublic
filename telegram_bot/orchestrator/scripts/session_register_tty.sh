#!/usr/bin/env bash
# Register this session's Terminal tty into logs/.orch_tty_<role> for wake-script use.
# WHY(2026-08-30 u_re-fix pt.2): title-phrase-based window matching(Kong 역할 설정 확인/
#   Kong 워커 역할 정의) is fragile — that phrase is auto-derived by Claude Code from the
#   session's opening prompt/summary and can change on a fresh session. tty is stable for
#   the life of a Terminal tab regardless of title text — anchor on that instead.
# usage: bash session_register_tty.sh <role>   (role = "orch" or "worker1")
# Call once near session start(or whenever role is (re)confirmed). Idempotent(overwrites).
set -euo pipefail
ROLE="${1:?usage: session_register_tty.sh <orch|worker1>}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
mkdir -p "$REPO_ROOT/logs"
OUT="$REPO_ROOT/logs/.orch_tty_${ROLE}"

# Walk up the parent-process chain from this shell to find the `claude` process,
# then read its tty(the Terminal tab actually running this session).
p=$$
tty=""
for _ in $(seq 1 10); do
  ppid=$(ps -o ppid= -p "$p" 2>/dev/null | tr -d ' ')
  [ -z "$ppid" ] && break
  cmd=$(ps -o command= -p "$ppid" 2>/dev/null || true)
  case "$cmd" in
    claude*)
      tty=$(ps -o tty= -p "$ppid" 2>/dev/null | tr -d ' ')
      break
      ;;
  esac
  p="$ppid"
done

if [ -z "$tty" ] || [ "$tty" = "??" ]; then
  echo "FAIL: could not resolve claude-process tty from parent chain" >&2
  exit 1
fi

echo "/dev/$tty" > "$OUT"
echo "OK: role=$ROLE tty=/dev/$tty -> $OUT"
