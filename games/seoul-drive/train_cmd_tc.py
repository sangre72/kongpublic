#!/usr/bin/env python3
"""u_5754 temporal-consistency loss for the direct-command head.

  L = MSE(y_t, lab_t) + lambda * MSE( (y_t - y_{t-1}), (lab_t - lab_{t-1}) )

i.e. the penalty is on the FIRST DIFFERENCE, matched to the teacher's own first difference -
not a plain smoothness prior. That matters: the teacher is not constant (2.1-2.3 rev/s), so
forcing dy->0 would fight real steering. We ask the model's CHANGE to match the teacher's CHANGE.
Trained on contiguous sequences (train/val split BY RUN, no sequence straddles the split).
"""
import sys, os, glob, json, numpy as np, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from net import DriveNet
import gpu_guard
from train_geo import holdout_mask
DEV = gpu_guard.require_gpu()
MAXSTEER = 0.62
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
        if len(idx) < 16: continue
        for seg in np.split(idx, np.where(np.diff(idx) != 1)[0] + 1):
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
    return (torch.from_numpy(xb).to(DEV),
            torch.from_numpy(Y[ids, 0].astype(np.float32)).unsqueeze(1).to(DEV),
            torch.from_numpy((Y[ids, 3] / 30.0).astype(np.float32)).unsqueeze(1).to(DEV))
def main():
    import argparse; ap = argparse.ArgumentParser()
    ap.add_argument('dirs'); ap.add_argument('out'); ap.add_argument('--lam', type=float, default=1.0)
    ap.add_argument('--epochs', type=int, default=6); ap.add_argument('--seq', type=int, default=32)
    ap.add_argument('--k', type=int, default=5); ap.add_argument('--init', default=None); ap.add_argument('--seed', type=int, default=0)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed); torch.manual_seed(a.seed)
    R = runs(a.dirs)
    if not R: print(json.dumps({'error': 'no runs'})); return
    rng.shuffle(R); cut = max(1, int(len(R) * 0.9)); TR, VA = R[:cut], R[cut:]
    W = lambda S: [(d, r, s) for d, r in S for s in range(0, len(r) - a.seq + 1, a.seq)]
    WTR, WVA = W(TR), W(VA)
    print(json.dumps({'lam': a.lam, 'runs': len(R), 'wtr': len(WTR), 'wva': len(WVA)}), flush=True)
    net = DriveNet(out=1, vin=True, vdim=1, in_ch=3 * a.k).to(DEV); gpu_guard.assert_on_gpu(net)
    if a.init:
        sd = torch.load(a.init, map_location=DEV); own = net.state_dict()
        okd = {kk: v for kk, v in sd.items() if kk in own and own[kk].shape == v.shape}
        net.load_state_dict(okd, strict=False)
    opt = torch.optim.Adam(net.parameters(), 5e-4 if a.init else 1e-3, weight_decay=1e-4); best = 1e9
    for ep in range(a.epochs):
        net.train()
        for j in rng.permutation(len(WTR)):
            d, r, s = WTR[j]
            xb, yb, vb = seq(d, r, s, a.seq, a.k)
            if len(xb) < 2: continue
            opt.zero_grad(); o = net(xb, vb, raw=True)
            l_pt = ((o - yb) ** 2).mean()
            l_dt = (((o[1:] - o[:-1]) - (yb[1:] - yb[:-1])) ** 2).mean()
            (l_pt + a.lam * l_dt).backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0); opt.step()
        net.eval(); mae = 0.0; c = 0; mrev = []; lrev = []
        with torch.no_grad():
            for d, r, s in WVA:
                xb, yb, vb = seq(d, r, s, a.seq, a.k)
                if len(xb) < 2: continue
                o = net(xb, vb, raw=True)
                mae += torch.abs(o - yb).sum().item(); c += len(xb)
                on = o.cpu().numpy().ravel(); ln = yb.cpu().numpy().ravel()
                for arr, acc in ((on, mrev), (ln, lrev)):
                    dd = np.diff(arr); sg = np.sign(dd); sg = sg[sg != 0]
                    acc.append(float(np.sum(sg[1:] != sg[:-1]) / (len(arr) / 30.0)) if len(sg) > 1 else 0.0)
        m = mae / max(1, c)
        res = dict(ep=ep, mae_rad=round(m * MAXSTEER, 5), model_rev=round(float(np.mean(mrev)), 3),
                   rule_rev=round(float(np.mean(lrev)), 3))
        res['ratio'] = round(res['model_rev'] / res['rule_rev'], 3) if res['rule_rev'] else None
        # u_5755: save rule = BEST RATIO subject to MAE <= cap. We were selecting on MAE while
        #   gating on ratio - an optimise/gate mismatch. Cap keeps accuracy admissible.
        cap = float(os.environ.get('MAE_CAP', '0.036'))
        rat = res['ratio'] if res['ratio'] is not None else 1e9
        res['saved'] = False
        if res['mae_rad'] <= cap and rat < best:
            best = rat; torch.save(net.state_dict(), a.out); res['saved'] = True
        print(json.dumps(res), flush=True)
    print(json.dumps({'done': a.out, 'lam': a.lam, 'best_ratio': (None if best>=1e9 else round(best,3))}), flush=True)
if __name__ == '__main__': main()
