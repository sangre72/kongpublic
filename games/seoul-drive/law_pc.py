#!/usr/bin/env python3
"""law monitor positive control(2026-09-26): 규칙 추종기에 고정 횡오프셋 dOff 를 걸고 /tel 을 5Hz 로 표본화해
차가 실제로 오프셋 주행했는지(geo.ey)와 법규 모니터 카운터(law)·억제 원인(lawDbg)을 같이 기록한다.
usage: python3 law_pc.py <from> <to> <dOff> <secs> [--noon] [--sx X --sy Y]   (--noon = pc_chain.sh 원본과 같이 on/force 없이 tgt 만)"""
import sys, json, time, subprocess, urllib.request, argparse, statistics as st

# ★브라우저 소유권 가드(2026-09-27 u_5695): 운세 등 GUI 잡이 크롬을 쓰는 동안 ODE 는 브라우저를 건드리지 않는다.
def _chrome_guard(name='ode'):
    import os, sys
    f = '/tmp/.chrome_owner'
    if os.path.exists(f) and os.environ.get('CHROME_OWNER_OVERRIDE') != '1':
        try: owner = open(f).read().strip()
        except Exception: owner = '?'
        print('[%s] ABORT - Chrome owned by %r. ODE must not touch the browser.' % (name, owner))
        sys.exit(9)
_chrome_guard(os.path.basename(__file__))

ap = argparse.ArgumentParser(); ap.add_argument('frm'); ap.add_argument('to'); ap.add_argument('doff', type=float); ap.add_argument('secs', type=float)
ap.add_argument('--noon', action='store_true'); ap.add_argument('--sx'); ap.add_argument('--sy'); ap.add_argument('--log', default='')
a = ap.parse_args()
B = 'http://localhost:8901'
def post(d): urllib.request.urlopen(urllib.request.Request(B + '/ctl', json.dumps(d).encode(), {'Content-Type': 'application/json'}), timeout=3).read()
def tel(): return json.load(urllib.request.urlopen(B + '/tel', timeout=3))
RESET = {'on': 0, 'force': 0, 'release': 1, 'tgt': 0, 'mode': 1, 'lp': 0.0, 'ld': -1, 'dOff': 0.0, 'vT': -1}
post(RESET)   # ★규칙: 매 실행 전 /ctl 초기화
url = f'{B}/index.html?go=1&hud=0&' + (f'sx={a.sx}&sy={a.sy}' if a.sx else f'from={a.frm}&to={a.to}')
r = subprocess.run(['bash', 'reload.sh', url, '120'], capture_output=True, text=True); print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:])
if r.returncode: sys.exit('reload failed')
time.sleep(3)
d0 = tel(); law0 = dict(d0.get('law') or {}); cr0 = int(d0.get('cr') or 0)
cmd = {'tgt': 1, 'dOff': a.doff, 'vT': -1, 'mode': 1} if a.noon else {'on': 1, 'force': 1, 'tgt': 1, 'dOff': a.doff, 'vT': -1, 'mode': 1}
rows = []; t0 = time.time(); logf = open(a.log, 'w') if a.log else None
while time.time() - t0 < a.secs:
    try: post(cmd)
    except Exception as e: print('post err', e)
    try:
        d = tel(); g = d.get('geo') or {}; L = d.get('law') or {}
        row = {'t': round(time.time() - t0, 1), 'ey': g.get('ey'), 'lat': g.get('lat'), 'li': g.get('li'), 'nl': g.get('nl'), 'v': d.get('v'), 'prog': d.get('prog'), 'mdlOn': d.get('mdlOn'), 'tgt': (d.get('mdl') or {}).get('tgt') if isinstance(d.get('mdl'), dict) else None,
               'str': L.get('straddle'), 'cen': L.get('center'), 'dbg': d.get('lawDbg'), 'pos': d.get('pos')}
        rows.append(row)
        if logf: logf.write(json.dumps(row, ensure_ascii=False) + '\n')
    except Exception as e: print('tel err', e)
    time.sleep(0.2)
post(RESET)
d = tel(); L = d.get('law') or {}
ey = [r['ey'] for r in rows if isinstance(r.get('ey'), (int, float))]; mv = [r for r in rows if isinstance(r.get('v'), (int, float)) and r['v'] > 2]
eyM = [r['ey'] for r in mv if isinstance(r.get('ey'), (int, float))]
print(json.dumps({'tag': f'PC dOff {a.doff} {a.frm}>{a.to}', 'secs': a.secs, 'n': len(rows), 'moving_n': len(mv), 'ey_med_moving': round(st.median(eyM), 2) if eyM else None,
    'ey_gt07_frac_moving': round(sum(abs(e) > 0.7 for e in eyM) / len(eyM), 2) if eyM else None, 'v_mean': round(st.mean([r['v'] for r in mv]), 1) if mv else 0,
    'prog': d.get('prog'), 'cr': int(d.get('cr') or 0) - cr0, 'mdlOn_frac': round(sum(1 for r in rows if r.get('mdlOn')) / max(1, len(rows)), 2),
    'law': {k: int((L.get(k) or 0) - (law0.get(k) or 0)) for k in ('turnLane', 'straddle', 'center', 'signal', 'solid')}, 'ev': (L.get('ev') or [])[-6:], 'lawDbg': d.get('lawDbg')}, ensure_ascii=False))
