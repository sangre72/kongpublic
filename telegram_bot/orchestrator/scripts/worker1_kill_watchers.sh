#!/usr/bin/env bash
# worker1_kill_watchers.sh — 자기 프로젝트(ROOT cwd)의 워커 감시 프로세스만 kill.
#   대상 = worker1_monitor_tick(Monitor 1) + worker1_watch2(Monitor 2 워치독 v2) 둘 다.
#
# 배경(worker_1.txt·och 사고 교훈): 재arm 정리에 `pkill -f "worker1_monitor_tick"` 을 쓰면,
#   한 머신에서 여러 프로젝트의 워커가 동시에 돌 때 명령줄이 전부 동일해 **다른 프로젝트(sky 등)의
#   살아있는 워커 감시까지 무차별 kill** 하는 사고가 난다. → 이 스크립트는 orch_kill_watchers.sh 와
#   동일한 lsof cwd 필터로 **자기 ROOT 것만** 죽인다. pkill 전면 금지.
#   (원본: telegram_bot/orchestrator/scripts/orch_kill_watchers.sh — 구조·안전장치 그대로 재사용, PATTERN 만 워커용.)
#
# 단일 책임: 이 스크립트는 kill 만 담당한다. tick 리셋은 호출부(재arm 절차)의 몫이다.
#   재arm 시 사용법:  worker1_kill_watchers.sh  &&  echo 0 > logs/.worker1_tick   # 이어서 tick 리셋
#
# 사용법:
#   worker1_kill_watchers.sh            # ROOT cwd 의 워커 감시 프로세스를 kill
#   worker1_kill_watchers.sh --dry-run  # kill 하지 않고 대상 목록만 출력(살아있는 감시 보호 검증용)
#
# 규칙 근거: 자기 프로젝트만 kill(격리), 소속 실측·조용한 통과 금지, orch_kill_watchers.sh 필터와 일치.
set -u

# 프로젝트 루트를 스크립트 위치 기준으로 자동 해석(범용 — 어느 경로에 복사돼도 동작).
# 이 스크립트: <ROOT>/telegram_bot/orchestrator/scripts/worker1_kill_watchers.sh → 3단계 상위가 ROOT.
# ★조용한 exit 0 금지: cd 실패 시 stderr 사유 + exit 1(정리 실패가 보이게).
SELF="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR="$(cd "$(dirname "$SELF")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$ROOT" 2>/dev/null || { echo "worker1_kill_watchers: ROOT cd 실패($ROOT) — 정리 중단" >&2; exit 1; }

# 대상 감시 프로세스 이름(워커는 2종: Monitor 1 tick + Monitor 2 워치독).
# pgrep -f 는 확장정규식 alternation 지원 → 두 패턴을 한 번에 매칭.
PATTERN="worker1_monitor_tick|worker1_watch2"

DRY_RUN=0
case "${1:-}" in
  --dry-run|-n) DRY_RUN=1 ;;
  "") : ;;
  *) echo "사용법: $0 [--dry-run]" >&2; exit 2 ;;
esac

# 자기 ROOT cwd 인지 실측(orch_kill_watchers.sh·봇 find_pid 와 동일한 필터).
#   반환: ROOT 소속(kill 대상) / 다른 cwd(건드리지 않음) / lsof 실패(소속 불명 → 건너뜀)
cwd_of() {
  # 프로세스 cwd 한 줄 반환(lsof -Fn 은 "n<path>" 형식). 실패 시 빈 문자열.
  lsof -a -p "$1" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | head -1
}

# pgrep 결과를 배열로 수집.
# ★bash 3.2(macOS 기본) 호환: mapfile 미지원 → while read 로 수집.
pids=()
while IFS= read -r _pid; do
  [ -n "$_pid" ] && pids+=("$_pid")
done < <(pgrep -f "$PATTERN" 2>/dev/null || true)

if [ "${#pids[@]}" -eq 0 ]; then
  echo "정리할 워커 감시 프로세스 없음 (pgrep -f \"$PATTERN\" 0건)"
  exit 0
fi

killed=0
skipped_other=0
skipped_unknown=0

for pid in "${pids[@]}"; do
  [ -n "$pid" ] || continue
  pcwd="$(cwd_of "$pid")"
  if [ -z "$pcwd" ]; then
    # 소속 불명은 조용히 통과하지 않고 사유를 stderr 에 남기고 건너뛴다(안전측).
    echo "PID $pid: 소속 불명(lsof cwd 조회 실패), 건너뜀" >&2
    skipped_unknown=$((skipped_unknown+1))
    continue
  fi
  if [ "$pcwd" != "$ROOT" ]; then
    # 다른 프로젝트 워커 감시 — 절대 건드리지 않는다(사고 재발 방지).
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
