#!/usr/bin/env python3
"""u_5683 경로 감사(데이터 게이트 공용). 현재 페이지의 /tel 로 경로 품질을 판정한다.
합격 조건: |Δ오프셋| ≤ 1.5m · 오프셋이 도로폭 안 · 같은 이름 조각 차로수 변화 < 2.
사용: python3 path_audit.py            → JSON 한 줄 {'ok':bool, ...}
      python3 path_audit.py --tel f.json
수집기는 이걸로 에피소드를 건너뛰거나 W=0 처리한다."""
import json, sys, urllib.request

def audit(tel, thresh=3.5):
    """★2026-09-27 문턱 보정: 1.5m 기준은 **정상 차로변경(1.63m=반차로)** 까지 전부 불량으로 잡아
    19구간 연속 GATE-SKIP(수집 0건)을 냈다. 실제 결함은 '한 번에 한 차로(3.25m)를 넘는 계단' 이므로
    3.5m(=1차로+여유) 로 올린다. 오너 케이스(밤고개로 9.75m·6.5m)는 그대로 걸린다."""
    w = tel.get('wpDbg') or {}
    tab = [r for r in (w.get('offTab') or []) if isinstance(r, list) and len(r) >= 8 and isinstance(r[1], (int, float))]
    WR = ('Lprep', 'Lexit', 'Lhold', 'Stl', 'Rtl', 'Ltl', 'bridge')
    jumps = []
    for i in range(1, len(tab)):
        a, b = tab[i-1], tab[i]
        if (a[5] in WR) != (b[5] in WR): continue          # 설계된 차로변경은 제외
        if abs(b[1] - a[1]) > thresh: jumps.append([b[0], round(a[1], 2), round(b[1], 2), b[7] or '', b[6]])
    out_road = [[r[0], r[1], r[3]] for r in tab if r[3] and abs(r[1]) > r[3]*3.25/2 + 0.01]
    lanejump = []
    for i in range(1, len(tab)):
        a, b = tab[i-1], tab[i]
        if b[7] and b[7] == a[7] and abs((b[3] or 0) - (a[3] or 0)) >= 2:
            lanejump.append([b[0], a[3], b[3], b[7], a[6], b[6]])
    # ★u_5709(2026-09-28): 같은 자리 반복 충돌은 경로 감사만으로 못 잡는다(이 게이트는 기하만 봤다).
    #   실사고: 자곡로 도착 직전 건물에 박힌 채 '건물 충돌' 1,172회. 같은 위치 충돌 >5 면 그 에피소드는 버린다.
    stuck = 0
    try:
        crk = tel.get('crk') or {}
        stuck = max([int(v) for v in crk.values()] or [0])
    except Exception:
        stuck = 0
    ok = (not jumps) and (not out_road) and (not lanejump) and stuck <= 5
    return {'ok': ok, 'repeat_crash_max': stuck, 'rows': len(tab), 'wpLen': tel.get('wpLen'),
            'jumps': jumps[:8], 'n_jumps': len(jumps),
            'offset_outside_road': out_road[:4], 'n_outside': len(out_road),
            'lane_count_jumps': lanejump[:4], 'n_lane_jumps': len(lanejump)}

if __name__ == '__main__':
    if '--tel' in sys.argv:
        tel = json.load(open(sys.argv[sys.argv.index('--tel')+1]))
    else:
        tel = json.load(urllib.request.urlopen('http://localhost:8901/tel', timeout=10))
    print(json.dumps(audit(tel), ensure_ascii=False))
