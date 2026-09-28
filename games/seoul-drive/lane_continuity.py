#!/usr/bin/env python3
"""u_5669 경로 차로 연속성 검출기.

사용:
  python3 lane_continuity.py --tel cases/tel_u5669.json          # 저장된 /tel 스냅샷 1건
  python3 lane_continuity.py --routes "강남역>이태원로42길,..."   # 페이지로 N 구간(주행 없음, 경로만 생성)

offTab 행 = [누적m, 오프셋m, roadW, l, o, 작성자, way, 이름, lf, lb, c]
판정: 인접 홉 |Δ오프셋| > THRESH(기본 3m = 1 차로 미만은 램프로 흡수 가능) 를 전부 나열하고 원인을 분류한다.
  map_frag   : 같은 이름 도로가 일방/양방 조각으로 갈리거나 차로수가 바뀌는 지점(지도 표현)
  author     : 차로수·일방성이 같은데 작성자만 다르고 부호가 뒤집힘(작성기 규약 불일치) ★진짜 결함
  lane_count : 같은 도로·같은 작성자인데 l 이 바뀜(차로수 변화 → 오프셋 재계산 필요)
  turn       : 회전 정점 근처(교차로) — 정상
"""
import json, sys, math, argparse, urllib.request, subprocess, time

def rows_of(tel):
    w = tel.get('wpDbg') or {}
    return [r for r in (w.get('offTab') or []) if isinstance(r, list) and len(r) >= 8 and isinstance(r[1], (int, float))]

def turn_xy(tel):
    return (tel.get('wpDbg') or {}).get('turnXY') or []

WRITERS = ('Lprep', 'Lexit', 'Lhold', 'Stl', 'Rtl', 'Ltl', 'bridge')

def classify(prev, cur, tel):
    _, o0, _, l0, ow0, a0, w0, n0 = prev[:8]
    _, o1, _, l1, ow1, a1, w1, n1 = cur[:8]
    # ★orch 2026-09-27(1): 작성자(안쪽차로) ↔ base(주행차로) 전환은 회전 준비/복귀로 **설계된 차로 변경**이다.
    # 결함이 아니므로 'design' 으로 분류해 점프 집계에서 제외한다(실측: author 로 잡히던 5건이 전부 이것).
    if (a0 in WRITERS) != (a1 in WRITERS):
        return 'design'
    if (n0 or '') == (n1 or '') and bool(ow0) != bool(ow1):
        return 'map_frag'                                   # 같은 도로가 일방↔양방으로 바뀜
    if (n0 or '') == (n1 or '') and l0 != l1:
        return 'lane_count'                                 # 같은 도로인데 차로수 변화
    if l0 == l1 and bool(ow0) == bool(ow1) and a0 != a1 and (o0 * o1) < 0:
        return 'author'                                     # 속성 동일 + 작성자 다름 + 부호 반전
    if l0 == l1 and bool(ow0) == bool(ow1) and (o0 * o1) < 0:
        return 'author'                                     # 속성 동일한데 부호만 반전
    if (n0 or '') != (n1 or ''):
        return 'road_change'
    return 'other'

def scan(tel, thresh=3.0, label=''):
    rs = rows_of(tel); out = []
    for i in range(1, len(rs)):
        d = rs[i][1] - rs[i-1][1]
        if abs(d) > thresh:
            out.append((rs[i][0], rs[i-1][1], rs[i][1], d, classify(rs[i-1], rs[i], tel),
                        rs[i-1][5], rs[i][5], rs[i][6], rs[i][7], rs[i-1][3], rs[i][3], rs[i-1][4], rs[i][4]))
    real = [j for j in out if j[4] != 'design']
    print(f"== {label or 'route'}: rows {len(rs)} jumps>{thresh}m: {len(real)} real (+{len(out)-len(real)} design)")
    for j in out:
        print("  %6.0fm %+.2f -> %+.2f (d%+.2f) [%s] %s->%s w%s %s l%s->%s o%s->%s"
              % (j[0], j[1], j[2], j[3], j[4], j[5], j[6], j[7], j[8], j[9], j[10], j[11], j[12]))
    from collections import Counter
    c = Counter(j[4] for j in out)
    print("  causes:", dict(c), "| real defects:", {k: v for k, v in c.items() if k != 'design'})
    return real

def fetch(frm, to, wait=90):
    subprocess.run(['bash', 'reload.sh',
                    f'http://localhost:8901/index.html?hud=0&asym=1&from={frm}&to={to}', str(wait)],
                   capture_output=True)
    time.sleep(2)
    return json.load(urllib.request.urlopen('http://localhost:8901/tel', timeout=10))

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--tel'); ap.add_argument('--routes'); ap.add_argument('--thresh', type=float, default=3.0)
    a = ap.parse_args()
    allj = []
    if a.tel:
        allj += scan(json.load(open(a.tel)), a.thresh, a.tel)
    if a.routes:
        for pair in a.routes.split(','):
            f, t = pair.split('>')
            allj += scan(fetch(f.strip(), t.strip()), a.thresh, pair)
    from collections import Counter
    print("TOTAL jumps", len(allj), dict(Counter(j[4] for j in allj)))
