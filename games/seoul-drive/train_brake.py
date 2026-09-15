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
import json, os, sys, glob
import numpy as np, torch, torch.nn as nn
from net import DriveNet
import gpu_guard

DEV = gpu_guard.require_gpu()
BS = 128


def batch(X, Y, ids, AUX=None):
    real = np.abs(ids) - 1
    xb = torch.from_numpy(np.ascontiguousarray(X[real])).float().div_(255.)
    yb = Y[real].copy()
    flip = ids < 0
    if flip.any():
        xb[flip] = torch.flip(xb[flip], dims=[3])
        yb[flip, 0] *= -1
    out = [xb.to(DEV), torch.from_numpy(yb).to(DEV)]
    if AUX is not None:
        out.append(torch.from_numpy(AUX[real].copy()).to(DEV))
    return out


def main(dirs, out, epochs=30):
    X = np.concatenate([np.load(f'{d}/X.npy') for d in dirs])
    _ys = [np.load(f'{d}/Y.npy') for d in dirs]
    _w = max(y.shape[1] for y in _ys)
    _ys = [y if y.shape[1] == _w else
           np.hstack([y, np.full((len(y), _w - y.shape[1]), -1.0, y.dtype)])
           for y in _ys]                      # 옛 라운드는 5열이 없다 → -1(없음)로 채운다
    Yall = np.concatenate(_ys).astype(np.float32)
    Y = Yall[:, :3]

    # ★u_5171 보조목표: lane_off(차로 중심 이탈량).
    #   사고의 77%가 도로 경계 이탈(건물27·인도25·도로12·차로13%)인데, 라벨이
    #   steer/thr/brake 뿐이라 '도로 위에 있어야 한다'를 한 번도 안 가르쳤다.
    #   같이 맞히게 하면 특징추출부가 도로 경계를 표현하도록 강제된다.
    #   추론 때는 앞 3개만 쓰므로 비용은 0에 가깝다(net.py 설계 의도).
    SPD = Yall[:, 3] if Yall.shape[1] > 3 else None
    AUX = None
    if Yall.shape[1] > 4:
        lo = Yall[:, 4]
        have = lo >= 0                        # -1 = 그 라운드엔 값이 없음
        if have.mean() > 0.2:
            AUX = np.clip(lo / 3.25, 0, 2.0).astype(np.float32)   # 차로폭으로 정규화
            AUX[~have] = -1.0
            print(json.dumps({'aux_lane_off_pct': round(100*float(have.mean()), 1)}),
                  flush=True)

    # ★u_5171 핵심 수정: '이미 서 있는데 계속 밟는' 프레임을 버린다.
    #   실측 — 수집 프레임의 58%가 v<0.5(정지)였다. 서 있는 그림이 데이터의
    #   절반을 넘으면 가중치를 어떻게 만져도 '서 있기'를 배운다(12배→4배로
    #   낮췄더니 정지 에피소드가 25%→50%로 오히려 늘었다).
    #   단, '달리다 서는' 제동은 반드시 배워야 하므로 그건 남긴다.
    #   판별: 정지 상태(v<0.5)인데 교사도 제동을 요구 → 버린다.
    #         정지 상태인데 교사가 출발하라고 함(제동<0.5) → 남긴다(출발 학습).
    if Yall.shape[1] > 3:
        v = Yall[:, 3]
        drop = (v < 0.5) & (Y[:, 2] > 0.5)
        keep = ~drop
        print(json.dumps({'dropped_idle_brake': int(drop.sum()),
                          'kept': int(keep.sum())}), flush=True)
        X, Y = X[keep], Y[keep]
        SPD = v[keep]
        if AUX is not None: AUX = AUX[keep]
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
    w = np.ones(n); w[brake] = float(os.environ.get('BRAKE_W','4.0'))
    # ★u_5171: 저속 복구 구간이 데이터를 지배하는 것도 막는다.
    #   r121 실측 — 속도 0~2 구간이 2045프레임(전체의 45%)이고 그 구간의
    #   조향 포화가 57%로 가장 높다. 사고 직후 기어나오는 장면이 데이터의
    #   절반이면 모델은 '기어가기'를 배운다(v6 가 정확히 그랬다: 180초 225m).
    #   버리지 않는다 — 복구는 배워야 한다. 비중만 낮춘다(SLOW_W, 기본 1.0=무효).
    _sw = float(os.environ.get('SLOW_W', '1.0'))
    if SPD is not None and _sw != 1.0:
        slow = (SPD < 2.0) & (~brake)          # 제동 프레임은 위에서 이미 다뤘다
        w[slow] *= _sw
        print(json.dumps({'slow_frames_pct': round(100*float(slow.mean()), 1),
                          'slow_w': _sw}), flush=True)
    Wtr = w[np.abs(tr) - 1]; Wtr = Wtr / Wtr.sum()

    net = DriveNet(out=3 if AUX is None else 4).to(DEV)
    opt = torch.optim.Adam(net.parameters(), 1e-3, weight_decay=1e-4)
    # 희소 클래스 보정. 오버샘플링 후의 실효 비율 기준으로 잡는다.
    pw = torch.tensor([float(os.environ.get('POS_W','3.0'))], device=DEV)
    bce = nn.BCEWithLogitsLoss(pos_weight=pw)
    mse = nn.MSELoss(reduction='none')
    best = 1e9

    def compute(xb, yb, ab=None):
        # ★raw 로짓으로 받는다. 추론의 tanh/sigmoid 와 학습 손실이 어긋나면
        #   학습은 로짓을 올리는데 활성화가 반대로 눌러버린다(실사고: 제동 -0.846).
        o = net(xb, raw=True)
        l_st = mse(torch.tanh(o[:, 0]), yb[:, 0]).mean()
        # 스로틀: 제동 프레임에서 5배 — 제동만 밟고 스로틀을 안 떼면 소용없다
        wt = torch.where(yb[:, 2] > 0.5, 5.0, 1.0)
        l_th = (mse(torch.sigmoid(o[:, 1]), yb[:, 1]) * wt).mean()
        # 제동: 이진 결정으로 학습(로짓 그대로 BCE)
        l_br = bce(o[:, 2], (yb[:, 2] > 0.5).float())
        loss = l_st + l_th + l_br
        # 보조목표: 차로 중심 이탈량. -1 은 '값 없음'이라 손실에서 뺀다.
        if ab is not None and o.shape[1] > 3:
            m = ab >= 0
            if m.any():
                loss = loss + 0.3 * mse(torch.sigmoid(o[:, 3]) * 2.0, ab)[m].mean()
        return loss

    for ep in range(int(epochs)):
        net.train()
        perm = np.random.choice(tr, size=len(tr), replace=True, p=Wtr)
        tot = 0.0
        for i in range(0, len(perm), BS):
            b = perm[i:i+BS]
            bb = batch(X, Y, b, AUX)
            opt.zero_grad(); l = compute(*bb); l.backward(); opt.step()
            tot += l.item() * len(b)
        net.eval(); vs = 0.0; cnt = 0
        with torch.no_grad():
            for i in range(0, len(va), BS):
                b = va[i:i+BS]
                vs += compute(*batch(X, Y, b, AUX)).item() * len(b); cnt += len(b)
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
