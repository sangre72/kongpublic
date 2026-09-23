#!/bin/bash
# collect today's 12 video ids from Studio content list: click each title link -> read URL via AppleScript (no screenshot OCR)
KT=/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol
P=$(pgrep -x "Google Chrome"|head -1)
OUT=/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp/a23/list.tsv; : > $OUT
Z=(쥐띠 소띠 호랑이띠 토끼띠 용띠 뱀띠 말띠 양띠 원숭이띠 닭띠 개띠 돼지띠)
K=(rat ox tiger rabbit dragon snake horse goat monkey rooster dog pig)
LIST="https://studio.youtube.com/channel/UCnWpdI21BQttu8hs2j41YpQ/videos/short"
for i in $(seq 0 11); do
  z=${Z[$i]}; k=${K[$i]}
  osascript -e "tell application \"Google Chrome\" to set URL of active tab of front window to \"$LIST\"" >/dev/null; sleep 6
  open -a "Google Chrome"; sleep 1
  C=$($KT see --pid $P --a11y 2>&1 | grep -E "^AXLink" | grep -v "미리보기" | grep -E "· 2026년 9월 23일 $z " | head -1 | grep -oE "@\([0-9]+,[0-9]+\)" | tr -d '@()' | tr ',' ' ')
  if [ -z "$C" ]; then echo "$z NO-LINK"; continue; fi
  $KT input click $C --yes >/dev/null; sleep 5
  U=$(osascript -e 'tell application "Google Chrome" to get URL of active tab of front window')
  ID=$(echo "$U" | grep -oE "video/[A-Za-z0-9_-]{11}" | head -1 | cut -d/ -f2)
  if [ -n "$ID" ]; then printf "%s\t%s\t%s\n" "$z" "$ID" "$k" >> $OUT; echo "$z $ID"; else echo "$z NO-ID url=$U"; fi
done
echo "IDS_DONE $(wc -l < $OUT)"
