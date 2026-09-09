#!/bin/bash
# Drive kongtrol to pixel-paint from pixel_plan_grouped.json.
# canvas origin (screen) = (238,191), ~1:1 to canvas coords. brush size ~4 (set once).
KT=/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol
PLAN=/Users/bumsuklee/git/kong-bot/kong3d/pixel_plan_grouped.json
OX=238; OY=191
setcol(){ $KT input click 132 173 --yes >/dev/null 2>&1; sleep 0.12; $KT input chord cmd a --yes >/dev/null 2>&1; sleep 0.08; $KT input text --yes "$1" >/dev/null 2>&1; sleep 0.08; $KT input click 132 205 --yes >/dev/null 2>&1; sleep 0.12; }
# iterate colors, set once, drag all its runs
python3 - "$PLAN" <<'PY' | while IFS=$'\t' read -r kind a b c d; do
import json,sys
plan=json.load(open(sys.argv[1]))
for grp in plan:
    print("C\t"+grp["c"]+"\t\t\t")
    for cy,x0,x1 in grp["runs"]:
        print(f"R\t{cy}\t{x0}\t{x1}\t")
PY
  if [ "$kind" = "C" ]; then setcol "$a"
  else
    sx0=$(python3 -c "print(int($OX+$b))"); sx1=$(python3 -c "print(int($OX+$c))"); sy=$(python3 -c "print(int($OY+$a))")
    $KT input drag $sx0 $sy $sx1 $sy --yes >/dev/null 2>&1; sleep 0.05
  fi
done
echo PIXEL_PAINT_DONE
