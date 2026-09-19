#!/usr/bin/env python3
"""밤샘 수집 중 사고 위치 군집 (2026-09-19). /tmp/sweep_crash.log(crash_watch 폴러) → 15m 격자 군집, 횟수·유형·구간.
결정적 지점(같은 자리 2회↑)만 회귀 케이스 후보로. 사용: python3 crash_hotspots.py [로그] [시작시각 HH:MM]"""
import json, sys, collections
log = sys.argv[1] if len(sys.argv) > 1 else '/tmp/sweep_crash.log'
t0 = sys.argv[2] if len(sys.argv) > 2 else '20:45'
S = 6.0
rows = [json.loads(l) for l in open(log) if l.strip()]
rows = [r for r in rows if r.get('t', '') >= t0 and (r.get('cr') or 0) > 0]
seen = {}; cl = collections.defaultdict(list)
for r in rows:
    key = (r['load'], r['cr'])
    if key in seen: continue
    seen[key] = 1
    x, y = r['pos'][0] / S, r['pos'][1] / S
    cl[(round(x / 15), round(y / 15))].append(r)
out = []
for k, rs in cl.items():
    types = collections.Counter()
    for r in rs:
        for t, n in (r.get('crk') or {}).items(): types[t] += 1
    x = sum(r['pos'][0] for r in rs) / len(rs) / S; y = sum(r['pos'][1] for r in rs) / len(rs) / S
    out.append((len(rs), round(x, 1), round(y, 1), dict(types), sorted({r.get('doneM') for r in rs})[:4], len({r['load'] for r in rs})))
out.sort(reverse=True)
print(json.dumps({'crash_events': len(seen), 'clusters': len(out)}))
for n, x, y, types, ms, loads in out[:15]:
    print(f"{n}x  ({x},{y})m  loads={loads}  m={ms}  {types}   sx={round(x*S,1)}&sy={round(y*S,1)}")
