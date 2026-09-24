#!/usr/bin/env python3
"""a_5612 D4 오프라인 관문(2026-09-24): 홀드아웃(X,S,L) 에서 (a) 라벨→기하 일관성(--label), (b) 모델 IoU + 모델 마스크→e_y/e_psi 오차·부호반전/s, nl≤4 / 5-8 버킷.
사용: python3 seg_gate.py <ode_seg.pt|--label> 'data/dagger_r30*'   → JSON 요약. 목표 id = L.li+1(지도, 규칙층)."""
import sys, glob, json, numpy as np, os
RES = int(os.environ.get('RES', '256')); GEO_OLD = os.environ.get('GEO_OLD', '1') == '1'; REF = os.environ.get('REF', 'geo')   # REF=map: map_ref 기준(S 없는 홀드아웃도 가능)   # 2026-09-24 game.js geo lat 부호 수정 전 수집분(r≤27xx)
def to_res(x, nearest=False):
    import torch, torch.nn.functional as F
    if x.shape[-1] == RES: return x
    return F.interpolate(x[:, None].float() if nearest else x, size=(RES, RES), mode='nearest' if nearest else 'bilinear', **({} if nearest else {'align_corners': False, 'antialias': True}))[:, 0].to(x.dtype) if nearest else F.interpolate(x, size=(RES, RES), mode='bilinear', align_corners=False, antialias=True)
from seg_geo import lane_line, CAR_ROW, CAR_COL, Accum
ACC = float(os.environ.get('ACC', '0'))
from seg_net import NCLS
from map_ref import ref
model = sys.argv[1]; dirs = sorted(glob.glob(sys.argv[2])); net = None; cm = None
import torch
if model.endswith('.mlpackage'):   # CoreML CPU 경로(MPS 학습과 병행 가능, GPU 미사용)
    sys.modules['tensorflow'] = None; import coremltools as ct; cm = ct.models.MLModel(model, compute_units=ct.ComputeUnit.CPU_ONLY); net = True
elif model != '--label':
    import gpu_guard; from seg_net import SegNet
    DEV = gpu_guard.require_gpu(); net = SegNet().to(DEV); net.load_state_dict(torch.load(model, map_location=DEV)); net.eval()
def predict(xb):   # xb (B,3,RES,RES) float tensor(cpu) → (B,RES,RES) uint8
    if cm is not None: return np.stack([np.asarray(list(cm.predict({'img': xb[i:i + 1].numpy(), 'v': np.zeros((1, 1), np.float32)}).values())[0]).reshape(NCLS, RES, RES).argmax(0) for i in range(len(xb))]).astype(np.uint8)
    with torch.no_grad(): return net(xb.to(DEV)).argmax(1).cpu().numpy().astype(np.uint8)
