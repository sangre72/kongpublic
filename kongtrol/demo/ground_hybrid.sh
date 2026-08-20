#!/usr/bin/env bash
# ground_hybrid.sh — a11y-FIRST then REMOTE VL (a_47). LOGICAL only.
#   contract: FOUND <lx> <ly> <a11y|vl>   or NOTFOUND
#   a11y for labeled chrome. VL only if a11y NOTFOUND (canvas/unlabeled).
#   REMOTE-ONLY VL. No local daemon. No UI-TARS.
# 사용:
#   ground_hybrid.sh <App> "<a11y라벨>" ["<VL설명>"]
#   예: ground_hybrid.sh Keynote "차트" "the chart insert button in toolbar"
set -u
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="$1"; A11Y_LABEL="$2"; VL_DESC="${3:-$2}"

# 1) a11y first (LOGICAL, ground.sh VISION_SCALE default 1.0).
R=$("$DIR/ground.sh" "$APP" "$A11Y_LABEL" 2>/dev/null)
if [[ "$R" == FOUND* ]]; then
  echo "$R" | awk '{print "FOUND",$2,$3,"a11y"}'
  exit 0
fi

# 2) a11y miss → REMOTE VL (already LOGICAL).
R=$("$DIR/ground_vl.sh" find "$VL_DESC" 2>/dev/null)
if [[ "$R" == FOUND* ]]; then
  echo "$R" | awk '{print "FOUND",$2,$3,"vl"}'
  exit 0
fi

echo "NOTFOUND (a11y+VL)"; exit 1
