#!/bin/bash
# up.sh <NN>  — upload scene_NN.mp4 for <DATE> with title line NN, publish public.
set -e
N="$1"; NN=$(printf "%02d" "$N")
KT=/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol
DIR="/Users/bumsuklee/workspace-egov/youtube-top/python-server/projects/<YYYYMMDD>_<DATE>_12간지_오늘의_운세_ko"
TITLE=$(sed -n "${N}p" /tmp/yt_titles_<DATE>.txt)
[ -n "$TITLE" ] || { echo "FAIL no title line $N"; exit 1; }
P=$(pgrep -x "Google Chrome"|head -1)
say(){ echo "[$NN] $*"; }
# a11y coord lookup: co "<AXType>" "<label regex>" -> "X Y" (2026-09-20: window width changed, hardcoded coords missed 만들기 by 240px)
co(){ $KT see --pid $P --a11y 2>&1 | grep -E "^$1 " | grep -E "· $2\$" | head -1 | grep -oE "@\([0-9]+,[0-9]+\)" | tr -d '@()' | tr ',' ' '; }
clk(){ local c; c=$(co "$1" "$2"); [ -n "$c" ] || { say "FAIL no a11y $1 $2"; exit 1; }; $KT input click $c --yes >/dev/null; }

# 1. fresh page + open dropzone
open -a "Google Chrome"; sleep 1.5
if $KT see --pid $P --a11y 2>&1 | grep -q "· 동영상 처리 중"; then $KT input key esc --yes >/dev/null; sleep 2; fi   # 이전 게시의 "처리 중" 다이얼로그 닫기
$KT input chord cmd r --yes >/dev/null; sleep 7
clk AXButton "만들기"; sleep 2
if ! $KT see --pid $P --a11y 2>&1 | grep -q "동영상 파일을 드래그"; then
  MI=""; for w in 1 2 3 4 5; do MI=$($KT see --pid $P --a11y 2>&1 | grep -m1 "AXMenuItem.*동영상 업로드" | sed -E 's/.*@\(([0-9]+),([0-9]+)\).*/\1 \2/'); [ -n "$MI" ] && break; sleep 2; done   # <DATE> scene09: 메뉴가 2초 안에 안 떠서 실패 → 최대 10초 폴링
  if [ -z "$MI" ]; then clk AXButton "만들기"; sleep 3; MI=$($KT see --pid $P --a11y 2>&1 | grep -m1 "AXMenuItem.*동영상 업로드" | sed -E 's/.*@\(([0-9]+),([0-9]+)\).*/\1 \2/'); fi
  [ -n "$MI" ] || { say "FAIL no upload entry"; exit 1; }
  $KT input click $(echo $MI) --yes >/dev/null; sleep 3
fi
$KT see --pid $P --a11y 2>&1 | grep -q "동영상 파일을 드래그" || { say "FAIL dropzone absent"; exit 1; }

# 2. Finder: select the file by name, verify 1 selected
open "$DIR"; sleep 2
open -a Finder; sleep 1
W=$($KT see --pid $(pgrep -x Finder) --a11y 2>&1 | grep -m1 "AXWindow" | sed -E 's/.*@\(([0-9]+),([0-9]+)\).*/\1 \2/')
WX=$(echo $W|cut -d' ' -f1)
if [ "$WX" -lt 1400 ]; then $KT input drag $WX 253 1400 253 --yes --human >/dev/null; sleep 1.5; fi
C=$($KT see --pid $(pgrep -x Finder) --a11y 2>&1 | grep -m1 "scene_${NN}\.mp4" | sed -E 's/.*@\(([0-9]+),([0-9]+)\).*/\1 \2/')
[ -n "$C" ] || { say "FAIL file coord"; exit 1; }
FX=$(echo $C|cut -d' ' -f1); FY=$(echo $C|cut -d' ' -f2)
$KT input click $FX $FY --yes >/dev/null; sleep 1
$KT see --pid $(pgrep -x Finder) --a11y 2>&1 | grep -q "1/17 선택됨" || { say "FAIL not 1 selected"; exit 1; }

# 3. drag to dropzone circle
DZ=$($KT see --pid $P --a11y 2>&1 | grep -m1 "동영상 파일을 드래그" | grep -oE "@\([0-9]+,[0-9]+\)" | tr -d '@()'); DX=${DZ%,*}; DY=$(( ${DZ#*,} - 100 ))   # 드롭 = 캡션 위 원 중심(레시피: 캡션 텍스트가 아니라 원)
[ -n "$DZ" ] || { say "FAIL no dropzone coord"; exit 1; }; say "dropzone $DX $DY"
$KT input drag $FX $FY $DX $DY --yes --human >/dev/null; sleep 7
GOT=$($KT see --pid $P --a11y 2>&1 | grep -A1 "파일 이름" | grep -o "scene_[0-9]*\.mp4" | head -1)
[ "$GOT" = "scene_${NN}.mp4" ] || { say "FAIL wrong file: $GOT"; exit 1; }

# 4. title
TC=$($KT see --pid $P --a11y 2>&1 | grep -E "^AXTextArea" | grep "제목 추가" | head -1 | grep -oE "@\([0-9]+,[0-9]+\)" | tr -d '@()' | tr ',' ' '); [ -n "$TC" ] || { say "FAIL no title field"; exit 1; }; say "title field $TC"; $KT input click $TC --yes >/dev/null; sleep 1
$KT input key backspace --repeat 80 --yes >/dev/null; sleep 0.5
$KT input text "$TITLE" --yes >/dev/null; sleep 2
CNT=$($KT see --pid $P --a11y 2>&1 | grep -oE "[0-9]+/100" | head -1)
[ "${CNT%%/*}" -gt 10 ] || { say "FAIL title empty ($CNT)"; exit 1; }
say "title ok $CNT"

# 5. next x3 -> visibility
for i in 1 2 3; do clk AXButton "다음"; sleep 2.5; done
$KT see --pid $P --a11y 2>&1 | grep -q "저장 또는 게시" || { say "FAIL not on visibility tab"; exit 1; }
clk AXRadioButton "공개"; sleep 1.5

# 6. publish — ★<DATE> scene08: '검사 중' 이면 게시 버튼이 비활성이라 클릭이 무시되고 다음 cmd+r 이 '사이트에서 나가시겠습니까' 를 띄워 이후 전부 막혔다. 검사 완료까지 최대 12분 대기.
for w in $(seq 1 72); do if $KT see --pid $P --a11y 2>&1 | grep -q "검사가 완료되었습니다"; then break; fi; sleep 10; done
$KT see --pid $P --a11y 2>&1 | grep -q "검사가 완료되었습니다" || { say "FAIL checks not finished"; exit 1; }
$KT see --pid $P --a11y 2>&1 | grep -qE "AXButton .*· 게시$" || { say "FAIL no publish button"; exit 1; }
clk AXButton "게시"
OK=0
for t in 1 2 3 4 5 6 7 8; do sleep 5
  if $KT see --pid $P --a11y 2>&1 | grep -qE "AXHeading .*· 링크 공유|AXHeading .*· 동영상 처리 중"; then OK=1; break; fi   # 처리 전 게시 → "동영상 처리 중" 다이얼로그(공개 예정)도 성공
done
[ "$OK" = 1 ] || { say "FAIL publish not confirmed"; exit 1; }
clk AXButton "닫기"; sleep 2
say "PUBLISHED"
