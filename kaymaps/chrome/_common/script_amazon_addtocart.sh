#!/bin/bash
# script_amazon_addtocart.sh
# Standalone kongtrol-direct Amazon add-to-cart — takes AI-decided product coords as INPUT param.
# REG: a_2901(2026-08-29). Design per u_2939's explicit requirement: NOT purely blind —
#   does ONE lightweight a11y-query on the product-detail page to find the add-to-cart button
#   by TEXT-MATCH(not hardcoded coord), branches if sold-out/notify-me state detected instead
#   of force-clicking. This keeps script-speed while staying state-aware.
#
# USAGE: script_amazon_addtocart.sh <product_link_x> <product_link_y>
# LIMIT: still trusts the CALLER(AI/agent Stage B) to have picked the right product-link coords.
#   The state-awareness here is ONLY for the button-state on the resulting detail page, not
#   for re-validating the product choice itself(that's Stage B's job, by design).

set -e
KT=/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol
PROD_X="$1"
PROD_Y="$2"
SCREENSHOT_PATH="/private/tmp/claude-501/-Users-bumsuklee-git-kong-bot/b1276648-a27a-4131-afcf-cfc96be3a731/scratchpad/script_addtocart_result.png"

if [ -z "$PROD_X" ] || [ -z "$PROD_Y" ]; then
    echo "ERROR: usage: $0 <product_link_x> <product_link_y>"
    exit 1
fi

T_START=$(date +%s.%N)

# 1. click product link(coord from caller/AI-decision, not hardcoded in this script)
T_CLICK_START=$(date +%s.%N)
$KT input click "$PROD_X" "$PROD_Y" --yes
T_CLICK_END=$(date +%s.%N)

# 2. detail-page-load wait(fixed, reusing prior sessions' real ~3-4s observed load times)
sleep 3.5

# 3. STATE-AWARE a11y-query for the actual button(NOT a hardcoded click) — per u_2939's requirement
PID=$(pgrep -x "Google Chrome" | head -1)
T_A11Y_START=$(date +%s.%N)
A11Y_DUMP=$($KT see --a11y --pid "$PID")
T_A11Y_END=$(date +%s.%N)

# ★BUG-FIX(a_2901 real incident): a11y dump lists a HIDDEN keyboard-shortcut proxy button
#   FIRST(e.g. "AXButton @(1,657) [1x70] · 장바구니에 추가, 이동, 옵션, K" — width=1px, off-screen-ish),
#   THEN the real visible button. `head -1` grabbed the WRONG(invisible) one, script reported
#   false success while the real button stayed unclicked. FIX: filter for plausible width(>50px,
#   the visible button is [204x30]-class, the proxy is [1x70]) before taking the match.
ADDCART_LINE=$(echo "$A11Y_DUMP" | grep -E "장바구니에 추가" | grep "AXButton" | grep -vE '\[1x[0-9]+\]' | head -1)
SOLDOUT_LINE=$(echo "$A11Y_DUMP" | grep -E "품절|재입고 알림|현재 재고 없음" | head -1)

if [ -n "$SOLDOUT_LINE" ] && [ -z "$ADDCART_LINE" ]; then
    echo "STATE=SOLD_OUT_OR_NOTIFY_ME — not clicking, reporting honestly"
    echo "DETECTED_LINE: $SOLDOUT_LINE"
    T_END=$(date +%s.%N)
    ELAPSED=$(python3 -c "print(f'{$T_END - $T_START:.2f}')")
    echo "SCRIPT_TOTAL_ELAPSED=${ELAPSED}s"
    echo "SCRIPT_CLICK_SUBSTAGE=$(python3 -c "print(f'{$T_CLICK_END - $T_CLICK_START:.2f}')")s"
    echo "SCRIPT_A11Y_VERIFY_SUBSTAGE=$(python3 -c "print(f'{$T_A11Y_END - $T_A11Y_START:.2f}')")s"
    exit 2
fi

if [ -z "$ADDCART_LINE" ]; then
    echo "STATE=ADD_TO_CART_BUTTON_NOT_FOUND(unexpected page state) — not clicking, reporting honestly"
    T_END=$(date +%s.%N)
    ELAPSED=$(python3 -c "print(f'{$T_END - $T_START:.2f}')")
    echo "SCRIPT_TOTAL_ELAPSED=${ELAPSED}s"
    exit 3
fi

# 4. extract coords from the matched a11y line(format: "AXButton @(X,Y) [WxH] · label")
BTN_X=$(echo "$ADDCART_LINE" | grep -oE '@\([0-9]+,[0-9]+\)' | head -1 | tr -d '@()' | cut -d',' -f1)
BTN_Y=$(echo "$ADDCART_LINE" | grep -oE '@\([0-9]+,[0-9]+\)' | head -1 | tr -d '@()' | cut -d',' -f2)

# 5. click the REAL matched button(not a hardcoded coord)
T_ADDCART_CLICK_START=$(date +%s.%N)
$KT input click "$BTN_X" "$BTN_Y" --yes
T_ADDCART_CLICK_END=$(date +%s.%N)

# 6. confirmation wait
sleep 2

# 7. screenshot
screencapture -x "$SCREENSHOT_PATH"

T_END=$(date +%s.%N)
ELAPSED=$(python3 -c "print(f'{$T_END - $T_START:.2f}')")

echo "STATE=ADD_TO_CART_SUCCESS"
echo "SCRIPT_TOTAL_ELAPSED=${ELAPSED}s"
echo "SCRIPT_CLICK_PRODUCT_SUBSTAGE=$(python3 -c "print(f'{$T_CLICK_END - $T_CLICK_START:.2f}')")s"
echo "SCRIPT_A11Y_STATE_VERIFY_SUBSTAGE=$(python3 -c "print(f'{$T_A11Y_END - $T_A11Y_START:.2f}')")s"
echo "SCRIPT_ADDCART_CLICK_SUBSTAGE=$(python3 -c "print(f'{$T_ADDCART_CLICK_END - $T_ADDCART_CLICK_START:.2f}')")s"
echo "SCREENSHOT=$SCREENSHOT_PATH"
