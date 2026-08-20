#!/usr/bin/env bash
# ground.sh — a11y grounding (a_47). Emits LOGICAL cx,cy for `kongtrol input click X Y --scale 1.0`.
#   a11y tree dump → label match → FOUND <lx> <ly>. Labeled chrome only (INV1).
#   Canvas / unlabeled → caller uses ground_hybrid.sh (a11y-first) / ground_vl.sh (REMOTE).
# 사용:
#   ground.sh <App> "<label>"   → FOUND <lx> <ly>   (LOGICAL pt)
#   예: ground.sh Keynote "차트"  → then: kongtrol input click $lx $ly --scale 1.0
# 반환: `FOUND <lx> <ly>` or `NOTFOUND`.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="$ROOT/target/release/kongtrol"
# default 1.0 = emit LOGICAL (INV1). Override VISION_SCALE only if caller wants scaled-out.
SCALE="${VISION_SCALE:-1.0}"
APP="$1"; LABEL="$2"
PID=$(pgrep -x "$APP" | head -1)
[ -z "$PID" ] && { echo "NOTFOUND (앱 '$APP' 미실행)"; exit 1; }

# a11y dump(JSON) — 5s cache (a_66). Prefer input run for multi-label.
JSON=$("$ROOT/demo/a11y_dump_cached.sh" "$PID") || JSON=""
RESULT=$(printf '%s' "$JSON" | python3 -c "
import sys, json
lbl = '''$LABEL'''
try: d = json.load(sys.stdin)['data']
except Exception: print('NOTFOUND'); sys.exit()
scale = float($SCALE)
cand = [e for e in d if e.get('label','')==lbl]
if not cand: cand = [e for e in d if lbl and lbl in e.get('label','')]
if not cand: print('NOTFOUND'); sys.exit()
cand.sort(key=lambda e: e['w']*e['h'])   # 작은 요소=더 구체적
e = cand[0]
print(f\"FOUND {int(round(e['cx']*scale))} {int(round(e['cy']*scale))}\")
")
echo "$RESULT"
