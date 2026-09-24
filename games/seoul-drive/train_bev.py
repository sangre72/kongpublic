#!/usr/bin/env python3
"""C(BEV) 학습기(2026-09-24): 화면 256×256 → 자차 기준 격자 3×64×64(차로중심선·주행가능·진행방향 차로선), BCE(양성 가중). 입력 = 픽셀(+v 없음).
사용: python3 train_bev.py 'data/dagger_r25*,data/dagger_r26*' ode_bev1.pt [--epochs 8] [--seed 0]. 홀드아웃 청크 제외(Q pos), 이벤트 ±3s 제외."""
import sys, os, glob, json, numpy as np, torch, torch.nn as nn
import gpu_guard
DEV = gpu_guard.require_gpu(); BS = 32
from train_stage import augment, AUG
from train_geo import holdout_mask
class BevNet(nn.Module):   # DriveNet 인코더(5×stride2 → 128×6×6) + 업샘플 디코더 → 3×64×64 로짓
    def __init__(s):
        super().__init__()
        s.f = nn.Sequential(nn.Conv2d(3, 16, 5, 2), nn.ReLU(), nn.Conv2d(16, 32, 3, 2), nn.ReLU(), nn.Conv2d(32, 64, 3, 2), nn.ReLU(), nn.Conv2d(64, 96, 3, 2), nn.ReLU(), nn.Conv2d(96, 128, 3, 2), nn.ReLU())
        s.fc = nn.Sequential(nn.Flatten(), nn.Linear(128 * 6 * 6, 1024), nn.ReLU(), nn.Linear(1024, 64 * 8 * 8), nn.ReLU())
        s.up = nn.Sequential(nn.ConvTranspose2d(64, 64, 4, 2, 1), nn.ReLU(), nn.ConvTranspose2d(64, 32, 4, 2, 1), nn.ReLU(), nn.ConvTranspose2d(32, 16, 4, 2, 1), nn.ReLU(), nn.Conv2d(16, 3, 3, 1, 1))
    def forward(s, x, v=None, raw=True): return s.up(s.fc(s.f(x)).view(-1, 64, 8, 8))
class LazyX:
    def __init__(s, parts): s.parts = parts; s.off = np.cumsum([0] + [len(i) for _, i in parts])
    def __len__(s): return int(s.off[-1])
    def __getitem__(s, ids):
        out = np.empty((len(ids),) + s.parts[0][0].shape[1:], np.uint8)
        for k, g in enumerate(ids): p = int(np.searchsorted(s.off, g, side='right') - 1); out[k] = s.parts[p][0][s.parts[p][1][g - s.off[p]]]
        return out
def load(dirs):
    plan = []
    for d in dirs:
        try: X = np.load(f'{d}/X.npy', mmap_mode='r'); B = np.load(f'{d}/B.npy', mmap_mode='r'); Q = np.load(f'{d}/Q.npy'); Y = np.load(f'{d}/Y.npy')
        except Exception as e: print(json.dumps({'skip': d, 'why': str(e)[:50]}), flush=True); continue
        if not (len(X) == len(B) == len(Q)): continue
        ok = (Y[:, 3] > 1.0) & (B.reshape(len(B), -1).sum(1) > 50) & holdout_mask(Q)
        ev = np.where((np.diff(Q[:, 1]) > 0) | (np.diff(Q[:, 2]) > 0))[0] + 1
        for e in ev: ok &= ~(np.abs(Q[:, 3] - Q[e, 3]) <= 3.0)
        idx = np.where(ok)[0]
        if len(idx): plan.append((d, idx)); print(json.dumps({'dir': d.split('/')[-1], 'kept': int(len(idx))}), flush=True)
    if not plan: return None
    return LazyX([(np.load(f'{d}/X.npy', mmap_mode='r'), idx) for d, idx in plan]), LazyX([(np.load(f'{d}/B.npy', mmap_mode='r'), idx) for d, idx in plan])
def main():
    import argparse; ap = argparse.ArgumentParser(); ap.add_argument('dirs'); ap.add_argument('out'); ap.add_argument('--epochs', type=int, default=8); ap.add_argument('--seed', type=int, default=0); a = ap.parse_args()
    rng = np.random.default_rng(a.seed); torch.manual_seed(a.seed); dirs = [d for p in a.dirs.split(',') for d in sorted(glob.glob(p))]; got = load(dirs)
    if not got: print(json.dumps({'error': 'no frames'})); return
    X, B = got; n = len(X); print(json.dumps({'frames': n}), flush=True); idx = rng.permutation(n); cut = int(n * 0.9); tr, va = idx[:cut], idx[cut:]
    net = BevNet().to(DEV); gpu_guard.assert_on_gpu(net); opt = torch.optim.Adam(net.parameters(), 1e-3, weight_decay=1e-4)
    pw = torch.tensor([8.0, 1.0, 8.0], device=DEV).view(1, 3, 1, 1); best = 1e9
    def bce(o, y): return nn.functional.binary_cross_entropy_with_logits(o, y, pos_weight=pw)
    for ep in range(a.epochs):
        net.train(); tot = 0.0; perm = rng.permutation(tr)
        for i in range(0, len(perm), BS):
            ids = np.sort(perm[i:i + BS]); xb = torch.from_numpy(np.ascontiguousarray(X[ids])).float().div_(255.).to(DEV); yb = torch.from_numpy(B[ids]).float().to(DEV)
            if AUG: xb = augment(xb)
            opt.zero_grad(); l = bce(net(xb), yb); l.backward(); opt.step(); tot += l.item() * len(ids)
        net.eval(); vs = 0.0; c = 0; iou = np.zeros(3); cnt = 0
        with torch.no_grad():
            for i in range(0, len(va), BS):
                ids = np.sort(va[i:i + BS]); xb = torch.from_numpy(np.ascontiguousarray(X[ids])).float().div_(255.).to(DEV); yb = torch.from_numpy(B[ids]).float().to(DEV); o = net(xb)
                vs += bce(o, yb).item() * len(ids); c += len(ids); p = (o > 0).float(); inter = (p * yb).sum((0, 2, 3)); uni = ((p + yb) > 0).float().sum((0, 2, 3)); iou += (inter / uni.clamp(min=1)).cpu().numpy() * len(ids); cnt += len(ids)
        vl = vs / max(1, c); iou /= max(1, cnt)
        if vl < best: best = vl; torch.save(net.state_dict(), a.out)
        print(json.dumps({'ep': ep, 'train': round(tot / len(perm), 4), 'val': round(vl, 4), 'iou': [round(float(z), 3) for z in iou]}), flush=True)
    print(json.dumps({'done': a.out, 'best_val': round(best, 4)}), flush=True)
if __name__ == '__main__': main()
