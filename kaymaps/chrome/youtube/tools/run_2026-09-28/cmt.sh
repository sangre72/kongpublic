#!/bin/bash
# Recipe [12]: post the partners first comment on a Short and PIN it.
# usage: cmt.sh <label> <videoId>
# ★u_5332: NO cmd+a anywhere. address bar is set via AppleScript, not select-all.
set -e
L=$1; VID=$2
KT=/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol
SP=${SP:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}
PID=$(pgrep -x "Google Chrome"|head -1)
fg(){ osascript -e 'tell application "Google Chrome" to activate' >/dev/null; sleep 1.2; }
coord(){ $KT see --pid $PID --a11y 2>&1 | grep -E "$1" | grep -E "· $2\$" | head -1 \
         | grep -oE "@\([0-9]+,[0-9]+\)" | tr -d '@()' | tr ',' ' '; }
die(){ echo "CMT_$L FAIL: $1"; exit 1; }

echo "=== comment $L ($VID)"
osascript -e "tell application \"Google Chrome\" to set URL of active tab of front window to \"https://www.youtube.com/shorts/$VID\"" >/dev/null
sleep 9
fg

# wait for THIS video's comment button (a11y right after nav still shows the PREVIOUS page)
CBTN=""
for w in 1 2 3 4 5 6 7 8; do
  CBTN=$($KT see --pid $PID --a11y 2>&1 | grep -E "AXButton" | grep -oE "· 댓글( [0-9]+개)? 보기" | head -1)
  [ -n "$CBTN" ] && break
  sleep 2
done
[ -z "$CBTN" ] && die "comments button not found"
read CX CY < <($KT see --pid $PID --a11y 2>&1 | grep -E "AXButton" \
               | grep -E "· 댓글( [0-9]+개)? 보기\$" | head -1 \
               | grep -oE "@\([0-9]+,[0-9]+\)" | tr -d '@()' | tr ',' ' ')
echo "  button: $CBTN"
fg; $KT input click $CX $CY --yes >/dev/null; sleep 4

# decide from the button LABEL: '댓글 보기' = 0 comments, '댓글 N개 보기' = already has some
SKIP=""
if echo "$CBTN" | grep -qE "[0-9]+개"; then
  if $KT see --pid $PID --a11y 2>&1 | grep -q "오늘 운세 보신 김에"; then
    $KT see --pid $PID --a11y 2>&1 | grep -qE "고정함" && { echo "  ALREADY comment+pinned -> skip"; exit 0; }
    echo "  comment exists, not pinned -> pin only"; SKIP=1
  fi
fi

if [ -z "$SKIP" ]; then
  BX=""; BY=""
  read BX BY < <($KT see --pid $PID --a11y 2>&1 | grep -E "AXTextField" | grep -E "댓글 추가" \
                 | head -1 | grep -oE "@\([0-9]+,[0-9]+\)" | tr -d '@()' | tr ',' ' ') || true
  if [ -z "$BX" ]; then
    read SBX SBY < <(coord AXButton "댓글") || true
    [ -z "$SBX" ] && die "comment box not found"
    BX=$((SBX-180)); BY=$((SBY-33))
  fi
  fg; $KT input click $BX $BY --yes >/dev/null; sleep 1.5
  bash $SP/typecmt.sh
  sleep 2
  read SX SY < <(coord AXButton "댓글")
  [ -z "$SX" ] && die "submit button not found"
  $KT input click $SX $SY --yes >/dev/null; sleep 7
  $KT see --pid $PID --a11y 2>&1 | grep -q "오늘 운세 보신 김에" || die "comment body absent after submit"
fi

# [12].4 PIN (mandatory — comment without pin = incomplete)
read MX MY < <(coord AXButton "작업 메뉴")
[ -z "$MX" ] && die "comment kebab not found"
fg; $KT input click $MX $MY --yes >/dev/null; sleep 2.5
read PX PY < <($KT see --pid $PID --a11y 2>&1 | grep -E "AXMenuItem" | grep -E "· 고정\$" \
               | head -1 | grep -oE "@\([0-9]+,[0-9]+\)" | tr -d '@()' | tr ',' ' ')
[ -z "$PX" ] && die "고정 menu item not found"
$KT input click $PX $PY --yes >/dev/null; sleep 2.5
read KX KY < <(coord AXButton "고정")
[ -z "$KX" ] && die "고정 confirm not found"
$KT input click $KX $KY --yes >/dev/null; sleep 5
$KT see --pid $PID --a11y 2>&1 | grep -qE "고정함" && echo "  OK $L comment+PINNED" \
  || die "pin marker not found via a11y"
