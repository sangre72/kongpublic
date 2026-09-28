# ★브라우저 소유권 가드 (MUST — 2026-09-27 u_5693/u_5695, 같은 사고 2회)
# 사고: ODE 스크립트(reload.sh 를 호출하는 collect_*/case_loop 포함)가 **CineBot 탭을 갈아치워**
#       운세 작업의 텍스트 12건·시나리오 12씬이 통째로 소실됐다(복구 불가, 재생성).
# 규칙: (1) 크롬을 쓰는 모든 ODE 스크립트는 시작할 때 이 가드를 통과해야 한다.
#       (2) /tmp/.chrome_owner 가 있으면(= 운세 등 GUI 잡이 소유) **즉시 종료**한다.
#       (3) 자기가 열지 않은 탭을 절대 navigate 하지 않는다 — 자기 탭/창을 새로 연다.
CHROME_OWNER_FILE=/tmp/.chrome_owner
chrome_guard(){ local me="${1:-ode}"
  if [ -f "$CHROME_OWNER_FILE" ] && [ "${CHROME_OWNER_OVERRIDE:-0}" != "1" ]; then
    echo "[$me] ABORT — Chrome owned by '$(cat "$CHROME_OWNER_FILE" 2>/dev/null)'. ODE must not touch the browser."
    return 9
  fi
  return 0; }
# ODE 전용 탭 확보: 우리가 연 탭만 쓴다(없으면 새로 연다). 기존 탭은 건드리지 않는다.
chrome_own_tab(){ local url="$1"
  osascript >/dev/null 2>&1 <<OSA
tell application "Google Chrome"
  set found to false
  repeat with w in windows
    repeat with t in tabs of w
      if (URL of t) contains "localhost:8901" then
        set active tab index of w to index of t
        set found to true
        exit repeat
      end if
    end repeat
    if found then exit repeat
  end repeat
  if not found then
    make new window with properties {URL:"$url"}
  end if
end tell
OSA
}
