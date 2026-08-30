#!/usr/bin/env bash
# 오케 → 워커(kongewalker) 터미널 창에 텍스트 주입(Terminal.app "do script", System Events 아님 — 권한불요).
# 용도: kongmaster.py(자동재기동 데몬, 무한재기동 버그로 08-20 이후 제거됨) 대체 —
#   오케가 유저 요청시 수동으로 워커를 깨워 지시서 확인시키는 역할.
# ★2026-08-30 u_re-fix pt.2: title-phrase matching(구 "Kong 워커 역할 정의") 은 Claude Code가
#   세션 시작 프롬프트에서 자동생성하는 문구라 새 세션마다 바뀔 수 있어 fragile. tty 기반 우선:
#   logs/.orch_tty_worker1(session_register_tty.sh 로 등록) 있으면 그 tty로 창 특정, 없으면 문구매칭 폴백.
# usage: bash orch_wake_worker.sh ["msg"]  (default="check new a_ dispatch.")
# ★K7(u_2803): internal-comm injection = compressed-EN, never KR-literal — caller must pass EN msg too.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TTY_FILE="$REPO_ROOT/logs/.orch_tty_worker1"

BASE_MSG="${1:-check new a_ dispatch.}"
# ★K7 리마인더 자동첨부(u_2802): 워커 깨울 때마다 압축영문+기호(K7 COMPRESSED-COMMS) 준수를
#   같이 상기시킴 — 반복 위반(K7 위반 재발) 방지, och.txt 1G/embed-feedback-reminder 패턴과 동일 취지.
MSG="${BASE_MSG} [K7·EN-think·min-out]"
WINDOW_HINT="Kong 워커 역할 정의"

TARGET_TTY=""
if [ -f "$TTY_FILE" ]; then
  TARGET_TTY="$(tr -d '[:space:]' < "$TTY_FILE")"
fi

# ★2026-08-28 u_2803/2804 fix: `do script "text" in w` on a Claude-Code TUI can QUEUE
#   the text without submitting(prompt shows "Press up to edit queued messages", no Enter).
#   Fix = 2nd do-script call sending bare newline to actually submit.
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
    if name of w contains "$WINDOW_HINT" then
      do script "$MSG" in w
      delay 0.3
      do script (return & "") in w
      return "SUCCESS(title-fallback): " & (name of w)
    end if
  end repeat
  return "FAIL: no tty match(" & targetTty & ") and no title-fallback match(hint=$WINDOW_HINT)"
end tell
EOF
)

echo "$RESULT"
[[ "$RESULT" == SUCCESS* ]]
