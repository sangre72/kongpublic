#!/usr/bin/env bash
# worker_1 kongewalker 10초 감시 (1틱) — ROOT=kong-bot only (not sky). Monitor 루프에서 호출.
# ★중복 이벤트 방출 방지(노이즈 제거, 유저 지시 2026-08-05): 이미 방출한 seq 는
#   logs/.worker1_seen 에 기록 → 재방출 안 함. ar 생기면(처리됨) seen 에서 제거.
# 방출(stdout 1줄=이벤트): 새 PENDING_A / 새 NEEDS_INFO / (240틱마다) MONITOR_RESET_DUE.
#
# ★2026-08-13 CPU 근본최적화(user "모니터가 13% 먹냐"): 매틱 28개 a_ × fork 8~10개(basename·echo|sed·
#   glob·grep) = 250+ 프로세스/틱 = CPU 93%·0.35s. → 파일당 fork 0(bash 내장 parameter-expansion·
#   [[ ]]·globbing·read 루프). seen 은 1회 읽어 문자열 매칭. 동작 100% 보존(같은 이벤트 방출).
#   ★macOS /bin/bash=3.2 호환: 연관배열(declare -A)·printf %()T 불가 → 문자열 seen + date 1 fork 만.
set -u
SELF="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR="$(cd "$(dirname "$SELF")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
# Pin: verify SCRIPT_DIR-derived ROOT actually contains this project's marker (block accidental sky/other cwd pollution)
if [ ! -d "$ROOT/telegram_bot/orchestrator/protocol/a" ]; then
  echo "worker1_monitor_tick: ROOT verify 실패($ROOT) — 감시 중단" >&2
  exit 1
fi
cd "$ROOT" 2>/dev/null || { echo "worker1_monitor_tick: ROOT cd 실패($ROOT) — 감시 중단" >&2; exit 1; }
AD=telegram_bot/orchestrator/protocol/a
ARD=telegram_bot/orchestrator/protocol/ar
ST=logs/worker1_status.txt
CTL=logs/monitor-control.txt
SEEN=logs/.worker1_seen
TICKF=logs/.worker1_tick

setopt NULL_GLOB 2>/dev/null || true
shopt -s nullglob 2>/dev/null || true

[ -e "$SEEN" ] || : > "$SEEN"
# ★macOS /bin/bash 3.2 는 $(<file) 가 빈값 반환하는 버그 → tick·seen 리셋(dedup 붕괴).
#   $(cat …) 로 교체(정확성 위해 fork 감수). 2026-08-13 fix.
tick=$(cat "$TICKF" 2>/dev/null); tick=${tick:-0}; tick=$((tick+1)); printf '%s' "$tick" > "$TICKF"

# seen 파일 전체를 1회 읽어 개행구분 문자열로(매 파일 grep 제거). 매칭은 case 로 fork 없이.
seen=$(cat "$SEEN" 2>/dev/null) || seen=""
seen="
$seen
"
# seen_has P|N seq → 문자열에 "\n<tag>:<seq>\n" 있으면 0
seen_has() { case "$seen" in *"
$1:$2
"*) return 0;; esac; return 1; }
seen_add() { seen="$seen$1:$2
"; changed=1; }
seen_del() { # 라인 삭제(문자열 치환)
  local t="
$1:$2
"; seen="${seen/$t/
}"; changed=1;
}

# 파일에서 [STATUS] 값·[ANSWER] 유무를 fork 없이 read 루프로.
# ★2026-08-13: printf|tr(파일당 fork 2개) 제거 — 소문자화 대신 아래 case 에서 대/소문자
#   패턴 병기(bash3.2 는 ${v,,} 없음). status 값은 소문자 하이픈 규칙이나 방어적 병기.
status_of() { REPLY_ST=""; local ln
  while IFS= read -r ln || [ -n "$ln" ]; do
    case "$ln" in *'[STATUS]'*|*'[status]'*) REPLY_ST="${ln#*']'}"; return;; esac
  done < "$1"; }
has_answer() { local ln; while IFS= read -r ln || [ -n "$ln" ]; do case "$ln" in *'[ANSWER]'*|*'[answer]'*) return 0;; esac; done < "$1"; return 1; }

pend=""; ni=""; changed=0
for a in "$AD"/a_*.txt; do
  b=${a##*/}                       # basename (내장)
  n=${b#a_}; n=${n%.txt}           # seq (내장)

  # ★ar 매칭 = ar_<full-stem>.txt 양 경로(a/·ar/). 별표없는 리터럴 경로는 nullglob
  #   미적용→미존재시 리터럴 잔존 → 반드시 -e 로 실존 파일만 채택(2026-08-13 fix).
  hit=""
  for cand in "$AD"/ar_${n}.txt "$ARD"/ar_${n}.txt "$AD"/ar_${n}_*.txt "$ARD"/ar_${n}_*.txt; do
    [ -e "$cand" ] && { hit="$cand"; break; }
  done
  if [ -n "$hit" ]; then
    seen_has P "$n" && seen_del P "$n"
    status_of "$hit"
    if [[ $REPLY_ST == *needs-info* || $REPLY_ST == *NEEDS-INFO* || $REPLY_ST == *Needs-Info* ]] && ! has_answer "$hit"; then
      ni="$ni $n"
      if ! seen_has N "$n"; then echo "NEEDS_INFO $b (${hit##*/})"; seen_add N "$n"; fi
    else
      seen_has N "$n" && seen_del N "$n"
    fi
    continue
  fi

  status_of "$a"
  # 대/소문자 병기(status_of 가 더는 소문자화 안 함). status 값은 소문자 규칙이나 방어적.
  case "$REPLY_ST" in
    *in-progress*|*done*|*blocked*|*error*|*failed*|*needs-info*| \
    *IN-PROGRESS*|*DONE*|*BLOCKED*|*ERROR*|*FAILED*|*NEEDS-INFO*| \
    *In-Progress*|*Done*|*Blocked*|*Error*|*Failed*|*Needs-Info*)
      seen_has P "$n" && seen_del P "$n"; continue ;;
  esac
  pend="$pend $n"
  # First emit + re-emit every 6 ticks (~60s @10s). One-shot seen used to swallow
  # PENDING_A when no session Monitor was listening (launchd stdout, Grok deny).
  if ! seen_has P "$n"; then
    echo "PENDING_A $b (no ar, 지시서=pending seq $n)"
    seen_add P "$n"
  elif [ $((tick % 6)) -eq 0 ]; then
    echo "PENDING_A $b (still no ar, reemit tick=$tick)"
  fi
done

# seen 변경 시에만 재기록(앞뒤 빈줄 정리)
if [ "$changed" -eq 1 ]; then
  printf '%s\n' "$seen" | grep -E '^(P|N):' > "$SEEN" 2>/dev/null || : > "$SEEN"
fi

if [ $((tick % 240)) -eq 0 ]; then
  ctl=$(cat "$CTL" 2>/dev/null) || ctl=""
  [[ $ctl == *RESET_MONITOR* ]] && echo "MONITOR_RESET_DUE tick=$tick (40min@10s) — 세션은 이 Monitor TaskStop 후 재arm"
fi

ts=$(date '+%Y-%m-%d %H:%M:%S')   # date = 유일한 불가피 fork(1/틱)
rem=$(( (240 - tick % 240) * 5 / 60 ))
printf '[%s] worker_1 kongewalker(kong-bot) · tick=%s · pending=[%s] needs-info=[%s] · 다음 리셋체크 ~%s분\n' \
  "$ts" "$tick" "${pend# }" "${ni# }" "$rem" > "$ST"
