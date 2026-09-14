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

def batch(X, Y, ids):
    """ids 가 음수면 '좌우반전본'을 뜻한다(복사 없이 표현)."""
    real = np.abs(ids) - 1
    xb = torch.from_numpy(np.ascontiguousarray(X[real])).float().div_(255.)
    yb = Y[real].copy()
    flip = ids < 0
    if flip.any():
        xb[flip] = torch.flip(xb[flip], dims=[3])
        yb[flip, 0] *= -1
    return xb.to(DEV), torch.from_numpy(yb).to(DEV)

def main(d, out, epochs=25):
    X = np.load(f'{d}/X.npy', mmap_mode='r')
    Yr = np.load(f'{d}/Y.npy')
    Y = np.stack([Yr[:,0], Yr[:,1], Yr[:,2]], 1).astype(np.float32)   # steer,thr,brake
    n = len(X)
    idx = np.random.permutation(n); cut = int(n*0.85)
    tr_r, va_r = idx[:cut], idx[cut:]
    # +1 오프셋: 0 은 부호가 없어 반전 표현이 불가능하므로 1-based 로 쓴다
    tr = np.concatenate([tr_r + 1, -(tr_r + 1)])
    va = np.concatenate([va_r + 1, -(va_r + 1)])
    net = DriveNet().to(DEV)
    opt = torch.optim.Adam(net.parameters(), 1e-3, weight_decay=1e-4)
    lossf = nn.MSELoss()
    best = 1e9
    for ep in range(int(epochs)):
        net.train(); perm = np.random.permutation(tr); tot = 0.0
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
