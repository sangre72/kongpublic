#!/usr/bin/env python3
"""오드 주행 평가 — 도착·사고를 잰다 (u_5161).

★상관계수·loss 로 판단하지 않는다. 오드가 실제로 강남역→시청역에 가느냐만 본다.
  이전에 corr 0.99 인데 실주행 조향 상관이 0.011(잡음)이었던 적이 있다.

사용: python3 eval_ode.py <model.pt> <초>
"""
import sys, os, json, time, subprocess, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TEL = 'http://localhost:8901/tel'


def tel():
    try:
        return json.load(urllib.request.urlopen(TEL, timeout=3))
    except Exception:
        return None


def main(model, secs):
    secs = float(secs)
    subprocess.run(['open', '-a', 'Google Chrome'], capture_output=True)
    time.sleep(2)
    t0 = time.time()
    p0 = None; pmax = 0.0; last = None; n = 0; mdl = 0
    while time.time() - t0 < secs:
        d = tel()
        if d:
            n += 1
            if d.get('mdlOn'): mdl += 1
            p = d.get('prog') or 0
            if p0 is None: p0 = p
            pmax = max(pmax, p); last = d
            if p >= 0.95:
                print(json.dumps({'ARRIVED': True, 'prog': p})); break
        time.sleep(2)
    if not last:
        print(json.dumps({'err': 'no telemetry'})); return
    import collections
    L = last.get('lde') or []
    print(json.dumps({
        'model': model,
        'drv': last.get('drv'),
        'model_pct': round(100 * mdl / max(1, n), 1),
        'prog_start': round(p0 or 0, 4),
        'prog_end': round(last.get('prog') or 0, 4),
        'prog_max': round(pmax, 4),
        'crashes': last.get('cr'),
        'crash_types': dict(collections.Counter(x['k'] for x in L)),
        'v': last.get('v'),
        'samples': n,
    }, ensure_ascii=False))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 90)
