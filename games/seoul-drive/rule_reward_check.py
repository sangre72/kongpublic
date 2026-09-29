#!/usr/bin/env python3
"""u_5771 OBJECTIVE VALIDATION: score the RULE controller under the SAME reward as the RL policy.
If the rule does not clearly beat a random-init policy, the reward is wrong and PPO cannot help.
No model drives here - the rule drives, we only observe /tel and compute reward."""
import sys, os, json, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
TEL = 'http://localhost:8901/tel'
W = float(os.environ.get('W', '0.5'))
def tel():
    try:
        with urllib.request.urlopen(TEL, timeout=4) as r: return json.load(r)
    except Exception: return None
def reward(prev, cur, w, dlp):
    g = cur.get('geo') or {}
    ey = g.get('ey'); ey = abs(float(ey)) if isinstance(ey, (int, float)) else 2.0
    dprog = (float(cur.get('prog') or 0) - float(prev.get('prog') or 0)) * 100.0
    cr = int(cur.get('cr') or 0) - int(prev.get('cr') or 0)
    _crk = cur.get('crk') or {}
    _dep = sum(v for k, v in _crk.items() if '이탈' in str(k)) if isinstance(_crk, dict) else 0
    off = 1 if (_dep > prev.get('_dep', 0) or ey > 3.5) else 0
    cur['_dep'] = _dep
    r = -ey - w * abs(dlp) + 3.0 * dprog
    done = bool(cr > 0 or off)
    if done: r -= 10.0
    return r, done
def main():
    eps = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    steps = int(sys.argv[2]) if len(sys.argv) > 2 else 250
    out = []
    for e in range(eps):
        prev = tel()
        if not prev: print(json.dumps({'abort': 'no telemetry'})); return
        tot = 0.0; n = 0; last_lat = float((prev.get('geo') or {}).get('ey') or 0.0)
        for _ in range(steps):
            time.sleep(0.05)
            cur = tel()
            if not cur: continue
            lat = float((cur.get('geo') or {}).get('ey') or 0.0)
            dlp = lat - last_lat; last_lat = lat          # rule's own lateral command change
            r, done = reward(prev, cur, W, dlp)
            tot += r; n += 1; prev = cur
            if done: break
        if n:
            out.append(dict(ep=e, n=n, ep_r=round(tot, 1), mean_r=round(tot / n, 3),
                            prog=round(float(prev.get('prog') or 0) * 100, 1)))
            print(json.dumps(out[-1]), flush=True)
    if out:
        m = sum(o['mean_r'] for o in out) / len(out)
        print(json.dumps({'RULE_mean_r': round(m, 3), 'eps': len(out)}), flush=True)
if __name__ == '__main__': main()
