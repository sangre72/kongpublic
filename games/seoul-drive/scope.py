#!/usr/bin/env python3
"""★SCOPE(u_5705, 2026-09-28): 작업 범위 = 강남구 + 송파구.
OSM admin_level=6 경계 폴리곤(data/scope_gangnam_songpa.json)을 게임 좌표(m)로 변환해 점/경로 포함을 판정한다.
모든 도구(경로 생성·eval20 구간 선정·수집기·지도 감사)가 이걸 쓴다.

사용:
  from scope import in_scope, scope_bbox_m, load_scope
  in_scope(x_m, y_m) -> bool
  python3 scope.py --check <x_m> <y_m>
"""
import json, os, math

S_LAT, S_LON = 37.4979, 127.0276              # 게임 원점(강남역) — pbf_to_chunks.py 와 동일해야 한다
M_PER_DEG_LAT = 111320.0
HERE = os.path.dirname(os.path.abspath(__file__))
_SC = None

def _ll2m(lat, lon):
    y = (lat - S_LAT) * M_PER_DEG_LAT
    x = (lon - S_LON) * M_PER_DEG_LAT * math.cos(math.radians(S_LAT))
    return x, y

def load_scope(path=None):
    global _SC
    if _SC is not None: return _SC
    p = path or os.path.join(HERE, 'data/scope_gangnam_songpa.json')
    raw = json.load(open(p, encoding='utf-8'))
    polys = []
    for gu, v in raw.items():
        for ring in v['rings']:
            polys.append((gu, [_ll2m(lat, lon) for lon, lat in ring]))
    xs = [p[0] for _, r in polys for p in r]; ys = [p[1] for _, r in polys for p in r]
    _SC = {'polys': polys, 'bbox': (min(xs), min(ys), max(xs), max(ys))}
    return _SC

def scope_bbox_m():
    return load_scope()['bbox']

def _pt_in_ring(x, y, ring):
    inside = False; n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]; x2, y2 = ring[(i + 1) % n]
        if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-12) + x1):
            inside = not inside
    return inside

def in_scope(x_m, y_m):
    sc = load_scope()
    x0, y0, x1, y1 = sc['bbox']
    if not (x0 <= x_m <= x1 and y0 <= y_m <= y1): return False
    return any(_pt_in_ring(x_m, y_m, ring) for _, ring in sc['polys'])

def which_gu(x_m, y_m):
    for gu, ring in load_scope()['polys']:
        if _pt_in_ring(x_m, y_m, ring): return gu
    return None

if __name__ == '__main__':
    import sys
    sc = load_scope()
    print(json.dumps({'bbox_m': [round(v) for v in sc['bbox']], 'rings': len(sc['polys'])}, ensure_ascii=False))
    if '--check' in sys.argv:
        i = sys.argv.index('--check'); x, y = float(sys.argv[i+1]), float(sys.argv[i+2])
        print(json.dumps({'x': x, 'y': y, 'in_scope': in_scope(x, y), 'gu': which_gu(x, y)}, ensure_ascii=False))
