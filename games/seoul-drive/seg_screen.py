#!/usr/bin/env python3
"""u_5768: does the MASK->geometry decode jitter less than the scalar-regression head?
Same held-out frames, same derived-command metric as percep_gate: run the rule follower's
lp = lc20 + lane shift -> Pure-Pursuit, on (a) seg-decoded geometry, (b) /tel truth."""
import sys, os, glob, json, numpy as np, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from train_geo import holdout_mask
from seg_net import SegNet, NCLS
import seg_geo
MP = sys.argv[1]; PAT = sys.argv[2] if len(sys.argv) > 2 else 'data/dagger_r30*'
WB, LD = 2.76, 20.0
sd = torch.load(MP, map_location='cpu'); m = SegNet(); m.load_state_dict(sd); m.eval()
def pursuit(lp):
    a = np.arctan2(lp, LD); return np.arctan2(2 * WB * np.sin(a), np.hypot(LD, lp))
def rev(x, n, fps=30.0):
    dd = np.diff(x); s = np.sign(dd); s = s[s != 0]
    return float(np.sum(s[1:] != s[:-1]) / (n / fps)) if len(s) > 1 else 0.0
R = []
for d in sorted(glob.glob(PAT)):
    try:
        L = np.load(f'{d}/L.npy').astype(np.float32); Y = np.load(f'{d}/Y.npy').astype(np.float32); Q = np.load(f'{d}/Q.npy')
        X = np.load(f'{d}/X.npy', mmap_mode='r')
    except Exception: continue
    if L.shape[1] < 12: continue
    ok = (L[:, 11] > 0) & (Y[:, 3] > 1.0)
    if 'r30' not in d: ok &= ~holdout_mask(Q)
    idx = np.where(ok)[0]
    for r in np.split(idx, np.where(np.diff(idx) != 1)[0] + 1):
        if len(r) >= 24: R.append((d, r[:400]))
    if len(R) >= 18: break
mrev = []; trev = []; eyerr = []; eperr = []
for d, r in R:
    X = np.load(f'{d}/X.npy', mmap_mode='r'); L = np.load(f'{d}/L.npy').astype(np.float32)
    base = np.asarray(X[r], dtype=np.float32)
    if base.ndim == 4 and base.shape[-1] in (1, 3): base = base.transpose(0, 3, 1, 2)
    if base.max() > 1.5: base = base / 255.0
    with torch.no_grad():
        lo = m(torch.from_numpy(base)).numpy()
    mk = lo.argmax(1).astype(np.uint8)
    lp_m = []; ey_m = []; ep_m = []
    for t in range(len(r)):
        tgt = int(round(float(L[r[t], 6]))) + 1
        try: g = seg_geo.lane_geo(mk[t], tgt)
        except Exception: g = None
        if g is None or not np.isfinite(g.get('ey', float('nan'))):
            lp_m.append(lp_m[-1] if lp_m else 0.0); ey_m.append(np.nan); ep_m.append(np.nan); continue
        ey_m.append(g['ey']); ep_m.append(g['ep'])
        _lc = g.get('lc20'); lp_m.append(_lc if (_lc is not None and np.isfinite(_lc)) else g['ey'])
    lp_m = np.array(lp_m, float)
    mrev.append(rev(pursuit(lp_m), len(r))); trev.append(rev(pursuit(L[r, 4]), len(r)))
    e = np.array(ey_m, float); p = np.array(ep_m, float)
    if np.isfinite(e).any(): eyerr.append(np.nanmean(np.abs(e - L[r, 0])))
    if np.isfinite(p).any(): eperr.append(np.nanmean(np.abs(p - L[r, 1])))
res = dict(runs=len(R), seg_rev=round(float(np.mean(mrev)), 3), tel_rev=round(float(np.mean(trev)), 3),
           mae_ey=round(float(np.mean(eyerr)), 4) if eyerr else None,
           mae_epsi=round(float(np.mean(eperr)), 4) if eperr else None)
res['ratio'] = round(res['seg_rev'] / res['tel_rev'], 3) if res['tel_rev'] else None
print(json.dumps(res))
