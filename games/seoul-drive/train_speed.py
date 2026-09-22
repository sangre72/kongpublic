#!/usr/bin/env python3
"""속도 판단 모델 (2026-09-22, 축소안 A: 조향=규칙 추종기, 모델=목표속도).
   입력 = 화면(ODE_CROP 적용 X.npy) + 현재 속도(v/30). 라벨 = 같은 라운드에서 ≈1초 뒤 실제 속도(v[t+H]/30, H=13프레임≈1초@13fps) — 교사가 '앞으로 1초 동안 어떻게 할지'.
   교사 주행(순차) 라운드만 사용(가상 샘플링 r80*/r82* 은 프레임이 불연속이라 제외). 출력 4 = [steer(미사용), thr, brake, vT/30].
   사용: python3 train_speed.py 'data/dagger_r81*,data/dagger_r7*' ode_v1.pt [--epochs 12] [--H 13]"""
import argparse, glob, json, os, sys
import numpy as np, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gpu_guard
from net import DriveNet
from train_stage import augment, AUG
DEV = gpu_guard.require_gpu(); BS = 64
LABEL = os.environ.get('SPEED_LABEL', 'future')   # future = 1초 뒤 실제 v / vmax = 규칙 목표속도(L.npy[:,2])

def load(dirs, H):
    Xs, Ys, Vs = [], [], []
    for d in dirs:
        try:
            X = np.load(f'{d}/X.npy', mmap_mode='r'); Yf = np.load(f'{d}/Y.npy').astype(np.float32)   # ★u_5555 mmap
        except Exception as e:
            print(json.dumps({'skip': d, 'why': str(e)[:60]}), flush=True); continue
        n = len(Yf)
        if n <= H + 1: continue
        if X.ndim != 4 or X.shape[1] != 3: print(json.dumps({'skip': d, 'why': 'X channels %s' % str(X.shape[1:])}), flush=True); continue   # 프레임 스택 평가 라운드(6ch) 제외
        idx = np.arange(0, n - H)
        try:
            Q = np.load(f'{d}/Q.npy')
            if len(Q) == n:   # 순간이동·사고 ±3초 제외(속도 라벨이 깨진다)
                ev = np.where((np.diff(Q[:, 1]) > 0) | (np.diff(Q[:, 2]) > 0))[0] + 1
                ok = np.ones(n - H, bool)
                for e in ev: ok &= ~(np.abs(Q[idx, 3] - Q[e, 3]) <= 3.0)
                idx = idx[ok]
        except Exception: pass
        vT = np.clip(Yf[idx + H, 3] / 30.0, 0, 1)
        if LABEL == 'vmax':   # 규칙(추종기)의 목표속도 — 모델 주행 라운드(DAgger)에서도 유효한 라벨. L.npy 3열(2026-09-22 이후 수집분).
            try:
                L = np.load(f'{d}/L.npy')
                if L.shape[1] >= 3 and np.isfinite(L[idx, 2]).mean() > 0.9: vT = np.clip(np.nan_to_num(L[idx, 2], nan=0.0) / 30.0, 0, 1)
                else: print(json.dumps({'skip': d, 'why': 'no vmax label'}), flush=True); continue
            except Exception: print(json.dumps({'skip': d, 'why': 'no L.npy'}), flush=True); continue
        Y = np.stack([Yf[idx, 0], Yf[idx, 1], Yf[idx, 2], vT], 1).astype(np.float32)
        Xs.append((X, idx)); Ys.append(Y); Vs.append((Yf[idx, 3] / 30.0).astype(np.float32))   # ★lazy: (mmap, idx)
        print(json.dumps({'dir': d.split('/')[-1], 'total': n, 'kept': int(len(idx)), 'vT_mean': round(float(vT.mean() * 30), 1)}), flush=True)
    if not Xs: return None
    from train_lp import LazyX
    return LazyX(Xs), np.concatenate(Ys), np.concatenate(Vs)

def batch(X, Y, V, ids, train=False):
    real = np.abs(ids) - 1
    xb = torch.from_numpy(np.ascontiguousarray(X[real])).float().div_(255.); yb = Y[real].copy(); flip = ids < 0
    if flip.any(): xb[flip] = torch.flip(xb[flip], dims=[3]); yb[flip, 0] *= -1
    xb = xb.to(DEV)
    if train and AUG: xb = augment(xb)
    return xb, torch.from_numpy(yb).to(DEV), torch.from_numpy(V[real]).to(DEV)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('dirs'); ap.add_argument('out'); ap.add_argument('--epochs', type=int, default=12); ap.add_argument('--H', type=int, default=13); ap.add_argument('--init', default=None)
    a = ap.parse_args(); rng = np.random.default_rng(0)
    dirs = [d for p in a.dirs.split(',') for d in sorted(glob.glob(p))]
    got = load(dirs, a.H)
    if not got: print(json.dumps({'error': 'no frames'})); return
    X, Y, V = got; n = len(X)
    print(json.dumps({'frames': n, 'vT_mean_ms': round(float(Y[:, 3].mean() * 30), 2), 'vT_std_ms': round(float(Y[:, 3].std() * 30), 2)}), flush=True)
    idx = rng.permutation(n); cut = int(n * 0.85)
    tr = np.concatenate([idx[:cut] + 1, -(idx[:cut] + 1)]); va = np.concatenate([idx[cut:] + 1, -(idx[cut:] + 1)])
    net = DriveNet(out=4, vin=True).to(DEV); gpu_guard.assert_on_gpu(net)
    if a.init: net.load_state_dict(torch.load(a.init, map_location=DEV), strict=False)
    opt = torch.optim.Adam(net.parameters(), 1e-3, weight_decay=1e-4)
    wcol = torch.tensor([0.1, 0.5, 0.5, 4.0], device=DEV); best = 1e9
    for ep in range(a.epochs):
        net.train(); tot = 0.0; perm = rng.permutation(tr)
        for i in range(0, len(perm), BS):
            ids = perm[i:i+BS]; xb, yb, vb = batch(X, Y, V, ids, train=True)
            opt.zero_grad(); o = net(xb, vb); l = (((o - yb) ** 2) * wcol).mean(); l.backward(); opt.step(); tot += l.item() * len(ids)
        net.eval(); vs = 0.0; c = 0; ve = 0.0
        with torch.no_grad():
            for i in range(0, len(va), BS):
                ids = va[i:i+BS]; xb, yb, vb = batch(X, Y, V, ids); o = net(xb, vb)
                vs += (((o - yb) ** 2) * wcol).mean().item() * len(ids); ve += (torch.abs(o[:, 3] - yb[:, 3]) * 30).sum().item(); c += len(ids)
        vl = vs / max(1, c)
        if vl < best: best = vl; torch.save(net.state_dict(), a.out)
        print(json.dumps({'ep': ep, 'train': round(tot / len(perm), 5), 'val': round(vl, 5), 'vT_mae_ms': round(ve / max(1, c), 3)}), flush=True)
    print(json.dumps({'done': a.out, 'best_val': round(best, 5)}), flush=True)

if __name__ == '__main__':
    main()
