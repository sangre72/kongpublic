#!/bin/bash
D=/Users/bumsuklee/git/kong-bot/kaymaps/chrome/youtube/tools/run_2026-09-29
S=/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/scripts/yt_comment_state.sh
while IFS=$'\t' read -r Z ID K; do
  bash $S done 2026-09-29 "$K" 2>/dev/null && { echo "SKIP $Z"; continue; }
  if bash /Users/bumsuklee/git/kong-bot/kaymaps/chrome/youtube/tools/run_2026-09-29/cmt.sh "$Z" "$ID" 2>&1 | tail -1 | grep -q "PINNED"; then
    bash $S mark 2026-09-29 "$K" pinned >/dev/null; echo "DONE $Z"
  else echo "FAIL $Z"; fi
done < $D/list.tsv
