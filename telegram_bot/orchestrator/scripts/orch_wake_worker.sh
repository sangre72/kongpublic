#!/usr/bin/env bash
# 오케 → 워커(kongewalker) 터미널 창에 텍스트 주입(Terminal.app "do script", System Events 아님 — 권한불요).
# 용도: kongmaster.py(자동재기동 데몬, 무한재기동 버그로 08-20 이후 제거됨) 대체 —
#   오케가 유저 요청시 수동으로 워커를 깨워 지시서 확인시키는 역할.
# 사용: bash orch_wake_worker.sh ["메시지"]  (기본메시지="지시서를 확인하세요.")
set -euo pipefail

MSG="${1:-지시서를 확인하세요.}"
WINDOW_HINT="Worker_1.txt"

RESULT=$(osascript <<EOF
tell application "Terminal"
  repeat with w in windows
    if name of w contains "$WINDOW_HINT" then
      do script "$MSG" in w
      return "SUCCESS: " & (name of w)
    end if
  end repeat
  return "FAIL: window not found (hint=$WINDOW_HINT)"
end tell
EOF
)

echo "$RESULT"
[[ "$RESULT" == SUCCESS:* ]]
