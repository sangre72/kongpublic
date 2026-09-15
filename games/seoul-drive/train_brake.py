#!/usr/bin/env python3
"""오드 재학습 — 제동 채널을 실제로 배우게 한다.

왜 새로 짜나(u_5170 실측):
  ode_dag1.pt 는 교사가 완전정지를 지시한 프레임에서 제동 0.104 만 냈다.
  제동 재현율 2%. 앞차를 보고도 100% 가속해서 박는다 → 추돌이 사고 1위.

bc_train2.py 의 오버샘플링(20배)만으로는 부족했다. 이유:
  1) 제동은 회귀가 아니라 사실상 '밟는다/안 밟는다' 결정이다.
     MSE 는 0.1 을 내도 손실이 작아서, 애매한 값으로 수렴한다.
  2) 스로틀이 같이 안 내려간다. 제동 1.0 + 스로틀 0.47 은 안 선다.
     game.js 의 제동 게이트가 brake > thr + 0.1 을 요구하기 때문에
     스로틀을 못 내리면 제동 자체가 무시된다.

조치:
  · 제동 채널만 BCE(이진분류) — 애매한 중간값에 큰 벌점.
  · 제동 프레임의 스로틀 오차에 가중치(스로틀도 같이 0 으로 내려야 한다).
  · pos_weight 로 희소 클래스 보정(오버샘플링과 병행).
"""
import json, sys, glob
import numpy as np, torch, torch.nn as nn
from net import DriveNet
import gpu_guard

DEV = gpu_guard.require_gpu()
BS = 128


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
    X = np.concatenate([np.load(f'{d}/X.npy') for d in dirs])
    Y = np.concatenate([np.load(f'{d}/Y.npy') for d in dirs])[:, :3].astype(np.float32)
    n = len(X)
    brake = Y[:, 2] > 0.5
    pos = float(brake.mean())
    print(json.dumps({'frames': n, 'brake_pct': round(100 * pos, 2)}), flush=True)

    idx = np.random.permutation(n); cut = int(n * 0.85)
    tr_r, va_r = idx[:cut], idx[cut:]
    tr = np.concatenate([tr_r + 1, -(tr_r + 1)])
    va = np.concatenate([va_r + 1, -(va_r + 1)])

    # 오버샘플링: 제동 프레임을 자주 보여준다.
    # ★u_5171 실사고: 12배 + pos_weight 를 같이 걸었더니 오드가 '안 움직이면
    #   안 박는다'를 배웠다. 90초 내내 사고 0건인데 진행률 0.001 인 에피소드가
    #   12개 중 3개. 서 있으니 앞차가 계속 앞에 있고, 교사는 정당하게 '서라'고
    #   라벨한다 → 그걸로 또 학습하면 더 선다(자기강화). 교사 제동요구가
    #   7.0% → 28.2% 로 4배 뛴 게 그 증거다.
    #   ⇒ 가중치를 4배로 낮추고, '정지 상태에서의 제동' 프레임은 제외한다.
    #     움직이다 서는 건 배워야 하지만, 이미 선 채로 계속 밟는 건 배우면 안 된다.
    w = np.ones(n); w[brake] = 4.0
    Wtr = w[np.abs(tr) - 1]; Wtr = Wtr / Wtr.sum()

    net = DriveNet(out=3).to(DEV)
    opt = torch.optim.Adam(net.parameters(), 1e-3, weight_decay=1e-4)
    # 희소 클래스 보정. 오버샘플링 후의 실효 비율 기준으로 잡는다.
    pw = torch.tensor([min(3.0, (1 - pos) / max(pos, 1e-3) / 4.0)], device=DEV)
    bce = nn.BCEWithLogitsLoss(pos_weight=pw)
    mse = nn.MSELoss(reduction='none')
    best = 1e9

    def compute(xb, yb):
        # ★raw 로짓으로 받는다. 추론의 tanh/sigmoid 와 학습 손실이 어긋나면
        #   학습은 로짓을 올리는데 활성화가 반대로 눌러버린다(실사고: 제동 -0.846).
        o = net(xb, raw=True)
        l_st = mse(torch.tanh(o[:, 0]), yb[:, 0]).mean()
        # 스로틀: 제동 프레임에서 5배 — 제동만 밟고 스로틀을 안 떼면 소용없다
        wt = torch.where(yb[:, 2] > 0.5, 5.0, 1.0)
        l_th = (mse(torch.sigmoid(o[:, 1]), yb[:, 1]) * wt).mean()
        # 제동: 이진 결정으로 학습(로짓 그대로 BCE)
        l_br = bce(o[:, 2], (yb[:, 2] > 0.5).float())
        return l_st + l_th + l_br

    for ep in range(int(epochs)):
        net.train()
        perm = np.random.choice(tr, size=len(tr), replace=True, p=Wtr)
        tot = 0.0
        for i in range(0, len(perm), BS):
            b = perm[i:i+BS]; xb, yb = batch(X, Y, b)
            opt.zero_grad(); l = compute(xb, yb); l.backward(); opt.step()
            tot += l.item() * len(b)
        net.eval(); vs = 0.0; cnt = 0
        with torch.no_grad():
            for i in range(0, len(va), BS):
                b = va[i:i+BS]; xb, yb = batch(X, Y, b)
                vs += compute(xb, yb).item() * len(b); cnt += len(b)
        vl = vs / cnt
        if vl < best:
            best = vl; torch.save(net.state_dict(), out)
        print(json.dumps({'ep': ep, 'train': round(tot/len(perm), 5),
                          'val': round(vl, 5)}), flush=True)

    # ★검증: 제동 재현율. val loss 가 낮아도 제동을 못 밟으면 실패다.
    net.load_state_dict(torch.load(out, map_location=DEV)); net.eval()
    P = []
    with torch.no_grad():
        for i in range(0, len(X), 256):
            xb = torch.from_numpy(np.ascontiguousarray(X[i:i+256])).float().div_(255.).to(DEV)
            P.append(net(xb).cpu().numpy())      # 추론 경로 그대로
    P = np.concatenate(P)
    m = brake
    print(json.dumps({
        'brake_recall_pct': round(100 * float((P[m, 2] > 0.5).mean()), 1),
        'brake_pred_on': round(float(P[m, 2].mean()), 3),
        'brake_pred_off': round(float(P[~m, 2].mean()), 3),
        'thr_on_brake': round(float(P[m, 1].mean()), 3),
    }), flush=True)


if __name__ == '__main__':
    dirs = sorted(glob.glob('data/dagger_r9*')) if len(sys.argv) < 2 else sys.argv[1].split(',')
    main(dirs, sys.argv[2] if len(sys.argv) > 2 else 'ode_brake.pt')
