#!/usr/bin/env python3
"""오드 1단계: 직진만 먼저 가르친다 (u_5172 오너 지시 "직진부터 가능하게해").

★왜 단계를 나누나:
  지금까지는 추월·회피·코너를 한꺼번에 섞어 학습시켰고, 그 결과 어느 것도
  제대로 못 한다. 실측 — 교사 라벨의 직진 비율이 3~15% 뿐이라 '곧게 가기'를
  보여준 적이 거의 없다. 기본이 안 되면 그 위에 아무것도 못 쌓는다.

★어떻게:
  곧은 구간 프레임만 뽑아 학습한다. 코너·교차로는 2단계로 미룬다.
  판별은 교사 조향의 5프레임 이동평균이 작은 곳 — 한 순간 작은 게 아니라
  '작은 상태가 이어지는' 곳이어야 진짜 직선이다.

★평가도 직진으로:
  전체 주행거리가 아니라 '곧은 구간에서 차로를 유지하며 간 거리'를 본다.

사용: python3 train_straight.py <데이터디렉토리,쉼표구분> <출력.pt>
"""
import json, os, sys, glob
import numpy as np, torch, torch.nn as nn
from net import DriveNet
import gpu_guard

DEV = gpu_guard.require_gpu()
BS = 128


def straight_mask(Y, win=5, thr_avg=0.25, thr_now=0.30):
    """곧은 구간 판별. 이동평균으로 '이어지는' 직선만 잡는다."""
    s = np.abs(Y[:, 0])
    sm = np.convolve(s, np.ones(win) / win, 'same')
    return (sm < thr_avg) & (s < thr_now)


def batch(X, Y, ids):
    real = np.abs(ids) - 1
    xb = torch.from_numpy(np.ascontiguousarray(X[real])).float().div_(255.)
    yb = Y[real].copy()
    flip = ids < 0
    if flip.any():
        xb[flip] = torch.flip(xb[flip], dims=[3])
        yb[flip, 0] *= -1
    return xb.to(DEV), torch.from_numpy(yb).to(DEV)


def main(dirs, out, epochs=30):
    Xs, Ys = [], []
    for d in dirs:
        try:
            X = np.load(f'{d}/X.npy'); Y = np.load(f'{d}/Y.npy')[:, :3].astype(np.float32)
        except Exception:
            continue
        m = straight_mask(Y)
        if m.sum() < 20:
            continue
        Xs.append(X[m]); Ys.append(Y[m])
        print(json.dumps({'dir': d.split('/')[-1], 'total': len(Y),
                          'straight': int(m.sum())}), flush=True)
    if not Xs:
        print(json.dumps({'error': 'no straight frames'}), flush=True); return
    X = np.concatenate(Xs); Y = np.concatenate(Ys)
    n = len(X)
    print(json.dumps({'frames': n,
                      'steer_std': round(float(Y[:, 0].std()), 4),
                      'thr_mean': round(float(Y[:, 1].mean()), 3)}), flush=True)
    if n < 200:
        print(json.dumps({'warn': 'too few straight frames — collect more first'}),
              flush=True)

    idx = np.random.permutation(n); cut = int(n * 0.85)
    tr = np.concatenate([idx[:cut] + 1, -(idx[:cut] + 1)])
    va = np.concatenate([idx[cut:] + 1, -(idx[cut:] + 1)])

    net = DriveNet(out=3).to(DEV)
    gpu_guard.assert_on_gpu(net)
    opt = torch.optim.Adam(net.parameters(), 1e-3, weight_decay=1e-4)
    mse = nn.MSELoss()
    best = 1e9
    for ep in range(epochs):
        net.train(); tot = 0.0
        perm = np.random.permutation(tr)
        for i in range(0, len(perm), BS):
            xb, yb = batch(X, Y, perm[i:i+BS])
            opt.zero_grad()
            o = net(xb)
            l = mse(o, yb)
            # ★u_5172 오너 지적 "경로선은 직선인데 차는 우측으로 커브".
            #   실측: 오드 조향이 100% 양수(평균 +0.046). 학습 데이터는
            #   좌우 균형(양45%/음46%)인데 모델만 편향돼 있었다.
            #   원인은 출력 bias(+0.047) — 회색·흰색 같은 무의미한 입력에도
            #   조향 +0.05 가 나온다. 직진 구간은 시각 단서가 약해 모델이
            #   bias 쪽으로 수렴하고, 작은 값이 누적돼 완만한 우회전이 된다.
            #   ⇒ 좌우 대칭을 손실로 강제한다: 뒤집은 그림의 조향은
            #     원본의 부호 반대여야 한다. 대칭이면 bias 는 0 으로 밀린다.
            xf = torch.flip(xb, dims=[3])
            of = net(xf)
            l = l + 0.5 * ((o[:, 0] + of[:, 0]) ** 2).mean()
            l.backward(); opt.step()
            tot += l.item() * len(perm[i:i+BS])
        net.eval(); vs = 0.0; c = 0
        with torch.no_grad():
            for i in range(0, len(va), BS):
                xb, yb = batch(X, Y, va[i:i+BS])
                vs += mse(net(xb), yb).item() * len(va[i:i+BS]); c += len(va[i:i+BS])
        vl = vs / c
        if vl < best:
            best = vl; torch.save(net.state_dict(), out)
        print(json.dumps({'ep': ep, 'train': round(tot/len(perm), 5),
                          'val': round(vl, 5)}), flush=True)

    # ★검증: 직진 상황에서 조향이 실제로 작은가. loss 가 낮아도 흔들면 실패다.
    net.load_state_dict(torch.load(out, map_location=DEV)); net.eval()
    P = []
    with torch.no_grad():
        for i in range(0, n, 256):
            xb = torch.from_numpy(np.ascontiguousarray(X[i:i+256])).float().div_(255.).to(DEV)
            P.append(net(xb).cpu().numpy())
    P = np.concatenate(P)
    print(json.dumps({
        'pred_steer_abs_mean': round(float(np.abs(P[:, 0]).mean()), 4),
        'label_steer_abs_mean': round(float(np.abs(Y[:, 0]).mean()), 4),
        'pred_over_0.3_pct': round(100 * float((np.abs(P[:, 0]) > 0.3).mean()), 1),
        'thr_mean': round(float(P[:, 1].mean()), 3),
        # ★편향 확인: 양수 비율이 50% 에서 크게 벗어나면 한쪽으로만 꺾는다
        'pred_positive_pct': round(100 * float((P[:, 0] > 0).mean()), 1),
        'pred_steer_mean': round(float(P[:, 0].mean()), 4),
    }), flush=True)


if __name__ == '__main__':
    dirs = (sys.argv[1].split(',') if len(sys.argv) > 1
            else sorted(glob.glob('data/dagger_r*')))
    main(dirs, sys.argv[2] if len(sys.argv) > 2 else 'ode_straight.pt')
