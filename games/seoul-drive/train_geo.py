#!/usr/bin/env python3
"""a_5598 접근 A/B 공용 학습기(2026-09-23): 화면 → 차로 기하 12열(L.npy: ey epsi k0 lc10 lc20 lc40 li nl lw dl dr valid).
사용: python3 train_geo.py 'data/dagger_r2*' ode_geo1.pt [--epochs 8] [--init prev.pt] [--seed 0]
정규화(추론 디코딩과 반드시 일치): ey/2, epsi/0.5, k0*20, lc/16, li/8, nl/8, lw/5, dl/15, dr/15, valid.
필터: valid==1, v>1m/s, |ey|≤2.5, |epsi|≤0.7, |lc|≤20, 이벤트(순간이동·사고) ±3s 제외, 홀드아웃 청크+이웃 제외(Q.npy pos px/6 → floor(m/1000)). 교란 프레임(|ey|>0.4) 가중 0.5(RESEARCH §FINAL(3))."""
import sys, os, glob, json, math, numpy as np, torch
from net import DriveNet
import gpu_guard
DEV = gpu_guard.require_gpu(); BS = 64
SCALE = np.array([2.0, 0.5, 0.05, 16.0, 16.0, 16.0, 8.0, 8.0, 5.0, 15.0, 15.0, 1.0], np.float32)   # target = L / SCALE (k0*20 == /0.05)
WCOL = torch.tensor([4.0, 3.0, 1.0, 2.0, 2.0, 1.0, 2.0, 1.0, 0.5, 1.0, 1.0, 0.5], device=DEV)
from train_stage import augment, AUG   # 광도 증강만(좌우반전은 라벨 부호가 얽혀 미사용)
def holdout_mask(Q):
    try: H = set(tuple(k) for k in json.load(open('data/holdout_chunks.json'))['chunks'])
    except Exception: return np.ones(len(Q), bool)
    cx = np.floor(Q[:, 4] / 6.0 / 1000.0); cy = np.floor(Q[:, 5] / 6.0 / 1000.0); bad = np.zeros(len(Q), bool)
    for hx, hy in H: bad |= (np.abs(cx - hx) <= 1) & (np.abs(cy - hy) <= 1)
    return ~bad
def load(dirs):
    plan = []
    for d in dirs:
        try: X = np.load(f'{d}/X.npy', mmap_mode='r'); Yf = np.load(f'{d}/Y.npy').astype(np.float32); L = np.load(f'{d}/L.npy').astype(np.float32); Q = np.load(f'{d}/Q.npy')
        except Exception as e: print(json.dumps({'skip': d, 'why': str(e)[:60]}), flush=True); continue
        if L.shape[1] < 12 or not (len(X) == len(Yf) == len(L) == len(Q)): print(json.dumps({'skip': d, 'why': 'shape'}), flush=True); continue
        ok = (L[:, 11] > 0) & np.isfinite(L[:, :11]).all(1) & (Yf[:, 3] > 1.0) & (np.abs(L[:, 0]) <= 2.5) & (np.abs(L[:, 1]) <= 0.7) & (np.abs(L[:, 3:6]) <= 20).all(1)
        ok &= holdout_mask(Q)
        ev = np.where((np.diff(Q[:, 1]) > 0) | (np.diff(Q[:, 2]) > 0))[0] + 1
        for e in ev: ok &= ~(np.abs(Q[:, 3] - Q[e, 3]) <= 3.0)
        idx = np.where(ok)[0]
        if len(idx) == 0: continue
        Y = (L[idx, :12] / SCALE).astype(np.float32); V = (Yf[idx, 3] / 30.0).astype(np.float32).reshape(-1, 1); W = (np.where(np.abs(L[idx, 0]) > 0.4, 0.5, 1.0) * np.where(L[idx, 7] >= 3, float(os.environ.get('WIDE_W', '2.0')), 1.0)).astype(np.float32)   # A': 대로(진행방향 ≥4차로) 프레임 가중 WIDE_W
        plan.append((d, idx, Y, V, W)); print(json.dumps({'dir': d.split('/')[-1], 'total': len(X), 'kept': int(len(idx)), 'ey_std': round(float(L[idx, 0].std()), 3), 'perturbed%': round(100 * float((np.abs(L[idx, 0]) > 0.4).mean()), 1)}), flush=True)
    if not plan: return None
    class LazyX:
        def __init__(s, parts): s.parts = parts; s.off = np.cumsum([0] + [len(i) for _, i in parts])
        def __len__(s): return int(s.off[-1])
        def prev(s, g, j):   # 전역 인덱스 g 의 j 프레임 전(같은 파트=에피소드 안에서만; 경계는 반복)
            p = int(np.searchsorted(s.off, g, side='right') - 1); loc = s.parts[p][1][g - s.off[p]]; return s.parts[p][0][max(0, loc - j)]
        def __getitem__(s, ids):
            out = np.empty((len(ids),) + s.parts[0][0].shape[1:], np.uint8)
            for k, g in enumerate(ids):
                p = int(np.searchsorted(s.off, g, side='right') - 1); out[k] = s.parts[p][0][s.parts[p][1][g - s.off[p]]]
            return out
    XA = LazyX([(np.load(f'{d}/X.npy', mmap_mode='r'), idx) for d, idx, _, _, _ in plan])
    return XA, np.concatenate([p[2] for p in plan]), np.concatenate([p[3] for p in plan]), np.concatenate([p[4] for p in plan])
