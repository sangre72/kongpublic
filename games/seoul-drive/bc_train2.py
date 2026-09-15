"""행동복제(BC) 학습 v2 — 메모리 안전판 (2026-09-14 u_4969).

★왜 새로 쓰나: bc_train.py 는 X 전체를 float32 텐서로 올린 뒤 좌우반전본을
  concat 한다. 11,718프레임 × 3×256×256 이면 float32 만 9GB, 반전본까지 18GB로
  터진다(예전 데이터는 수백~수천 프레임이라 문제가 안 됐다).
  여기서는 X 를 uint8 mmap 으로 두고 배치 단위로만 float 변환한다.
  반전도 인덱스로 표현해서(복사 없음) 메모리를 쓰지 않는다.

★검증 규칙은 그대로 유지(bc_train.py 주석 참고):
  - 좌우반전은 train/val 양쪽에 적용한다. 교사가 좌회전 위주라 원본 검증셋은
    편향돼 있고, 그걸로 재면 '무조건 좌회전' 모델도 점수가 잘 나온다.
  - 반드시 '평균만 찍는 모델' 대비 개선율로 판정한다(LEARNED/COLLAPSED).

사용: python3 bc_train2.py <data_dir> <out.pt> [epochs]
"""
import sys, os, json, time
import numpy as np, torch, torch.nn as nn
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from net import DriveNet

DEV = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
BS = 64

def sample_weights(Y):
    """★급제동 프레임 가중치 상향 (u_4980 (b)).

    실측 문제: 42,716프레임 중 brake>0.5 가 77개(0.18%)뿐이라, 평균제곱오차를
    그냥 최소화하면 '브레이크는 거의 안 밟는다'가 최적해가 된다. 실제로 학습된
    모델이 실제 0.98 자리에 0.53 을 냈다(상황 인식은 하는데 덜 밟음).
    → 제동 프레임을 뽑을 확률을 올려 손실에서 차지하는 비중을 키운다.
      데이터를 조작하는 게 아니라 '자주 보여주는' 것이다(오버샘플링).
    """
    b = Y[:, 2]
    w = np.ones(len(b), np.float64)
    w[b > 0.35] = 6.0        # 감속
    w[b > 0.7]  = 20.0       # 급제동 — 드물지만 제일 중요
    return w / w.sum()


def batch(X, Y, ids):
    """ids 가 음수면 '좌우반전본'을 뜻한다(복사 없이 표현)."""
    real = np.abs(ids) - 1
    xb = torch.from_numpy(np.ascontiguousarray(X[real])).float().div_(255.)
    yb = Y[real].copy()
    flip = ids < 0
    if flip.any():
        xb[flip] = torch.flip(xb[flip], dims=[3])
        yb[flip, 0] *= -1
        # 도로 경계 보조목표: 좌우반전하면 중심선 기준 반대편이 된다
        if yb.shape[1] > 3:
            yb[flip, 3] = 1.0 - yb[flip, 3]
    return xb.to(DEV), torch.from_numpy(yb).to(DEV)

