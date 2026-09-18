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
    env=dict(__import__('os').environ)
    if c.get('extra_qs'): env['EXTRA_Q']=c['extra_qs']
    out=subprocess.run(['python3','focus_test.py',str(c['secs']),f"{c['from']}>{c['to']}"], env=env,
                       capture_output=True,text=True,timeout=c['secs']+300).stdout
    # ★2026-09-19: 이벤트 줄(teleport/crash)을 안 찍어서 갇힘 위치를 두 번이나 다시 재현해야 했다. 같이 찍는다.
    for l in out.strip().split('\n'):
        if '"teleport"' in l or '"crash"' in l:
            try:
                e=json.loads(l); k='teleport' if 'teleport' in e else 'crash'; t=e[k]; g=t.get('g2',{}); da=t.get('da',{})
                print('    EVT %s t=%s m=%s v=%s crk=%s | roadW=%s nl=%s laneF=%s turn=%s/%s lat=%s | vmax=%s xt=%s gp=%s'%(k,t.get('t'),t.get('m'),t.get('v'),t.get('crk'),g.get('roadW'),g.get('nl'),g.get('laneF'),g.get('aTurn'),g.get('aD'),g.get('lat'),da.get('vmax'),da.get('xt'),da.get('gp')))
            except Exception: print('    EVT', l[:160])
    last=[l for l in out.strip().split('\n') if '"result"' in l]
    if not last: print('    FAIL: no result'); bad+=1; continue
    r=json.loads(last[-1]); print('   ',json.dumps(r,ensure_ascii=False))
    for k,v in c['expect'].items():
        got=r.get(k)
        if got!=v: print(f"    ★REGRESSION {k}: expect {v}, got {got}"); bad+=1
print(f"\n{'ALL PASS' if not bad else str(bad)+' REGRESSION(S)'}")
sys.exit(1 if bad else 0)
PY
