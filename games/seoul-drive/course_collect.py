#!/usr/bin/env python3
"""a_5818: RULE demonstrations on the standalone course page -> train_geo-format dataset.
One dir per episode (data/course_s1/e<NNN>_<dir>_o<off>_h<hd>/{X,Y,L,Q}.npy).
Frames and labels come from the page's /frame push (JPEG + X-Lbl of the SAME frame), so there is
no capture/telemetry skew. Labels L = course-truth geometry (train_geo 12-col schema); Y = the
control actually applied [st, 0, 0, v] (ode-teacher-todo D-00). Q pos is written far off-map on
purpose: the course sits at the origin, which is holdout chunk [0,0], and train_geo would drop it.
usage: python3 course_collect.py <outroot> [--quick]"""
import sys, os, json, time, subprocess, urllib.request, argparse
import numpy as np, cv2, torch, gpu_guard
from net import preprocess
DEV = gpu_guard.require_gpu()
B = 'http://localhost:8901'
def post(d):
    urllib.request.urlopen(urllib.request.Request(B + '/ctl', json.dumps(d).encode(), {'Content-Type': 'application/json'}), timeout=3).read()
def frame(since):
    r = urllib.request.urlopen(f'{B}/frame?since={since}', timeout=3)
    if r.status == 204: return None, since
    return (r.read(), json.loads(r.headers.get('X-Lbl') or '{}')), int(r.headers.get('X-Seq'))
def episode(url, secs=40):
    post({'on': 0, 'force': 0, 'release': 1, 'tgt': 0, 'mode': 1, 'lp': 0.0, 'ld': -1, 'vT': -1})
    try: frame(-1)                       # a consumer read turns push on (server push=1 for 2s)
    except Exception: pass
    # reload in the BACKGROUND: the recovery happens in the first ~2s, which reload.sh spends waiting
    # for readiness. Read frames from the start; lock onto the first NEW page (el<1.5, not done).
    pr = subprocess.Popen(['bash', 'reload.sh', url, '45'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    old_lid = None
    try: old_lid = json.load(urllib.request.urlopen(B + '/tel', timeout=3)).get('loadId')
    except Exception: pass
    X, Y, L, Q = [], [], [], []; since = -1; t0 = time.time(); last = None; lid = None
    while time.time() - t0 < secs:
        try: got, since = frame(since)
        except Exception: time.sleep(0.02); continue
        if got is None: time.sleep(0.01); continue
        jpg, lb = got; g = lb.get('geo')
        if lid is None:
            if lb.get('lid') and lb.get('lid') != old_lid and not lb.get('done') and lb.get('el', 9) < 1.5: lid = lb['lid']
            else: continue
        if lb.get('lid') != lid: continue
        if lb.get('done'): last = lb; break
        if not g or lb.get('drv') not in ('RULE', 'MODEL'): continue
        img = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
        x = preprocess(img, device=DEV)
        X.append((x.cpu().numpy() * 255).astype(np.uint8))
        Y.append([lb['st'], 0.0, 0.0, lb['v']]); L.append(g)
        Q.append([0, 0, 0, lb.get('el', 0.0), 6.0e7 + lb['pos'][0] * 6, 6.0e7 + lb['pos'][1] * 6])
        last = lb
    pr.wait(timeout=60)
    if lid is None: return None, 'page never started: ' + (pr.stdout.read() or '')[-160:]
    return (np.stack(X) if X else None, np.array(Y, np.float32), np.array(L, np.float32), np.array(Q, np.float32), last), None
def plan(quick=False):
    P = []
    for d in ('L', 'R'):
        P += [(d, 0, 0)] * (1 if quick else 3)
        if quick: continue
        P += [(d, o, 0) for o in (-2, -1, 1, 2)] + [(d, 0, h) for h in (-20, -10, 10, 20)]
        P += [(d, 1.5, -15), (d, -1.5, 15), (d, 1.5, 15), (d, -1.5, -15)]
    return P
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('outroot'); ap.add_argument('--quick', action='store_true')
    ap.add_argument('--extra', default='', help='extra URL params, e.g. &cturn=70'); ap.add_argument('--start', type=int, default=0)
    a = ap.parse_args(); os.makedirs(a.outroot, exist_ok=True)
    for k, (d, o, h) in enumerate(plan(a.quick)):
        n = a.start + k
        url = f'{B}/course_page.html?course=1&cdir={d}&poff={o}&phd={h}{a.extra}'
        res, err = episode(url)
        if err or res is None or res[0] is None: print(json.dumps({'ep': n, 'url': url, 'error': err or 'no frames'}), flush=True); continue
        X, Y, L, Q, last = res
        od = f'{a.outroot}/e{n:03d}_{d}_o{o}_h{h}'; os.makedirs(od, exist_ok=True)
        for nm, arr in (('X', X), ('Y', Y), ('L', L), ('Q', Q)): np.save(f'{od}/{nm}.npy', arr)
        dt = np.diff(Q[:, 3]); fps = round(1 / float(np.median(dt)), 1) if len(dt) else 0
        print(json.dumps({'ep': n, 'dir': od.split('/')[-1], 'frames': len(X), 'fps': fps, 'ey_max': round(float(np.abs(L[:, 0]).max()), 2),
                          'epsi_max_deg': round(float(np.degrees(np.abs(L[:, 1]).max())), 1), 'done': (last or {}).get('done'), 'touch': (last or {}).get('touch'),
                          'prog': (last or {}).get('prog')}), flush=True)
    post({'on': 0, 'force': 0, 'release': 1, 'tgt': 0, 'mode': 1, 'lp': 0.0, 'ld': -1, 'vT': -1})
