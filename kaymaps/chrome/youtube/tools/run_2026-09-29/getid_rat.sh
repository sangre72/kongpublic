#!/bin/bash
KT=/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol
P=$(pgrep -x "Google Chrome"|head -1)
OUT=/Users/bumsuklee/git/kong-bot/kaymaps/chrome/youtube/tools/run_2026-09-29/list.tsv
LIST="https://studio.youtube.com/channel/UCnWpdI21BQttu8hs2j41YpQ/videos/short"
z=${1:-쥐띠}   # 2026-09-27: 인자로 띠 지정
case "$z" in 쥐띠)KEY=rat;; 소띠)KEY=ox;; 호랑이띠)KEY=tiger;; 토끼띠)KEY=rabbit;; 용띠)KEY=dragon;; 뱀띠)KEY=snake;; 말띠)KEY=horse;; 양띠)KEY=goat;; 원숭이띠)KEY=monkey;; 닭띠)KEY=rooster;; 개띠)KEY=dog;; 돼지띠)KEY=pig;; *)KEY=unknown;; esac
find_link(){ $KT see --pid $P --a11y 2>&1 | grep -E "^AXLink" | grep -v "미리보기" | grep -E "· 2026년 9월 28일 $z " | head -1 | grep -oE "@\([0-9]+,[0-9]+\)" | tr -d '@()' | tr ',' ' '; }
osascript -e "tell application \"Google Chrome\" to set URL of active tab of front window to \"$LIST\"" >/dev/null; sleep 7
open -a "Google Chrome"; sleep 1
# A) scroll: focus the list by clicking the column header text "동영상", then arrow down
H=$($KT see --pid $P --a11y 2>&1 | grep -E "^AXStaticText" | grep -E "· 동영상$" | head -1 | grep -oE "@\([0-9]+,[0-9]+\)" | tr -d '@()' | tr ',' ' ')
[ -n "$H" ] && { $KT input click $H --yes >/dev/null; sleep 1; }
C=""
for s in 1 2 3 4 5 6 7 8; do $KT input key down --repeat 10 --yes >/dev/null 2>&1; sleep 1; C=$(find_link); [ -n "$C" ] && { echo "found by scroll ($s)"; break; }; done
# B) search box fallback
if [ -z "$C" ]; then
  S=$($KT see --pid $P --a11y 2>&1 | grep -E "^AXTextField" | grep -vE "주소창" | head -1 | grep -oE "@\([0-9]+,[0-9]+\)" | tr -d '@()' | tr ',' ' ')
  $KT input click $S --yes >/dev/null; sleep 1; $KT input key backspace --repeat 60 --yes >/dev/null; sleep 0.5
  $KT input text "쥐띠" --yes >/dev/null; sleep 1; $KT input key enter --yes >/dev/null; sleep 7
  C=$(find_link); [ -n "$C" ] && echo "found by search"
  [ -z "$C" ] && { $KT see --pid $P --a11y 2>&1 | grep -E "9월 23일|검색 결과|결과 없음" | head -5 | cut -c1-120; }
fi
[ -n "$C" ] || { echo "$z NO-LINK"; exit 1; }
$KT input click $C --yes >/dev/null; sleep 6
U=$(osascript -e 'tell application "Google Chrome" to get URL of active tab of front window')
ID=$(echo "$U" | grep -oE "video/[A-Za-z0-9_-]{11}" | head -1 | cut -d/ -f2)
[ -n "$ID" ] && { printf "%s\t%s\t%s\n" "$z" "$ID" "$KEY" >> $OUT; echo "$z $ID"; } || echo "$z NO-ID url=$U"
