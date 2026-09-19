#!/usr/bin/env python3
"""오드 커리큘럼(단계별) 학습 — 오너 u_5427 "레이어를 쌓듯이 난이도에 따라 단계별로".

★단계(stage)와 프레임 선별 기준(M.npy 상황 태그, dagger.py 가 프레임마다 저장):
   M = [gap(앞차 m), ped(보행자 m), sig(적신호 m), turn(0 S/1 L/2 R/3 U), aD(회전까지 m), v, laneF, nl]
   straight : 직진·주변 자극 없음  (turn==0, gap>60, ped>40, sig>60)
   follow   : 앞차 추종·감속       (gap<40)
   ped      : 보행자 주의·정지     (ped<30)
   signal   : 신호 정지/출발       (sig<60)
   turn     : 좌·우회전            (turn∈{1,2}, aD<80)
   uturn    : 유턴                 (turn==3, aD<80)
★이전 단계 망각 방지: 이전 체크포인트(--init)에서 이어서 학습하고, 선별 밖 프레임을 REPLAY 비율만큼 섞는다.
★함정(ode-training-pitfalls): 정지 프레임을 증폭하지 않는다 — 선별만 하고 복제·가중 증폭은 없다.
★가중치 W.npy(u_5426, 사고 직전 3초=0)는 그대로 손실에 곱한다.

사용: python3 train_stage.py <stage> <데이터디렉토리,쉼표> <출력.pt> [--init 이전.pt] [--epochs 20] [--replay 0.2]
"""
import argparse, glob, json, os, sys
import numpy as np, torch, torch.nn as nn
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from net import DriveNet
import gpu_guard

DEV = gpu_guard.require_gpu()
BS = 128
STAGES = {
    # ★2026-09-20 실측: M[:,3](aTurn)은 '다음 회전 종류'라 회전 600m 전부터 L/R 로 찍힌다(전체 32,621 중 S=13,592).
    #   turn==0 만 직진으로 치면 4,323프레임(13%)뿐 → aD>150m 이면 직진 구간으로 본다(10,952프레임). 회전 준비 차로변경은 'turn' 단계.
    'straight': lambda M: ((M[:, 3] == 0) | (M[:, 4] > 150)) & (M[:, 0] > 60) & (M[:, 1] > 40) & (M[:, 2] > 60) & (M[:, 5] > 1.0),   # v>1: 정지 프레임은 '서 있기'를 가르친다(ode-training-pitfalls; r110 ep3 1.75% 진행)
    'follow':   lambda M: M[:, 0] < 40,
    'ped':      lambda M: M[:, 1] < 30,
    'signal':   lambda M: M[:, 2] < 60,
    'turn':     lambda M: ((M[:, 3] == 1) | (M[:, 3] == 2)) & (M[:, 4] < 80),
    'uturn':    lambda M: (M[:, 3] == 3) & (M[:, 4] < 80),
}

