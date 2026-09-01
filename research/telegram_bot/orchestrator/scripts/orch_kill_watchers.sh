#!/usr/bin/env bash
# orch_kill_watchers.sh — 자기 프로젝트(ROOT cwd)의 오케 감시(orch_monitor_tick) 프로세스만 kill.
#
# 배경(och.txt §3-A-★★★): 과거 재arm 정리에 `pkill -f "orch_monitor_tick"` 을 썼다가,
#   한 머신에서 여러 프로젝트의 오케가 동시에 돌 때 명령줄이 전부 동일해 **다른 프로젝트의
#   살아있는 감시까지 무차별 kill** 하는 사고가 발생했다. → 이 스크립트는 봇 find_pid 와
#   동일한 lsof cwd 필터로 **자기 ROOT 것만** 죽인다. pkill 전면 금지.
#
# 단일 책임: 이 스크립트는 kill 만 담당한다. tick 리셋은 호출부(재arm 절차)의 몫이다.
#   재arm 시 사용법:  orch_kill_watchers.sh  &&  echo 0 > logs/.orch_tick   # 이어서 tick 리셋
#
# 사용법:
#   orch_kill_watchers.sh            # ROOT cwd 의 orch_monitor_tick 프로세스를 kill
#   orch_kill_watchers.sh --dry-run  # kill 하지 않고 대상 목록만 출력(살아있는 감시 보호 검증용)
#
# 규칙 근거: och.txt §3-A-★★★(자기 프로젝트만 kill), §11.5 규칙 A(소속 실측·조용한 통과 금지),
#           scripts/start_orchestrator.sh:26-30 find_pid 와 필터 일치.
set -u

# 프로젝트 루트를 스크립트 위치 기준으로 자동 해석(범용 — 어느 경로에 복사돼도 동작).
# 이 스크립트: <ROOT>/telegram_bot/orchestrator/scripts/orch_kill_watchers.sh → 3단계 상위가 ROOT.
# ★조용한 exit 0 금지(2026-08-07 사고 핵심): cd 실패 시 stderr 사유 + exit 1(정리 실패가 보이게).
SELF="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR="$(cd "$(dirname "$SELF")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$ROOT" 2>/dev/null || { echo "orch_kill_watchers: ROOT cd 실패($ROOT) — 정리 중단" >&2; exit 1; }

# 대상 감시 프로세스 이름(봇 find_pid 의 MODULE 대응).
PATTERN="orch_monitor_tick"

DRY_RUN=0
# NEVER-STOP-M1-M2 (user 2026-08-14): refuse bare kill. Only P5 re-arm reset or dry-run.
case "${1:-}" in
  --dry-run|-n) DRY_RUN=1 ;;
  --for-rearm) : ;;
  "")
    echo "orch_kill_watchers: REFUSED (NEVER-STOP-M1-M2). Need --for-rearm (then ARM same turn) or --dry-run." >&2
    exit 3
    ;;
  *) echo "사용법: $0 --for-rearm | --dry-run" >&2; exit 2 ;;
esac

# 자기 ROOT cwd 인지 실측(봇 find_pid 와 동일한 필터).
#   반환: 0 = ROOT 소속(kill 대상), 1 = 다른 cwd(건드리지 않음), 2 = lsof 실패(소속 불명 → 건너뜀)
cwd_of() {
  # 프로세스 cwd 한 줄 반환(lsof -Fn 은 "n<path>" 형식). 실패 시 빈 문자열.
  lsof -a -p "$1" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | head -1
}

# pgrep 결과를 배열로 수집(자기 자신·부모 셸은 pgrep -f 가 잡지 않는 tick 스크립트 이름 기준).
# ★bash 3.2(macOS 기본) 호환: mapfile 미지원 → while read 로 수집.
pids=()
while IFS= read -r _pid; do
  [ -n "$_pid" ] && pids+=("$_pid")
done < <(pgrep -f "$PATTERN" 2>/dev/null || true)

if [ "${#pids[@]}" -eq 0 ]; then
  echo "정리할 감시 프로세스 없음 (pgrep -f \"$PATTERN\" 0건)"
  exit 0
fi

killed=0
skipped_other=0
skipped_unknown=0

for pid in "${pids[@]}"; do
  [ -n "$pid" ] || continue
  pcwd="$(cwd_of "$pid")"
  if [ -z "$pcwd" ]; then
    # och.txt §11.5 규칙 A — 소속 불명은 조용히 통과하지 않고 사유를 stderr 에 남기고 건너뛴다(안전측).
    echo "PID $pid: 소속 불명(lsof cwd 조회 실패), 건너뜀" >&2
    skipped_unknown=$((skipped_unknown+1))
    continue
  fi
  if [ "$pcwd" != "$ROOT" ]; then
    # 다른 프로젝트 감시 — 절대 건드리지 않는다(사고 재발 방지).
    echo "PID $pid: 다른 cwd($pcwd) ≠ ROOT($ROOT), 건너뜀"
    skipped_other=$((skipped_other+1))
    continue
  fi

  # 여기부터 ROOT 소속 확정 → kill 대상.
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "[dry-run] KILL 대상 PID $pid (cwd=$pcwd)"
    killed=$((killed+1))
    continue
  fi

  echo "KILL PID $pid (cwd=$pcwd) — SIGTERM"
  kill "$pid" 2>/dev/null || true
  # 짧은 유예 후에도 살아 있으면 SIGKILL.
  sleep 1
  if kill -0 "$pid" 2>/dev/null; then
    echo "KILL PID $pid — 잔존, SIGKILL"
    kill -9 "$pid" 2>/dev/null || true
  fi
  killed=$((killed+1))
done

if [ "$DRY_RUN" -eq 1 ]; then
  echo "요약(dry-run): 대상 $killed · 다른cwd건너뜀 $skipped_other · 소속불명건너뜀 $skipped_unknown"
else
  echo "요약: kill $killed · 다른cwd건너뜀 $skipped_other · 소속불명건너뜀 $skipped_unknown"
fi
exit 0
