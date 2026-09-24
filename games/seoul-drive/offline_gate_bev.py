#!/usr/bin/env python3
"""C 오프라인 관문: BevNet 을 홀드아웃 연속 프레임에 돌려 bev_to_geo 로 (ey, lc20) 추출 → 부호반전/s, |Δ| p90, e_y MAE(vs L). usage: offline_gate_bev.py <bev.pt> '<dirs>'"""
import sys, glob, json, numpy as np, torch
import gpu_guard; from train_bev import BevNet; from bev_ctl import bev_to_geo
DEV = gpu_guard.require_gpu(); net = BevNet().to(DEV); net.load_state_dict(torch.load(sys.argv[1], map_location=DEV)); net.eval(); rows = []
for d in sorted(glob.glob(sys.argv[2])):
    X = np.load(f'{d}/X.npy', mmap_mode='r'); Y = np.load(f'{d}/Y.npy'); L = np.load(f'{d}/L.npy'); Q = np.load(f'{d}/Q.npy'); n = len(X); P = np.full((n, 4), np.nan, np.float32); prev = 0.0; iou = []
    with torch.no_grad():
        for s in range(0, n, 64):
            ids = range(s, min(n, s + 64)); o = net(torch.from_numpy(np.ascontiguousarray(X[list(ids)])).float().div_(255.).to(DEV)).cpu().numpy()
            for k, i in enumerate(ids):
                r = bev_to_geo(o[k], 0.0, prev)
                if r: P[i] = r; prev = r[0]
    t = Q[:, 3]; mv = Y[:, 3] > 1.0; v = (L[:, 11] > 0) & mv & np.isfinite(P[:, 0])
    def rev(x): x = x[np.isfinite(x)]; return float(np.sum(np.diff(np.sign(np.diff(x))) != 0)) / max(t[-1] - t[0], 1e-3)
    r = {'ep': d.split('/')[-1], 'n': n, 'valid_frac': round(float(np.isfinite(P[:, 0]).mean()), 3), 'ey_rev_s': round(rev(P[mv, 0]), 2), 'lc20_rev_s': round(rev(P[mv, 3]), 2), 'ey_dp90': round(float(np.nanpercentile(np.abs(np.diff(P[:, 0])), 90)), 3), 'ey_mae': round(float(np.abs(P[v, 0] - L[v, 0]).mean()), 3) if v.any() else None, 'epsi_mae_deg': round(float(np.degrees(np.abs(P[v, 1] - L[v, 1]).mean())), 2) if v.any() else None, 'lc20_mae': round(float(np.abs(P[v, 3] - L[v, 4]).mean()), 2) if v.any() else None}
    for name, lo, hi in [('nl<=4', 0, 4), ('nl5-8', 5, 8)]:
        b = (L[:, 7] >= lo) & (L[:, 7] <= hi) & v
        if b.sum() >= 30: r[name] = {'n': int(b.sum()), 'ey_mae': round(float(np.abs(P[b, 0] - L[b, 0]).mean()), 3), 'ey_rev_s': round(rev(P[b, 0]), 2)}
    rows.append(r); print(json.dumps(r, default=float), flush=True)
m = lambda k: round(float(np.mean([r[k] for r in rows if r.get(k) is not None])), 3)
print(json.dumps({'model': sys.argv[1], 'episodes': len(rows), 'valid_frac': m('valid_frac'), 'ey_rev_s': m('ey_rev_s'), 'lc20_rev_s': m('lc20_rev_s'), 'ey_dp90': m('ey_dp90'), 'ey_mae': m('ey_mae'), 'epsi_mae_deg': m('epsi_mae_deg'), 'lc20_mae': m('lc20_mae')}, default=float))
