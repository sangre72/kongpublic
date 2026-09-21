#!/usr/bin/env python3
"""앞점(lookahead) 모델 학습 — 프레임 스택판(입력 6채널 = 직전+현재 프레임, 2026-09-21 갈지자 대책) (2026-09-21, 오너 u_5489 진행(A)).
   입력 = 화면(256, ODE_CROP 적용된 X.npy) + 속도(v/30). 출력 4 = [steer(미사용), thr, brake, (lp+8)/16].
   라벨: Y.npy [st, th, br, v, ...] + L.npy [lp, ld]. 프레임 품질 Q.npy 가 있으면 xt<XT_MAX·이벤트 ±3초 밖만.
   사용: python3 train_lp.py 'data/dagger_r7*,data/dagger_r8*' ode_lp1.pt [--epochs 15] [--init prev.pt]"""
import argparse, glob, json, os, sys
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
    """메모리: 직전 프레임을 복사하지 않는다(8.8만 장×2 = 35GB 로 조용히 죽었다, 2026-09-22 00:0x). 전체 X 를 하나로 잇고 kept 인덱스·직전 인덱스만 든다."""
    Xs, Ys, Vs, Ws = [], [], [], []
    GI, GP = [], []; base = 0   # 전역 인덱스(kept), 전역 직전 인덱스
    synth = set(synth)
    for d in list(dirs) + [x for x in synth if x not in dirs]:
        try:
            X = np.load(f'{d}/X.npy'); Yf = np.load(f'{d}/Y.npy').astype(np.float32); L = np.load(f'{d}/L.npy').astype(np.float32)
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
        if len(idx) == 0: continue
        Y = np.stack([Yf[idx, 0], Yf[idx, 1], Yf[idx, 2], (L[idx, 0] + LP_MAX) / (2 * LP_MAX)], 1).astype(np.float32)
        Xs.append(X); GI.append(base + idx); GP.append(base + np.maximum(idx - 1, 0)); base += len(X); Ys.append(Y); Vs.append((Yf[idx, 3] / 30.0).astype(np.float32)); Ws.append(np.ones(len(idx), np.float32))
        print(json.dumps({'dir': d.split('/')[-1], 'total': len(X), 'kept': int(len(idx)), 'lp_std': round(float(L[idx, 0].std()), 2)}), flush=True)
    if not Xs: return None
    return np.concatenate(Xs), np.concatenate(Ys), np.concatenate(Vs), np.concatenate(Ws), (np.concatenate(GI), np.concatenate(GP))

def batch(X, Y, V, ids, train=False, XP=None):
    real = np.abs(ids) - 1; gi, gp = XP[0][real], XP[1][real]
    xb = torch.cat([torch.from_numpy(np.ascontiguousarray(X[gp])).float().div_(255.), torch.from_numpy(np.ascontiguousarray(X[gi])).float().div_(255.)], dim=1); yb = Y[real].copy(); flip = ids < 0
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
    X, Y, V, W, XP = got; n = len(Y)
    print(json.dumps({'frames': n, 'lp_mean_m': round(float(Y[:, 3].mean() * 2 * LP_MAX - LP_MAX), 2), 'lp_std_m': round(float(Y[:, 3].std() * 2 * LP_MAX), 2)}), flush=True)
    idx = rng.permutation(n); cut = int(n * 0.85)
    tr = np.concatenate([idx[:cut] + 1, -(idx[:cut] + 1)]); va = np.concatenate([idx[cut:] + 1, -(idx[cut:] + 1)])
    net = DriveNet(out=4, vin=True, in_ch=6).to(DEV); gpu_guard.assert_on_gpu(net)
    if a.init: net.load_state_dict(torch.load(a.init, map_location=DEV), strict=False); print(json.dumps({'init': a.init}), flush=True)
    opt = torch.optim.Adam(net.parameters(), 5e-4 if a.init else 1e-3, weight_decay=1e-4)
    wcol = torch.tensor([0.2, 0.5, 0.5, 4.0], device=DEV)   # lp 가 주 목표
    best = 1e9
    for ep in range(a.epochs):
        net.train(); tot = 0.0; perm = rng.permutation(tr)
        for i in range(0, len(perm), BS):
            ids = perm[i:i+BS]; xb, yb, vb = batch(X, Y, V, ids, train=True, XP=XP)
            opt.zero_grad(); o = net(xb, vb); l = (((o - yb) ** 2) * wcol).mean(); l.backward(); opt.step(); tot += l.item() * len(ids)
        net.eval(); vs = 0.0; c = 0; lpe = 0.0
        with torch.no_grad():
            for i in range(0, len(va), BS):
                ids = va[i:i+BS]; xb, yb, vb = batch(X, Y, V, ids, XP=XP); o = net(xb, vb)
                vs += (((o - yb) ** 2) * wcol).mean().item() * len(ids); lpe += (torch.abs(o[:, 3] - yb[:, 3]) * 2 * LP_MAX).sum().item(); c += len(ids)
        vl = vs / max(1, c)
        if vl < best: best = vl; torch.save(net.state_dict(), a.out)
        print(json.dumps({'ep': ep, 'train': round(tot / len(perm), 5), 'val': round(vl, 5), 'lp_mae_m': round(lpe / max(1, c), 3)}), flush=True)
    print(json.dumps({'done': a.out, 'best_val': round(best, 5)}), flush=True)

if __name__ == '__main__':
    main()
