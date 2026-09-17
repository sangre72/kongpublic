#!/bin/bash
# u_5341/u_5342: 사고 구간 회귀시험 일괄 실행. 새 수정이 과거 사고를 되살리는지 매번 확인한다.
cd "$(dirname "$0")"
python3 - <<'PY'
import json,subprocess,sys
cs=json.load(open('regression_cases.json'))['cases']
bad=0
for c in cs:
    print(f"\n=== {c['id']} ({c['from']} > {c['to']}, {c['secs']}s) ===")
    print(f"    증상: {c['symptom']}")
    out=subprocess.run(['python3','focus_test.py',str(c['secs']),f"{c['from']}>{c['to']}"],
                       capture_output=True,text=True,timeout=c['secs']+300).stdout
    last=[l for l in out.strip().split('\n') if '"result"' in l]
    if not last: print('    FAIL: no result'); bad+=1; continue
    r=json.loads(last[-1]); print('   ',json.dumps(r,ensure_ascii=False))
    for k,v in c['expect'].items():
        got=r.get(k)
        if got!=v: print(f"    ★REGRESSION {k}: expect {v}, got {got}"); bad+=1
print(f"\n{'ALL PASS' if not bad else str(bad)+' REGRESSION(S)'}")
sys.exit(1 if bad else 0)
PY
