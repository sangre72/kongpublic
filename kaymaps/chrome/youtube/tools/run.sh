#!/bin/bash
D=/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp/a19
S=/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/yt_comment_state.sh
while IFS=$'\t' read -r Z ID K; do
  bash $S done 2026-09-19 "$K" 2>/dev/null && { echo "SKIP $Z"; continue; }
  if bash $D/cmt.sh "$Z" "$ID" 2>&1 | tail -1 | grep -q "PINNED"; then
    bash $S mark 2026-09-19 "$K" pinned >/dev/null; echo "DONE $Z"
  else echo "FAIL $Z"; fi
done < $D/list.tsv