AUG = os.environ.get('AUG', '1') == '1'
def augment(xb):
    """도메인 랜덤화(오너 u_5439, 2026-09-19): 밝기·대비 지터, 가우시안 노이즈, 일부는 흑백 — 그래픽 스타일이 아니라
       도로/차선/장애물 형태에 반응하도록. 검증 배치에는 적용하지 않는다."""
    n = xb.shape[0]
    b = (torch.rand(n, 1, 1, 1, device=xb.device) - 0.5) * 0.4          # 밝기 ±0.2
    c = 1.0 + (torch.rand(n, 1, 1, 1, device=xb.device) - 0.5) * 0.6    # 대비 0.7~1.3
    m = xb.mean(dim=(1, 2, 3), keepdim=True)
    xb = (xb - m) * c + m + b
    xb = xb + torch.randn_like(xb) * 0.03
    g = torch.rand(n, device=xb.device) < 0.25                            # 25% 흑백
    if g.any():
        gray = xb[g].mean(dim=1, keepdim=True).expand(-1, 3, -1, -1)
        xb = xb.clone(); xb[g] = gray
    # u_5440: 채널별 색 지터(±0.05), 흐림(다운→업샘플, 30%), 가림 사각형(실차·표지판에 가려짐 흉내, 30%)
    xb = xb + (torch.rand(n, 3, 1, 1, device=xb.device) - 0.5) * 0.10
    bl = torch.rand(n, device=xb.device) < 0.30
    if bl.any():
        small = torch.nn.functional.interpolate(xb[bl], scale_factor=0.5, mode='bilinear', align_corners=False)
        xb = xb.clone(); xb[bl] = torch.nn.functional.interpolate(small, size=xb.shape[-2:], mode='bilinear', align_corners=False)
    oc = torch.rand(n, device=xb.device) < 0.30
    if oc.any():
        xb = xb.clone(); H, Wd = xb.shape[-2:]
        for i in torch.nonzero(oc).flatten().tolist():
            h = int(H * (0.08 + 0.17 * torch.rand(1).item())); w = int(Wd * (0.08 + 0.17 * torch.rand(1).item()))
            y0 = int(torch.randint(0, H - h, (1,)).item()); x0 = int(torch.randint(0, Wd - w, (1,)).item())
            xb[i, :, y0:y0 + h, x0:x0 + w] = torch.rand(1).item()
    return xb.clamp_(0, 1)

def batch(X, Y, ids, train=False):
    real = np.abs(ids) - 1
    xb = torch.from_numpy(np.ascontiguousarray(X[real])).float().div_(255.)
    yb = Y[real].copy()
    flip = ids < 0
    if flip.any():
        xb[flip] = torch.flip(xb[flip], dims=[3]); yb[flip, 0] *= -1
    xb = xb.to(DEV)
    if train and AUG: xb = augment(xb)
    return xb, torch.from_numpy(yb).to(DEV)

