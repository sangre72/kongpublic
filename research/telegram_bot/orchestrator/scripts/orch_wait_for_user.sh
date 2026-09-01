#!/usr/bin/env bash
# ★폐기예정 (a_152, 2026-08-05): 제5원칙 전환으로 이 자동깨움 감시기는 오케의 /loop 이 대체한다.
#   봇에 감시기 재기동 로직을 붙였다 크래시(a_152) → 감시는 loop 하나로 단순화. 이 스크립트는
#   즉시 삭제하지 않고 안 쓰는 상태로 둔다(삭제는 오케 판단). loop 이 텔레그램·워커 5초 감시를 한다.
# 오케스트레이터 — 새 유저요청(미처리 protocol/u/u_*.txt) 감지 시 즉시 종료.
# harness 백그라운드로 실행 → "종료 시 에이전트 재호출" 특성을 이용해 자동 처리 유도.
# 처리 사이클: 이 스크립트 백그라운드 실행 → NEW=u_xxx 뜨면 exit → 세션(오케스트레이터) 깨어남
#            → 텔레그램 유저 요청 처리 → logs/.orch_seen_u 에 basename 등록 → 다시 이 스크립트 실행.
# 미처리 판별: logs/.orch_seen_u(줄마다 처리완료 u_ 파일 basename) 에 없는 u_*.txt = 새 요청.
#            이미 seen 에 있는 파일은 무시(같은 요청으로 반복 깨움 방지).
# 이 스크립트 자신은 seen 에 추가하지 않는다 — 처리 주체(세션)가 처리 완료 후 등록.
# worker1_wait_for_pending.sh 와 동일 구조(protocol/a → protocol/u 버전).
#
# 경로(u_136 이동): 이 스크립트 = <repo>/telegram_bot/orchestrator/scripts/
#  - OCH_DIR(../)        = telegram_bot/orchestrator  → 큐 protocol/ 위치
#  - REPO_ROOT(../../../) = repo 루트                 → logs/ 위치(cwd)
set -euo pipefail
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OCH_DIR="$(cd "$SELF_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SELF_DIR/../../.." && pwd)"
cd "$REPO_ROOT"
U_DIR="$OCH_DIR/protocol/u"

MAX_WAIT="${ORCH_WAIT_MAX_SEC:-21600}"   # 6h 안전 타임아웃
SEEN_FILE="logs/.orch_seen_u"
ALIVE_FILE="logs/.orch_alive"            # 오케 생존신호(봇이 mtime 관찰 → 끊기면 경보). och 제2원칙 C.
mkdir -p logs
touch "$SEEN_FILE"

start=$(date +%s)

while true; do
  # ★오케 생존신호 갱신 — 이 감시기가 도는 것 = 오케 세션이 §9-0 을 준수하며 살아있다는 뜻.
  #   봇(orchestrator.py check_orch_alive)이 이 mtime 을 관찰해 오래 끊기면 유저에게 경보한다.
  date '+%Y-%m-%dT%H:%M:%S' > "$ALIVE_FILE" 2>/dev/null || true
  new_base=""
  new_path=""
  shopt -s nullglob
  for f in "$U_DIR"/u_*.txt; do
    base=$(basename "$f")
    if ! grep -qxF "$base" "$SEEN_FILE" 2>/dev/null; then
      new_base="$base"
      new_path="$f"
      break
    fi
  done
  shopt -u nullglob

  if [[ -n "$new_base" ]]; then
    seq="${new_base#u_}"
    seq="${seq%%_*}"
    firstline=$(head -1 "$new_path" 2>/dev/null || true)
    echo "ORCH_USER_PICKUP $(date '+%H:%M:%S') NEW=u_${seq} \"${firstline}\""
    echo "→ protocol/u 새 요청 처리 후 이 스크립트를 다시 백그라운드 실행하세요."
    exit 0
  fi

  now=$(date +%s)
  if (( now - start >= MAX_WAIT )); then
    echo "ORCH_WAIT_TIMEOUT $(date '+%H:%M:%S') (${MAX_WAIT}s 무요청 — 재실행 필요)"
    exit 0
  fi
  sleep 5
done
