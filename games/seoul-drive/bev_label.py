#!/usr/bin/env python3
"""C(BEV) 오프라인 라벨(2026-09-24): 지도(data/data6.js CHUNKS)+자세(Q.npy pos px/6, 8열 ang) → 자차 기준 격자 64×64 @0.5m(전방 26m·후방 6m·좌우 ±16m).
채널: 0 차로중심선(전 차로) 1 주행가능(차도 폭) 2 진행방향 차로중심선(헤딩 ±90° 안 방향의 차로만). 값 0/1(선은 1셀 두께).
사용: python3 bev_label.py 'data/dagger_r25*'  → 각 라운드 B.npy (N,3,64,64) uint8. game.js laneOffset/laneFix 규약 동일(원점 도로 좌측 가장자리, 일방=전 차로 오른쪽 배치)."""
import sys, glob, json, math, numpy as np
LW = 3.25; G = 64; RES = 0.5; FWD = 26.0; BACK = 6.0; HALF = 16.0
def load_map():
    s = open('data/data6.js', encoding='utf-8').read(); i = s.index('const CHUNKS='); j = s.index(';\nconst', i + 10); return json.loads(s[i + 13:j])
def lane_fix(l, o): l = l or 2; return max(1, l // 2) if (o and l >= 7) else l
def lane_offsets(l, o):   # (offset m from centerline along road-left normal(−sin,cos), direction sign: +1 = road ang, −1 = reverse) per lane
    lf = lane_fix(l, o); out = []
    if o:
        rw = lf * LW
        for k in range(lf): out.append((-rw / 2 + (k + 0.5) * LW, +1))
    else:
        h = max(1, lf // 2)
        for k in range(h): out.append(((k + 0.5) * LW, +1)); out.append((-(k + 0.5) * LW, -1))
    return out, lane_fix(l, o) * LW
def roads_near(CH, x, y):
    cx, cy = math.floor(x / 1000), math.floor(y / 1000); rs = []
    for i in (-1, 0, 1):
        for j in (-1, 0, 1): rs += (CH.get(f'{cx+i},{cy+j}') or {}).get('r') or []
    return rs
def raster(CH, x, y, ang):
    g = np.zeros((3, G, G), np.uint8); ca, sa = math.cos(ang), math.sin(ang)
    def cell(px, py):   # world m → grid (row from top = forward)
        dx, dy = px - x, py - y; f = dx * ca + dy * sa; l = dx * sa - dy * ca   # 우측 양(+): 캔버스 y-down 좌표계 → geo e_y 규약과 대조(r2500 실측 mae 0.39 vs 0.76)
        r = int((FWD - f) / RES); c = int((l + HALF) / RES); return r, c
    for w in roads_near(CH, x, y):
        P = w['p']; offs, rw = lane_offsets(w.get('l'), w.get('o'))
        for i in range(len(P) - 1):
            (ax, ay), (bx, by) = P[i], P[i + 1]
            if min(abs(ax - x), abs(bx - x)) > 60 or min(abs(ay - y), abs(by - y)) > 60: continue
            sang = math.atan2(by - ay, bx - ax); nx, ny = -math.sin(sang), math.cos(sang); L = math.hypot(bx - ax, by - ay); n = max(2, int(L / 0.25))
            for k in range(n + 1):
                t = k / n; cx0, cy0 = ax + (bx - ax) * t, ay + (by - ay) * t
                for q in np.arange(-rw / 2, rw / 2 + 1e-6, 0.25):   # 주행가능
                    r, c = cell(cx0 + nx * q, cy0 + ny * q)
                    if 0 <= r < G and 0 <= c < G: g[1, r, c] = 1
                for off, d in offs:   # 차로중심선
                    r, c = cell(cx0 + nx * off, cy0 + ny * off)
                    if 0 <= r < G and 0 <= c < G:
                        g[0, r, c] = 1
                        dd = (ang - (sang + (0 if d > 0 else math.pi)) + 3 * math.pi) % (2 * math.pi) - math.pi
                        if abs(dd) <= math.pi / 2: g[2, r, c] = 1
    return g
_CH = None
def _work(args):
    global _CH
    if _CH is None: _CH = load_map()
    x, y, a = args
    return raster(_CH, x, y, a) if (np.isfinite(x) and np.isfinite(y) and np.isfinite(a)) else np.zeros((3, G, G), np.uint8)
def lane_lat_at(g, fwd_m, ego_lat=0.0):   # 진행방향 차로선(ch2)에서 fwd_m 앞 행의 차로 횡위치 중 ego_lat 에 가장 가까운 값(m). 없으면 nan
    r = int((FWD - fwd_m) / RES); cs = np.where(g[2, r] > 0)[0]
    if len(cs) == 0: return float('nan')
    lat = (cs + 0.5) * RES - HALF; return float(lat[np.argmin(np.abs(lat - ego_lat))])
def main():
    import multiprocessing as mp
    for d in sorted(glob.glob(sys.argv[1])):
        try: Q = np.load(f'{d}/Q.npy')
        except Exception: continue
        if Q.shape[1] < 8: print(json.dumps({'skip': d, 'why': 'no ang col'})); continue
        jobs = [(Q[i, 4] / 6.0, Q[i, 5] / 6.0, Q[i, 7]) for i in range(len(Q))]
        with mp.Pool(6) as pool: B = np.stack(pool.map(_work, jobs, chunksize=32))
        np.save(f'{d}/B.npy', B); info = {'dir': d.split('/')[-1], 'n': len(Q), 'lane_px_mean': round(float(B[:, 0].sum((1, 2)).mean()), 1), 'driv_px_mean': round(float(B[:, 1].sum((1, 2)).mean()), 1)}
        try:   # 검증: 격자에서 읽은 20m 앞 차로 횡위치 vs geo 라벨 lc20(현재 차로 중심) — 부호·규약 일치 확인
            L = np.load(f'{d}/L.npy'); v = L[:, 11] > 0; err = []
            for i in np.where(v)[0][::7]:
                z = lane_lat_at(B[i], 20.0, -L[i, 0]); 
                if np.isfinite(z): err.append(z - L[i, 4])
            if err: err = np.array(err); info['lc20_check_mae'] = round(float(np.abs(err).mean()), 2); info['lc20_check_bias'] = round(float(err.mean()), 2); info['lc20_check_n'] = len(err)
        except Exception as e: info['check_err'] = str(e)[:60]
        print(json.dumps(info), flush=True)
if __name__ == '__main__': main()
