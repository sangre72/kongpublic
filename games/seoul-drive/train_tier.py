#!/usr/bin/env python3
"""관제(등급) 모델 — 화면만 보고 난이도 등급 T0~T3 을 맞히는 초소형 분류기 (오너 u_5443, 2026-09-19).

★왜: 오드에선 텔레메트리 태그(M.npy)로 등급이 공짜지만, 3D·실영상엔 텔레메트리가 없다 → 화면→등급 분류기가 필요.
   학습 라벨은 태그에서 자동 파생하므로 추가 수집이 없다.
★등급(태그 기준, ode-hierarchical-control.md): T0 직진·자극 없음 / T1 추종·회전 준비·차선변경 / T2 보행자 근접·신호 정지·골목 / T3 정지거리 안 돌발.
★검증: 정확도보다 **어려운 등급(T2·T3) 재현율**. 확신도(softmax max)가 낮으면 상위 등급으로 올린다(오판 방향 = 안전 쪽).

사용: python3 train_tier.py 'data/dagger_r1*' tier_net.pt [--epochs 15]
"""
import argparse, glob, json, os, sys
import numpy as np, torch, torch.nn as nn
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gpu_guard
DEV = gpu_guard.require_gpu()
BS = 128

def tier_labels(M, Y):
    """태그 → 등급. M=[gap, ped, sig, turn, aD, v, laneF, nl(, env, ep, fi)], Y=[st,th,br,v,fl,fr]"""
    gap, ped, sig, turn, aD, v, laneF, nl = [M[:, i] for i in range(8)]
    t = np.zeros(len(M), np.int64)
    t[(gap < 60) | ((turn > 0) & (aD < 200))] = 1                        # 추종·회전 준비
    t[(ped < 40) | (sig < 60) | (nl <= 1)] = 2                            # 보행자·신호·골목
    stop_d = v * 0.7 + v * v / 8.0                                        # 정지거리(m)
    t[(ped < np.maximum(8, stop_d)) | (gap < np.maximum(6, stop_d * 0.5))] = 3   # 정지거리 안 돌발
    return t

class TierNet(nn.Module):
    """수 레이어 초소형 CNN — 서브 밀리초 목표. 입력 해상도는 도메인별(오너 u_5445): 2D 64~128, 3D/실영상 128~224."""
    def __init__(self, n=4, res=64):
        super().__init__()
        self.res = res
        self.f = nn.Sequential(
            nn.AvgPool2d(max(1, 256 // res)),                  # 256→res
            nn.Conv2d(3, 16, 5, 2, 2), nn.ReLU(), nn.Conv2d(16, 32, 3, 2, 1), nn.ReLU(),
            nn.Conv2d(32, 64, 3, 2, 1), nn.ReLU(), nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(64, n))
    def forward(self, x): return self.f(x)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('dirs'); ap.add_argument('out'); ap.add_argument('--epochs', type=int, default=15); ap.add_argument('--res', type=int, default=64)
    a = ap.parse_args()
    Xs, Ts = [], []
    for d in [d for p in a.dirs.split(',') for d in sorted(glob.glob(p))]:
        try: X = np.load(f'{d}/X.npy'); Y = np.load(f'{d}/Y.npy'); M = np.load(f'{d}/M.npy')
        except Exception: continue
        if not (len(X) == len(M) == len(Y)): continue
        if X.ndim != 4 or X.shape[1] != 3: continue   # 프레임 스택 평가 라운드(6ch) 제외(2026-09-22)
        Xs.append(X); Ts.append(tier_labels(M, Y))
    if not Xs: print(json.dumps({'error': 'no data'})); return
    X = np.concatenate(Xs); T = np.concatenate(Ts); n = len(X)
    dist = {int(k): int(v) for k, v in zip(*np.unique(T, return_counts=True))}
    print(json.dumps({'frames': n, 'tier_dist': dist, 'res': a.res}), flush=True)
    rng = np.random.default_rng(0); idx = rng.permutation(n); cut = int(n * 0.85); tr, va = idx[:cut], idx[cut:]
    net = TierNet(res=a.res).to(DEV); gpu_guard.assert_on_gpu(net)
    # 클래스 불균형: 희소 등급(T2·T3) 가중 — 놓치면 위험한 쪽을 더 벌한다
    w = torch.tensor([1.0 / max(1, dist.get(k, 1)) for k in range(4)], dtype=torch.float32); w = (w / w.sum() * 4).to(DEV)
    opt = torch.optim.Adam(net.parameters(), 1e-3); ce = nn.CrossEntropyLoss(weight=w)
    def batch(ids):
        xb = torch.from_numpy(np.ascontiguousarray(X[ids])).float().div_(255.).to(DEV); return xb, torch.from_numpy(T[ids]).to(DEV)
    best = -1.0
    for ep in range(a.epochs):
        net.train(); perm = rng.permutation(tr); tot = 0.0
        for i in range(0, len(perm), BS):
            xb, tb = batch(perm[i:i + BS]); opt.zero_grad(); l = ce(net(xb), tb); l.backward(); opt.step(); tot += l.item() * len(tb)
        net.eval(); P = []; C = []
        with torch.no_grad():
            for i in range(0, len(va), BS):
                o = torch.softmax(net(batch(va[i:i + BS])[0]), 1); c, p = o.max(1); P.append(p.cpu().numpy()); C.append(c.cpu().numpy())
        P = np.concatenate(P); C = np.concatenate(C); tv = T[va]
        acc = float((P == tv).mean())
        rec = {k: (float((P[tv == k] == k).mean()) if (tv == k).any() else None) for k in range(4)}
        # 안전 방향 보정: 확신도 < 0.6 이면 한 등급 올림 → 어려운 등급 재현율이 오르는지
        P2 = np.where(C < 0.6, np.minimum(3, P + 1), P); rec2 = {k: (float((P2[tv == k] == k).mean()) if (tv == k).any() else None) for k in range(4)}
        hard = [r for k, r in rec.items() if k >= 2 and r is not None]; score = float(np.mean(hard)) if hard else acc
        if score > best: best = score; torch.save(net.state_dict(), a.out)
        print(json.dumps({'ep': ep, 'loss': round(tot / len(perm), 4), 'acc': round(acc, 3), 'recall': {k: (round(v, 3) if v is not None else None) for k, v in rec.items()},
                          'recall_conf_up': {k: (round(v, 3) if v is not None else None) for k, v in rec2.items()}}), flush=True)
    print(json.dumps({'done': a.out, 'best_hard_recall': round(best, 3), 'res': a.res}), flush=True)

if __name__ == '__main__':
    main()
