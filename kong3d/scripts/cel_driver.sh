#!/bin/bash
KT=/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol
PLAN=/Users/bumsuklee/git/kong-bot/kong3d/cel_plan.json
OX=238; OY=191
setcol(){ $KT input click 132 173 --yes >/dev/null 2>&1; sleep 0.1; $KT input chord cmd a --yes >/dev/null 2>&1; sleep 0.07; $KT input text --yes "$1" >/dev/null 2>&1; sleep 0.07; $KT input click 132 205 --yes >/dev/null 2>&1; sleep 0.1; }
setbrush(){ $KT input click 132 366 --yes >/dev/null 2>&1; sleep 0.15; }
setsize(){ $KT input drag 74 310 $1 310 --yes >/dev/null 2>&1; sleep 0.15; }
# ZONES: brush ~8 flat fills
setbrush
setsize 90
python3 - "$PLAN" <<'PY' | while IFS=$'\t' read -r kind a b c; do
import json,sys
p=json.load(open(sys.argv[1]))
for z in p["fills"]:
    print("C\t"+z["c"]+"\t\t")
    for cy,x0,x1 in z["runs"]: print(f"R\t{cy}\t{x0}\t{x1}")
PY
  if [ "$kind" = "C" ]; then setcol "$a"
  else
    sx0=$(python3 -c "print(int($OX+$b))"); sx1=$(python3 -c "print(int($OX+$c))"); sy=$(python3 -c "print(int($OY+$a))")
    $KT input drag $sx0 $sy $sx1 $sy --yes >/dev/null 2>&1; sleep 0.04
  fi
done
echo ZONES_DONE
# OUTLINES: size 4, dark, each contour = one continuous chained drag sequence
setsize 80
setbrush
setcol "#161616"
python3 - "$PLAN" "$OX" "$OY" <<'PY' | while IFS=$'\t' read x0 y0 x1 y1; do
import json,sys
p=json.load(open(sys.argv[1])); ox=int(sys.argv[2]); oy=int(sys.argv[3])
for c in p["contours"]:
    for i in range(len(c)-1):
        a=c[i]; b=c[i+1]
        print(f"{ox+int(a[0])}\t{oy+int(a[1])}\t{ox+int(b[0])}\t{oy+int(b[1])}")
PY
  $KT input drag $x0 $y0 $x1 $y1 --yes >/dev/null 2>&1; sleep 0.03
done
echo CEL_DONE
