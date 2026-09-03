#!/usr/bin/env bash
# 텔레그램 u_ 도착시 오케(이 세션) 자신의 터미널창에 텍스트 주입(Terminal.app "do script").
# orch_wake_worker.sh의 오케-자기자신 버전.
# ★2026-08-30 u_re-fix pt.2: title-phrase matching(이전 "Kong 역할 설정 확인") 은 Claude Code가
#   세션 시작 프롬프트로부터 자동생성하는 문구라 새 세션마다 바뀔 수 있어 fragile. tty 기반으로 전환:
#   logs/.orch_tty_orch(session_register_tty.sh 로 등록) 이 있으면 그 tty로 창을 특정(안정적),
#   없으면 구 문구매칭으로 폴백(등록 전/구버전 호환).
# 용도: M1(10s polling) 보완 — 폴링 지연 없이 즉시 오케를 깨워 u_ 처리 트리거.
# 사용: bash orch_wake_self.sh ["메시지"]  (기본메시지="새 텔레그램 요청 접수됨. u_ 확인하세요.")
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TTY_FILE="$REPO_ROOT/logs/.orch_tty_orch"

BASE_MSG="${1:-new u_ received, check now.}"
# ★K7 리마인더 자동첨부(u_2802/2803/3xxx): 오케 깨울 때 압축영문+기호 사고 + 워커통신(a_)도 EN+기호 명시.
# u_3444: symbolic-opcode form(수식기호사고). think∈{sym,formula}; ¬KR-think; ¬prose. tg=KR.
# ★a_3561: BASE_MSG 가 슬래시명령(/compact 등)이면 K7 접미사 붙이지 않고 그대로 주입(접미사가 붙으면
#   "/compact [think...]" 가 되어 슬래시명령 인식이 깨짐 — orch_wake_worker.sh 의 동일 가드와 일치).
if [[ "$BASE_MSG" == /* ]]; then
  MSG="$BASE_MSG"
else
  MSG="${BASE_MSG} [think=∑sym/formula ¬prose ¬KR; a_,wkr-msg=sym; out=min; tg-reply=KR; job∈registry→exec(no-delib); wrap-up=short ¬recap(shorter=faster-turn)]"
fi

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
  -- fallback: old title-phrase match(pre-tty-registration sessions)
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