conf = np.zeros((NCLS, NCLS), np.int64); rows = []; rev = {'n': 0, 'rev': 0, 't': 0.0}
for d in dirs:
    X = np.load(f'{d}/X.npy', mmap_mode='r'); L = np.load(f'{d}/L.npy'); Q = np.load(f'{d}/Q.npy'); Y = np.load(f'{d}/Y.npy')
    try: S = np.load(f'{d}/S.npy', mmap_mode='r')
    except Exception: S = None
    n = len(X); prev = None
    if Q.shape[1] < 8:   # 옛 라운드(홀드아웃 r3000~): car.ang 열 없음 → 위치 차분 헤딩(±3프레임, 이동 중만)
        dx = np.gradient(Q[:, 4]); dy = np.gradient(Q[:, 5]); k = np.ones(7) / 7; dx = np.convolve(dx, k, 'same'); dy = np.convolve(dy, k, 'same')
        ang = np.where(np.hypot(dx, dy) > 0.3, np.arctan2(dy, dx), np.nan); Q = np.concatenate([Q, ang[:, None]], 1)
    for s in range(0, n, 32):
        ids = list(range(s, min(n, s + 32)))
        if net is None and S is None: continue
        if net is None: P = to_res(torch.from_numpy(np.asarray(S[ids])), True).numpy() if S[ids].shape[-1] != RES else np.asarray(S[ids])
        else:
            P = predict(to_res(torch.from_numpy(np.ascontiguousarray(X[ids])).float().div_(255.)))
            if S is not None:
                sb = to_res(torch.from_numpy(np.asarray(S[ids])), True).numpy(); m = sb != 255; conf += np.bincount((sb[m].astype(np.int64) * NCLS + P[m]), minlength=NCLS * NCLS).reshape(NCLS, NCLS)
        for k, i in enumerate(ids):
            if L[i, 11] <= 0 or Y[i, 3] < 1.0: prev = None; continue
            if REF == 'map':   # 지도 독립 기준(map_ref): 차에 가장 가까운 내 방향 차로 → (ey, id)
                r_ = ref(Q[i, 4] / 6.0, Q[i, 5] / 6.0, Q[i, 7])
                if r_ is None: prev = None; continue
                ey_l, tid = r_[0], r_[1]
            else:
                li, nl = int(round(L[i, 6])), int(round(L[i, 7])); one = abs((L[i, 9] + L[i, 10]) - nl * L[i, 8]) < 0.5   # 일방 = 도로폭 == nl·lw
                tid = (nl - li if (one and GEO_OLD) else li + 1); ey_l = -L[i, 0] if GEO_OLD else L[i, 0]   # GEO_OLD: 옛 geo(lat 부호 반전) 라벨 — 일방 li 는 우측 기준
            if ACC > 0:   # 누적 모드: 연속 프레임(dt<0.5s)만 상태 유지, 끊기면 리셋
                if prev is None or i != prev[0] + 1: accum = Accum(tau=ACC)
                _dt = float(Q[i, 3] - Q[i - 1, 3]) if i > 0 else 0.03; _dps = float((Q[i, 7] - Q[i - 1, 7] + np.pi) % (2 * np.pi) - np.pi) if (i > 0 and np.isfinite(Q[i, 7]) and np.isfinite(Q[i - 1, 7])) else 0.0
                g0 = lane_line(P[k], tid); accum.step(P[k], float(Y[i, 3]), _dps, min(max(_dt, 0.01), 0.2), determined=np.isfinite(g0[0])); ga = accum.geo(tid)
                ey, ep, nr, used = (ga['ey'], ga['ep'], ga['n'], ga['used']) if np.isfinite(ga['ey']) else g0
            else: ey, ep, nr, used = lane_line(P[k], tid)
            if not np.isfinite(ey): prev = None; continue
            rows.append((L[i, 7], ey - ey_l, ep - L[i, 1], used == tid, 1 <= int(P[k][int(CAR_ROW), int(CAR_COL)]) <= 8))   # 5열: 차 픽셀이 차로(미결정 아님)
            if prev is not None and i == prev[0] + 1:
                rev['n'] += 1; rev['t'] += float(Q[i, 3] - prev[2]); rev['rev'] += int(np.sign(ey) != np.sign(prev[1]) and abs(ey - prev[1]) > 0.1)
            prev = (i, ey, Q[i, 3])
R = np.array(rows, np.float64); out = {'model': model, 'frames': len(R)}
def bucket(name, m):
    if m.sum() == 0: return
    out[name] = {'n': int(m.sum()), 'ey_mae': round(float(np.abs(R[m, 1]).mean()), 3), 'ey_bias': round(float(R[m, 1].mean()), 3), 'ey_med': round(float(np.median(np.abs(R[m, 1]))), 3), 'ey_p90': round(float(np.percentile(np.abs(R[m, 1]), 90)), 3), 'epsi_mae_deg': round(float(np.degrees(np.abs(R[m, 2])).mean()), 2), 'target_found%': round(100 * float(R[m, 3].mean()), 1)}
if len(R):
    bucket('all', np.ones(len(R), bool)); bucket('narrow_nl<=4', R[:, 0] <= 4); bucket('wide_nl5-8', (R[:, 0] >= 5) & (R[:, 0] <= 8)); bucket('nl>=9', R[:, 0] >= 9)
    lf = R[:, 4] > 0; bucket('lane_frames_all', lf); bucket('lane_frames_narrow', lf & (R[:, 0] <= 4)); bucket('lane_frames_wide', lf & (R[:, 0] >= 5) & (R[:, 0] <= 8)); out['undetermined%'] = round(100 * float(1 - lf.mean()), 1)
    out['ey_rev_s'] = round(rev['rev'] / max(1e-6, rev['t']), 3)
if net is not None and conf.sum():
    tp = np.diag(conf); io = tp / np.maximum(1, conf.sum(0) + conf.sum(1) - tp); out['iou'] = [round(float(v), 3) for v in io]; out['miou_lanes'] = round(float(io[1:9][conf.sum(1)[1:9] > 0].mean()), 3); out['iou_line'] = round(float(io[9]), 3)
print(json.dumps(out))
