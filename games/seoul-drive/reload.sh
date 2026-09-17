#!/bin/bash
# 같은 창에서 새로고침 + 규격 해상도(763x762 캔버스) 강제(u_5089, u_5075 "브라우저는 왜 새로떠").
# ★`open -na --new-window` 금지 — 창이 쌓인다(실제 3개까지).
#
# ★2026-09-17 하드닝(u_5255 "브라우저 크래시가 지금 가장 큰 문제"). 실측으로 잡힌 두 가지:
#   (1) 어제 저녁 렌더러 OOM 크래시 3회(Crashpad 19:42~22:43) — 페이지가 8.7MB CHUNKS 를
#       인라인으로 들고 있어 로드 1회에 렌더러 600~760MB.
#   (2) 오늘 "멈춤"은 크래시가 아니었다 — 크롬 재시작 직후 콜드 로드가 32초 넘게 걸리는데
#       호출부가 24~40초 고정 sleep 뒤 /tel 을 읽어 wpLen=0 을 '죽음'으로 오판했다.
#       또 창이 사라진 상태에서 osascript 가 조용히 실패해도 아무도 몰랐다.
# ⇒ 고정 sleep 대신 /tel 을 폴링해 실제 준비(wpLen>100, go=1 이면 autoOn)를 확인하고,
#   창이 없거나 렌더러가 부풀었으면 크롬을 재기동한 뒤 1회 재시도한다. 준비 못 되면 exit 1.
URL="${1:-http://localhost:8901/index.html}"
MAXWAIT="${2:-120}"           # 준비 대기 상한(초). 예전 2번째 인자(고정 sleep)와 호환.
RSS_LIMIT_MB=900              # 이 위면 재기동 후 로드(OOM 예방)
TEL=http://localhost:8901/tel

need_go=0; case "$URL" in *go=1*) need_go=1;; esac

renderer_mb(){ ps -eo rss,command | grep "Google Chrome Helper (Renderer)" | grep -v grep | sort -rn | head -1 | awk '{printf "%d",$1/1024}'; }
win_count(){ osascript -e 'tell application "Google Chrome" to count windows' 2>/dev/null || echo 0; }
# ★준비 = '이번 로드'의 텔레메트리여야 한다(loadId 가 이전 값과 달라야). 루프 전에 죽은 페이지는
#   /tel 을 못 올리고 서버가 이전 스냅샷을 돌려줘 3초 만에 '준비'로 오판했었다(실측).
PREV_ID=$(python3 -c "
import json,urllib.request
try: print(json.load(urllib.request.urlopen('http://localhost:8901/tel',timeout=3)).get('loadId'))
except Exception: print('None')")
tab_title(){ osascript -e 'tell application "Google Chrome" to get title of active tab of front window' 2>/dev/null; }
ready(){ python3 - "$need_go" "$PREV_ID" <<'PY'
import sys,json,urllib.request
try:
    d=json.load(urllib.request.urlopen("http://localhost:8901/tel",timeout=3))
    fresh = d.get("loadId") is not None and str(d.get("loadId")) != sys.argv[2]
    ok = fresh and (d.get("wpLen") or 0)>100 and (not int(sys.argv[1]) or d.get("autoOn")==1)
    sys.exit(0 if ok else 1)
except Exception: sys.exit(1)
PY
}
restart_chrome(){
  pkill -f "Google Chrome" 2>/dev/null; sleep 4
  open -a "Google Chrome"; sleep 6
}
navigate(){
  if [ "$(win_count)" = "0" ]; then open -a "Google Chrome" "$URL"; sleep 4; fi
  osascript -e "tell application \"Google Chrome\"
    set bounds of front window to {0, 25, 763, 862}
    set URL of active tab of front window to \"$URL\"
  end tell" >/dev/null 2>&1
}
wait_ready(){  # $1 = 초
  local t=0
  while [ $t -lt "$1" ]; do
    sleep 3; t=$((t+3))
    local ttl; ttl=$(tab_title)
    case "$ttl" in ERR:*) echo "reload: PAGE ERROR — $ttl"; return 2;; esac
    if ready; then echo "reload: ready in ${t}s (loadId changed, title='$ttl')"; return 0; fi
  done
  echo "reload: timeout; last title='$(tab_title)'"
  return 1
}

# 0) 사전 위생: 창 없음 / 렌더러 비대 → 재기동
R=$(renderer_mb); [ -z "$R" ] && R=0
if [ "$(win_count)" = "0" ] || [ "$R" -gt "$RSS_LIMIT_MB" ]; then
  echo "reload: pre-restart (windows=$(win_count), renderer=${R}MB)"; restart_chrome
fi

# 1) 로드 + 준비 확인
navigate
wait_ready "$MAXWAIT"; WR=$?
[ $WR -eq 0 ] && exit 0
[ $WR -eq 2 ] && { echo "reload: FAILED — script error in page (not a browser problem)"; exit 2; }

# 2) 1회 복구 재시도
echo "reload: not ready after ${MAXWAIT}s (windows=$(win_count), renderer=$(renderer_mb)MB) — restarting Chrome"
restart_chrome; navigate
if wait_ready "$MAXWAIT"; then exit 0; fi
echo "reload: FAILED — page never became ready"; exit 1
