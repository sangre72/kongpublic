#!/usr/bin/env bash
# 스카이워커 — 새 지시서(미처리 a_*) 감지 시 즉시 종료.
# harness 백그라운드로 실행 → "종료 시 에이전트 재호출" 특성을 이용해 자동 처리 유도.
# 처리 사이클: 이 스크립트 백그라운드 실행 → PENDING 뜨면 exit → 에이전트 깨어남 → 지시 처리 → 다시 이 스크립트 실행.
# poll5s(현황판)와 별개. 최대 대기(기본 6시간) 후 타임아웃 종료(생존 안전).
set -euo pipefail
# 경로(u_136 이동): OCH_DIR(..)=telegram_bot/orchestrator(protocol), ROOT(../../..)=repo루트
SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
OCH_DIR="$(cd "$SELF_DIR/.." && pwd)"
ROOT="$(cd "$SELF_DIR/../../.." && pwd)"
cd "$ROOT"
A_DIR="$OCH_DIR/protocol/a"
MAX_WAIT="${WORKER1_MAX_WAIT_SEC:-21600}"   # 6h 안전 타임아웃
start=$(date +%s)

while true; do
  pending=""
  shopt -s nullglob
  for f in "$A_DIR"/a_*.txt; do
    base=$(basename "$f")
    ar="$A_DIR/ar_${base#a_}"
    if [[ ! -f "$ar" ]]; then
      pending+="${base} "
      continue
    fi
    # ar 있어도 미종결(done|blocked|error|needs-info|failed 아님)이면 미처리로 간주
    if ! grep -qE '\[STATUS\][[:space:]]*(done|blocked|error|needs-info|failed)' "$ar" 2>/dev/null; then
      # in-progress 는 내가 잡은 것 → 대기 계속. 상태 미표기(unknown)만 PENDING.
      if ! grep -qiE '\[STATUS\][[:space:]]*in[-_]?progress' "$ar" 2>/dev/null; then
        pending+="${base}(unknown) "
      fi
    fi
  done
  shopt -u nullglob

  if [[ -n "$pending" ]]; then
    echo "WORKER1_PICKUP $(date '+%H:%M:%S') PENDING=${pending}"
    echo "→ 위 지시서(들)를 즉시 처리하세요. 처리 후 이 스크립트를 다시 백그라운드로 실행해 대기를 이어가세요."
    exit 0
  fi

  now=$(date +%s)
  if (( now - start >= MAX_WAIT )); then
    echo "WORKER1_WAIT_TIMEOUT $(date '+%H:%M:%S') (${MAX_WAIT}s 무지시 — 재실행 필요)"
    exit 0
  fi
  sleep 5
done
