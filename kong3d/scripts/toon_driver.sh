#!/bin/bash
KT=/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol
PLAN=/Users/bumsuklee/git/kong-bot/kong3d/toon_plan.json
OX=238; OY=191
setcol(){ $KT input click 132 173 --yes >/dev/null 2>&1; sleep 0.12; $KT input chord cmd a --yes >/dev/null 2>&1; sleep 0.08; $KT input text --yes "$1" >/dev/null 2>&1; sleep 0.08; $KT input click 132 205 --yes >/dev/null 2>&1; sleep 0.12; }
python3 - "$PLAN" <<'PY' | while IFS=$'\t' read -r kind a b c; do
import json,sys
p=json.load(open(sys.argv[1]))
for grp in p["fills"]:
    print("C\t"+grp["c"]+"\t\t")
    for cy,x0,x1 in grp["runs"]: print(f"R\t{cy}\t{x0}\t{x1}")
print("C\t#141414\t\t")        # bold dark outline color
for cy,x0,x1 in p["outline"]: print(f"O\t{cy}\t{x0}\t{x1}")
PY
  if [ "$kind" = "C" ]; then setcol "$a"
  else
    sx0=$(python3 -c "print(int($OX+$b))"); sx1=$(python3 -c "print(int($OX+$c))"); sy=$(python3 -c "print(int($OY+$a))")
    $KT input drag $sx0 $sy $sx1 $sy --yes >/dev/null 2>&1; sleep 0.05
  fi
done
echo TOON_DONE
