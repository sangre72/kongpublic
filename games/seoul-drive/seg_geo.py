"""a_5612 D3 규칙 기하(2026-09-24): 픽셀 클래스 마스크(256×256) + 목표 차로 id → e_y(m, +=차가 차로중심의 오른쪽) · e_psi(rad) . 지도는 목표 id 로만 들어온다.
화면 기하(수집·추론 공통, ODE_CROP=0.6 캔버스 763×750 lead 25m S=6): 차 위치 row 241 col 128, px/m x 3.361 y 4.478. 전방 8~30m 띠에서 열-중앙값 → 직선 적합."""
import numpy as np, os
_cc = float(os.environ.get('ODE_CROP', '0.6') or 0.6)
def geom(pw=763, ph=750, lead=25.0, S=6.0, size=256):
    hc = ph - int(round(ph * 0.236)); h, w = int(hc * _cc), int(pw * _cc); y0, x0 = (hc - h) // 2, (pw - w) // 2
    cy = ph * 0.62 + lead * S - int(round(ph * 0.236)) - y0; cx = pw / 2 - x0
    return cy * size / h, cx * size / w, size / w * S, size / h * S   # car_row, car_col, pxm_x, pxm_y
RES = int(os.environ.get('RES', '256')); CAR_ROW, CAR_COL, PXM_X, PXM_Y = geom(size=RES)
def _fit(band, cid, r1):
    """띠 안 클래스 cid 픽셀을 차에서 위로 행마다 추적: 각 행의 연속 구간(run) 중 직전 행 중앙(첫 행은 차 열)에 가장 가까운 것만 쓴다(교차 도로의 같은 클래스 배제)."""
    m = band == cid; med = []; rr = []; ref = CAR_COL
    for r in range(band.shape[0] - 1, -1, -1):
        cs = np.flatnonzero(m[r])
        if len(cs) == 0: continue
        cuts = np.flatnonzero(np.diff(cs) > 1) + 1; runs = np.split(cs, cuts)
        c = min(((r_ := (run[0] + run[-1]) / 2.0), abs(r_ - ref)) for run in runs)[0]
        if abs(c - ref) > 4.0 * PXM_X: continue   # 행 사이 4m 넘게 튀면 다른 도로
        med.append(c); rr.append(r + r1); ref = c
    if len(rr) < 3: return None
    fwd = (CAR_ROW - np.array(rr)) / PXM_Y; lat = (np.array(med) - CAR_COL) / PXM_X   # m, +=오른쪽
    (sl, ic), *_ = np.linalg.lstsq(np.stack([fwd, np.ones_like(fwd)], 1), lat, rcond=None)
    k0 = 0.0
    if len(rr) >= 8: (qa, _, _), *_ = np.linalg.lstsq(np.stack([fwd ** 2, fwd, np.ones_like(fwd)], 1), lat, rcond=None); k0 = float(2 * qa)   # lat ≈ ½κ f² → κ(+=우회전, 화면 우측)
    lc20 = float(np.interp(20.0, fwd[::-1], lat[::-1])) if fwd.min() <= 20.0 <= fwd.max() else float(sl * 20.0 + ic)   # 20m 앞 차로중심 횡오프셋(차 기준, +=우측)
    return -float(ic), -float(np.arctan(sl)), int(len(rr)), k0, lc20   # e_y: 차가 중심의 오른쪽이면 양수(중심이 왼쪽 = lat<0)
def _near(mask, cid):
    """차 위치 행(±1.5m) 에서 클래스 cid 의 차 열에 가장 가까운 run 중앙 → e_y(m). 없으면 nan. (띠 적합의 8m 외삽 오차·카메라 회전 지연 tilt 오차 제거)"""
    lat = []; rows = list(range(min(mask.shape[0] - 1, int(CAR_ROW + 1.0 * PXM_Y)), max(0, int(CAR_ROW - 8.0 * PXM_Y)), -1))   # 차 1m 뒤 → 8m 앞, 가까운 행부터
    for r in rows:
        cs = np.flatnonzero(mask[r] == cid)
        if len(cs) == 0:
            if len(lat) >= 3: break   # 차로 구간이 끝남(교차로 진입)
            continue
        runs = np.split(cs, np.flatnonzero(np.diff(cs) > 1) + 1); c = min(((run[0] + run[-1]) / 2.0 for run in runs), key=lambda z: abs(z - CAR_COL))
        if abs(c - CAR_COL) <= 4.0 * PXM_X: lat.append((c - CAR_COL) / PXM_X)
        if len(lat) >= int(2.5 * PXM_Y): break   # 2.5m 어치면 충분
    return -float(np.median(lat)) if len(lat) >= 2 else float('nan')
