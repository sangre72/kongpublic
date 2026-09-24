"""C(BEV) 제어 어댑터(2026-09-24): 격자 로짓(3×64×64) → (e_y, e_psi, κ, lc20) — 이후 MergePlannerKF/앞점 경로 공용. 규약 bev_label.py 와 동일(FWD 26 BACK 6 HALF 16 RES 0.5)."""
import math, numpy as np
G = 64; RES = 0.5; FWD = 26.0; HALF = 16.0
def _lat_at(ch, fwd_m, near):
    r = int((FWD - fwd_m) / RES)
    if r < 0 or r >= G: return float('nan')
    cs = np.where(ch[r] > 0)[0]
    if len(cs) == 0: return float('nan')
    lat = (cs + 0.5) * RES - HALF
    # 인접 셀 묶음 → 각 차로선 중심
    groups = np.split(lat, np.where(np.diff(cs) > 1)[0] + 1); cen = np.array([g.mean() for g in groups])
    return float(cen[np.argmin(np.abs(cen - near))])
def bev_to_geo(logit, shift=0.0, prev_ey=0.0):
    """logit: (3,64,64). shift = 목표차로 이동(m, 규칙층). 반환 ey(+우), epsi(rad), k0(1/m), lc20(m, 목표차로 기준), valid"""
    ch = (logit[2] > 0).astype(np.uint8)
    l0 = _lat_at(ch, 0.5, -prev_ey); l5 = _lat_at(ch, 5.0, l0 if np.isfinite(l0) else 0.0); l10 = _lat_at(ch, 10.0, l5 if np.isfinite(l5) else 0.0); l20 = _lat_at(ch, 20.0, l10 if np.isfinite(l10) else 0.0)
    if not (np.isfinite(l0) and np.isfinite(l10)): return None
    ey = -l0                                   # 차로중심이 왼쪽(−)에 있으면 차는 오른쪽(+)
    epsi = -math.atan2(l10 - l0, 10.0)         # 차로선이 앞에서 오른쪽으로 기울면 차 헤딩은 왼쪽 → 부호 반전
    k0 = 0.0
    if np.isfinite(l20): k0 = 2.0 * ((l20 - l0) - 2.0 * (l10 - l0)) / (10.0 ** 2) * 0.5   # 2차 미분 근사(1/m)
    lc20 = (l20 if np.isfinite(l20) else l10 + (l10 - l0)) + shift
    return ey, epsi, k0, lc20
