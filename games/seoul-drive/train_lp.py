#!/usr/bin/env python3
"""앞점(lookahead) 모델 학습 (2026-09-21, 오너 u_5489 진행(A)).
   입력 = 화면(256, ODE_CROP 적용된 X.npy) + 속도(v/30). 출력 4 = [steer(미사용), thr, brake, (lp+8)/16].
   라벨: Y.npy [st, th, br, v, ...] + L.npy [lp, ld]. 프레임 품질 Q.npy 가 있으면 xt<XT_MAX·이벤트 ±3초 밖만.
   사용: python3 train_lp.py 'data/dagger_r7*,data/dagger_r8*' ode_lp1.pt [--epochs 15] [--init prev.pt]"""
import os, argparse, glob, json, os, sys
import numpy as np, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gpu_guard
from net import DriveNet
from train_stage import augment, AUG
DEV = gpu_guard.require_gpu(); BS = 64
XT_MAX = float(os.environ.get('XT_MAX', '0.6'))
XT_MAX_DAGGER = float(os.environ.get('XT_MAX_DAGGER', '4.0'))
LP_MAX = 12.0   # lp 인코딩 범위 ±12m: (lp+12)/24. dagger.py 디코딩과 반드시 일치

def load(dirs, synth=()):
    Xs, Ys, Vs, Ws = [], [], [], []
    synth = set(synth)
    # ★2026-09-22 밤샘 lp9 OOM(14.5만 장 ≈28GB + concatenate 복사 = 51GB 초과, 메시지 없이 죽음): X 는 mmap 으로 열고
    #   선택 프레임만 미리 잡아둔 배열에 채운다(복사 1회). 오래된 기본 라운드(r85*~r91*)는 STRIDE 로 솎는다(최신 DAgger·교란 라운드는 전부).
    STRIDE = int(os.environ.get('LP_STRIDE', '1'))
    plan = []   # (d, idx, Y, V)
    for d in list(dirs) + [x for x in synth if x not in dirs]:
        try:
            X = np.load(f'{d}/X.npy', mmap_mode='r'); Yf = np.load(f'{d}/Y.npy').astype(np.float32); L = np.load(f'{d}/L.npy').astype(np.float32)
        except Exception as e:
            print(json.dumps({'skip': d, 'why': str(e)[:60]}), flush=True); continue
        if not (len(X) == len(Yf) == len(L)): print(json.dumps({'skip': d, 'why': 'len'})); continue
        ok = np.isfinite(L[:, 0]) & (np.abs(L[:, 0]) <= LP_MAX)
        try:
            Q = np.load(f'{d}/Q.npy')
            if len(Q) == len(Yf) and d not in synth:
                # DAgger 라운드(모델 주행, r9xx)는 '벗어난 상태의 교정'이 목적이라 xt 상한을 넓게(경로를 잃은 프레임만 제외); 교사 라운드는 XT_MAX.
                _xm = XT_MAX_DAGGER if '/dagger_r9' in d else XT_MAX
                ok &= Q[:, 0] < _xm
                ev = np.where((np.diff(Q[:, 1]) > 0) | (np.diff(Q[:, 2]) > 0))[0] + 1
                for e in ev: ok &= ~(np.abs(Q[:, 3] - Q[e, 3]) <= 3.0)
        except Exception: pass
        idx = np.where(ok)[0]
        if STRIDE > 1 and d not in synth and ('/dagger_r8' in d or '/dagger_r91' in d): idx = idx[::STRIDE]
        if len(idx) == 0: continue
        Y = np.stack([Yf[idx, 0], Yf[idx, 1], Yf[idx, 2], (L[idx, 0] + LP_MAX) / (2 * LP_MAX)], 1).astype(np.float32)
        plan.append((d, idx, Y, (Yf[idx, 3] / 30.0).astype(np.float32)))
        print(json.dumps({'dir': d.split('/')[-1], 'total': len(X), 'kept': int(len(idx)), 'lp_std': round(float(L[idx, 0].std()), 2)}), flush=True)
    if not plan: return None
    N = sum(len(i) for _, i, _, _ in plan); shp = np.load(f'{plan[0][0]}/X.npy', mmap_mode='r').shape[1:]
    print(json.dumps({'frames': int(N), 'gb': round(N * int(np.prod(shp)) / 1e9, 1)}), flush=True)
    XA = np.empty((N,) + tuple(shp), np.uint8); o = 0
    for d, idx, _, _ in plan:
        X = np.load(f'{d}/X.npy', mmap_mode='r'); XA[o:o + len(idx)] = X[idx]; o += len(idx); del X
    return XA, np.concatenate([y for _, _, y, _ in plan]), np.concatenate([v for _, _, _, v in plan]), np.ones(N, np.float32)

