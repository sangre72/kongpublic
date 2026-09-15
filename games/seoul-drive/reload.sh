#!/bin/bash
# 같은 창에서 새로고침한다 (u_5075 오너 지적: "브라우저는 왜 새로떠").
# ★`open -na --new-window` 금지 — 호출할 때마다 창이 하나씩 쌓인다(실제로 3개까지 쌓였다).
URL="${1:-http://localhost:8901/index.html}"
osascript -e "tell application \"Google Chrome\"
  set URL of active tab of front window to \"$URL\"
  set bounds of front window to {0, 25, 900, 720}
end tell" >/dev/null
sleep "${2:-13}"
