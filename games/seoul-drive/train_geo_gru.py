#!/usr/bin/env python3
"""u_5743 trial2: GRU head over the existing conv trunk, trained on CONTIGUOUS sequences.
Reuses train_geo's loader/filters/SCALE/WCOL so the only change vs cn is the temporal head.
Train/val split is BY RUN (never mid-sequence) so val frames are from runs the net never saw.
Usage: GEO_GRU=1 python3 train_geo_gru.py 'data/dagger_r35*' out.pt [--epochs 8] [--seq 32] [--k 5]"""
import sys, os, glob, json, math, numpy as np, torch
os.environ.setdefault('GEO_GRU', '1')
from net import DriveNet
import gpu_guard
from train_geo import SCALE, WCOL, holdout_mask
DEV = gpu_guard.require_gpu()

def runs_of(dirs, k):
    """contiguous valid index runs per round dir -> list of (dir, idx_array)"""
    out = []
    for d in dirs:
        try:
            L = np.load(f'{d}/L.npy').astype(np.float32); Yf = np.load(f'{d}/Y.npy').astype(np.float32); Q = np.load(f'{d}/Q.npy')
            X = np.load(f'{d}/X.npy', mmap_mode='r')
        except Exception: continue
        if L.shape[1] < 12 or not (len(X) == len(Yf) == len(L) == len(Q)): continue
        ok = (L[:, 11] > 0) & np.isfinite(L[:, :11]).all(1) & (Yf[:, 3] > 1.0) & (np.abs(L[:, 0]) <= 2.5) & (np.abs(L[:, 1]) <= 0.7) & (np.abs(L[:, 3:6]) <= 20).all(1)
        ok &= holdout_mask(Q)
        ev = np.where((np.diff(Q[:, 1]) > 0) | (np.diff(Q[:, 2]) > 0))[0] + 1
        for e in ev: ok &= ~(np.abs(Q[:, 3] - Q[e, 3]) <= 3.0)
        idx = np.where(ok)[0]
        if len(idx) < 16: continue
        for r in np.split(idx, np.where(np.diff(idx) != 1)[0] + 1):
            if len(r) >= 16: out.append((d, r))
    return out

def seq_batch(d, r, s, T, k):
    X = np.load(f'{d}/X.npy', mmap_mode='r'); L = np.load(f'{d}/L.npy').astype(np.float32); Yf = np.load(f'{d}/Y.npy').astype(np.float32)
    ids = r[s:s + T]
    base = np.asarray(X[ids], dtype=np.float32)
    if base.ndim == 4 and base.shape[-1] in (1, 3): base = base.transpose(0, 3, 1, 2)
    if base.max() > 1.5: base = base / 255.0
    sl = [np.clip(np.arange(len(ids)) - (k - 1 - j), 0, None) for j in range(k)]
    xb = np.concatenate([base[q] for q in sl], 1)
    yb = (L[ids, :12] / SCALE).astype(np.float32)
    vb = (Yf[ids, 3] / 30.0).astype(np.float32).reshape(-1, 1)
    return (torch.from_numpy(xb).to(DEV), torch.from_numpy(yb).to(DEV), torch.from_numpy(vb).to(DEV))

def main():
    import argparse; ap = argparse.ArgumentParser()
    ap.add_argument('dirs'); ap.add_argument('out'); ap.add_argument('--epochs', type=int, default=8)
    ap.add_argument('--seq', type=int, default=32); ap.add_argument('--k', type=int, default=5)
    ap.add_argument('--init', default=None); ap.add_argument('--seed', type=int, default=0)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed); torch.manual_seed(a.seed)
    dirs = [d for p in a.dirs.split(',') for d in sorted(glob.glob(p))]
    R = runs_of(dirs, a.k)
    # u_5751: restrict to the 35/35/30 balanced index if present (the road-deficit phase
    # over-collected arterial, which became the LARGEST raw class - training on the raw pool
    # would re-introduce the very skew the mix requirement exists to prevent).
    mixf = os.environ.get('MIX_INDEX', 'data/train_index_mix.json')
    if os.path.exists(mixf):
        mix = json.load(open(mixf))
        allow = set()
        for k, v in mix.items():
            for d, r in v: allow.add((d, int(r)))
        R2 = []
        for d, r in R:
            keep = np.array([i for i in r if (d, int(i)) in allow], dtype=r.dtype)
            if len(keep) >= 16:
                for seg in np.split(keep, np.where(np.diff(keep) != 1)[0] + 1):
                    if len(seg) >= 16: R2.append((d, seg))
        print(json.dumps({'mix_index': mixf, 'runs_before': len(R), 'runs_after': len(R2)}), flush=True)
        R = R2
    if not R: print(json.dumps({'error': 'no runs'})); return
    rng.shuffle(R); cut = max(1, int(len(R) * 0.9)); TR, VA = R[:cut], R[cut:]
    nf = sum(len(r) for _, r in R)
    print(json.dumps({'runs': len(R), 'frames': int(nf), 'train_runs': len(TR), 'val_runs': len(VA), 'seq': a.seq, 'k': a.k}), flush=True)
    net = DriveNet(out=12, vin=True, vdim=1, in_ch=3 * a.k).to(DEV); gpu_guard.assert_on_gpu(net)
    if a.init:
        sd = torch.load(a.init, map_location=DEV); own = net.state_dict()
        okd = {kk: v for kk, v in sd.items() if kk in own and own[kk].shape == v.shape}
        net.load_state_dict(okd, strict=False); print(json.dumps({'init': a.init, 'loaded': len(okd)}), flush=True)
    opt = torch.optim.Adam(net.parameters(), 5e-4 if a.init else 1e-3, weight_decay=1e-4); best = 1e9
    def windows(S):
        w = []
        for d, r in S:
            for s in range(0, len(r) - a.seq + 1, a.seq): w.append((d, r, s))
        return w
    WTR, WVA = windows(TR), windows(VA)
    for ep in range(a.epochs):
        net.train(); net._T = a.seq; tot = 0.0; c = 0
        for j in rng.permutation(len(WTR)):
            d, r, s = WTR[j]
            xb, yb, vb = seq_batch(d, r, s, a.seq, a.k)
            if len(xb) < a.seq: continue
            opt.zero_grad(); o = net(xb, vb, raw=True)
            l = (((o - yb) ** 2) * WCOL).mean()
            l.backward(); torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0); opt.step()
            tot += l.item() * len(xb); c += len(xb)
        net.eval(); vs = 0.0; vc = 0
        with torch.no_grad():
            for d, r, s in WVA:
                xb, yb, vb = seq_batch(d, r, s, a.seq, a.k)
                if len(xb) < a.seq: continue
                o = net(xb, vb, raw=True); vs += (((o - yb) ** 2) * WCOL).mean().item() * len(xb); vc += len(xb)
        vl = vs / max(1, vc)
        if vl < best: best = vl; torch.save(net.state_dict(), a.out)
        print(json.dumps({'ep': ep, 'train': round(tot / max(1, c), 5), 'val': round(vl, 5)}), flush=True)
    print(json.dumps({'done': a.out, 'best_val': round(best, 5)}), flush=True)
if __name__ == '__main__': main()
