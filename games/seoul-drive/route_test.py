#!/usr/bin/env python3
"""구간별 주행 시험 + 도로교통법 준수 검증 (u_5201).

오너 지시: "각 구간 교차로 차선 유지 그리고 회전 도로법 잘 준수하고
다니는지 확인해야돼"

사고 수만 세는 게 아니라 '법규를 지켰는가'를 본다:
  · 차로 유지 — 점선과 점선 사이(차로 중앙)로 가는가
  · 회전 차로 — 좌회전은 좌측, 우회전은 우측 차로에서 하는가
  · 차선변경 — 한 번에 한 칸씩인가
  · 중앙선 — 넘지 않는가

사용: python3 route_test.py <출발> <도착> [초]
      python3 route_test.py 시청역 노원역 900
"""
import json, subprocess, sys, time, urllib.request, collections
import statistics as st

LW = 3.25
CARW = 1.8
TEL = 'http://localhost:8901/tel'


def post(p):
    urllib.request.urlopen(urllib.request.Request(
        'http://localhost:8901/ctl', data=json.dumps(p).encode(),
        headers={'Content-Type': 'application/json'}), timeout=5).read()


def tel():
    try:
        return json.load(urllib.request.urlopen(TEL, timeout=3))
    except Exception:
        return None


def set_route(start, dest):
    """★?go=1 은 강남역→시청역 고정이므로, 다른 구간은 URL 파라미터로 넘긴다.
       game.js 의 자동경로 설정이 qs/q 입력칸을 읽으므로 거기에 값을 넣는다."""
    here = __file__.rsplit('/', 1)[0]
    url = ('http://localhost:8901/index.html?go=1'
           '&from=' + urllib.parse.quote(start) + '&to=' + urllib.parse.quote(dest))
    subprocess.run(['bash', here + '/reload.sh', url], capture_output=True, timeout=120)
    for _ in range(40):
        time.sleep(1)
        d = tel()
        if d and (d.get('wpLen') or 0) > 100:
            return d
    return tel()


def judge_lane(g):
    """차로 준수 판정. 일방은 좌측가장자리, 왕복은 중심선이 원점."""
    lat, rw, o = g.get('lat'), g.get('roadW') or 0, g.get('o')
    if lat is None or not rw:
        return None
    if o:
        x = rw / 2 + lat
        edge = min(x % LW, LW - (x % LW))
        return {'straddle': edge < CARW / 2, 'offroad': x < 0 or x > rw, 'wrong': False}
    if lat < 0:
        return {'straddle': True, 'offroad': False, 'wrong': True}   # 중앙선 넘음
    edge = min(lat % LW, LW - (lat % LW))
    return {'straddle': edge < CARW / 2, 'offroad': lat > rw / 2, 'wrong': False}


def main():
    start = sys.argv[1] if len(sys.argv) > 1 else '강남역'
    dest = sys.argv[2] if len(sys.argv) > 2 else '시청역'
    secs = float(sys.argv[3]) if len(sys.argv) > 3 else 900

    d0 = set_route(start, dest)
    if not d0 or (d0.get('wpLen') or 0) < 100:
        print(json.dumps({'error': 'route not built', 'wpLen': d0 and d0.get('wpLen')},
                         ensure_ascii=False)); return
    routeM = d0.get('routeM') or 0
    print(json.dumps({'start': start, 'dest': dest, 'routeM': routeM,
                      'wpLen': d0.get('wpLen')}, ensure_ascii=False), flush=True)

    t0 = time.time()
    n = straddle = offroad = wrong = 0
    turns = []            # 회전 시 차로 준수
    lanef_prev = None
    multi = 0             # 한 번에 여러 차로
    last_cr = 0
    crashes = collections.Counter()
    mark = 0

    while time.time() - t0 < secs:
        d = tel()
        if not d:
            time.sleep(0.3); continue
        g = (d.get('tch') or {}).get('g2') or {}
        m = (d.get('prog') or 0) * (routeM or 1)
        cr = d.get('cr') or 0

        if cr > last_cr:
            crashes.update(d.get('crk') or {})
            print(json.dumps({'crash_at_m': round(m), 'total': cr,
                              'types': d.get('crk')}, ensure_ascii=False), flush=True)
            last_cr = cr

        if (d.get('v') or 0) > 1 and g.get('lat') is not None:
            j = judge_lane(g)
            if j:
                n += 1
                straddle += j['straddle']; offroad += j['offroad']; wrong += j['wrong']
            # 회전 시 차로: 좌회전이면 0에 가까워야, 우회전이면 nl-1
            if g.get('aTurn') in ('L', 'R') and (g.get('aD') or 999) < 40:
                nl = g.get('nl') or 1
                want = 0 if g['aTurn'] == 'L' else nl - 1
                turns.append(abs((g.get('laneF') or 0) - want) <= 0.6)
            lf = g.get('laneF')
            if lanef_prev is not None and lf is not None and abs(lf - lanef_prev) > 1.0:
                multi += 1
            lanef_prev = lf

        if m - mark >= 2000:
            mark = m
            print(json.dumps({'m': round(m), 'crashes': cr}, ensure_ascii=False), flush=True)
        if routeM and m > routeM * 0.97:
            print(json.dumps({'arrived_m': round(m), 'crashes': cr}, ensure_ascii=False), flush=True)
            break
        time.sleep(0.25)

    d = tel() or {}
    print(json.dumps({
        'result': '%s→%s' % (start, dest),
        'driven_m': round((d.get('prog') or 0) * (routeM or 1)),
        'routeM': routeM, 'crashes': d.get('cr'), 'types': d.get('crk'),
        'samples': n,
        'straddle_pct': round(100 * straddle / max(n, 1), 1),
        'offroad_pct': round(100 * offroad / max(n, 1), 1),
        'wrongway_pct': round(100 * wrong / max(n, 1), 1),
        'turn_lane_ok_pct': round(100 * sum(turns) / max(len(turns), 1), 1) if turns else None,
        'turn_samples': len(turns),
        'multi_lane_jumps': multi,
    }, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    import urllib.parse
    main()
