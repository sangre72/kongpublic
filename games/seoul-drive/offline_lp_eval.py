#!/usr/bin/env python3
"""화면 없이 앞점 모델 오차 진단(2026-09-23): 규칙 주행 라운드(on-policy 상태)에 모델을 돌려 횡오프셋 예측 오차를 상황별로 집계.
사용: python3 offline_lp_eval.py <model.pt> '<dirs glob>'  → 상황(직진/좌/우/유턴, 회전까지 거리)별 lp10..80 MAE(m)."""
import sys, glob, json, numpy as np, torch
from net import DriveNet, cond_vec, vdim_of
import gpu_guard
DEV = gpu_guard.require_gpu()
sd = torch.load(sys.argv[1], map_location='cpu'); sd = sd.get('model', sd) if isinstance(sd, dict) and 'model' in sd else sd
out = sd['hv.2.weight'].shape[0]; vd = vdim_of(sd)
net = DriveNet(out=out, vin=True, vdim=vd).to(DEV); net.load_state_dict(sd); net.eval()
rows = []
for d in sorted(glob.glob(sys.argv[2])):
    X = np.load(f'{d}/X.npy', mmap_mode='r'); Y = np.load(f'{d}/Y.npy'); L = np.load(f'{d}/L.npy'); M = np.load(f'{d}/M.npy')
    n = len(X); idx = np.arange(0, n, 3)
    for s in range(0, len(idx), 128):
        ii = idx[s:s + 128]
        xb = torch.from_numpy(np.ascontiguousarray(X[ii])).float().div_(255.).to(DEV)
        vb = (Y[ii, 3] / 30.0).astype(np.float32).reshape(-1, 1) if vd == 1 else np.stack([cond_vec(Y[i, 3], int(M[i, 3]), M[i, 4], M[i, 6], M[i, 7], (M[i, 11] if vd == 9 else None)) for i in ii]).astype(np.float32)   # a_5577: vdim=1(속도만) 모델도 평가(mp3c8)
        with torch.no_grad(): p = net(xb, torch.from_numpy(vb).to(DEV)).cpu().numpy()
        lp_pred = p[:, 3:7] * 128 - 64; lp_true = L[ii, 3:7]
        ok = np.isfinite(lp_true).all(1) & (np.abs(lp_true) < 64).all(1) & (Y[ii, 3] > 2)
        for k in np.where(ok)[0]:
            i = ii[k]; rows.append((int(M[i, 3]), float(M[i, 4]), float(Y[i, 3]), *np.abs(lp_pred[k] - lp_true[k]), *(lp_pred[k] - lp_true[k])))
R = np.array(rows); print(json.dumps({'model': sys.argv[1], 'vdim': vd, 'out': out, 'frames': len(R)}))
def rep(name, m):
    if m.sum() < 30: return
    e = R[m][:, 3:7]; b = R[m][:, 7:11]
    print(f'{name:28s} n={int(m.sum()):6d}  MAE lp10/20/40/80 = {e[:,0].mean():.2f} {e[:,1].mean():.2f} {e[:,2].mean():.2f} {e[:,3].mean():.2f} m   bias20={b[:,1].mean():+.2f}  p90_20={np.percentile(e[:,1],90):.2f}')
T = ['S', 'L', 'R', 'U']
rep('ALL', np.ones(len(R), bool))
for t in range(4): rep(f'turn={T[t]}', R[:, 0] == t)
for t in (1, 2):
    for lo, hi in ((0, 30), (30, 80), (80, 200), (200, 1e9)): rep(f'turn={T[t]} aD {lo}-{hi}', (R[:, 0] == t) & (R[:, 1] >= lo) & (R[:, 1] < hi))
for lo, hi in ((2, 8), (8, 15), (15, 40)): rep(f'v {lo}-{hi} m/s', (R[:, 2] >= lo) & (R[:, 2] < hi))
