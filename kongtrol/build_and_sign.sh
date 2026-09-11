#!/usr/bin/env bash
# kongtrol 빌드 + 고정 identifier 재서명(MUST).
#
# WHY: cargo build 결과물은 서명이 없거나 랜덤 identifier로 잡힌다. macOS TCC는 서명 identifier로
#   앱을 식별하므로, 서명이 바뀌거나 사라지면 "다른 앱"으로 보고 손쉬운 사용(Accessibility) 권한을
#   취소한다. 그러면 kongtrol input click/key 가 조용히 전부 no-op 이 된다(에러도 안 남).
#   2026-09-12 사고: 서명이 통째로 사라져(codesign -dvvv = "not signed at all") 마우스·키보드 입력이
#   모두 죽었고, 게임 레벨 자체의 문제로 오진해 수십 동작을 낭비했다.
#   cf .claude/rules/kongtrol-base-reference.md, memory: kongtrol-fixed-identifier-tcc-persist
#
# usage: bash kongtrol/build_and_sign.sh [--release|--debug]   (default: --release)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IDENT="com.kongbot.kongtrol"   # ★고정값. 절대 바꾸지 말 것(바꾸면 권한 재인증 필요).

PROFILE="${1:---release}"
case "$PROFILE" in
  --release) BIN="$SCRIPT_DIR/target/release/kongtrol" ;;
  --debug)   BIN="$SCRIPT_DIR/target/debug/kongtrol" ;;
  *) echo "FAIL: unknown profile $PROFILE (use --release|--debug)" >&2; exit 1 ;;
esac

echo "[1/3] cargo build $PROFILE"
( cd "$SCRIPT_DIR" && cargo build ${PROFILE#--debug} 2>&1 | tail -3 ) || {
  echo "FAIL: cargo build" >&2; exit 1; }

test -x "$BIN" || { echo "FAIL: binary not found: $BIN" >&2; exit 1; }

echo "[2/3] codesign --identifier $IDENT"
codesign -s - --force --identifier "$IDENT" "$BIN"

echo "[3/3] verify"
GOT="$(codesign -dv "$BIN" 2>&1 | awk -F= '/^Identifier=/{print $2}')"
if [[ "$GOT" != "$IDENT" ]]; then
  echo "FAIL: identifier mismatch (got='$GOT' want='$IDENT')" >&2; exit 1
fi
echo "OK: $BIN signed as $IDENT"
echo
echo "NOTE: 재서명 직후에는 macOS가 재인증을 요구할 수 있다."
echo "  시스템 설정 > 개인정보 보호 및 보안 > 손쉬운 사용 에서 kongtrol 항목을 껐다 켜거나 재추가."
echo "  확인: kongtrol see --a11y --compact  (권한 부족 오류가 안 나면 정상)"
