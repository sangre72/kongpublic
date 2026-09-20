#!/bin/bash
# missing ids via Studio search box (rows below the fold never enter a11y)
KT=/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol
P=$(pgrep -x "Google Chrome"|head -1)
OUT=/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp/a20/list.tsv
declare -A KEY=([쥐띠]=rat [소띠]=ox [호랑이띠]=tiger [토끼띠]=rabbit [용띠]=dragon [뱀띠]=snake [말띠]=horse [양띠]=goat [원숭이띠]=monkey [닭띠]=rooster [개띠]=dog [돼지띠]=pig)
LIST="https://studio.youtube.com/channel/UCnWpdI21BQttu8hs2j41YpQ/videos/short"
for z in 쥐띠 소띠 호랑이띠 토끼띠 용띠 뱀띠 말띠 양띠 원숭이띠 닭띠 개띠 돼지띠; do
  grep -q "^$z	" $OUT && continue
  osascript -e "tell application \"Google Chrome\" to set URL of active tab of front window to \"$LIST\"" >/dev/null; sleep 7
  open -a "Google Chrome"; sleep 1
  S=$($KT see --pid $P --a11y 2>&1 | grep -E "^AXTextField" | grep -vE "주소창" | head -1 | grep -oE "@\([0-9]+,[0-9]+\)" | tr -d '@()' | tr ',' ' ')
  [ -n "$S" ] || { echo "$z NO-SEARCH"; continue; }
  $KT input click $S --yes >/dev/null; sleep 1
  $KT input key backspace --repeat 60 --yes >/dev/null; sleep 0.5
  $KT input text "9월 20일 $z" --yes >/dev/null; sleep 1
  $KT input key enter --yes >/dev/null; sleep 6
  C=$($KT see --pid $P --a11y 2>&1 | grep -E "^AXLink" | grep -v "미리보기" | grep -E "· 2026년 9월 20일 $z " | head -1 | grep -oE "@\([0-9]+,[0-9]+\)" | tr -d '@()' | tr ',' ' ')
  [ -n "$C" ] || { echo "$z NO-LINK-AFTER-SEARCH"; continue; }
  $KT input click $C --yes >/dev/null; sleep 6
  U=$(osascript -e 'tell application "Google Chrome" to get URL of active tab of front window')
  ID=$(echo "$U" | grep -oE "video/[A-Za-z0-9_-]{11}" | head -1 | cut -d/ -f2)
  if [ -n "$ID" ]; then printf "%s\t%s\t%s\n" "$z" "$ID" "${KEY[$z]}" >> $OUT; echo "$z $ID"; else echo "$z NO-ID url=$U"; fi
done
echo "IDS3_DONE $(wc -l < $OUT)"
