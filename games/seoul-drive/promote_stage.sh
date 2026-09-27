#!/bin/bash
# 스테이징 지도(data6_stage.js: 비대칭 lf/lb + 연결로 일방 ol) 승격 — cases/map_fix_2026-09-26.md §4. 주행 중 실행 금지(리로드 포함).
# 사용: bash games/seoul-drive/promote_stage.sh [--no-reload]   (레포 루트 기준 경로)
set -e; cd /Users/bumsuklee/git/kong-bot; D=games/seoul-drive; TS=2026-09-26
[ -f $D/data/data6_stage.js ] || { echo "no stage pack"; exit 1; }
n=$(pgrep -fl python3 | grep -Ec 'python3 (gpu_drive|dagger|eval20|offline_gate|seg_gate)' || true); [ "${n:-0}" -gt 0 ] && { echo "page/GPU busy ($n) — abort"; exit 2; }   # ★grep -c 는 0건일 때 exit 1 → set -e 로 스크립트가 조용히 죽는다(2026-09-26 실측)
[ -f $D/data/data6_prev_$TS.js ] || cp $D/data/data6.js $D/data/data6_prev_$TS.js            # 백업(1회만)
cp $D/data/data6_stage.js $D/data/data6.js                                                   # 승격
python3 $D/build_search_index.py                                                             # 검색 인덱스(data6.js 기준)
python3 $D/build.py                                                                          # index.html 재빌드(기본값 유지: --speed 금지, 규칙 §7)
grep -o "__TARGET_KMH=[0-9]*" $D/index.html | grep -q 120 || { echo "TARGET_KMH != 120"; exit 3; }
python3 $D/map_verify.py $D/data/data6_prev_$TS.js $D/data/data6.js --report $D/data/map_fixes_$TS.json --out $D/data/map_verify_promote_$TS.json | tail -3
[ "$1" = "--no-reload" ] && { echo "promoted (no reload)"; exit 0; }
bash $D/reload.sh "http://localhost:8901/index.html?go=1" 120 | tail -1
bash $D/run_regression.sh                                                                    # 회귀(regression_cases.json): 순간이동 0·갇힘 0·회피가능 사고 0
echo "PROMOTE_DONE $(date +%H:%M)"
# 되돌리기: cp $D/data/data6_prev_$TS.js $D/data/data6.js && python3 $D/build_search_index.py && python3 $D/build.py && bash $D/reload.sh ...
