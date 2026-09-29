#!/usr/bin/env python3
"""u_5757 AUTOREGRESSIVE direct-command net: y_{t-1} is fed in as an input channel.
Tests the stateful-controller explanation directly. The GRU failed because its OUTPUT was never
tied to its own previous OUTPUT (context smoothing, not state). Here it is.

Training: teacher forcing (feed lab_{t-1}) with SCHEDULED SAMPLING - probability p of feeding the
model's own previous prediction instead, ramped 0 -> SS_MAX over training so the net sees its own
error distribution (otherwise it is only ever conditioned on perfect history and drifts at test).
Eval/gate: fully autoregressive (always its own previous output), which is deployment behaviour.
Loss: same per-frame MSE + lambda * first-difference-matched term.
"""
import sys, os, glob, json, numpy as np, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from net import DriveNet
import gpu_guard
from train_geo import holdout_mask
DEV = gpu_guard.require_gpu(); MAXSTEER = 0.62
def runs(pat, mixf='data/train_index_mix.json'):
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
        for seg in (np.split(idx, np.where(np.diff(idx) != 1)[0] + 1) if len(idx) else []):
            if len(seg) >= 16: R.append((d, seg))
    return R
def seq(d, r, s, T, k):
    X = np.load(f'{d}/X.npy', mmap_mode='r'); Y = np.load(f'{d}/Y.npy').astype(np.float32)
    ids = r[s:s + T]
    base = np.asarray(X[ids], dtype=np.float32)
    if base.ndim == 4 and base.shape[-1] in (1, 3): base = base.transpose(0, 3, 1, 2)
    if base.max() > 1.5: base = base / 255.0
    sl = [np.clip(np.arange(len(ids)) - (k - 1 - j), 0, None) for j in range(k)]
    xb = np.concatenate([base[q] for q in sl], 1)
    lab = Y[ids, 0].astype(np.float32)
    prev = np.concatenate([[lab[0]], lab[:-1]])          # lab_{t-1}, first frame repeats
    return (torch.from_numpy(xb).to(DEV),
            torch.from_numpy(lab).unsqueeze(1).to(DEV),
            torch.from_numpy((Y[ids, 3] / 30.0).astype(np.float32)).to(DEV),
            torch.from_numpy(prev).to(DEV))
def main():
    import argparse; ap = argparse.ArgumentParser()
    ap.add_argument('dirs'); ap.add_argument('out'); ap.add_argument('--lam', type=float, default=300.0)
    ap.add_argument('--epochs', type=int, default=8); ap.add_argument('--seq', type=int, default=32)
    ap.add_argument('--k', type=int, default=5); ap.add_argument('--ss', type=float, default=0.5); ap.add_argument('--seed', type=int, default=0)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed); torch.manual_seed(a.seed)
    R = runs(a.dirs)
    if not R: print(json.dumps({'error': 'no runs'})); return
    rng.shuffle(R); cut = max(1, int(len(R) * 0.9)); TR, VA = R[:cut], R[cut:]
    W = lambda S: [(d, r, s) for d, r in S for s in range(0, len(r) - a.seq + 1, a.seq)]
    WTR, WVA = W(TR), W(VA)
    print(json.dumps({'mode': 'autoregressive', 'vdim': 2, 'runs': len(R), 'wtr': len(WTR), 'lam': a.lam, 'ss_max': a.ss}), flush=True)
    net = DriveNet(out=1, vin=True, vdim=2, in_ch=3 * a.k).to(DEV); gpu_guard.assert_on_gpu(net)
    opt = torch.optim.Adam(net.parameters(), 1e-3, weight_decay=1e-4); best = 1e9
    cap = float(os.environ.get('MAE_CAP', '0.036'))
    for ep in range(a.epochs):
        p_ss = a.ss * ep / max(1, a.epochs - 1)          # 0 -> ss_max
        net.train()
        for j in rng.permutation(len(WTR)):
            d, r, s = WTR[j]
            xb, yb, vb, prev = seq(d, r, s, a.seq, a.k)
            if len(xb) < 2: continue
            opt.zero_grad()
            # scheduled sampling: run the sequence, substituting own prediction with prob p_ss
            outs = []; cur = prev[0:1]
            for t in range(len(xb)):
                vin = torch.stack([vb[t:t+1], cur], 1)
                o = net(xb[t:t+1], vin, raw=True)
                outs.append(o)
                nxt = prev[t+1:t+2] if t + 1 < len(xb) else None
                if nxt is not None:
                    cur = o.detach().reshape(1) if (rng.random() < p_ss) else nxt
            o = torch.cat(outs, 0)
            l = ((o - yb) ** 2).mean() + a.lam * (((o[1:] - o[:-1]) - (yb[1:] - yb[:-1])) ** 2).mean()
            l.backward(); torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0); opt.step()
        # eval: FULLY autoregressive
        net.eval(); mae = 0.0; c = 0; mrev = []; lrev = []
        with torch.no_grad():
            for d, r, s in WVA:
                xb, yb, vb, prev = seq(d, r, s, a.seq, a.k)
                if len(xb) < 2: continue
                outs = []; cur = prev[0:1]
                for t in range(len(xb)):
                    o = net(xb[t:t+1], torch.stack([vb[t:t+1], cur], 1), raw=True)
                    outs.append(o); cur = o.reshape(1)
                o = torch.cat(outs, 0)
                mae += torch.abs(o - yb).sum().item(); c += len(xb)
                for arr, acc in ((o.cpu().numpy().ravel(), mrev), (yb.cpu().numpy().ravel(), lrev)):
                    dd = np.diff(arr); sg = np.sign(dd); sg = sg[sg != 0]
                    acc.append(float(np.sum(sg[1:] != sg[:-1]) / (len(arr) / 30.0)) if len(sg) > 1 else 0.0)
        m = mae / max(1, c) * MAXSTEER
        res = dict(ep=ep, p_ss=round(p_ss, 2), mae_rad=round(m, 5),
                   model_rev=round(float(np.mean(mrev)), 3), rule_rev=round(float(np.mean(lrev)), 3))
        res['ratio'] = round(res['model_rev'] / res['rule_rev'], 3) if res['rule_rev'] else None
        res['saved'] = False
        if res['mae_rad'] <= cap and res['ratio'] is not None and res['ratio'] < best:
            best = res['ratio']; torch.save(net.state_dict(), a.out); res['saved'] = True
        print(json.dumps(res), flush=True)
    print(json.dumps({'done': a.out, 'best_ratio': (None if best >= 1e9 else round(best, 3))}), flush=True)
if __name__ == '__main__': main()
