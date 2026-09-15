"""주행 평가 — '사람처럼 운전하는가' (u_5016).

오너 지적: 코드 품질이 아니라 주행 자체를 평가해야 한다.
  목적지로 가려면 좌/우회전·유턴을 해야 하고, 차선을 지켜야 하고,
  필요할 때 차선을 바꿔야 한다. 그게 실제로 되는지 측정한다.

측정 항목(운전에 필요한 것들을 직접 정했다):
  1) 차로유지   — 도로 위 비율, 차로중심 이탈 거리
  2) 조향 건전성 — 포화(|steer|>0.95) 비율. 항상 끝까지 꺾여 있으면 조향을 '하는' 게 아니다
  3) 회전       — 방향각 변화로 좌/우회전·유턴 횟수를 센다
  4) 목적지 도달 — 경로 진행률이 실제로 올라가는가
  5) 속도       — 목표속도 대비, 정지 비율
  6) 안전       — 사고, 급제동
사용: python3 eval_driving.py [초]
"""
import sys, time, json, math
import numpy as np
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import capture as C
from decode import decode

def main(secs=60.0):
    if C.find_window() is None:
        print(json.dumps({'err': 'no chrome window'})); return
    C.start_background(); time.sleep(1)
    seq = None; R = []
    t0 = time.time()
    try:
        while time.time() - t0 < secs:
            f, seq = C.latest(seq)
            if f is None: continue
            d = decode(f)
            if d: R.append((time.time()-t0, d))
    finally:
        C.stop_background()
    if not R:
        print(json.dumps({'err': 'no frames decoded'})); return

    t   = np.array([r[0] for r in R])
    st  = np.array([r[1]['steer'] for r in R])
    v   = np.array([r[1]['v'] for r in R]) * 3.6
    ln  = np.array([r[1]['lane'] for r in R])
    on  = np.array([r[1]['on_road'] for r in R])
    br  = np.array([r[1]['brake'] for r in R])
    cr  = np.array([r[1]['crashes'] for r in R])
    hd  = np.array([r[1].get('heading', 0) for r in R])
    pg  = np.array([r[1].get('progress', 0) for r in R])
    au  = np.array([r[1].get('auto', 0) for r in R])

    # 회전 판정: 방향각 누적변화. 언랩해서 연속으로 만든 뒤 구간별 총회전량을 본다
    uh = np.unwrap(hd)
    # 2초 창으로 회전량 측정
    turns = {'left': 0, 'right': 0, 'uturn': 0}
    win = 2.0
    i = 0
    while i < len(t):
        j = i
        while j < len(t) and t[j] - t[i] < win: j += 1
        if j >= len(t): break
        d = uh[j-1] - uh[i]
        deg = math.degrees(d)
        if deg > 140:   turns['uturn'] += 1;  i = j
        elif deg < -140: turns['uturn'] += 1; i = j
        elif deg > 55:  turns['right'] += 1;  i = j
        elif deg < -55: turns['left']  += 1;  i = j
        else: i += 1

    sat = float((np.abs(st) > 0.95).mean())
    out = {
        'frames': len(R), 'secs': round(float(t[-1]), 1),
        # 1) 차로유지
        'on_road_pct': round(float(on.mean()*100), 1),
        'lane_dist_median_m': round(float(np.median(ln)), 2),
        # 2) 조향 건전성
        'steer_saturated_pct': round(sat*100, 1),
        'steer_std': round(float(st.std()), 3),
        # 3) 회전
        'turns': turns,
        'heading_total_deg': round(float(math.degrees(abs(uh[-1]-uh[0]))), 0),
        # 4) 목적지
        'autopilot_pct': round(float(au.mean()*100), 1),
        'progress_start': round(float(pg[0]), 3),
        'progress_end': round(float(pg[-1]), 3),
        # 5) 속도
        'speed_median_kmh': round(float(np.median(v)), 1),
        'stopped_pct': round(float((v < 3).mean()*100), 1),
        # 6) 안전
        # ★max-min 은 틀린다(u_5016 실측: 사고 0인데 124 로 나왔다).
        #   사고가 나면 리셋으로 0 으로 돌아가므로, '증가한 순간'만 센다.
        'crashes': int((np.diff(cr) > 0).sum()),
        'hard_brake_pct': round(float((br > 0.7).mean()*100), 1),
    }
    # 판정
    verdict = []
    if out['on_road_pct'] < 95: verdict.append('차로유지 미달')
    if out['steer_saturated_pct'] > 20: verdict.append('조향 포화')
    if sum(turns.values()) == 0: verdict.append('회전 없음(직진만)')
    if out['autopilot_pct'] > 5 and out['progress_end'] <= out['progress_start']:
        verdict.append('경로 진행 안 함')
    out['verdict'] = verdict or ['통과']
    print(json.dumps(out, ensure_ascii=False))

if __name__ == '__main__':
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 60.0)
