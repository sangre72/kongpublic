#!/usr/bin/env python3
"""a_5598 offline reversal gate(u_5602): 헤드를 홀드아웃 에피소드의 연속 프레임에 돌려 e_y·lc20 예측의 부호반전/s 와 |Δ| p90 를 잰다(폐루프 전 관문).
사용: python3 offline_gate.py <model.pt> 'data/dagger_r3[0-2]*' [--k 1]   (--k>1: 시간 스택 입력, 직전 k-1 프레임 채널 연결)
출력: per-episode {fps, ey_rev_s, lc20_rev_s, ey_dp90, lc20_dp90, ey_mae, lc20_mae} + 평균. 라벨 비교는 valid 프레임만."""
import sys, os, glob, json, argparse, numpy as np, torch
from net import DriveNet
import gpu_guard
ap = argparse.ArgumentParser(); ap.add_argument('model'); ap.add_argument('dirs'); ap.add_argument('--k', type=int, default=1); a = ap.parse_args()
DEV = gpu_guard.require_gpu(); sd = torch.load(a.model, map_location=DEV); in_ch = int(sd['f.0.weight'].shape[1])
net = DriveNet(out=12, vin=True, vdim=1, in_ch=in_ch).to(DEV); net.load_state_dict(sd); net.eval(); K = in_ch // 3
SCALE = np.array([2.0, 0.5, 0.05, 16.0, 16.0, 16.0, 8.0, 8.0, 5.0, 15.0, 15.0, 1.0], np.float32)
def stack(X, i):
    fr = [X[max(0, i - j)] for j in range(K - 1, -1, -1)]   # 과거→현재 순, 채널 연결
    return np.concatenate(fr, 0)
