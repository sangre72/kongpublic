#!/usr/bin/env python3
"""a_5612 D4 오프라인 관문(2026-09-24): 홀드아웃(X,S,L) 에서 (a) 라벨→기하 일관성(--label), (b) 모델 IoU + 모델 마스크→e_y/e_psi 오차·부호반전/s, nl≤4 / 5-8 버킷.
사용: python3 seg_gate.py <ode_seg.pt|--label> 'data/dagger_r30*'   → JSON 요약. 목표 id = L.li+1(지도, 규칙층)."""
import sys, glob, json, numpy as np
from seg_geo import lane_line
from seg_net import NCLS
model = sys.argv[1]; dirs = sorted(glob.glob(sys.argv[2])); net = None
if model != '--label':
    import torch, gpu_guard; from seg_net import SegNet
    DEV = gpu_guard.require_gpu(); net = SegNet().to(DEV); net.load_state_dict(torch.load(model, map_location=DEV)); net.eval()
conf = np.zeros((NCLS, NCLS), np.int64); rows = []; rev = {'n': 0, 'rev': 0, 't': 0.0}
for d in dirs:
    X = np.load(f'{d}/X.npy', mmap_mode='r'); L = np.load(f'{d}/L.npy'); Q = np.load(f'{d}/Q.npy'); Y = np.load(f'{d}/Y.npy')
    try: S = np.load(f'{d}/S.npy', mmap_mode='r')
    except Exception: S = None
    n = len(X); prev = None
    for s in range(0, n, 32):
        ids = list(range(s, min(n, s + 32)))
        if net is None: P = np.asarray(S[ids])
        else:
            with torch.no_grad(): P = net(torch.from_numpy(np.ascontiguousarray(X[ids])).float().div_(255.).to(DEV)).argmax(1).cpu().numpy().astype(np.uint8)
            if S is not None:
                sb = np.asarray(S[ids]); m = sb != 255; conf += np.bincount((sb[m].astype(np.int64) * NCLS + P[m]), minlength=NCLS * NCLS).reshape(NCLS, NCLS)
        for k, i in enumerate(ids):
            if L[i, 11] <= 0 or Y[i, 3] < 1.0: prev = None; continue
            tid = int(round(L[i, 6])) + 1; ey, ep, nr, used = lane_line(P[k], tid)
            if not np.isfinite(ey): prev = None; continue
            rows.append((L[i, 7], ey - L[i, 0], ep - L[i, 1], used == tid))
            if prev is not None and i == prev[0] + 1:
                rev['n'] += 1; rev['t'] += float(Q[i, 3] - prev[2]); rev['rev'] += int(np.sign(ey) != np.sign(prev[1]) and abs(ey - prev[1]) > 0.1)
            prev = (i, ey, Q[i, 3])
R = np.array(rows, np.float64); out = {'model': model, 'frames': len(R)}
def bucket(name, m):
    if m.sum() == 0: return
    out[name] = {'n': int(m.sum()), 'ey_mae': round(float(np.abs(R[m, 1]).mean()), 3), 'ey_bias': round(float(R[m, 1].mean()), 3), 'epsi_mae_deg': round(float(np.degrees(np.abs(R[m, 2])).mean()), 2), 'target_found%': round(100 * float(R[m, 3].mean()), 1)}
if len(R):
    bucket('all', np.ones(len(R), bool)); bucket('narrow_nl<=4', R[:, 0] <= 4); bucket('wide_nl5-8', (R[:, 0] >= 5) & (R[:, 0] <= 8)); bucket('nl>=9', R[:, 0] >= 9)
    out['ey_rev_s'] = round(rev['rev'] / max(1e-6, rev['t']), 3)
if net is not None and conf.sum():
    tp = np.diag(conf); io = tp / np.maximum(1, conf.sum(0) + conf.sum(1) - tp); out['iou'] = [round(float(v), 3) for v in io]; out['miou_lanes'] = round(float(io[1:9][conf.sum(1)[1:9] > 0].mean()), 3); out['iou_line'] = round(float(io[9]), 3)
print(json.dumps(out))
