#!/usr/bin/env python3
"""u_5680 정지 바 영향 측정: 주행 중 /tel 을 5Hz 로 표집해 모델 조향 프레임을
(a) 빨간불 40m 이내 접근 (b) 그 외 로 나눠 |ey| 평균/p95, 조향 변화율 p95, 횡드리프트 부호를 비교한다.
사용: python3 sigbar_probe.py <secs> [tag]   (주행은 별도 프로세스가 돌린다)"""
import json, sys, time, urllib.request
import numpy as np

secs = float(sys.argv[1]) if len(sys.argv) > 1 else 300
tag = sys.argv[2] if len(sys.argv) > 2 else 'sig'
A, B = [], []          # (ey, steer, t)
t0 = time.time(); prev = None
while time.time() - t0 < secs:
    try:
        d = json.load(urllib.request.urlopen('http://localhost:8901/tel', timeout=3))
    except Exception:
        time.sleep(0.2); continue
    g = d.get('geo') or {}; da = d.get('da') or {}; tch = (d.get('tch') or {})
    ey, st = g.get('ey'), da.get('st')
    sig = tch.get('sig')                      # 적신호까지 거리(m), 없으면 1e9
    mdl = (d.get('mdl') or {}).get('on') if isinstance(d.get('mdl'), dict) else None
    if ey is None or st is None: time.sleep(0.2); continue
    row = (float(ey), float(st), time.time())
    if sig is not None and 0 < float(sig) < 40: A.append(row)
    else: B.append(row)
    time.sleep(0.2)

def stat(rows, name):
    if len(rows) < 5: return {'set': name, 'n': len(rows)}
    ey = np.array([r[0] for r in rows]); st = np.array([r[1] for r in rows]); t = np.array([r[2] for r in rows])
    dt = np.diff(t); dst = np.abs(np.diff(st)) / np.maximum(dt, 1e-3)
    return {'set': name, 'n': len(rows),
            'ey_mean': round(float(ey.mean()), 3), 'ey_abs_mean': round(float(np.abs(ey).mean()), 3),
            'ey_p95': round(float(np.percentile(np.abs(ey), 95)), 3),
            'steer_rate_p95': round(float(np.percentile(dst, 95)), 3) if len(dst) else None,
            'drift_sign': ('right' if ey.mean() > 0.05 else 'left' if ey.mean() < -0.05 else 'none')}
out = {'tag': tag, 'red_within_40m': stat(A, 'red<40m'), 'other': stat(B, 'other')}
print(json.dumps(out, ensure_ascii=False))
