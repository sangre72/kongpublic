#!/usr/bin/env python3
"""u_5779: on-policy perception correction, ey channel ONLY.
- loss = |ey_pred - ey_true| on MODEL-DRIVEN states (pixels in, /tel map truth as the signal).
- eval = ey MAE on HELD-OUT EPISODES (whole directories withheld, never frames: a frame-level split
  leaks, since consecutive frames of one episode are near-duplicates).
- the reported curve is the held-out MODEL-DRIVEN ey MAE, which is the quantity we are moving -
  not the training loss (u_5779 condition 2).
Reward/loss on ey alone per u_5776: epsi 0.999x and lc/li/nl at label-spread scale carry no signal,
so including them adds gradient variance and no information."""
import os, sys, json, glob, math, argparse
import numpy as np, torch
import gpu_guard
from net import DriveNet
import train_geo as TG

DEV = gpu_guard.require_gpu()
BS = TG.BS

def ey_mae(net, dirs, bs=64):
    """ey MAE in metres over whole episode dirs."""
    tot = 0.0; cnt = 0; per = []
    for d in dirs:
        pl = TG.load([d])
        if not pl: continue
        X, Y, V, W = pl
        if len(Y) < 50: continue
        t = 0.0; c = 0
        for i in range(0, len(Y), bs):
            ids = np.arange(i, min(i + bs, len(Y)))
            xb, yb, vb, _ = TG.batch(X, Y, V, W, ids)
            with torch.no_grad(): o = net(xb, vb, raw=True)
            t += float(torch.abs(o[:, 0] - yb[:, 0]).sum()) * float(TG.SCALE[0]); c += len(ids)
        if c: per.append(t / c); tot += t; cnt += c
    if not cnt: return None, []
    return tot / cnt, per

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('train_glob'); ap.add_argument('out')
    ap.add_argument('--holdout', required=True, help='file listing held-out episode dirs')
    ap.add_argument('--epochs', type=int, default=10)
    ap.add_argument('--init', default=None)
    ap.add_argument('--k', type=int, default=5)
    ap.add_argument('--eval-every', type=int, default=1)
    ap.add_argument('--seed', type=int, default=0)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed); torch.manual_seed(a.seed)
    TG.KSTACK = a.k

    ho = [l.strip() for l in open(a.holdout) if l.strip()]
    tr_dirs = [d for d in sorted(glob.glob(a.train_glob)) if d not in set(ho)]
    print(json.dumps({'train_eps': len(tr_dirs), 'holdout_eps': len(ho)}), flush=True)

    got = TG.load(tr_dirs)
    if not got: print(json.dumps({'error': 'no frames'})); return
    X, Y, V, W = got; n = len(X)

    net = DriveNet(out=12, vin=True, vdim=1, in_ch=3 * a.k).to(DEV); gpu_guard.assert_on_gpu(net)
    if a.init:
        sd = torch.load(a.init, map_location=DEV); own = net.state_dict()
        ok = {k: v for k, v in sd.items() if k in own and own[k].shape == v.shape}
        # u_5776 STANDING CHECK: a partial load is silent and yields bogus numbers.
        if len(ok) != len(own):
            raise SystemExit(json.dumps({'FATAL': 'checkpoint/arch mismatch', 'loaded': len(ok),
                                         'expected': len(own), 'hint': 'wrong family or wrong --k'}))
        net.load_state_dict(ok, strict=False)
        print(json.dumps({'init': a.init, 'loaded': len(ok), 'of': len(own)}), flush=True)

    base, base_per = ey_mae(net, ho)
    print(json.dumps({'update': 0, 'holdout_ey_mae': round(base, 4),
                      'n_eps': len(base_per), 'note': 'pre-training baseline'}), flush=True)

    opt = torch.optim.Adam(net.parameters(), 5e-4 if a.init else 1e-3, weight_decay=1e-4)
    best = base; curve = [round(base, 4)]
    for ep in range(a.epochs):
        net.train(); perm = rng.permutation(n); tot = 0.0
        for i in range(0, len(perm), BS):
            ids = np.sort(perm[i:i + BS])
            xb, yb, vb, wb = TG.batch(X, Y, V, W, ids, train=True)
            opt.zero_grad()
            o = net(xb, vb, raw=True)
            l = (torch.abs(o[:, 0] - yb[:, 0]) * wb).mean()   # ey ONLY
            l.backward(); opt.step(); tot += l.item() * len(ids)
        if (ep + 1) % a.eval_every == 0:
            net.eval(); m, per = ey_mae(net, ho)
            curve.append(round(m, 4))
            sd = float(np.std(per, ddof=1)) if len(per) > 1 else 0.0
            print(json.dumps({'update': ep + 1, 'train_ey_loss': round(tot / len(perm), 5),
                              'holdout_ey_mae': round(m, 4), 'sd': round(sd, 4),
                              'n_eps': len(per), 'best': round(min(best, m), 4)}), flush=True)
            if m < best: best = m; torch.save(net.state_dict(), a.out)
    print(json.dumps({'done': a.out, 'baseline': round(base, 4), 'best_holdout_ey_mae': round(best, 4),
                      'curve': curve, 'target': 0.20, 'rule_driven_ref': 0.1148}), flush=True)

if __name__ == '__main__': main()
