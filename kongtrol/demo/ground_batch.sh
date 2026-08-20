#!/usr/bin/env bash
# ground_batch.sh — a11y 배치 grounding (a_25). ★1 a11y-dump → N개 라벨 좌표 한번에 추출.
#   목적: 워커 매스텝 LLM왕복(스샷→판단→클릭) 제거. 1덤프(0.33s)로 서브작업 전체 좌표 확보 →
#         shell이 클릭/타이핑 시퀀스를 LLM 개입 없이 연속 실행. (K6 observe=dump, act=sequence)
# 사용:
#   ground_batch.sh <App> "라벨1" "라벨2" ...   → 각 줄 `라벨\t<px> <py>` or `라벨\tNOTFOUND`
#   (좌표는 LOGICAL pt. default SCALE=1.0. `kongtrol input click X Y` default --scale 1.0)
# ★결정적: 라벨 매칭이 곧 확인 → 스샷 불필요. 화면 구조 변경(새 패널/다이얼로그) 시에만 재덤프.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="$ROOT/target/release/kongtrol"
SCALE="${VISION_SCALE:-1.0}"
APP="$1"; shift
PID=$(pgrep -x "$APP" | head -1)
[ -z "$PID" ] && { echo "ERR 앱 '$APP' 미실행"; exit 1; }

# a_66: 5s dump cache (same helper as ground.sh).
JSON=$("$ROOT/demo/a11y_dump_cached.sh" "$PID") || JSON=""
printf '%s' "$JSON" | SCALE="$SCALE" python3 -c "
import sys, json, os
scale=float(os.environ['SCALE'])
labels=sys.argv[1:]
try: d=json.load(sys.stdin)['data']
except Exception:
    for l in labels: print(f'{l}\tNOTFOUND')
    sys.exit()
for lbl in labels:
    cand=[e for e in d if e.get('label','')==lbl]
    if not cand: cand=[e for e in d if lbl and lbl in e.get('label','')]
    if not cand: print(f'{lbl}\tNOTFOUND'); continue
    cand.sort(key=lambda e: e['w']*e['h'])   # 작은=구체적
    e=cand[0]
    print(f'{lbl}\t{int(e[\"cx\"]*scale)} {int(e[\"cy\"]*scale)}')
" "$@"
