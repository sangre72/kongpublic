"""행동복제(BC) 학습 — 화면 픽셀 → 조작.  (2026-09-14)

교사는 자료를 만드는 도구일 뿐이고, 최종 주행은 이 신경망이 화면만 보고 한다.
GPU(MPS) 사용. 규칙 기반 특징(광선·바닥색) 일절 없음.

사용: python3 bc_train.py data.npz model.pt [epochs]
"""
import sys, json, time, os
import numpy as np, torch, torch.nn as nn
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from net import DriveNet

DEV = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')


def main(npz, out, epochs=40):
    d = np.load(npz)
    X = torch.tensor(d['X'].astype(np.float32))
    Yr = d['Y']                                   # steer, thr, brake, rev
    Y = torch.tensor(np.stack([Yr[:,0], Yr[:,1], Yr[:,2]], 1).astype(np.float32))
    n = len(X); idx = np.random.permutation(n); cut = int(n*0.85)
    tr, va = idx[:cut], idx[cut:]
    # ★1차 학습 실패 대응(2026-09-14): 모델이 모든 화면에 조향 -0.63 한 값만 뱉었다
    #   (평균 예측 대비 개선 0.2%). 표본이 적고 연속 프레임이라 거의 같은 그림이어서다.
    #   좌우 반전 증강으로 표본을 2배 늘리고 조향 대칭성도 같이 가르친다.
    #   ★검증셋도 같이 뒤집어야 한다(2026-09-14 발견). 교사가 좌회전 위주로 달려서
    #     원본 데이터가 좌 61% / 우 3.3%(평균 조향 -0.458)로 심하게 치우쳐 있었고,
    #     치우친 검증셋으로 재면 '무조건 좌회전' 모델도 점수가 잘 나온다(개선 63.8%로 부풀려짐).
    #     좌우 대칭 검증셋에서 재야 진짜 실력이 나온다.
    Xf = torch.flip(X, dims=[3]); Yf = Y.clone(); Yf[:, 0] *= -1
    X = torch.cat([X, Xf]); Y = torch.cat([Y, Yf])
    tr = np.concatenate([tr, n + tr]); va = np.concatenate([va, n + va])
    net = DriveNet().to(DEV)
    opt = torch.optim.Adam(net.parameters(), 1e-3, weight_decay=1e-4)
    lossf = nn.MSELoss()
    best = 1e9
    for ep in range(int(epochs)):
        net.train(); perm = np.random.permutation(tr)
        tot = 0
        for i in range(0, len(perm), 64):
            b = perm[i:i+64]
            xb, yb = X[b].to(DEV), Y[b].to(DEV)
            opt.zero_grad(); l = lossf(net(xb), yb); l.backward(); opt.step()
            tot += l.item()*len(b)
        net.eval()
        with torch.no_grad():
            vl = lossf(net(X[va].to(DEV)), Y[va].to(DEV)).item()
        if vl < best:
            best = vl; torch.save(net.state_dict(), out)
        print(json.dumps({'ep':ep,'train':round(tot/len(perm),5),'val':round(vl,5)}), flush=True)
    # ★반드시 '평균만 찍는 모델'과 비교한다. val loss 가 낮아도 상수만 뱉으면 실패다
    #   (1차 학습이 정확히 그랬다 — 수렴했지만 개선 0.2%).
    net.load_state_dict(torch.load(out, map_location=DEV)); net.eval()
    with torch.no_grad():
        P = net(X[va].to(DEV)).cpu().numpy()
    Yv = Y[va].numpy()
    mse_m = float(((P - Yv) ** 2).mean())
    mse_b = float(((Yv.mean(0) - Yv) ** 2).mean())
    p = sum(q.numel() for q in net.parameters())
    print(json.dumps({'done':True,'params':p,'best_val':round(best,5),'model':out,'n':n,
                      'mse_model':round(mse_m,5),'mse_mean_baseline':round(mse_b,5),
                      'improve_pct':round((1-mse_m/mse_b)*100,1),
                      'pred_steer_std':round(float(P[:,0].std()),4),
                      'VERDICT':('LEARNED' if (1-mse_m/mse_b)>0.15 and P[:,0].std()>0.05
                                 else 'COLLAPSED/INSUFFICIENT')}))

if __name__ == '__main__':
    main(*sys.argv[1:4])