KSTACK = 1
def batch(X, Y, V, W, ids, train=False):
    if KSTACK > 1:   # ★A3(u_5602): 직전 K-1 프레임 채널 스택(같은 에피소드 안, 인덱스 순). 자차 이동 보정은 근사 생략(≈70ms, <1m) — 기록.
        xs = [np.concatenate([X.prev(g, j) for j in range(KSTACK - 1, -1, -1)], 0) for g in ids]; xb = torch.from_numpy(np.stack(xs)).float().div_(255.).to(DEV)
    else: xb = torch.from_numpy(np.ascontiguousarray(X[ids])).float().div_(255.).to(DEV)
    if train and AUG: xb = augment(xb)
    return xb, torch.from_numpy(Y[ids]).to(DEV), torch.from_numpy(V[ids]).to(DEV), torch.from_numpy(W[ids]).to(DEV)
def main():
    import argparse; ap = argparse.ArgumentParser(); ap.add_argument('dirs'); ap.add_argument('out'); ap.add_argument('--epochs', type=int, default=8); ap.add_argument('--init', default=None); ap.add_argument('--seed', type=int, default=0); ap.add_argument('--k', type=int, default=1, help='시간 스택 프레임 수(A3)'); a = ap.parse_args()
    rng = np.random.default_rng(a.seed); torch.manual_seed(a.seed)
    dirs = [d for p in a.dirs.split(',') for d in sorted(glob.glob(p))]; got = load(dirs)
    if not got: print(json.dumps({'error': 'no frames'})); return
    X, Y, V, W = got; n = len(X); print(json.dumps({'frames': n, 'gb': round(n * 3 * 256 * 256 / 1e9, 1), 'k': a.k}), flush=True)
    idx = rng.permutation(n); cut = int(n * 0.9); tr, va = idx[:cut], idx[cut:]
    global KSTACK; KSTACK = a.k; net = DriveNet(out=12, vin=True, vdim=1, in_ch=3 * a.k).to(DEV); gpu_guard.assert_on_gpu(net)
    if a.init:
        _sd = torch.load(a.init, map_location=DEV); _own = net.state_dict(); _ok = {k: v for k, v in _sd.items() if k in _own and _own[k].shape == v.shape}; net.load_state_dict(_ok, strict=False); print(json.dumps({'init': a.init, 'loaded': len(_ok)}), flush=True)
    opt = torch.optim.Adam(net.parameters(), 5e-4 if a.init else 1e-3, weight_decay=1e-4); best = 1e9
    for ep in range(a.epochs):
        net.train(); tot = 0.0; perm = rng.permutation(tr)
        for i in range(0, len(perm), BS):
            ids = np.sort(perm[i:i + BS]); xb, yb, vb, wb = batch(X, Y, V, W, ids, train=True)
            opt.zero_grad(); o = net(xb, vb, raw=True); l = ((((o - yb) ** 2) * WCOL).mean(1) * wb).mean(); l.backward(); opt.step(); tot += l.item() * len(ids)
        net.eval(); vs = 0.0; c = 0; mae = np.zeros(12)
        with torch.no_grad():
            for i in range(0, len(va), BS):
                ids = np.sort(va[i:i + BS]); xb, yb, vb, wb = batch(X, Y, V, W, ids); o = net(xb, vb, raw=True)
                vs += (((o - yb) ** 2) * WCOL).mean().item() * len(ids); mae += (torch.abs(o - yb).sum(0).cpu().numpy() * SCALE); c += len(ids)
        vl = vs / max(1, c); mae /= max(1, c)
        if vl < best: best = vl; torch.save(net.state_dict(), a.out)
        print(json.dumps({'ep': ep, 'train': round(tot / len(perm), 5), 'val': round(vl, 5), 'mae': {'ey_m': round(float(mae[0]), 3), 'epsi_deg': round(float(math.degrees(mae[1])), 2), 'lc20_m': round(float(mae[4]), 3), 'li': round(float(mae[6]), 3)}}), flush=True)
    print(json.dumps({'done': a.out, 'best_val': round(best, 5)}), flush=True)
if __name__ == '__main__': main()
