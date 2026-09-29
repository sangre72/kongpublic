#!/usr/bin/env python3
"""u_5758 PERCEPTION-ONLY offline gate. Model supplies geometry; the RULE follower consumes it.
Reports:
  (a) per-channel MAE on held-out frames (ey/epsi called out - the follower is most sensitive there)
  (b) sign-reversals/s of the DERIVED command when the rule follower runs on MODEL geometry
      vs on /tel (ground-truth) geometry, over the SAME recorded frames.
(b) is the predictor: it is what the follower will actually chase. Bar: model-derived <= 2x tel-derived.
Derivation mirrors gpu_drive --geo: lp = lc20 + (tgt - round(li))*lw, then Pure-Pursuit at Ld=20.
"""
import sys, os, glob, json, numpy as np, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from train_geo import holdout_mask
import net as N
SC = np.array([2.0,0.5,0.05,16.0,16.0,16.0,8.0,8.0,5.0,15.0,15.0,1.0], np.float32)
NAMES = ['ey','epsi','k0','lc10','lc20','lc40','li','nl','lw','dl','dr']
WB, LD = 2.76, 20.0
MP = sys.argv[1]; PAT = sys.argv[2] if len(sys.argv) > 2 else 'data/dagger_r30*'
GRU = os.environ.get('GRU', '0') == '1'
os.environ['GEO_GRU'] = '1' if GRU else '0'
import importlib; importlib.reload(N)
sd = torch.load(MP, map_location='cpu')
k = sd['f.0.weight'].shape[1] // 3; out = sd['h.6.weight'].shape[0]
vd = sd['hv.0.weight'].shape[1] - 256 if 'hv.0.weight' in sd else 1
m = N.DriveNet(out=out, vin=True, vdim=vd, in_ch=3 * k); m.load_state_dict(sd, strict=False); m.eval()
def pursuit(lp):
    a = np.arctan2(lp, LD); L = np.hypot(LD, lp)
    return np.arctan2(2 * WB * np.sin(a), L)
def rev(x, n, fps=30.0):
    dd = np.diff(x); s = np.sign(dd); s = s[s != 0]
    return float(np.sum(s[1:] != s[:-1]) / (n / fps)) if len(s) > 1 else 0.0
R = []
for d in sorted(glob.glob(PAT)):
    try:
        L = np.load(f'{d}/L.npy').astype(np.float32); Y = np.load(f'{d}/Y.npy').astype(np.float32); Q = np.load(f'{d}/Q.npy')
    except Exception: continue
    if L.shape[1] < 12: continue
    ok = (L[:, 11] > 0) & (Y[:, 3] > 1.0)
    if 'r30' not in d: ok &= ~holdout_mask(Q)
    idx = np.where(ok)[0]
    for r in np.split(idx, np.where(np.diff(idx) != 1)[0] + 1):
        if len(r) >= 24: R.append((d, r))
err = {n: [] for n in NAMES}; mrev = []; trev = []
for d, r in R:
    X = np.load(f'{d}/X.npy', mmap_mode='r'); Y = np.load(f'{d}/Y.npy').astype(np.float32); L = np.load(f'{d}/L.npy').astype(np.float32)
    base = np.asarray(X[r], dtype=np.float32)
    if base.ndim == 4 and base.shape[-1] in (1, 3): base = base.transpose(0, 3, 1, 2)
    if base.max() > 1.5: base = base / 255.0
    sl = [np.clip(np.arange(len(r)) - (k - 1 - j), 0, None) for j in range(k)]
    xb = torch.from_numpy(np.concatenate([base[q] for q in sl], 1))
    vb = torch.from_numpy((Y[r, 3] / 30.0).astype(np.float32).reshape(-1, 1))
    if GRU: m._T = len(r)
    with torch.no_grad(): o = m(xb, vb, raw=True).numpy() * SC[:out]
    tru = L[r, :11]
    for i, n in enumerate(NAMES):
        if i < out: err[n].append(np.abs(o[:, i] - tru[:, i]))
    # derived command: same lane target from the rule layer both sides -> isolate geometry quality
    lw = 3.25
    lp_m = o[:, 4] + (np.round(tru[:, 6]) - np.round(o[:, 6])) * lw
    lp_t = tru[:, 4]
    mrev.append(rev(pursuit(lp_m), len(r))); trev.append(rev(pursuit(lp_t), len(r)))
res = {'heldout_runs': len(R), 'model': os.path.basename(MP)}
for n in NAMES:
    if err[n]: res['mae_' + n] = round(float(np.concatenate(err[n]).mean()), 4)
res['derived_rev_model'] = round(float(np.mean(mrev)), 3)
res['derived_rev_tel'] = round(float(np.mean(trev)), 3)
res['ratio'] = round(res['derived_rev_model'] / res['derived_rev_tel'], 3) if res['derived_rev_tel'] else None
res['bar'] = 2.0
res['PASS'] = bool(res['ratio'] is not None and res['ratio'] <= 2.0)
print(json.dumps(res))
