#!/usr/bin/env python3
"""a_5818: the MODEL drives the course (geo head -> look-ahead point -> page mode 2, the same path as
gpu_drive --geo), plus same-session RULE controls. Page runs with ?wait=1 for model runs: no rule
fallback, the car parks if commands stop (DRV=WAIT), so model share is measured, not assumed.
usage: python3 course_drive.py <model.pt> --dirs L,R --reps 3 --rule-reps 3 [--extra '&cturn=70'] [--ld 10]"""
import sys, os, json, time, subprocess, urllib.request, argparse
import numpy as np, cv2, torch, gpu_guard
from net import preprocess, DriveNet
import train_geo as TG
DEV = gpu_guard.require_gpu(); B = 'http://localhost:8901'
def post(d):
    try: urllib.request.urlopen(urllib.request.Request(B + '/ctl', json.dumps(d).encode(), {'Content-Type': 'application/json'}), timeout=2).read()
    except Exception: pass
def tel():
    try: return json.load(urllib.request.urlopen(B + '/tel', timeout=3))
    except Exception: return {}
def frame(since):
    r = urllib.request.urlopen(f'{B}/frame?since={since}', timeout=3)
    if r.status == 204: return None, since
    return (r.read(), json.loads(r.headers.get('X-Lbl') or '{}')), int(r.headers.get('X-Seq'))
RESET = {'on': 0, 'force': 0, 'release': 1, 'tgt': 0, 'mode': 1, 'lp': 0.0, 'ld': -1, 'vT': -1}
def run(url, net=None, ld=10.0, vT=8.0, secs=60, video=None):
    post(RESET)
    try: frame(-1)
    except Exception: pass
    old = tel().get('loadId')
    pr = subprocess.Popen(['bash', 'reload.sh', url, '45'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    since = -1; lid = None; t0 = time.time(); drv = {}; err = []; infs = []; vw = None
    while time.time() - t0 < secs:
        try: got, since = frame(since)
        except Exception: time.sleep(0.02); continue
        if got is None: time.sleep(0.005); continue
        jpg, lb = got
        if lid is None:
            if lb.get('lid') and lb.get('lid') != old and not lb.get('done') and lb.get('el', 9) < 1.5: lid = lb['lid']
            else: continue
        if lb.get('lid') != lid: continue
        if lb.get('done'): break
        drv[lb.get('drv')] = drv.get(lb.get('drv'), 0) + 1
        img = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
        if video is not None:
            if vw is None: vw = cv2.VideoWriter(video, cv2.VideoWriter_fourcc(*'mp4v'), 15, (img.shape[1], img.shape[0]))
            vw.write(img)
        if net is None: continue
        ti = time.time()
        with torch.no_grad():
            x = preprocess(img, device=DEV)[None]; v = torch.tensor([[lb.get('v', 0.0) / 30.0]], device=DEV)
            o = (net(x, v, raw=True)[0].float().cpu().numpy()) * TG.SCALE
        infs.append((time.time() - ti) * 1000)
        g = lb.get('geo')
        if g: err.append([o[0] - g[0], o[1] - g[1], o[3] - g[3]])
        post({'on': 1, 'force': 1, 'tgt': 1, 'mode': 2, 'lp': float(o[3]) * (ld / 10.0), 'ld': ld, 'vT': vT})
    post(RESET); pr.wait(timeout=60)
    if vw is not None: vw.release()
    time.sleep(0.3); c = (tel().get('course') or {})
    n = sum(drv.values()) or 1; E = np.abs(np.array(err)) if err else None
    tl = tel()
    return dict(result=c.get('result'), why=c.get('failWhy'), wallN=c.get('wallN'), lineN=c.get('lineN'), endWallN=c.get('endWallN'),
                cornerMaxDev=c.get('cornerMaxDev'), stopDist=c.get('stopDist'), l1Frames=tl.get('l1Frames'), score=c.get('score'), touchN=c.get('touchN'), elapsed=round(c.get('elapsed') or 0, 1),
                prog=c.get('progress'), model_share=round(drv.get('MODEL', 0) / n, 3), drv=drv, started=lid is not None,
                perc_mae=(None if E is None else {'ey': round(float(E[:, 0].mean()), 3), 'epsi_deg': round(float(np.degrees(E[:, 1].mean())), 2), 'lc10': round(float(E[:, 2].mean()), 3)}),
                inf_ms=(round(float(np.median(infs)), 2) if infs else None))
def summ(rows):
    s = [r['score'] for r in rows if isinstance(r.get('score'), (int, float))]; t = [r['touchN'] or 0 for r in rows]
    return dict(n=len(rows), pass_n=sum(r['result'] == 'PASS' for r in rows), why={w: sum(r.get('why') == w for r in rows) for w in ('wall', 'line', 'timeout')}, score_mean=round(float(np.mean(s)), 3) if s else None,
                score_sd=round(float(np.std(s, ddof=1)), 3) if len(s) > 1 else None, touch_mean=round(float(np.mean(t)), 2), touch_sd=round(float(np.std(t, ddof=1)), 2) if len(t) > 1 else None)
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('model'); ap.add_argument('--dirs', default='L,R'); ap.add_argument('--reps', type=int, default=3)
    ap.add_argument('--rule-reps', type=int, default=3); ap.add_argument('--extra', default=''); ap.add_argument('--ld', type=float, default=10.0)
    ap.add_argument('--vT', type=float, default=8.0); ap.add_argument('--video', default=None); ap.add_argument('--out', default=None)
    a = ap.parse_args()
    net = DriveNet(out=12, vin=True, vdim=1, in_ch=3).to(DEV); net.load_state_dict(torch.load(a.model, map_location=DEV)); net.eval(); gpu_guard.assert_on_gpu(net)
    M, R = [], []
    for d in a.dirs.split(','):
        for k in range(a.reps):
            r = run(f'{B}/course_page.html?course=1&cdir={d}&wait=1{a.extra}', net, a.ld, a.vT, video=(a.video if (a.video and k == 0 and d == a.dirs.split(",")[0]) else None))
            r.update(policy='MODEL', dir=d, rep=k); M.append(r); print(json.dumps(r, ensure_ascii=False), flush=True)
    for k in range(a.rule_reps):
        d = a.dirs.split(',')[k % len(a.dirs.split(','))]
        r = run(f'{B}/course_page.html?course=1&cdir={d}{a.extra}', None); r.update(policy='RULE', dir=d, rep=k); R.append(r); print(json.dumps(r, ensure_ascii=False), flush=True)
    out = {'model': a.model, 'extra': a.extra, 'MODEL': summ(M), 'RULE': summ(R) if R else None}
    print(json.dumps(out, ensure_ascii=False), flush=True)
    if a.out: json.dump({'summary': out, 'runs': M + R}, open(a.out, 'w'), ensure_ascii=False, indent=1)
