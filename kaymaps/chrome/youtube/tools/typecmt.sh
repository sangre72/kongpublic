#!/bin/bash
# Type the multi-line comment into the focused YouTube comment box.
# ★measured (a_5066, still true): `input text` containing newlines types 0 chars;
#   one 300-char line is fine => it is the newlines, not the length.
#   `enter` SUBMITS the comment, so line breaks must be `chord shift enter`.
# ★u_5332: no cmd+a anywhere.
set -e
KT=/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol
SP=${SP:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}
first=1
while IFS= read -r line || [ -n "$line" ]; do
  [ $first -eq 0 ] && { $KT input chord shift enter --yes >/dev/null; sleep 0.25; }
  first=0
  [ -z "$line" ] && continue          # blank line = the shift+enter alone
  $KT input text "$line" --yes >/dev/null
  sleep 0.35
done < "$SP/comment.txt"
