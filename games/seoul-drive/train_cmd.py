#!/usr/bin/env python3
"""u_5753 direct-command parameterisation: screen -> applied steer (normalised, = delta/0.62).
Label = Y[:,0], verified r=1.0 against the follower's own same-tick delta (probe n=2667).
Same conv trunk + speed input as cn; single output. Uses the 35/35/30 balanced index."""
import sys, os, glob, json, numpy as np, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from net import DriveNet
import gpu_guard
from train_geo import holdout_mask
DEV = gpu_guard.require_gpu(); BS = 64
def load(pat, k):
    mixf = os.environ.get('MIX_INDEX', 'data/train_index_mix.json')
    allow = None
    if os.path.exists(mixf):
        allow = set()
        for kk, v in json.load(open(mixf)).items():
            for d, r in v: allow.add((d, int(r)))
    P = []
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
        if len(idx) < 8: continue
        P.append((d, idx))
    return P
def batch(P, picks, k):
    xs, ys, vs = [], [], []
    for d, i in picks:
        X = np.load(f'{d}/X.npy', mmap_mode='r'); Y = np.load(f'{d}/Y.npy').astype(np.float32)
        sl = [max(0, i - (k - 1 - j)) for j in range(k)]
        f = np.asarray(X[sl], dtype=np.float32)
        if f.ndim == 4 and f.shape[-1] in (1, 3): f = f.transpose(0, 3, 1, 2)
        if f.max() > 1.5: f = f / 255.0
        xs.append(np.concatenate(list(f), 0)); ys.append(Y[i, 0]); vs.append(Y[i, 3] / 30.0)
    return (torch.from_numpy(np.stack(xs)).to(DEV),
            torch.from_numpy(np.array(ys, np.float32)).unsqueeze(1).to(DEV),
            torch.from_numpy(np.array(vs, np.float32)).unsqueeze(1).to(DEV))
def main():
    import argparse; ap = argparse.ArgumentParser()
    ap.add_argument('dirs'); ap.add_argument('out'); ap.add_argument('--epochs', type=int, default=8)
    ap.add_argument('--k', type=int, default=5); ap.add_argument('--init', default=None); ap.add_argument('--seed', type=int, default=0)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed); torch.manual_seed(a.seed)
    P = load(a.dirs, a.k)
    if not P: print(json.dumps({'error': 'no frames'})); return
    flat = [(d, int(i)) for d, idx in P for i in idx]
    rng.shuffle(flat); cut = int(len(flat) * 0.9); TR, VA = flat[:cut], flat[cut:]
    print(json.dumps({'frames': len(flat), 'train': len(TR), 'val': len(VA), 'k': a.k}), flush=True)
    net = DriveNet(out=1, vin=True, vdim=1, in_ch=3 * a.k).to(DEV); gpu_guard.assert_on_gpu(net)
    if a.init:
        sd = torch.load(a.init, map_location=DEV); own = net.state_dict()
        okd = {kk: v for kk, v in sd.items() if kk in own and own[kk].shape == v.shape}
        net.load_state_dict(okd, strict=False); print(json.dumps({'init': a.init, 'loaded': len(okd)}), flush=True)
    opt = torch.optim.Adam(net.parameters(), 5e-4 if a.init else 1e-3, weight_decay=1e-4); best = 1e9
    for ep in range(a.epochs):
        net.train(); tot = 0.0; n = 0
        perm = rng.permutation(len(TR))
        for i in range(0, len(perm), BS):
            picks = [TR[j] for j in perm[i:i + BS]]
            xb, yb, vb = batch(P, picks, a.k)
            opt.zero_grad(); o = net(xb, vb, raw=True); l = ((o - yb) ** 2).mean()
            l.backward(); opt.step(); tot += l.item() * len(picks); n += len(picks)
        net.eval(); vs = 0.0; c = 0; mae = 0.0
        with torch.no_grad():
            for i in range(0, len(VA), BS):
                picks = VA[i:i + BS]
                xb, yb, vb = batch(P, picks, a.k); o = net(xb, vb, raw=True)
                vs += ((o - yb) ** 2).mean().item() * len(picks); mae += torch.abs(o - yb).sum().item(); c += len(picks)
        vl = vs / max(1, c)
        if vl < best: best = vl; torch.save(net.state_dict(), a.out)
        print(json.dumps({'ep': ep, 'train': round(tot / max(1, n), 6), 'val': round(vl, 6),
                          'mae_norm': round(mae / max(1, c), 5), 'mae_rad': round(0.62 * mae / max(1, c), 5)}), flush=True)
    print(json.dumps({'done': a.out, 'best_val': round(best, 6)}), flush=True)
if __name__ == '__main__': main()
