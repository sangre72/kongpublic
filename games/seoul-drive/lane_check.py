#!/usr/bin/env python3
"""차선 준수 측정 (u_5181). 도로 유형별로 기준이 다르다.

★일방통행(o=1): laneOffset 이 -(roadW/2)+(lane+0.5)*LW → 원점은 도로 좌측.
  차로 k 의 중심 = (k+0.5)*LW, 점선은 k*LW.
★왕복(o=0):     laneOffset 이 (k+0.5)*LW(진행방향 부호) → 원점은 중심선.
  진행방향 차로만 보면 되고, 중심선에서의 거리로 판정한다.
  중심선을 넘으면 역주행이므로 별도로 센다.

내가 두 번 틀린 지점이라 스크립트로 고정한다:
  · cross(ct)로 재면 '교사 목표 기준'이라 목표가 틀려도 0 이 나온다.
  · 왕복도로를 좌측 가장자리 기준으로 환산하면 위치가 6~8m 로 나온다.
"""
import urllib.request, json, time, statistics as st, sys

LW = 3.25
CARW = 1.8


def post(p):
    urllib.request.urlopen(urllib.request.Request(
        'http://localhost:8901/ctl', data=json.dumps(p).encode(),
        headers={'Content-Type': 'application/json'}), timeout=5).read()


def sample(secs=100, teacher=True):
    if teacher:
        # ★teach:'fwd' 는 교사 '모드'만 켠다(drv=TEACH). 그 상태로는 차가 안 굴러
        #   속도 0.6 짜리 무효 측정이 나온다. 실제 주행은 경로추종(GEOM)이 한다.
        post({'release': 1}); time.sleep(1)
        post({'teach': 'off'}); time.sleep(1)
        # 경로가 살아있어야 GEOM 이 돈다
        d = json.load(urllib.request.urlopen('http://localhost:8901/tel', timeout=3))
        if not (d.get('autoOn') and (d.get('wpLen') or 0) > 100):
            import subprocess, os
            here = os.path.dirname(os.path.abspath(__file__))
            subprocess.run(['bash', here + '/reload.sh',
                            'http://localhost:8901/index.html?go=1'],
                           capture_output=True, timeout=120)
            time.sleep(16)
        time.sleep(3)
    rows = []
    t0 = time.time()
    while time.time() - t0 < secs:
        try:
            d = json.load(urllib.request.urlopen('http://localhost:8901/tel', timeout=3))
            t = d.get('tch') or {}; g = t.get('g2') or {}
            if t.get('ok') and g.get('lat') is not None:
                rows.append({'lat': g['lat'], 'rw': g.get('roadW') or 0,
                             'nl': g.get('nl'), 'o': g.get('o'),
                             'off': g.get('off'), 'laneF': g.get('laneF'),
                             'v': float(d.get('v') or 0), 'drv': d.get('drv')})
        except Exception:
            pass
        time.sleep(0.2)
    return rows


def judge(r):
    """(차선 뭄, 도로 밖, 역주행) 반환. lat 은 중심선 기준 부호거리(진행방향 보정됨)."""
    lat, rw, o = r['lat'], r['rw'], r['o']
    if o:                                    # 일방통행: 좌측 가장자리 원점
        x = rw / 2 + lat
        edge = min(x % LW, LW - (x % LW))
        return edge < CARW / 2, (x < 0 or x > rw), False
    # 왕복: 중심선 기준. 진행방향 차로는 중심선 오른쪽.
    if lat < 0:                              # 중심선 넘음 = 역주행
        return True, False, True
    k = lat / LW
    edge = min(lat % LW, LW - (lat % LW))
    half = rw / 2
    return edge < CARW / 2, lat > half, False


def main():
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 100
    rows = sample(secs)
    if not rows:
        print('샘플 없음'); return
    J = [judge(r) for r in rows]
    n = len(rows)
    print(json.dumps({
        'samples': n, 'secs': secs, 'v_mean': round(st.mean(r['v'] for r in rows), 1),
        'drv': sorted(set(r['drv'] for r in rows)),
        'straddle_pct': round(100 * sum(1 for a, _, _ in J if a) / n, 1),
        'offroad_pct': round(100 * sum(1 for _, b, _ in J if b) / n, 1),
        'wrongway_pct': round(100 * sum(1 for _, _, c in J if c) / n, 1),
    }, ensure_ascii=False), flush=True)
    import collections
    by = collections.defaultdict(list)
    for r, j in zip(rows, J):
        by[(r['nl'], bool(r['o']))].append(j)
    for key in sorted(by, key=lambda k: -len(by[k])):
        v = by[key]
        print('  %d차로 %s %3d샘플 → 차선뭄 %2.0f%% 도로밖 %2.0f%% 역주행 %2.0f%%' % (
            key[0], '일방' if key[1] else '왕복', len(v),
            100 * sum(1 for a, _, _ in v if a) / len(v),
            100 * sum(1 for _, b, _ in v if b) / len(v),
            100 * sum(1 for _, _, c in v if c) / len(v)), flush=True)


if __name__ == '__main__':
    main()
