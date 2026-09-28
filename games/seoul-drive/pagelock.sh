# 서울드라이브 공용 페이지 락 (MUST — 2026-09-27 orch). 주행 스크립트는 반드시 이 락을 잡고 돈다.
# 획득 실패 = 조용히 진행 금지, 즉시 종료. 근거: 체인 3개 동시 실행으로 다수 런이 frames 0(무효)인데 측정된 것처럼 보고될 뻔했다.
# 사용: source pagelock.sh ; lock_page "<name>" || exit 9 ; trap unlock_page EXIT
LOCK=${PAGE_LOCK:-/tmp/.seoul_drive_page.lock}
lock_page(){ local me="$1" n=0 owner opid
  while :; do
    # mkdir 은 원자적이다. 성공 즉시 pid 를 쓰고 나온다.
    if mkdir "$LOCK" 2>/dev/null; then echo $$ > "$LOCK/pid"; echo "$me" > "$LOCK/owner"; LOCK_HELD=1; return 0; fi
    opid=$(cat "$LOCK/pid" 2>/dev/null)
    # ★회수는 'pid 파일이 실제로 있고 그 프로세스가 죽었을 때'만. pid 가 아직 안 쓰였으면(생성 직후 경쟁) 기다린다 —
    #   이 구분을 안 하면 두 번째 요청자가 갓 만들어진 락을 고아로 오인해 지우고 들어온다(2026-09-27 자체 시험에서 검출).
    if [ -n "$opid" ] && ! kill -0 "$opid" 2>/dev/null; then rm -rf "$LOCK"; continue; fi
    sleep 5; n=$((n+1)); [ $n -gt 3600 ] && { echo "lock timeout ($me), held by $(cat "$LOCK/owner" 2>/dev/null) pid $opid"; return 1; }
  done; }
unlock_page(){ [ "${LOCK_HELD:-0}" = 1 ] && [ "$(cat "$LOCK/pid" 2>/dev/null)" = "$$" ] && rm -rf "$LOCK"; LOCK_HELD=0; return 0; }
