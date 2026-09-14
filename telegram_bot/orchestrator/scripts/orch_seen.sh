#!/bin/bash
# orch_seen.sh <u_number ...>  — register u_ as processed by NUMBER, not hand-typed filename.
# WHY(2026-09-13 u_4820/4823): orch typed the basename by hand, truncated it
# (u_4816_..._완전_종료.txt vs real ..._완전_종료_하도.txt) -> grep -qx miss ->
# orch_monitor_tick.sh treated it as unprocessed -> re-notify every 60s = storm,
# which buried live commands and caused the perceived ~30s response lag.
# Rule: NEVER `echo <name> >> logs/.orch_seen_u` by hand. Always use this script.
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
UD="$ROOT/telegram_bot/orchestrator/protocol/u"
SEEN="$ROOT/logs/.orch_seen_u"
touch "$SEEN"
for n in "$@"; do
  found=0
  for f in "$UD"/u_${n}_*.txt; do
    [ -e "$f" ] || continue
    b=$(basename "$f"); found=1
    grep -qx "$b" "$SEEN" || { echo "$b" >> "$SEEN"; echo "SEEN+ $b"; }
  done
  [ "$found" = 1 ] || echo "WARN no u_${n}_*.txt found"
done
# report anything still unprocessed (this is what drives re-notify)
u=0
for f in "$UD"/u_*.txt; do
  b=$(basename "$f"); grep -qx "$b" "$SEEN" || { echo "UNSEEN $b"; u=$((u+1)); }
done
echo "unseen_total=$u"