def main(d, out, epochs=25):
    X = np.load(f'{d}/X.npy', mmap_mode='r')
    Yr = np.load(f'{d}/Y.npy')
    """★도로 인식을 보조목표로 넣는다(u_5035 오너 지시).

    오너: "중요한 건 도로만, 도로로 인식할 수 있는 것만 주행하면 문제없는 것 아닌가".
    맞는 정리다. 인도/건물을 따로 구분할 필요가 없다 — '도로인가 아닌가'만 있으면 된다.

    ★왜 지금까지 못 배웠나(실측): M.npy 의 on_road 평균이 1.00 이다. 85,768프레임
      전부 도로 위다. 반례가 하나도 없으니 '도로를 벗어나면 안 된다'는 학습 자체가
      불가능했다. 라벨도 steer/thr/brake/rev 뿐이라 도로에 관한 신호가 없었다.

    ★해결: 반례를 만드는 대신, '도로 경계까지 남은 거리'를 같이 맞히게 한다.
      그러면 특징추출부가 도로 경계를 표현하도록 강제된다(auxiliary task).
      lane(중심선까지 거리)은 이미 M.npy 에 있다 — 실측 0.84~7.83m.
      좌우반전하면 부호가 뒤집히므로 중심 기준 정규화해서 넣는다.
    """
    Y = np.stack([Yr[:,0], Yr[:,1], Yr[:,2]], 1).astype(np.float32)   # steer,thr,brake
    try:
        M = np.load(f'{d}/M.npy', mmap_mode='r')
        lane = np.asarray(M[:, 1], np.float32)
        # 중심선 거리 → -1~1 (도로 반폭 7m 기준). 반전 시 부호가 뒤집히는 양이다.
        laneN = np.clip(lane / 7.0, 0, 1).astype(np.float32)
        Y = np.concatenate([Y, laneN[:, None]], 1)
        print(f'[aux] road-boundary target on: lane {lane.min():.2f}~{lane.max():.2f}m')
    except Exception as e:
        print('[aux] lane target unavailable:', e)
    n = len(X)
    idx = np.random.permutation(n); cut = int(n*0.85)
    tr_r, va_r = idx[:cut], idx[cut:]
    # +1 오프셋: 0 은 부호가 없어 반전 표현이 불가능하므로 1-based 로 쓴다
    tr = np.concatenate([tr_r + 1, -(tr_r + 1)])
    va = np.concatenate([va_r + 1, -(va_r + 1)])
    net = DriveNet(out=Y.shape[1]).to(DEV)
    opt = torch.optim.Adam(net.parameters(), 1e-3, weight_decay=1e-4)
    lossf = nn.MSELoss()
    best = 1e9
    W = sample_weights(Y)
    Wtr = W[np.abs(tr) - 1]; Wtr = Wtr / Wtr.sum()
    for ep in range(int(epochs)):
        net.train()
        # 가중 복원추출: 급제동 프레임이 에폭마다 더 자주 등장한다
        perm = np.random.choice(tr, size=len(tr), replace=True, p=Wtr)
        tot = 0.0
        for i in range(0, len(perm), BS):
            b = perm[i:i+BS]
            xb, yb = batch(X, Y, b)
            opt.zero_grad(); l = lossf(net(xb), yb); l.backward(); opt.step()
            tot += l.item()*len(b)
        net.eval(); vs = 0.0; cnt = 0
        with torch.no_grad():
            for i in range(0, len(va), BS):
                b = va[i:i+BS]; xb, yb = batch(X, Y, b)
                vs += lossf(net(xb), yb).item()*len(b); cnt += len(b)
        vl = vs/cnt
        if vl < best:
            best = vl; torch.save(net.state_dict(), out)
        print(json.dumps({'ep':ep,'train':round(tot/len(perm),5),'val':round(vl,5)}), flush=True)
    # 평균 예측 baseline 과 비교 — val loss 가 낮아도 상수만 뱉으면 실패다
    net.load_state_dict(torch.load(out, map_location=DEV)); net.eval()
    P, T = [], []
    with torch.no_grad():
        for i in range(0, len(va), BS):
            b = va[i:i+BS]; xb, yb = batch(X, Y, b)
            P.append(net(xb).cpu().numpy()); T.append(yb.cpu().numpy())
    P = np.concatenate(P); T = np.concatenate(T)
    mse_m = float(((P-T)**2).mean())
    mse_b = float(((T.mean(0)-T)**2).mean())
    imp = (1-mse_m/mse_b)*100
    print(json.dumps({'done':True,
        'params':sum(q.numel() for q in net.parameters()),
        'n':n, 'best_val':round(best,5),
        'mse_model':round(mse_m,5), 'mse_mean_baseline':round(mse_b,5),
        'improve_pct':round(imp,1),
        'verdict':'LEARNED' if imp>15 else 'COLLAPSED',
        'steer_pred_std':round(float(P[:,0].std()),3),
        'model':out}))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv)>3 else 25)
