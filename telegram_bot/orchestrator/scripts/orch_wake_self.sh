#!/usr/bin/env bash
# 텔레그램 u_ 도착시 오케(이 세션) 자신의 터미널창에 텍스트 주입(Terminal.app "do script").
# orch_wake_worker.sh의 오케-자기자신 버전 — 창 힌트 = "kong-bot"(프로젝트명) AND "och.txt"(오케 세션 마커)
#   둘 다 포함해야 함(sibling 프로젝트 sky도 "och.txt" 창을 갖고 있어 kong-bot만으로는 부족·och.txt만으로도 부족).
# 용도: M1(10s polling) 보완 — 폴링 지연 없이 즉시 오케를 깨워 u_ 처리 트리거.
# 사용: bash orch_wake_self.sh ["메시지"]  (기본메시지="새 텔레그램 요청 접수됨. u_ 확인하세요.")
set -euo pipefail

BASE_MSG="${1:-새 텔레그램 요청 접수됨. u_ 확인하세요.}"
# ★K7 리마인더 자동첨부(u_2802/2803): 오케 깨울 때도 압축영문+기호(터미널 narration) 준수 상기.
MSG="${BASE_MSG} [K7: orch own terminal narration=compressed-EN+symbol too, full-KR explain=telegram ONLY]"

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
