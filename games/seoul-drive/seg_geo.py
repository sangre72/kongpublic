"""a_5612 D3 규칙 기하(2026-09-24): 픽셀 클래스 마스크(256×256) + 목표 차로 id → e_y(m, +=차가 차로중심의 오른쪽) · e_psi(rad) . 지도는 목표 id 로만 들어온다.
화면 기하(수집·추론 공통, ODE_CROP=0.6 캔버스 763×750 lead 25m S=6): 차 위치 row 241 col 128, px/m x 3.361 y 4.478. 전방 8~30m 띠에서 열-중앙값 → 직선 적합."""
import numpy as np, os
_cc = float(os.environ.get('ODE_CROP', '0.6') or 0.6)
def geom(pw=763, ph=750, lead=25.0, S=6.0, size=256):
    hc = ph - int(round(ph * 0.236)); h, w = int(hc * _cc), int(pw * _cc); y0, x0 = (hc - h) // 2, (pw - w) // 2
    cy = ph * 0.62 + lead * S - int(round(ph * 0.236)) - y0; cx = pw / 2 - x0
    return cy * size / h, cx * size / w, size / w * S, size / h * S   # car_row, car_col, pxm_x, pxm_y
CAR_ROW, CAR_COL, PXM_X, PXM_Y = geom()
def _fit(band, cid, r1):
    rows, cols = np.nonzero(band == cid)
    if len(rows) < 8: return None
    rr = np.unique(rows)
    if len(rr) < 3: return None
    med = np.array([np.median(cols[rows == r]) for r in rr]); rr = rr + r1
    fwd = (CAR_ROW - rr) / PXM_Y; lat = (med - CAR_COL) / PXM_X   # m, +=오른쪽
    (sl, ic), *_ = np.linalg.lstsq(np.stack([fwd, np.ones_like(fwd)], 1), lat, rcond=None)
    return -float(ic), -float(np.arctan(sl)), int(len(rr))   # e_y: 차가 중심의 오른쪽이면 양수(중심이 왼쪽 = lat<0)
def lane_line(mask, tid, f0=8.0, f1=30.0, fallback=True):
    """mask(H,W uint8) 에서 클래스 tid 픽셀의 행별 중앙 열 → (e_y m, e_psi rad, n_rows, used_id). 목표 없으면 fallback: 차에 가장 가까운 내 차로(1..8)."""
    r1 = max(0, int(CAR_ROW - f1 * PXM_Y)); r0 = int(CAR_ROW - f0 * PXM_Y); band = mask[r1:r0]
    f = _fit(band, tid, r1)
    if f is not None: return f + (tid,)
    if fallback:
        c = [(abs(f[0]), f, cid) for cid in range(1, 9) if cid != tid for f in [_fit(band, cid, r1)] if f is not None]
        if c: _, f, cid = min(c, key=lambda z: z[0]); return f + (cid,)
    return float('nan'), float('nan'), 0, -1
