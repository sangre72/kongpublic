"""STT 텍스트를 대상 orch 세션의 Terminal 창에 주입.

★재사용(¬재발명): telegram_bot/orchestrator/scripts/orch_wake_worker.sh 의
Terminal "do script" 패턴을 그대로 따른다(System Events 아님 — 권한불요, security §3 pure-IO).
- tty 로 창 특정(logs/.orch_tty_orch)
- do script "<msg>" in w  후, bare newline 을 다시 do script 로 보내 실제 제출(u_2803/2804 fix).

보안(security §2): 주입 텍스트는 osascript 문자열-보간을 거치므로 따옴표/역슬래시/개행을
sanitize 한다(명령 주입/스크립트 깨짐 방지). STT 텍스트는 untrusted 취급.
"""

from __future__ import annotations

import subprocess


def _sanitize_for_osascript(text: str) -> str:
    """osascript do-script 문자열 안에서 안전하도록 정리.

    큰따옴표·역슬래시 이스케이프, 개행→공백. 제어문자 제거.
    (orch_wake_self.sh 의 sanitize 취지와 동일 — 문자열 깨짐/주입 방지.)
    """
    t = text.replace("\\", "\\\\").replace('"', '\\"')
    t = t.replace("\r", " ").replace("\n", " ")
    t = "".join(ch for ch in t if ch >= " " or ch == " ")
    return t.strip()


def inject_to_tty(tty: str, text: str) -> tuple[bool, str]:
    """주어진 tty 의 Terminal 창에 text 를 타이핑 후 제출. (성공, 메시지)."""
    safe = _sanitize_for_osascript(text)
    if not safe:
        return (False, "empty-after-sanitize")

    script = f'''
tell application "Terminal"
  set targetTty to "{tty}"
  repeat with w in windows
    if (tty of w) is targetTty then
      do script "{safe}" in w
      delay 0.3
      do script (return & "") in w
      return "SUCCESS(tty): " & (name of w)
    end if
  end repeat
  return "FAIL: no tty match(" & targetTty & ")"
end tell
'''
    try:
        out = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=10, check=False,
        )
    except Exception as e:  # noqa: BLE001
        return (False, f"osascript-error: {e}")
    result = (out.stdout or out.stderr or "").strip()
    return (result.startswith("SUCCESS"), result)
