#!/bin/bash
# Draw curved strokes: each stroke = chained short drags between consecutive polyline pts
# (shared endpoints → continuous curved line, not dots). fills first, outlines last.
KT=/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol
PLAN=/Users/bumsuklee/git/kong-bot/kong3d/stroke_plan.json
OX=238; OY=191
setcol(){ $KT input click 132 173 --yes >/dev/null 2>&1; sleep 0.1; $KT input chord cmd a --yes >/dev/null 2>&1; sleep 0.07; $KT input text --yes "$1" >/dev/null 2>&1; sleep 0.07; $KT input click 132 205 --yes >/dev/null 2>&1; sleep 0.1; }
# brush size preset: fills=9(slider x~92), outline=4(x~80). we set via slider drag when size changes.
setsize(){ $KT input drag 74 310 $1 310 --yes >/dev/null 2>&1; sleep 0.15; }
python3 - "$PLAN" <<'PY' | while IFS=$'\t' read -r kind a b; do
import json,sys
p=json.load(open(sys.argv[1]))
# order: fill strokes(non-black) then outlines(black) so outlines sit on top
fills=[s for s in p["strokes"] if s["c"]!="#161616"]
outs=[s for s in p["strokes"] if s["c"]=="#161616"]
last=None; lastsz=None
for s in fills+outs:
    if s["c"]!=last: print("C\t"+s["c"]+"\t"); last=s["c"]
    if s["size"]!=lastsz: print("S\t%d\t"%s["size"]); lastsz=s["size"]
    print("K\t"+json.dumps(s["pts"])+"\t")
PY
  case "$kind" in
    C) setcol "$a" ;;
    S) if [ "$a" -le 5 ]; then setsize 80; else setsize 92; fi ;;
    K) # chained drags through the polyline points
       python3 - "$a" "$OX" "$OY" <<'PY2' | while IFS=$'\t' read x0 y0 x1 y1; do
import json,sys
pts=json.loads(sys.argv[1]); ox=int(sys.argv[2]); oy=int(sys.argv[3])
for i in range(len(pts)-1):
    a=pts[i]; b=pts[i+1]
    print(f"{ox+int(a[0])}\t{oy+int(a[1])}\t{ox+int(b[0])}\t{oy+int(b[1])}")
PY2
         $KT input drag $x0 $y0 $x1 $y1 --yes >/dev/null 2>&1; sleep 0.03
       done ;;
  esac
done
echo STROKE_DONE