def lane_line(mask, tid, f0=8.0, f1=30.0, fallback=True):
    """mask(H,W uint8) 에서 클래스 tid 픽셀의 행별 중앙 열 → (e_y m, e_psi rad, n_rows, used_id). 목표 없으면 fallback: 차에 가장 가까운 내 차로(1..8)."""
    r1 = max(0, int(CAR_ROW - f1 * PXM_Y)); r0 = int(CAR_ROW - f0 * PXM_Y); band = mask[r1:r0]
    g = lane_geo(mask, tid, f0, f1, fallback); return g['ey'], g['ep'], g['n'], g['used']
def lane_geo(mask, tid, f0=8.0, f1=30.0, fallback=True):
    """→ {ey, ep, k0, lc20, n, used}. ey 는 차 행 근방(_near) 우선, 없으면 띠 적합 절편."""
    r1 = max(0, int(CAR_ROW - f1 * PXM_Y)); r0 = int(CAR_ROW - f0 * PXM_Y); band = mask[r1:r0]
    f = _fit(band, tid, r1); cid = tid
    if f is None and fallback:
        c = [(abs(f_[0]), f_, c_) for c_ in range(1, 9) if c_ != tid for f_ in [_fit(band, c_, r1)] if f_ is not None]
        if c: _, f, cid = min(c, key=lambda z: z[0])
    if f is None: return {'ey': float('nan'), 'ep': float('nan'), 'k0': 0.0, 'lc20': float('nan'), 'n': 0, 'used': -1}
    e = _near(mask, cid); return {'ey': (e if np.isfinite(e) else f[0]), 'ep': f[1], 'k0': f[3], 'lc20': f[4], 'n': f[2], 'used': cid}

class Accum:
    """orch a_5612 NEXT(2026-09-24): 자차 운동 보상 마스크 누적(규칙층). 프레임마다 직전 누적맵을 (전진 v·dt → 행 아래로, 요 dψ → 차 위치 중심 회전) 워프한 뒤 현재 마스크 one-hot 과 지수 혼합(시정수 tau s).
    미결정 프레임은 워프만 하고 누적 상태를 유지. e_y/e_psi 는 누적 목표차로 맵(임계 thr)에서 lane_geo 로."""
    def __init__(self, tau=0.7, thr=0.4, ncls=10):
        self.tau = tau; self.thr = thr; self.ncls = ncls; self.M = None; self.t = None
    def warp(self, v, dpsi, dt):
        import cv2
        if self.M is None: return
        A = cv2.getRotationMatrix2D((float(CAR_COL), float(CAR_ROW)), float(np.degrees(dpsi)) * ROT_SIGN, 1.0); A[1, 2] += v * dt * PXM_Y   # 장면은 차와 반대로: 전진 → 아래로, 우회전 → 반시계
        for k in range(self.ncls): self.M[k] = cv2.warpAffine(self.M[k], A, (self.M.shape[2], self.M.shape[1]), flags=cv2.INTER_LINEAR, borderValue=0.0)
    def step(self, mask, v, dpsi, dt, determined=True):
        if self.M is None: self.M = np.zeros((self.ncls,) + mask.shape, np.float32)
        else: self.warp(v, dpsi, dt)
        if determined:
            a = min(1.0, dt / self.tau); self.M *= (1.0 - a)
            for k in range(1, self.ncls): self.M[k] += a * (mask == k)
    def geo(self, tid):
        if self.M is None or not (1 <= tid < self.ncls): return {'ey': float('nan'), 'ep': float('nan'), 'k0': 0.0, 'lc20': float('nan'), 'n': 0, 'used': -1}
        b = (self.M[tid] >= self.thr).astype(np.uint8); g = lane_geo(b, 1, fallback=False); g['used'] = tid if g['n'] else -1; return g
ROT_SIGN = float(os.environ.get('ROT_SIGN', '1'))