rows = []
for d in sorted(glob.glob(a.dirs)):
    X = np.load(f'{d}/X.npy', mmap_mode='r'); Y = np.load(f'{d}/Y.npy'); L = np.load(f'{d}/L.npy'); Q = np.load(f'{d}/Q.npy')
    n = len(X); P = np.zeros((n, 12), np.float32)
    with torch.no_grad():
        for s in range(0, n, 64):
            ids = range(s, min(n, s + 64)); xb = torch.from_numpy(np.stack([stack(X, i) for i in ids])).float().div_(255.).to(DEV); vb = torch.from_numpy((Y[list(ids), 3] / 30.0).astype(np.float32).reshape(-1, 1)).to(DEV)
            P[s:s + len(ids)] = net(xb, vb, raw=True).cpu().numpy() * SCALE
    t = Q[:, 3]; fps = (n - 1) / max(t[-1] - t[0], 1e-3); mv = Y[:, 3] > 1.0
    def rev(x): return float(np.sum(np.diff(np.sign(np.diff(x))) != 0)) / max(t[-1] - t[0], 1e-3)
    ey, lc = P[:, 0], P[:, 4]; v = (L[:, 11] > 0) & mv
    r = {'ep': d.split('/')[-1], 'n': n, 'fps': round(fps, 1), 'ey_rev_s': round(rev(ey), 2), 'lc20_rev_s': round(rev(lc), 2), 'ey_dp90': round(float(np.percentile(np.abs(np.diff(ey)), 90)), 3), 'lc20_dp90': round(float(np.percentile(np.abs(np.diff(lc)), 90)), 3),
         'ey_mae': round(float(np.abs(ey[v] - L[v, 0]).mean()), 3) if v.any() else None, 'lc20_mae': round(float(np.abs(lc[v] - L[v, 4]).mean()), 3) if v.any() else None, 'label_ey_rev_s': round(rev(L[:, 0]), 2)}
    for name, lo, hi in [('nl<=4', 0, 4), ('nl5-8', 5, 8), ('nl>=9', 9, 99)]:   # u_5603: 차로수 구간별
        b = (L[:, 7] >= lo) & (L[:, 7] <= hi) & mv
        if b.sum() < 30: continue
        seg = np.where(b)[0]; dt = max(t[seg[-1]] - t[seg[0]], 1e-3)
        r[name] = {'n': int(b.sum()), 'ey_rev_s': round(float(np.sum(np.diff(np.sign(np.diff(ey[b]))) != 0)) / dt, 2), 'lc20_rev_s': round(float(np.sum(np.diff(np.sign(np.diff(lc[b]))) != 0)) / dt, 2), 'ey_dp90': round(float(np.percentile(np.abs(np.diff(ey[b])), 90)), 3), 'lc20_dp90': round(float(np.percentile(np.abs(np.diff(lc[b])), 90)), 3), 'li_err': round(float(np.abs(np.round(P[b, 6]) - L[b, 6]).mean()), 3), 'ey_mae': round(float(np.abs(ey[b & v] - L[b & v, 0]).mean()), 3) if (b & v).any() else None}
    # u_5604 명령 재생: lp(no hold) vs lp(hold: |ey|<0.3∧|epsi|<2° 진입, |ey|>0.3 0.5s 지속시 해제) 의 부호반전/s (같은 차로 목표 가정)
    lp0 = P[:, 4].copy(); lph = lp0.copy(); hold = False; out_t = None; hn = 0
    for i in range(n):
        inb = abs(P[i, 0]) < 0.3 and abs(P[i, 1]) < 0.0349
        if hold:
            if abs(P[i, 0]) > 0.3: out_t = t[i] if out_t is None else out_t; hold = not (t[i] - out_t >= 0.5)
            else: out_t = None
        elif inb: hold = True; out_t = None
        k0f = P[i, 2] if i == 0 else k0f + 0.1 * (P[i, 2] - k0f)
        if hold: lph[i] = 200.0 * k0f; hn += 1
    from merge_plan import MergePlanner
    from merge_plan import MergePlannerKF
    hd = np.arctan2(np.gradient(Q[:, 5]), np.gradient(Q[:, 4])) if Q.shape[1] >= 6 else None   # 위치 미분 헤딩(요레이트 근사)
    mp = MergePlannerKF(); lpm = lp0.copy()
    for i in range(n):
        yr = None
        if hd is not None and i > 0: dth = (hd[i] - hd[i - 1] + np.pi) % (2 * np.pi) - np.pi; yr = float(dth / max(t[i] - t[i - 1], 1e-3)) if Y[i, 3] > 1.5 else 0.0
        lpm[i], _ = mp.step(float(t[i]), float(P[i, 0]), float(P[i, 1]), float(P[i, 2]), float(Y[i, 3]), yr if os.environ.get('GATE_YAW', '1') == '1' else None)
    r['kf_rej_frac'] = round(mp.rej / max(mp.n, 1), 3)
    r['cmd_rev_s_merge'] = round(rev(lpm[mv]), 2) if mv.sum() > 10 else None; r['merge_hold_frac'] = round(mp.hold_n / max(n, 1), 3)
    r['cmd_rev_s'] = round(rev(lp0[mv]), 2) if mv.sum() > 10 else None; r['cmd_rev_s_hold'] = round(rev(lph[mv]), 2) if mv.sum() > 10 else None; r['hold_frac'] = round(hn / max(n, 1), 3)
    rows.append(r); print(json.dumps(r, default=float), flush=True)
m = lambda k: round(float(np.mean([r[k] for r in rows if r[k] is not None])), 3)
print(json.dumps({'model': a.model, 'k': K, 'episodes': len(rows), 'fps': m('fps'), 'ey_rev_s': m('ey_rev_s'), 'lc20_rev_s': m('lc20_rev_s'), 'ey_dp90': m('ey_dp90'), 'lc20_dp90': m('lc20_dp90'), 'ey_mae': m('ey_mae'), 'lc20_mae': m('lc20_mae'), 'label_ey_rev_s': m('label_ey_rev_s'), 'cmd_rev_s': m('cmd_rev_s'), 'cmd_rev_s_hold': m('cmd_rev_s_hold'), 'hold_frac': m('hold_frac'), 'cmd_rev_s_merge': m('cmd_rev_s_merge'), 'merge_hold_frac': m('merge_hold_frac'), 'kf_rej_frac': m('kf_rej_frac')}, default=float))