def load(dirs, stage, replay, rng, extra=()):
    """extra = DAgger 라운드(모델이 몰고 교사가 라벨) — 단계 필터를 거치지 않고 전 프레임(W 가중)을 넣는다.
       모델이 실제로 가는 상태(차선 이탈·복귀)의 정답이 핵심이라 상황 태그로 걸러내면 안 된다."""
    Xs, Ys, Ws, nsel, nrep = [], [], [], 0, 0
    extra = set(extra)
    for d in list(dirs) + [e for e in extra if e not in dirs]:
        try:
            X = np.load(f'{d}/X.npy'); Y = np.load(f'{d}/Y.npy')[:, :3].astype(np.float32); M = np.load(f'{d}/M.npy')
        except Exception as e:
            print(json.dumps({'skip': d, 'why': str(e)[:60]}), flush=True); continue
        try: W = np.load(f'{d}/W.npy').astype(np.float32)
        except Exception: W = np.ones(len(Y), np.float32)
        if not (len(M) == len(Y) == len(W)): print(json.dumps({'skip': d, 'why': 'len mismatch'})); continue
        # ★DAgger 라운드도 정지 프레임은 뺀다(2026-09-20 k=2 실측: r202 96% 가 v≈0·brake 라벨 → 다음 모델이 '서 있기'를 배움, 진행 0.6%).
        #   남기는 것: 차가 움직였거나(v>1) 교사가 '가라'(thr>0.3)고 한 프레임 — 출발·복귀 정답은 남고, 앞차 뒤 대기는 follow 단계 몫.
        sel = STAGES[stage](M) if d not in extra else ((M[:, 5] > 1.0) | (Y[:, 1] > 0.3))
        rest = np.where(~sel)[0]
        rep = rng.choice(rest, int(len(rest) * replay), replace=False) if len(rest) and replay > 0 else np.array([], int)
        idx = np.concatenate([np.where(sel)[0], rep])
        if len(idx) == 0: continue
        Xs.append(X[idx]); Ys.append(Y[idx]); Ws.append(W[idx]); nsel += int(sel.sum()); nrep += len(rep)
        print(json.dumps({'dir': d.split('/')[-1], 'total': len(Y), 'stage': int(sel.sum()), 'replay': len(rep), 'extra': int(d in extra)}), flush=True)
    if not Xs: return None
    return np.concatenate(Xs), np.concatenate(Ys), np.concatenate(Ws), nsel, nrep

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('stage', choices=sorted(STAGES)); ap.add_argument('dirs'); ap.add_argument('out')
    ap.add_argument('--init', default=None); ap.add_argument('--epochs', type=int, default=20); ap.add_argument('--replay', type=float, default=0.2)
    ap.add_argument('--extra', default='', help='DAgger 라운드 글롭(쉼표) — 필터 없이 전 프레임')
    a = ap.parse_args()
    rng = np.random.default_rng(0)
    dirs = [d for p in a.dirs.split(',') for d in sorted(glob.glob(p))]
    extra = [d for p in a.extra.split(',') if p for d in sorted(glob.glob(p))]
    got = load(dirs, a.stage, a.replay, rng, extra)
    if not got: print(json.dumps({'error': 'no frames for stage', 'stage': a.stage})); return
    X, Y, W, nsel, nrep = got; n = len(X)
    print(json.dumps({'stage': a.stage, 'aug': AUG, 'frames': n, 'stage_frames': nsel, 'replay_frames': nrep, 'w0': int((W == 0).sum()),
                      'steer_std': round(float(Y[:, 0].std()), 4), 'thr_mean': round(float(Y[:, 1].mean()), 3),
                      'stopped_pct': round(100 * float((Y[:, 1] < 0.05).mean()), 1)}), flush=True)
    if nsel < 200: print(json.dumps({'warn': 'stage frames < 200 — collect more of this situation first'}), flush=True)
    idx = rng.permutation(n); cut = int(n * 0.85)
    tr = np.concatenate([idx[:cut] + 1, -(idx[:cut] + 1)]); va = np.concatenate([idx[cut:] + 1, -(idx[cut:] + 1)])
    net = DriveNet(out=3).to(DEV); gpu_guard.assert_on_gpu(net)
    if a.init:
        net.load_state_dict(torch.load(a.init, map_location=DEV)); print(json.dumps({'init': a.init}), flush=True)
    opt = torch.optim.Adam(net.parameters(), 5e-4 if a.init else 1e-3, weight_decay=1e-4)
    best = 1e9
    for ep in range(a.epochs):
        net.train(); tot = 0.0; perm = rng.permutation(tr)
        for i in range(0, len(perm), BS):
            ids = perm[i:i+BS]; xb, yb = batch(X, Y, ids, train=True); wb = torch.from_numpy(W[np.abs(ids) - 1]).to(DEV)
            opt.zero_grad(); o = net(xb)
            l = (wb * ((o - yb) ** 2).mean(1)).sum() / wb.sum().clamp_min(1.0)
            of = net(torch.flip(xb, dims=[3])); l = l + 0.5 * ((o[:, 0] + of[:, 0]) ** 2).mean()   # 좌우 대칭(bias 억제)
            l.backward(); opt.step(); tot += l.item() * len(ids)
        net.eval(); vs = 0.0; c = 0
        with torch.no_grad():
            for i in range(0, len(va), BS):
                ids = va[i:i+BS]; xb, yb = batch(X, Y, ids); vs += ((net(xb) - yb) ** 2).mean().item() * len(ids); c += len(ids)
        vl = vs / max(1, c)
        if vl < best: best = vl; torch.save(net.state_dict(), a.out)
        print(json.dumps({'ep': ep, 'train': round(tot / len(perm), 5), 'val': round(vl, 5)}), flush=True)
    print(json.dumps({'done': a.out, 'best_val': round(best, 5), 'stage': a.stage}), flush=True)

if __name__ == '__main__':
    main()
