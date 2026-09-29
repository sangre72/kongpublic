#!/usr/bin/env bash
# u_5774: one route yields only ~6-7 usable perturbations before prog->1.0 and triggers stop.
# Loop routes until the target episode count is reached.
set -u
cd "$(dirname "${BASH_SOURCE[0]}")"
source ./park_page.sh; arm_park_trap
TARGET=${1:-32}; OUT=${2:-/tmp/rec_final.log}; : > "$OUT"
# u_5774: `grep -c` PRINTS 0 and EXITS 1 on no match, so `$(grep -c ... || echo 0)` yields "0\n0"
#   and every [ ] comparison dies with "integer expression expected" - the loop ran 0 routes.
have(){ grep -c '"cell"' "$OUT" 2>/dev/null | head -1 || true; }
ROUTES=('강동대로>삼학사로14길' '삼학사로14길>강동대로' '올림픽로37길>삼학사로19길' '삼학사로19길>올림픽로37길')
i=0
while [ "$(have)" -lt "$TARGET" ]; do
  R="${ROUTES[$((i % ${#ROUTES[@]}))]}"; i=$((i+1))
  echo "### route $i: $R  (have $(have)/$TARGET)" >> "$OUT"
  ROUTE="$R" bash recovery_run.sh 25 >> "$OUT" 2>&1
  if [ $i -ge 12 ]; then break; fi
  true
done
echo "### loop end routes=$i" >> "$OUT"
