#!/usr/bin/env bash
# vision_agent.sh — 순수 비전 자율 에이전트 코어 (a_18, u_21, P0. 범용·앱무관).
# ★USER: "비전으로 순수 비전으로만 인식·판단·계획·진행." = 완전 자율 비전 루프.
#   ROLE 분리: kongtrol=눈(캡처)+손(물리입력) / AI(워커)=뇌(스샷 read→판단→좌표).
#   ★kongtrol 은 판단 안 함(규칙solver·locator·geom좌표·osascript·고정시퀀스 전폐기).
#   폐루프: [캡처]→[AI가 스샷 봄=비전인식]→[판단·계획]→[물리실행]→[재캡처] 반복.
#
# 이 스크립트 = 눈+손 [단일 스텝 실행기]. 뇌(판단)는 워커가 매 스텝 스샷 Read 해서 주입.
# 사용:
#   vision_agent.sh see [out.png]            # 캡처(눈) — 워커가 이 png 를 Read 해 판단
#   vision_agent.sh click <x> <y> [--double|--right]   # 손: 물리좌표 클릭(AI가 스샷보고 지정)
#   vision_agent.sh move <x> <y>             # 손: 커서 이동만
#   vision_agent.sh type "<text>"            # 손: 텍스트 타이핑
#   vision_agent.sh key <name> [repeat]      # 손: 특수키
#   vision_agent.sh chord <mod> <key>        # 손: 조합키(⌘N 등)
#   vision_agent.sh rec-start / rec-stop     # 화면 녹화(과정 영상)
# ★--human 전역: 사람속도(보간이동·글자딜레이). 기본 빠름(속도 무관 user).
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="$ROOT/target/release/kongtrol"
SHOTDIR="${TMPDIR:-/tmp}/kongtrol_play_shots"
RECPID_FILE="$SHOTDIR/.vision_rec_pid"
SCALE="${VISION_SCALE:-2.0}"      # Retina backing scale(물리÷scale=논리). 실측 2.0.
HUMAN="${VISION_HUMAN:-}"          # VISION_HUMAN=1 이면 --human
mkdir -p "$SHOTDIR"
[ -x "$BIN" ] || { echo "빌드 필요: cargo build --release" >&2; exit 1; }
HFLAG=""; [ -n "$HUMAN" ] && HFLAG="--human"

cmd="${1:-see}"; shift || true
case "$cmd" in
  see)
    OUT="${1:-$SHOTDIR/vision_frame.png}"
    screencapture -x "$OUT" 2>/dev/null && echo "SEE $OUT" || { echo "capture 실패(화면기록 권한)"; exit 3; }
    ;;
  click)
    X="$1"; Y="$2"; shift 2 || true
    EXTRA=""
    for a in "$@"; do case "$a" in --double) EXTRA="$EXTRA --double";; --right) EXTRA="$EXTRA --right";; esac; done
    "$BIN" $HFLAG --yes input click "$X" "$Y" --scale "$SCALE" $EXTRA
    ;;
  move)
    "$BIN" $HFLAG --yes input move "$1" "$2" --scale "$SCALE"
    ;;
  type)
    "$BIN" $HFLAG --yes input text "$1"
    ;;
  key)
    R="${2:-1}"
    "$BIN" --yes input key "$1" --repeat "$R"
    ;;
  chord)
    "$BIN" --yes input chord "$1" "$2"
    ;;
  rec-start)
    REC="${1:-$SHOTDIR/vision_recording.mov}"; rm -f "$REC"
    screencapture -v "$REC" >/dev/null 2>&1 &
    echo $! > "$RECPID_FILE"
    echo "REC_START $REC (pid $(cat "$RECPID_FILE"))"
    ;;
  rec-stop)
    if [ -f "$RECPID_FILE" ]; then
      kill -INT "$(cat "$RECPID_FILE")" 2>/dev/null; sleep 2
      rm -f "$RECPID_FILE"
      echo "REC_STOP"
    else echo "녹화 중 아님"; fi
    ;;
  *)
    echo "unknown cmd: $cmd (see/click/move/type/key/chord/rec-start/rec-stop)" >&2; exit 2;;
esac
