#!/usr/bin/env bash
# 워커(kongewalker) → 오케 터미널 창에 완료알림 텍스트 주입(Terminal.app "do script").
# orch_wake_worker.sh(오케→워커)의 역방향 버전 — worker_1.txt §WORKER→ORCH WAKE-NOTIFY 패턴 구현.
# ★2026-08-30 u_re-fix pt.2: title-phrase matching(구 "Kong 역할 설정 확인") 은 Claude Code가
#   세션 시작 프롬프트에서 자동생성하는 문구라 새 세션마다 바뀔 수 있어 fragile. tty 기반 우선:
#   logs/.orch_tty_orch(session_register_tty.sh 로 등록) 있으면 그 tty로 창 특정, 없으면 문구매칭 폴백.
# usage: bash worker1_wake_orch.sh ["msg"]  (default="worker done. check ar_.")
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TTY_FILE="$REPO_ROOT/logs/.orch_tty_orch"

BASE_MSG="${1:-worker done. check ar_.}"
# ★K7 리마인더 자동첨부: 워커 종료 알림도 오케가 결과를 압축영문+기호로 요약해야 함을 상기.
MSG="${BASE_MSG} [K7·EN-think·min-out, telegram-reply=full-KR]"

TARGET_TTY=""
if [ -f "$TTY_FILE" ]; then
  TARGET_TTY="$(tr -d '[:space:]' < "$TTY_FILE")"
fi

# ★2026-08-28 u_2803/2804 fix: needs explicit 2nd newline do-script to submit.
RESULT=$(osascript <<EOF
tell application "Terminal"
  set targetTty to "$TARGET_TTY"
  if targetTty is not "" then
    repeat with w in windows
      if (tty of w) is targetTty then
        do script "$MSG" in w
        delay 0.3
        do script (return & "") in w
        return "SUCCESS(tty): " & (name of w)
      end if
    end repeat
  end if
  repeat with w in windows
    set wname to name of w
    if wname contains "kong-bot" and wname contains "Kong 역할 설정 확인" then
      do script "$MSG" in w
      delay 0.3
      do script (return & "") in w
      return "SUCCESS(title-fallback): " & wname
    end if
  end repeat
  return "FAIL: no tty match(" & targetTty & ") and no title-fallback match"
end tell
EOF
)

echo "$RESULT"
[[ "$RESULT" == SUCCESS* ]]
