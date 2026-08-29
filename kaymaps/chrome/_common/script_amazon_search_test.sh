#!/bin/bash
# script_amazon_search_test.sh
# Standalone kongtrol-direct Amazon search test — NO agent/LLM tool-call loop between steps.
# Purpose: isolate real automation-only time vs agent-driven runs(a_2898=64.18s).
# REG: a_2900(2026-08-29). Coords verified fresh this session(a_2900's one-time setup step) — re-verify if layout drifts.
# LIMIT: no a11y-adaptive-retry. If search-field coords drift(layout/zoom/window-size change), this script
#   fails SILENTLY(click lands on wrong element, kongtrol reports no error) — unlike an agent which can
#   re-query+adapt. Real speed-vs-robustness tradeoff, not a pure win. See ar_2900 for discussion.

set -e
KT=/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol
SCREENSHOT_PATH="/private/tmp/claude-501/-Users-bumsuklee-git-kong-bot/b1276648-a27a-4131-afcf-cfc96be3a731/scratchpad/script_amazon_search_result.png"

T_START=$(date +%s.%N)

# 1. address-bar focus + navigate
$KT input chord cmd l --yes
$KT input text "amazon.com" --yes
$KT input key return --yes

# 2. homepage-load wait(fixed, reusing a_2898/2899's real observed ~0.5-0.7s + safety margin)
sleep 1.5

# 3. click search field(coord verified fresh this session via one-time a11y check, NOT re-queried per-run)
$KT input click 918 156 --yes

# 4. type query + submit
$KT input text "silicone ladle" --yes
$KT input key return --yes

# 5. results-load wait(fixed, reusing a_2899's real 0.704s finding + safety margin)
sleep 1.5

# 6. screenshot
screencapture -x "$SCREENSHOT_PATH"

T_END=$(date +%s.%N)
ELAPSED=$(python3 -c "print(f'{$T_END - $T_START:.2f}')")

echo "SCRIPT_TOTAL_ELAPSED=${ELAPSED}s"
echo "SCREENSHOT=$SCREENSHOT_PATH"
