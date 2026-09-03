#!/usr/bin/env bash
# SessionStart bootstrap — auto-detect this session's role(orch|worker1) and run its P0.
# WHY(u_2026-09-03): orch & worker run from the SAME kong-bot dir → share one .claude/settings.json,
#   so the SessionStart hook can't statically know which role a given session is. This resolves it
#   at runtime by the session's own tty, so BOTH roles auto-register tty + run correct P0 with zero
#   manual steps(껐다 켜도 session_register_tty.sh 수동 불필요).
#
# Role-decision:
#   1) resolve THIS session's claude-process tty(parent chain, same logic as session_register_tty.sh).
#   2) if it equals logs/.orch_tty_worker1 → worker1 ; if equals .orch_tty_orch → orch (re-confirm).
#   3) else(new tab, unknown tty) → CLAIM a free role: orch if its tty file is stale/missing, else worker1.
#      staleness = the tty in the file no longer belongs to a live claude process.
# Then: write .orch_tty_<role> to THIS tty + exec the role's P0 (stdout injected into session).
set -u
SELF="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR="$(cd "$(dirname "$SELF")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$ROOT" || exit 1
mkdir -p logs

# --- resolve this session's claude tty (walk parent chain) ---
resolve_tty() {
  local p=$$ ppid cmd t
  for _ in $(seq 1 12); do
    ppid=$(ps -o ppid= -p "$p" 2>/dev/null | tr -d ' '); [ -z "$ppid" ] && break
    cmd=$(ps -o command= -p "$ppid" 2>/dev/null || true)
    case "$cmd" in
      claude*) t=$(ps -o tty= -p "$ppid" 2>/dev/null | tr -d ' '); [ -n "$t" ] && [ "$t" != "??" ] && echo "/dev/$t"; return ;;
    esac
    p="$ppid"
  done
}
# is a given /dev/ttysNNN currently a LIVE claude session tty?
tty_has_live_claude() {
  local dev="${1#/dev/}"; [ -z "$dev" ] && return 1
  ps -t "$dev" -o command= 2>/dev/null | grep -q '^claude'
}

MY_TTY="$(resolve_tty)"
ORCH_F=logs/.orch_tty_orch
WK_F=logs/.orch_tty_worker1

ROLE=""
if [ -n "$MY_TTY" ]; then
  if [ "$MY_TTY" = "$(cat "$WK_F" 2>/dev/null)" ]; then ROLE=worker1
  elif [ "$MY_TTY" = "$(cat "$ORCH_F" 2>/dev/null)" ]; then ROLE=orch
  else
    # unknown tab → claim a free role. orch first if its slot is stale/missing.
    if ! tty_has_live_claude "$(cat "$ORCH_F" 2>/dev/null)"; then ROLE=orch
    elif ! tty_has_live_claude "$(cat "$WK_F" 2>/dev/null)"; then ROLE=worker1
    else ROLE=worker1; fi   # both live → default to worker (orch usually the long-lived one)
  fi
else
  # couldn't resolve tty(rare) → fall back to worker1 P0(prev default), no tty write.
  echo "SESSION_BOOTSTRAP WARN: tty unresolved — running worker1 P0 as fallback(no tty register)."
  exec bash "$SCRIPT_DIR/worker1_session_p0.sh"
fi

echo "SESSION_BOOTSTRAP role=$ROLE tty=$MY_TTY"
# register tty for THIS role (idempotent overwrite) then run its P0.
if [ "$ROLE" = "orch" ]; then
  echo "/dev/${MY_TTY#/dev/}" > "$ORCH_F" 2>/dev/null || true; echo "$MY_TTY" > "$ORCH_F"
  exec bash "$SCRIPT_DIR/orch_session_p0.sh"
else
  echo "$MY_TTY" > "$WK_F"
  exec bash "$SCRIPT_DIR/worker1_session_p0.sh"
fi
