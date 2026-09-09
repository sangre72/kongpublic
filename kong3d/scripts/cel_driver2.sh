#!/bin/bash
# Robust driver: reads a STATIC command file (no live pipe → no BrokenPipe stall).
KT=/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol
CMDS=/Users/bumsuklee/git/kong-bot/kong3d/cel_cmds.txt
setcol(){ $KT input click 132 173 --yes >/dev/null 2>&1; sleep 0.1; $KT input chord cmd a --yes >/dev/null 2>&1; sleep 0.07; $KT input text --yes "$1" >/dev/null 2>&1; sleep 0.07; $KT input click 132 205 --yes >/dev/null 2>&1; sleep 0.1; }
while IFS=' ' read -r op a b c d; do
  case "$op" in
    BRUSH) $KT input click 132 366 --yes >/dev/null 2>&1; sleep 0.12 ;;
    SIZE)  $KT input drag 74 310 "$a" 310 --yes >/dev/null 2>&1; sleep 0.12 ;;
    COL)   setcol "$a" ;;
    DRAG)  $KT input drag "$a" "$b" "$c" "$d" --yes >/dev/null 2>&1; sleep 0.03 ;;
  esac
done < "$CMDS"
echo CEL2_DONE
