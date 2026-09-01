#!/usr/bin/env bash
# 오케스트레이터 봇 파이프 관리 스크립트 (봇 이름은 런타임 getMe 로 자동 취득)
# och.txt P0 규칙: 봇이 죽으면 즉시 되살린다. 이 스크립트가 status/start/stop/restart 를 제공.
#
# 사용(이동 후 — u_136 파이프 응집):
#   telegram_bot/orchestrator/scripts/start_orchestrator.sh status    # 생존 점검
#   telegram_bot/orchestrator/scripts/start_orchestrator.sh start     # 죽어 있으면 기동 (이미 떠 있으면 건드리지 않음)
#   telegram_bot/orchestrator/scripts/start_orchestrator.sh stop      # 정지
#   telegram_bot/orchestrator/scripts/start_orchestrator.sh restart   # 재기동
set -euo pipefail

# 이 스크립트: <repo>/telegram_bot/orchestrator/scripts/
# ../../.. = repo 루트(sky). 봇은 repo 루트를 cwd 로 기동해야 패키지 import(telegram_bot.orchestrator.*) 가 된다.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$REPO_ROOT"

LOG_DIR="$REPO_ROOT/logs"
LOG_FILE="$LOG_DIR/orchestrator.log"
MODULE="telegram_bot.orchestrator.kong_orchestrator"
PYTHON="${PYTHON:-python3}"

mkdir -p "$LOG_DIR"

# 봇 표시 이름(@username)을 하드코딩하지 않고 런타임에 자동 취득한다.
# 토큰은 .env.local(루트) → orchestrator/.env 순으로 찾는다(파이썬 _load_env 와 동일 우선순위).
# 네트워크/토큰 문제로 실패해도 상태 표시만 못 할 뿐 기동/정지에는 영향 없다.
bot_username() {
  local token=""
  for envf in "$REPO_ROOT/.env.local" "$REPO_ROOT/telegram_bot/orchestrator/.env"; do
    if [ -z "$token" ] && [ -f "$envf" ]; then
      token="$(grep -E '^TELEGRAM_BOT_TOKEN=' "$envf" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '[:space:]')"
    fi
  done
  [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && token="$TELEGRAM_BOT_TOKEN"
  [ -z "$token" ] && { echo "봇"; return; }
  local uname
  uname="$(curl -s --max-time 5 "https://api.telegram.org/bot${token}/getMe" 2>/dev/null \
    | sed -n 's/.*"username":"\([^"]*\)".*/\1/p')"
  if [ -n "$uname" ]; then echo "@$uname"; else echo "봇"; fi
}

# 이 repo(kong-bot)에서 뜬 봇 프로세스의 PID 만 찾는다.
# (workspace-egov 등 다른 경로의 동명 프로세스는 REPO_ROOT 로 걸러 제외)
# ★argv0 태그(kong-orchestrator, exec -a 로 고정)로 매칭 — 현재 $MODULE 문자열이 아닌
#   안정 불변값 기준(2026-08-27 a_2739): 모듈파일명이 리네임되어도(orchestrator.py→
#   kong_orchestrator.py 사례) 이전 경로로 떠 있던 프로세스를 계속 잡아낸다.
#   $MODULE 하드코딩 매칭이었을 때는 리네임 직후 구모듈 생존 PID를 놓쳐(정지로 오판)
#   start 가 중복 기동→같은 토큰 2중 폴링→Telegram 409 Conflict 발생(ar_2737 N).
find_pid() {
  pgrep -f "^kong-orchestrator " 2>/dev/null | while read -r pid; do
    # 프로세스의 cwd 가 이 repo 인지 확인 (lsof 순간 실패 대비 최대 2회 재시도 — 2026-08-27 flaky-false-dead 사고)
    local out=""
    for _try in 1 2; do
      out="$(lsof -a -p "$pid" -d cwd -Fn 2>/dev/null)"
      [ -n "$out" ] && break
    done
    if echo "$out" | grep -q "n$REPO_ROOT"; then
      echo "$pid"
    fi
  done | head -1
}

cmd_status() {
  local pid
  pid="$(find_pid || true)"
  if [ -n "${pid:-}" ]; then
    echo "✓ 봇 실행중 (PID $pid) $(bot_username)"
    return 0
  else
    echo "✗ 봇 정지"
    return 1
  fi
}

cmd_start() {
  local pid
  pid="$(find_pid || true)"
  if [ -n "${pid:-}" ]; then
    echo "✓ 이미 실행중 (PID $pid) — 건드리지 않음"
    return 0
  fi
  echo "→ 봇 기동중..."
  # ★프로세스명에 kong 식별 붙임(ps 에서 sky 등 타프로젝트와 구분·헷갈림 방지, user 2026-08-13).
  #   exec -a 로 argv[0]=kong-orchestrator → `ps|grep kong-orchestrator` 로 즉시 식별.
  PYTHONUNBUFFERED=1 nohup bash -c 'exec -a kong-orchestrator "$0" -u -m "$1"' "$PYTHON" "$MODULE" >> "$LOG_FILE" 2>&1 &
  sleep 3
  if cmd_status; then
    echo "  로그: $LOG_FILE"
  else
    echo "✗ 기동 실패 — 로그 확인:"
    tail -20 "$LOG_FILE"
    return 1
  fi
}

cmd_stop() {
  local pid
  pid="$(find_pid || true)"
  if [ -z "${pid:-}" ]; then
    echo "이미 정지 상태"
    return 0
  fi
  kill "$pid" 2>/dev/null || true
  sleep 1
  echo "✓ 정지됨 (PID $pid)"
}

cmd_restart() {
  cmd_stop
  cmd_start
}

case "${1:-status}" in
  status)  cmd_status ;;
  start)   cmd_start ;;
  stop)    cmd_stop ;;
  restart) cmd_restart ;;
  *) echo "사용법: $0 {status|start|stop|restart}"; exit 2 ;;
esac
