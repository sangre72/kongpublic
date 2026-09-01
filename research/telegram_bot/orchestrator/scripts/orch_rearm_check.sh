#!/usr/bin/env bash
# 오케 재무장 판정 헬퍼 (단일 호출) — "course 반복" 사고(2026-08-11) 방지책.
#
# WHY: idle 대기 구간에서 Monitor timeout→재무장 턴이 수십 번 반복되며
#      오케 세션이 매 턴 [생존확인 sleep11 + 재무장 + 상태요약] 여러 도구·산문을 뱉음
#      → degenerate token repetition("course course…")이 유저 세션에 노출.
# 조치(P5-RE): 재무장을 [이 스크립트 1회 호출]로 판정 → 오케는 결과만 보고 재무장 여부 결정,
#      산문 없이 Monitor 도구만 호출. 반복 턴의 텍스트 생성 자체를 최소화한다.
#
# 출력(1줄): REARM_M1 / REARM_M2 / REARM_BOTH / ALIVE_BOTH  + 근거.
#   - REARM_* = 해당 Monitor 도구를 재무장하라(오케가 Monitor 툴 호출).
#   - ALIVE_BOTH = 아무것도 안 함(재무장 불필요).
# ★21초 대기 포함(10s tick · 2틱 경계 오탐 방지) — 오케는 별도 sleep 하지 말 것.
# ★self-check: 최근 세션 로그에서 'course' 연속반복 감지 시 COURSE_LEAK 경보 병기.
set -uo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$REPO_ROOT" || { echo "REARM_BOTH cd실패"; exit 0; }

TICKF="logs/.orch_tick"
ALIVEF="logs/.orch_alive"
STALE_SEC=30
UID_N="$(id -u)"

# Fast path (u_295): if heartbeat + launchd/session loops are fresh, do NOT sleep 21s.
# 21s measure only when stale (was blocking the main Grok turn for 1m+).
now=$(date +%s)
alive_age=999
[ -f "$ALIVEF" ] && alive_age=$(( now - $(stat -f %m "$ALIVEF") ))
t1=$(cat "$TICKF" 2>/dev/null || echo 0)
m2_alive=0
pgrep -f "orch_monitor_watch2.sh" >/dev/null 2>&1 && m2_alive=1
launchctl print "gui/${UID_N}/com.kongbot.orch-tick" 2>/dev/null | grep -q 'state = running' && m1_launchd=1 || m1_launchd=0
if [ "$alive_age" -le 20 ] && [ "$m2_alive" -eq 1 ]; then
  echo "ALIVE_BOTH (fast alive_age=${alive_age}s tick=${t1} M2 up launchd_tick=${m1_launchd})"
  exit 0
fi
if [ "$alive_age" -le 20 ] && [ "$m1_launchd" -eq 1 ]; then
  echo "ALIVE_BOTH (fast alive_age=${alive_age}s tick=${t1} launchd_tick=1 M2=${m2_alive})"
  exit 0
fi

# Slow path: M1 생존 = tick 21초 증가 (10s period · 2 ticks)
sleep 21
t2=$(cat "$TICKF" 2>/dev/null || echo 0)
m1_alive=0; [ "$t2" -gt "$t1" ] && m1_alive=1
pgrep -f "orch_monitor_watch2.sh" >/dev/null 2>&1 && m2_alive=1

# 3) course-leak self-check (지속 감시): 최근 오케 transcript에서 'course' 3회+ 연속 반복 탐지
leak=""
TR=$(ls -t "$HOME"/.claude/projects/*/*.jsonl 2>/dev/null | head -1)
if [ -n "${TR:-}" ] && [ -f "$TR" ]; then
  # 마지막 20KB 내에서 course가 5회 이상 연속(공백/개행 사이)이면 경보
  if tail -c 20000 "$TR" 2>/dev/null | grep -oiE '(course[[:space:]]*){5,}' >/dev/null 2>&1; then
    leak=" COURSE_LEAK(재발감지! P5-RE 위반 — 산문금지·도구만)"
  fi
fi

# 판정
if [ "$m1_alive" -eq 1 ] && [ "$m2_alive" -eq 1 ]; then
  echo "ALIVE_BOTH (M1 tick ${t1}->${t2}, M2 loop up)${leak}"
elif [ "$m1_alive" -eq 0 ] && [ "$m2_alive" -eq 0 ]; then
  echo "REARM_BOTH (M1 tick frozen ${t1}, M2 loop down)${leak}"
elif [ "$m1_alive" -eq 0 ]; then
  echo "REARM_M1 (tick frozen ${t1}, M2 up)${leak}"
else
  echo "REARM_M2 (M2 loop down, M1 alive ${t1}->${t2})${leak}"
fi
exit 0
