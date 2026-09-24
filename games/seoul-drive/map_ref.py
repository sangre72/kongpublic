"""a_5612 지도 기준 참값(2026-09-24): Q(pos px/6, ang) + data6.js → 내 방향(±60°) 차로 중 차에 가장 가까운 차로의 (e_y m +=우측, 차로 id 1..8, 일방여부). geo 텔레메트리(lat 부호 반전 결함) 와 무관한 독립 기준."""
import math, numpy as np
from bev_label import load_map, roads_near, lane_offsets, LW
_CH = None
def ref(x, y, ang):
    global _CH
    if not (np.isfinite(x) and np.isfinite(y) and np.isfinite(ang)): return None
    if _CH is None: _CH = load_map()
    best = None
    for w in roads_near(_CH, x, y):
        P = w['p']; offs, rw = lane_offsets(w.get('l'), w.get('o')); one = bool(w.get('o'))
        for i in range(len(P) - 1):
            (ax, ay), (bx, by) = P[i], P[i + 1]
            if min(abs(ax - x), abs(bx - x)) > 30 or min(abs(ay - y), abs(by - y)) > 30: continue
            L2 = (bx - ax) ** 2 + (by - ay) ** 2
            if L2 < 1e-6: continue
            t = max(0.0, min(1.0, ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / L2)); px, py = ax + (bx - ax) * t, ay + (by - ay) * t
            sang = math.atan2(by - ay, bx - ax); lat = (x - px) * (-math.sin(sang)) + (y - py) * math.cos(sang)   # +=도로각 기준 우측
            if abs(lat) > rw / 2 + 1.0: continue
            for k, (off, d) in enumerate(offs):
                dd = (ang - (sang + (0 if d > 0 else math.pi)) + 3 * math.pi) % (2 * math.pi) - math.pi
                if abs(dd) > math.pi / 3: continue
                ey = (lat - off) * d
                if best is None or abs(ey) < abs(best[0]): best = (ey, (k if one else k // 2) + 1, one, dd)
    return best
