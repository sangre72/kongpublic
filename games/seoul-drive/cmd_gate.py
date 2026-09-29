#!/usr/bin/env python3
"""u_5753 OFFLINE GATE for the direct-command model.
Compares, on the SAME held-out consecutive frames:
  - reversals/s of the MODEL's own steer output
  - reversals/s of the RULE's applied steer (the label) = the reference the model imitates
  - cn's command reversals/s (the bar: model must be <= 0.5x of this)
plus MAE in radians. No driving."""
import sys, os, glob, json, numpy as np, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from train_geo import holdout_mask
SC = np.array([2.0,0.5,0.05,16.0,16.0,16.0,8.0,8.0,5.0,15.0,15.0,1.0], np.float32)
MAXSTEER = 0.62
CMD = sys.argv[1]; CN = sys.argv[2] if len(sys.argv) > 2 else 'models/ode_lp30cn.pt'
PAT = sys.argv[3] if len(sys.argv) > 3 else 'data/dagger_r30*'
import net as N
ORACLE_CH = [c for c in (os.environ.get('ORACLE_CH','').split(',')) if c]
_COL={'ey':0,'epsi':1,'k0':2,'lc10':3,'lc20':4,'lc40':5,'li':6,'nl':7}
_SCL={'ey':2.0,'epsi':0.5,'k0':0.05,'lc10':16.0,'lc20':16.0,'lc40':16.0,'li':8.0,'nl':8.0}
def load(path, out, gru=False):
    os.environ['GEO_GRU'] = '1' if gru else '0'
    import importlib; importlib.reload(N)
    sd = torch.load(path, map_location='cpu')
    k = sd['f.0.weight'].shape[1] // 3
    o = sd['h.6.weight'].shape[0] if 'h.6.weight' in sd else out
    vd = sd['hv.0.weight'].shape[1] - 256 if 'hv.0.weight' in sd else 1   # u_5756: infer vdim from the checkpoint
    m = N.DriveNet(out=o, vin=True, vdim=vd, in_ch=3 * k); m.load_state_dict(sd, strict=False); m.eval()
    return m, k
def runs(pat):
    R = []
    for d in sorted(glob.glob(pat)):
        try:
            L = np.load(f'{d}/L.npy').astype(np.float32); Y = np.load(f'{d}/Y.npy').astype(np.float32); Q = np.load(f'{d}/Q.npy')
        except Exception: continue
        if L.shape[1] < 12: continue
        ok = (L[:, 11] > 0) & np.isfinite(Y[:, 0]) & (Y[:, 3] > 1.0)
        if 'r30' not in d: ok &= ~holdout_mask(Q)
        idx = np.where(ok)[0]
        for r in np.split(idx, np.where(np.diff(idx) != 1)[0] + 1):
            if len(r) >= 24: R.append((d, r))
    return R
def rev(a, n, fps=30.0):
    dd = np.diff(a); s = np.sign(dd); s = s[s != 0]
    return float(np.sum(s[1:] != s[:-1]) / (n / fps)) if len(s) > 1 else 0.0
R = runs(PAT)
cmd, kc = load(CMD, 1)
cn, kn = load(CN, 12)
mrev = []; lrev = []; crev = []; maes = []
for d, r in R:
    X = np.load(f'{d}/X.npy', mmap_mode='r'); Y = np.load(f'{d}/Y.npy').astype(np.float32)
    base = np.asarray(X[r], dtype=np.float32)
    if base.ndim == 4 and base.shape[-1] in (1, 3): base = base.transpose(0, 3, 1, 2)
    if base.max() > 1.5: base = base / 255.0
    L = np.load(f'{d}/L.npy').astype(np.float32)
    _vv=[(Y[r,3]/30.0).astype(np.float32)]
    for _c in ORACLE_CH: _vv.append((L[r,_COL[_c]]/_SCL[_c]).astype(np.float32))
    vb = torch.from_numpy(np.stack(_vv,1))
    vb_cn = torch.from_numpy((Y[r, 3] / 30.0).astype(np.float32).reshape(-1, 1))
    def stack(k):
        sl = [np.clip(np.arange(len(r)) - (k - 1 - j), 0, None) for j in range(k)]
        return torch.from_numpy(np.concatenate([base[q] for q in sl], 1))
    with torch.no_grad():
        mo = cmd(stack(kc), vb, raw=True).numpy().ravel()
        co = cn(stack(kn), vb_cn, raw=True).numpy()
    lab = Y[r, 0]
    mrev.append(rev(mo, len(r))); lrev.append(rev(lab, len(r)))
    crev.append(rev(co[:, 4] * SC[4], len(r)))          # cn's 20m command
    maes.append(float(np.abs(mo - lab).mean()) * MAXSTEER)
res = dict(heldout_runs=len(R),
           model_rev_per_s=round(float(np.mean(mrev)), 3),
           rule_rev_per_s=round(float(np.mean(lrev)), 3),
           cn_rev_per_s=round(float(np.mean(crev)), 3),
           mae_rad=round(float(np.mean(maes)), 5))
res['ratio_vs_cn'] = round(res['model_rev_per_s'] / res['cn_rev_per_s'], 3) if res['cn_rev_per_s'] else None
res['ratio_vs_rule'] = round(res['model_rev_per_s'] / res['rule_rev_per_s'], 3) if res['rule_rev_per_s'] else None
res['bar'] = 0.5
res['PASS'] = bool(res['ratio_vs_cn'] is not None and res['ratio_vs_cn'] <= 0.5)
print(json.dumps(res))
