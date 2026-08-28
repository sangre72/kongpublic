#!/usr/bin/env bash
# 워커(kongewalker) → 오케 터미널 창에 완료알림 텍스트 주입(Terminal.app "do script").
# orch_wake_worker.sh(오케→워커)의 역방향 버전 — worker_1.txt §WORKER→ORCH WAKE-NOTIFY 패턴 구현.
# 창 힌트 = "kong-bot" AND "och.txt"(오케 세션 마커, orch_wake_self.sh와 동일 기준 — sky sibling과 구분).
# 사용: bash worker1_wake_orch.sh ["메시지"]  (기본메시지="워커 작업 완료. ar_ 확인하세요.")
set -euo pipefail

BASE_MSG="${1:-워커 작업 완료. ar_ 확인하세요.}"
# ★K7 리마인더 자동첨부: 워커 종료 알림도 오케가 결과를 압축영문+기호로 요약해야 함을 상기.
MSG="${BASE_MSG} [K7: ar_ result-summary=compressed-EN+symbol, telegram-user-reply=korean ONLY]"

RESULT=$(osascript <<EOF
tell application "Terminal"
  repeat with w in windows
    set wname to name of w
    if wname contains "kong-bot" and wname contains "och.txt" then
      do script "$MSG" in w
      return "SUCCESS: " & wname
    end if
  end repeat
  return "FAIL: window not found (need both 'kong-bot' and 'och.txt' in name)"
end tell
EOF
)

echo "$RESULT"
[[ "$RESULT" == SUCCESS:* ]]