def batch(X, Y, V, ids, train=False):
    real = np.abs(ids) - 1
    xb = torch.from_numpy(np.ascontiguousarray(X[real])).float().div_(255.); yb = Y[real].copy(); flip = ids < 0
    if flip.any():
        xb[flip] = torch.flip(xb[flip], dims=[3]); yb[flip, 0] *= -1; yb[flip, 3] = 1.0 - yb[flip, 3]   # 좌우 반전: lp 부호 반전
    xb = xb.to(DEV)
    if train and AUG: xb = augment(xb)
    return xb, torch.from_numpy(yb).to(DEV), torch.from_numpy(V[real]).to(DEV)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('dirs'); ap.add_argument('out'); ap.add_argument('--epochs', type=int, default=15); ap.add_argument('--init', default=None); ap.add_argument('--synth', default='', help='가상 샘플링 라운드 글롭(쉼표) — xt/이벤트 필터 제외(상태를 일부러 벗어나게 놓은 데이터)')
    a = ap.parse_args(); rng = np.random.default_rng(0)
    dirs = [d for p in a.dirs.split(',') for d in sorted(glob.glob(p))]
    synth = [d for p in a.synth.split(',') if p for d in sorted(glob.glob(p))]
    got = load(dirs, synth)
    if not got: print(json.dumps({'error': 'no frames'})); return
    X, Y, V, W = got; n = len(X)
    print(json.dumps({'frames': n, 'lp_mean_m': round(float(Y[:, 3].mean() * 2 * LP_MAX - LP_MAX), 2), 'lp_std_m': round(float(Y[:, 3].std() * 2 * LP_MAX), 2)}), flush=True)
    idx = rng.permutation(n); cut = int(n * 0.85)
    tr = np.concatenate([idx[:cut] + 1, -(idx[:cut] + 1)]); va = np.concatenate([idx[cut:] + 1, -(idx[cut:] + 1)])
    net = DriveNet(out=4, vin=True).to(DEV); gpu_guard.assert_on_gpu(net)
    if a.init: net.load_state_dict(torch.load(a.init, map_location=DEV), strict=False); print(json.dumps({'init': a.init}), flush=True)
    opt = torch.optim.Adam(net.parameters(), 5e-4 if a.init else 1e-3, weight_decay=1e-4)
    wcol = torch.tensor([0.2, 0.5, 0.5, 4.0], device=DEV)   # lp 가 주 목표
    best = 1e9
    for ep in range(a.epochs):
        net.train(); tot = 0.0; perm = rng.permutation(tr)
        for i in range(0, len(perm), BS):
            ids = perm[i:i+BS]; xb, yb, vb = batch(X, Y, V, ids, train=True)
            opt.zero_grad(); o = net(xb, vb); l = (((o - yb) ** 2) * wcol).mean(); l.backward(); opt.step(); tot += l.item() * len(ids)
        net.eval(); vs = 0.0; c = 0; lpe = 0.0
        with torch.no_grad():
            for i in range(0, len(va), BS):
                ids = va[i:i+BS]; xb, yb, vb = batch(X, Y, V, ids); o = net(xb, vb)
                vs += (((o - yb) ** 2) * wcol).mean().item() * len(ids); lpe += (torch.abs(o[:, 3] - yb[:, 3]) * 2 * LP_MAX).sum().item(); c += len(ids)
        vl = vs / max(1, c)
        if vl < best: best = vl; torch.save(net.state_dict(), a.out)
        print(json.dumps({'ep': ep, 'train': round(tot / len(perm), 5), 'val': round(vl, 5), 'lp_mae_m': round(lpe / max(1, c), 3)}), flush=True)
    print(json.dumps({'done': a.out, 'best_val': round(best, 5)}), flush=True)

if __name__ == '__main__':
    main()
