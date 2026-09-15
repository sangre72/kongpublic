#!/bin/bash
# u_ 처리 완료 등록. 번호만 주면 실제 파일명을 디렉토리에서 찾아 넣는다.
#   사용: bash seen_u.sh 5087 5088 5089
# ★파일명을 손으로 타이핑하지 않는다 — 추측한 이름은 SEEN 에 안 맞아
#   봇이 같은 u_ 를 계속 re-notify 한다(2026-09-15 실제 사고, 5건 반복 알림).
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
UDIR="$ROOT/telegram_bot/orchestrator/protocol/u"
SEEN="$ROOT/logs/.orch_seen_u"
for n in "$@"; do
  real=$(ls "$UDIR" | grep "^u_${n}_" | head -1)
  if [ -z "$real" ]; then echo "u_$n: 파일 없음(이미 아카이브됐을 수 있음)"; continue; fi
  if grep -qxF "$real" "$SEEN"; then echo "u_$n: 이미 등록됨"; else
    echo "$real" >> "$SEEN"; echo "u_$n: 등록 -> $real"; fi
done
