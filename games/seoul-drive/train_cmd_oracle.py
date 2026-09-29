#!/usr/bin/env python3
"""u_5756 ORACLE ABLATION (diagnostic, NOT deployable - uses privileged map geometry).
Same direct-command net, but the teacher's own geometry from L.npy is fed in as extra scalar
inputs alongside pixels, via the existing vdim path (v + geometry channels).
Question: does the model reach <=2x teacher when it is GIVEN what the teacher sees?
  pass -> the deficit is information the pixels do not carry (then ablate channels one at a time)
  fail -> the deficit is not information either; a per-frame feedforward net cannot reproduce a
          stateful controller regardless of inputs.
CH (default all): ey epsi k0 lc10 lc20 lc40 li nl   (--ch to subset, e.g. --ch ey,epsi,k0)
"""
import sys, os, glob, json, numpy as np, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from net import DriveNet
import gpu_guard
from train_geo import holdout_mask
DEV = gpu_guard.require_gpu(); MAXSTEER = 0.62
NAMES = ['ey','epsi','k0','lc10','lc20','lc40','li','nl']
COL   = {'ey':0,'epsi':1,'k0':2,'lc10':3,'lc20':4,'lc40':5,'li':6,'nl':7}
SCL   = {'ey':2.0,'epsi':0.5,'k0':0.05,'lc10':16.0,'lc20':16.0,'lc40':16.0,'li':8.0,'nl':8.0}
def runs(pat, chans, mixf='data/train_index_mix.json'):
    allow = None
    if os.path.exists(mixf):
        allow = set()
        for kk, v in json.load(open(mixf)).items():
            for d, r in v: allow.add((d, int(r)))
    R = []
    for d in sorted(glob.glob(pat)):
        try:
            Y = np.load(f'{d}/Y.npy').astype(np.float32); L = np.load(f'{d}/L.npy').astype(np.float32)
            Q = np.load(f'{d}/Q.npy'); X = np.load(f'{d}/X.npy', mmap_mode='r')
        except Exception: continue
        if L.shape[1] < 12 or not (len(X) == len(Y) == len(L) == len(Q)): continue
        ok = (L[:, 11] > 0) & np.isfinite(Y[:, 0]) & (Y[:, 3] > 1.0) & holdout_mask(Q)
        idx = np.where(ok)[0]
        if allow is not None:
            idx = np.array([i for i in idx if (d, int(i)) in allow], dtype=idx.dtype)
        for seg in np.split(idx, np.where(np.diff(idx) != 1)[0] + 1) if len(idx) else []:
            if len(seg) >= 16: R.append((d, seg))
    return R
def seq(d, r, s, T, k, chans):
    X = np.load(f'{d}/X.npy', mmap_mode='r'); Y = np.load(f'{d}/Y.npy').astype(np.float32); L = np.load(f'{d}/L.npy').astype(np.float32)
    ids = r[s:s + T]
    base = np.asarray(X[ids], dtype=np.float32)
    if base.ndim == 4 and base.shape[-1] in (1, 3): base = base.transpose(0, 3, 1, 2)
    if base.max() > 1.5: base = base / 255.0
    sl = [np.clip(np.arange(len(ids)) - (k - 1 - j), 0, None) for j in range(k)]
    xb = np.concatenate([base[q] for q in sl], 1)
    vv = [(Y[ids, 3] / 30.0).astype(np.float32)]
    for c in chans: vv.append((L[ids, COL[c]] / SCL[c]).astype(np.float32))
    return (torch.from_numpy(xb).to(DEV),
            torch.from_numpy(Y[ids, 0].astype(np.float32)).unsqueeze(1).to(DEV),
            torch.from_numpy(np.stack(vv, 1)).to(DEV))
def main():
    import argparse; ap = argparse.ArgumentParser()
    ap.add_argument('dirs'); ap.add_argument('out'); ap.add_argument('--ch', default=','.join(NAMES))
    ap.add_argument('--lam', type=float, default=300.0); ap.add_argument('--epochs', type=int, default=8)
    ap.add_argument('--seq', type=int, default=32); ap.add_argument('--k', type=int, default=5); ap.add_argument('--seed', type=int, default=0)
    a = ap.parse_args()
    chans = [c for c in a.ch.split(',') if c in COL]
    rng = np.random.default_rng(a.seed); torch.manual_seed(a.seed)
    R = runs(a.dirs, chans)
    if not R: print(json.dumps({'error': 'no runs'})); return
    rng.shuffle(R); cut = max(1, int(len(R) * 0.9)); TR, VA = R[:cut], R[cut:]
    W = lambda S: [(d, r, s) for d, r in S for s in range(0, len(r) - a.seq + 1, a.seq)]
    WTR, WVA = W(TR), W(VA)
    vdim = 1 + len(chans)
    print(json.dumps({'oracle_ch': chans, 'vdim': vdim, 'runs': len(R), 'wtr': len(WTR), 'lam': a.lam}), flush=True)
    net = DriveNet(out=1, vin=True, vdim=vdim, in_ch=3 * a.k).to(DEV); gpu_guard.assert_on_gpu(net)
    opt = torch.optim.Adam(net.parameters(), 1e-3, weight_decay=1e-4); best = 1e9
    cap = float(os.environ.get('MAE_CAP', '0.036'))
    for ep in range(a.epochs):
        net.train()
        for j in rng.permutation(len(WTR)):
            d, r, s = WTR[j]
            xb, yb, vb = seq(d, r, s, a.seq, a.k, chans)
            if len(xb) < 2: continue
            opt.zero_grad(); o = net(xb, vb, raw=True)
            l = ((o - yb) ** 2).mean() + a.lam * (((o[1:] - o[:-1]) - (yb[1:] - yb[:-1])) ** 2).mean()
            l.backward(); torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0); opt.step()
        net.eval(); mae = 0.0; c = 0; mrev = []; lrev = []
        with torch.no_grad():
            for d, r, s in WVA:
                xb, yb, vb = seq(d, r, s, a.seq, a.k, chans)
                if len(xb) < 2: continue
                o = net(xb, vb, raw=True)
                mae += torch.abs(o - yb).sum().item(); c += len(xb)
                for arr, acc in ((o.cpu().numpy().ravel(), mrev), (yb.cpu().numpy().ravel(), lrev)):
                    dd = np.diff(arr); sg = np.sign(dd); sg = sg[sg != 0]
                    acc.append(float(np.sum(sg[1:] != sg[:-1]) / (len(arr) / 30.0)) if len(sg) > 1 else 0.0)
        m = mae / max(1, c) * MAXSTEER
        res = dict(ep=ep, mae_rad=round(m, 5), model_rev=round(float(np.mean(mrev)), 3),
                   rule_rev=round(float(np.mean(lrev)), 3))
        res['ratio'] = round(res['model_rev'] / res['rule_rev'], 3) if res['rule_rev'] else None
        res['saved'] = False
        if res['mae_rad'] <= cap and res['ratio'] is not None and res['ratio'] < best:
            best = res['ratio']; torch.save(net.state_dict(), a.out); res['saved'] = True
        print(json.dumps(res), flush=True)
    print(json.dumps({'done': a.out, 'ch': chans, 'best_ratio': (None if best >= 1e9 else round(best, 3))}), flush=True)
if __name__ == '__main__': main()
