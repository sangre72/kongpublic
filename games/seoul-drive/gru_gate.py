#!/usr/bin/env python3
"""u_5743 trial2 OFFLINE GATE: sign-reversals/s of the 20m command on held-out CONSECUTIVE frames.
PASS = gru_rev_per_s <= 0.5 * cn_rev_per_s. Same runs, same stack k, same decode for both models.
Usage: python3 gru_gate.py <gru.pt> [cn.pt] [glob]"""
import sys, os, glob, json, numpy as np, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
SCALE = np.array([2.0,0.5,0.05,16.0,16.0,16.0,8.0,8.0,5.0,15.0,15.0,1.0], np.float32)
GRU = sys.argv[1]; CN = sys.argv[2] if len(sys.argv) > 2 else 'models/ode_lp30cn.pt'
PAT = sys.argv[3] if len(sys.argv) > 3 else 'data/dagger_r35*'
from train_geo import holdout_mask
import net as N

def load_net(path, gru):
    os.environ['GEO_GRU'] = '1' if gru else '0'
    import importlib; importlib.reload(N)
    sd = torch.load(path, map_location='cpu')
    out = sd['h.6.weight'].shape[0] if 'h.6.weight' in sd else 12
    k = sd['f.0.weight'].shape[1] // 3
    m = N.DriveNet(out=out, vin=True, vdim=1, in_ch=3 * k)
    m.load_state_dict(sd, strict=False); m.eval()
    return m, k, out

def runs(pat):
    R = []
    for d in sorted(glob.glob(pat)):
        try:
            L = np.load(f'{d}/L.npy').astype(np.float32); Yf = np.load(f'{d}/Y.npy').astype(np.float32); Q = np.load(f'{d}/Q.npy')
        except Exception: continue
        if L.shape[1] < 12: continue
        ok = (L[:, 11] > 0) & (Yf[:, 3] > 1.0) & (np.abs(L[:, 0]) <= 2.5) & (np.abs(L[:, 1]) <= 0.7) & (np.abs(L[:, 3:6]) <= 20).all(1)
        # HELD-OUT: use only frames the trainer excluded (holdout chunks)
        # u_5743: r35xx was COLLECTED with holdout chunks excluded, so ~no frames live there
        #   (18 runs / 361 frames, longest 49). For r30xx (never in r35xx training) use all valid frames;
        #   for r35xx keep the holdout-chunk restriction.
        if 'r30' not in d: ok &= ~holdout_mask(Q)
        idx = np.where(ok)[0]
        for r in np.split(idx, np.where(np.diff(idx) != 1)[0] + 1):
            if len(r) >= 24: R.append((d, r))
    return R

def rev_per_s(m, k, out, R, seq=None):
    revs = []
    for d, r in R:
        X = np.load(f'{d}/X.npy', mmap_mode='r'); Yf = np.load(f'{d}/Y.npy').astype(np.float32)
        base = np.asarray(X[r], dtype=np.float32)
        if base.ndim == 4 and base.shape[-1] in (1, 3): base = base.transpose(0, 3, 1, 2)
        if base.max() > 1.5: base = base / 255.0
        sl = [np.clip(np.arange(len(r)) - (k - 1 - j), 0, None) for j in range(k)]
        xb = torch.from_numpy(np.concatenate([base[q] for q in sl], 1))
        vb = torch.from_numpy((Yf[r, 3] / 30.0).astype(np.float32).reshape(-1, 1))
        if seq: m._T = len(r)
        with torch.no_grad(): o = m(xb, vb, raw=True).numpy()
        o = o * SCALE[:o.shape[1]]
        lc20 = o[:, 4]
        dd = np.diff(lc20); s = np.sign(dd); s = s[s != 0]
        if len(s) > 1: revs.append(float(np.sum(s[1:] != s[:-1]) / (len(r) / 30.0)))
    return float(np.mean(revs)) if revs else float('nan'), len(R)

R = runs(PAT)
cn, kc, oc = load_net(CN, False)
cn_rev, n = rev_per_s(cn, kc, oc, R)
gr, kg, og = load_net(GRU, True)
gr_rev, _ = rev_per_s(gr, kg, og, R, seq=True)
res = dict(heldout_runs=n, cn_rev_per_s=round(cn_rev, 3), gru_rev_per_s=round(gr_rev, 3),
           ratio=round(gr_rev / cn_rev, 3) if cn_rev else None, bar=0.5)
res['PASS'] = bool(res['ratio'] is not None and res['ratio'] <= 0.5)
print(json.dumps(res))
