#!/usr/bin/env python3
"""u_5203 — 서울 전역 60지점(30구간) 교차로 주행 일제 테스트.

오너 지시: "서울시내 양 극단 랜덤 30군데(=60지점) 교차로 주행 테스트.
도로교통법·차선·좌우회전·보행자 대응·추월까지 도로에서 쓸 수 있는 모든 테크닉 확인.
다 잘 되면 학습 데이터 수집."

채점 항목(구간별):
  crashes      사고 건수·종류
  straddle     차선 밟고 주행 비율   ← 차선 경계는 '도로 가장자리'부터 LW 배수
  offroad      도로 이탈 비율
  wrongway     중앙선 침범 비율      ← nlat(부호거리) 사용
  turn_lane    회전 전 올바른 차로 점유율(좌→1차로, 우→끝차로)
  ped_ok       보행자 접근 시 감속 여부
  overtake     추월 시도 횟수/성공
  multi_jump   한 번에 2차로 이상 변경 횟수

★측정 원칙(이 세션에서 비싸게 배운 것):
  · 새 지표는 반드시 게임 자체 판정(onroad)과 대조한다. 예전에 lat 을 도로 좌표로
    오해해 사고 2건짜리 주행을 '도로밖 75.8%' 로 채점했고, 차선 경계를 중심선부터
    세어 3·5차로 도로에서 차로 정중앙을 '차선 밟음' 으로 찍었다(79.8% 허수).
  · 차가 실제로 움직이는 표본만 센다(v>1). 정지 중 표본은 전부 완벽해 보인다.

사용: python3 sweep_test.py [--pairs /tmp/pairs.json] [--secs 420] [--limit N]
"""
import argparse, collections, json, subprocess, sys, time, urllib.parse, urllib.request

HERE = __file__.rsplit('/', 1)[0]
LW = 3.25        # 차로 폭(m)
CARW = 1.8       # 차폭(m)


def tel():
    try:
        return json.load(urllib.request.urlopen('http://localhost:8901/tel', timeout=3))
    except Exception:
        return None


def set_route(start, dest, wait=45):
    url = ('http://localhost:8901/index.html?go=1'
           '&from=' + urllib.parse.quote(start) + '&to=' + urllib.parse.quote(dest))
    subprocess.run(['bash', HERE + '/reload.sh', url], capture_output=True, timeout=180)
    for _ in range(wait):
        time.sleep(1)
        d = tel()
        if d and (d.get('wpLen') or 0) > 40:
            return d
    return tel()


def judge_lane(g):
    """차로 준수 판정. nd=도로 중심선까지 거리(부호없음), nlat=같은 것의 부호거리."""
    nd, rw, o = g.get('nd'), g.get('roadW') or 0, g.get('o')
    if nd is None or not rw:
        return None
    half = rw / 2
    offroad = nd > half
    # 차선은 도로 가장자리부터 LW 배수 지점에 그어진다(중심선 기준이 아니다).
    x = half - nd
    edge = min(x % LW, LW - (x % LW))
    straddle = edge < CARW / 2
    wrong = False
    # ★u_5227 오너 지적: "회전각이 안 맞아서 잠시 앞대가리가 중앙선 침범은 할 수 있지."
    #   맞다. 물리적으로 불가피하다 — 회전반경 5.5m 에서 차체 스윕폭이 3.28m 인데
    #   차로폭은 3.25m 다. 즉 최소회전반경으로 돌면 반드시 0.03m 넘친다.
    #   차 길이 4.6m 가 만드는 오프트래킹이라 운전을 잘해도 못 피한다.
    #   ⇒ 회전 중(aTurn L/R, 교차로 근접)에는 중앙선 침범을 위반으로 세지 않는다.
    #     직진 중 침범은 그대로 위반이다.
    in_turn = (g.get('aTurn') in ('L', 'R')) and (g.get('aD') is not None) and (g['aD'] < 20)
    if not o and not in_turn:
        nlat = g.get('nlat')
        if nlat is not None:
            wrong = nlat < -0.9
    return {'straddle': straddle, 'offroad': offroad, 'wrong': wrong}


def run_one(start, dest, secs):
    """secs 는 '상한'이 아니라 기본값이다. 실측 평균속도가 7m/s 라
       30km 경로는 70분이 걸린다 — 고정 7분으로 끊으면 긴 구간은 전부
       '미완주'로만 남고 회전·보행자 표본을 못 모은다. 경로 길이에 맞춰 늘린다."""
    # ★경로 생성이 실패하는 지점이 있다(실측: 지도 구석의 도로명, 중복 이름).
    #   그런 구간은 1회 재시도만 하고 넘어간다 — 30구간 전체를 붙잡지 않는다.
    for attempt in (1, 2):
        d0 = set_route(start, dest)
        routeM = (d0 or {}).get('routeM') or 0
        wpLen = (d0 or {}).get('wpLen') or 0
        if routeM and wpLen >= 40:
            break
    else:
        pass
    if not routeM or wpLen < 40:
        return {'from': start, 'to': dest, 'error': 'route_fail', 'wpLen': wpLen}
    # 평균 6m/s 가정 + 여유 1.4배, 최소 secs, 최대 40분
    # 구간당 상한. 목적은 '완주'가 아니라 '테크닉 표본 수집'이다
    # (교차로·회전·보행자·추월). 짧은 경로는 도착으로, 긴 경로는 상한으로 끝난다.
    budget = min(secs, max(300.0, routeM / 6.0 * 1.4))

    t0 = time.time()
    n = straddle = offroad = wrong = multi = 0
    turns, lanef_prev = [], None
    nl_prev = None                   # 같은 도로에서만 급차로변경을 센다
    straddle_ok = 0                  # u_5207: 정당한 차선 밟기(차로변경·회피 중)
    crashes = collections.Counter()
    last_cr, mmax = 0, 0
    ped_events, ped_ok = 0, 0        # 보행자 20m 이내 접근 / 그때 감속했나
    ped_active = False
    ot_max = 0
    # ★u_5205: 스테이지별 이벤트 집계. 좌/우회전, 회피, 돌발상황 대처.
    turn_L = turn_R = 0              # 실제로 통과한 교차로 회전 횟수
    turn_seen = None                 # 같은 회전을 여러 프레임 세지 않기 위한 상태
    avoid_n = 0                      # 회피: 장애물 근접 + 조향으로 비켜난 경우
    avoid_active = False
    emerg_n = 0                      # 돌발: 급제동(brake>0.7) 이벤트
    emerg_active = False
    slow_n = 0                       # u_5206 서행(보도 보행자 대비 예방 감속)
    slow_active = False
    lane_chg = 0                     # 차로 변경 완료 횟수(1칸)
    lane_base = None
    stall_t, last_m = time.time(), 0

    while time.time() - t0 < budget:
        d = tel()
        if not d:
            time.sleep(0.3); continue
        g = (d.get('tch') or {}).get('g2') or {}
        # ★tch 는 평평하다 — dbg 라는 하위 키는 없다(실측: tch keys 에 dbg 없음).
        #   이걸 .get('dbg') 로 읽어서 ped/cap/emergency/avoid 카운터가 전부
        #   0 으로 나왔다(1·2구간 보고서에 그대로 나갔다). tch 자체를 쓴다.
        dbg = d.get('tch') or {}
        m = (d.get('prog') or 0) * routeM
        mmax = max(mmax, m)
        cr = d.get('cr') or 0
        v = d.get('v') or 0
        ot_max = max(ot_max, d.get('otN') or 0)

        if cr > last_cr:
            crashes.update(d.get('crk') or {})
            last_cr = cr

        # ★최상위 brk/st 는 차에 '적용된' 값이라 교사 지령과 다르다
        #   (실측: 교사 br=1 st=-0.70 인데 최상위는 brk=0.149 st=0.01).
        #   급제동·회피 판정은 교사 지령(tch.br / tch.st)으로 해야 한다.
        #   이걸 몰라서 emergency·avoid 가 전 구간 0 으로 나왔다.
        brk = (d.get('tch') or {}).get('br')
        brk = brk if isinstance(brk, (int, float)) else (d.get('brk') or 0)
        st_ = (d.get('tch') or {}).get('st')
        st_ = abs(st_) if isinstance(st_, (int, float)) else abs(d.get('st') or 0)
        # 보행자 대응: 20m 안으로 들어온 구간을 1회 이벤트로 보고, 그동안 감속했나
        pd = dbg.get('ped')
        if isinstance(pd, (int, float)) and pd > 1e8:
            pd = None                      # 1e9 = '전방에 보행자 없음' 센티넬
        # ★트리거 거리도 속도비례여야 한다. 20m 고정이면 고속에서는 이미
        #   늦은 시점부터 세고, 저속에서는 아무 위험도 없는 상황을 '조우'로
        #   집계한다(실측: 조우 22회 중 실제 사고는 1건 — 과다집계).
        #   그리고 감속 판정은 교사 지령(tch.br)으로 봐야 한다 — 최상위 brk 는
        #   차에 적용된 값이라 다르다(같은 실수를 여기서 또 했다).
        ped_trig = max(12.0, (v * 0.7 + (v * v) / 8.0) * 1.1)
        if pd is not None and pd < ped_trig:
            if not ped_active:
                ped_active = True; ped_events += 1
                ped_v0 = v
            if v < max(1.0, ped_v0 * 0.7) or brk > 0.3:
                ped_ok += 0 if ped_active == 'ok' else 1
                ped_active = 'ok'
        elif pd is None or pd >= ped_trig * 1.3:
            ped_active = False

        # ── 이벤트 집계(u_5205) ────────────────────────────────
        # ★tch.d 는 조향 항(diff*1.8)이지 거리가 아니다 — 한 번 착각해서
        #   "앞차와 0m 로 붙어 간다"고 오판했다(u_5206). gap 이 실제 거리(m).
        obst = (d.get('tch') or {}).get('gap')

        # 회전: aTurn 이 L/R 이고 교차로에 근접(aD<15)했다가 벗어나면 1회로 센다
        at, ad = g.get('aTurn'), g.get('aD')
        if at in ('L', 'R') and ad is not None and ad < 15:
            if turn_seen != at:
                turn_seen = at
                if at == 'L': turn_L += 1
                else: turn_R += 1
        elif ad is None or ad > 40:
            turn_seen = None

        # 회피: 전방 장애물 8m 이내인데 제동보다 조향으로 비켜난 경우
        if obst is not None and 0 <= obst < 8 and st_ > 0.25 and v > 3:
            if not avoid_active:
                avoid_n += 1; avoid_active = True
        elif obst is None or obst > 12:
            avoid_active = False

        # 서행: 보도 보행자 때문에 속도 상한이 걸린 구간
        cap = dbg.get('cap')
        if isinstance(cap, (int, float)) and cap < v:
            if not slow_active:
                slow_n += 1; slow_active = True
        elif not isinstance(cap, (int, float)):
            slow_active = False

        # 돌발상황 대처: 급제동(brake > 0.7)
        if brk > 0.7:
            if not emerg_active:
                emerg_n += 1; emerg_active = True
        elif brk < 0.3:
            emerg_active = False

        if v > 1 and g.get('nd') is not None:
            j = judge_lane(g)
            if j:
                n += 1
                offroad += j['offroad']; wrong += j['wrong']
                if j['straddle']:
                    # ★u_5207 오너 기준: "주변 차로의 방해로 어쩔 수 없이 회피한 건
                    #   인정하지만 무단 이탈은 안 됨."
                    #   차선을 밟는 데에는 정당한 사유가 있다:
                    #     · 차로변경 중(laneF 가 정수가 아님) — 밟고 지나가는 게 정상
                    #     · 장애물 회피 중(전방 8m 이내 + 조향)
                    #   그 외에 차선을 물고 가는 건 무단이다. 둘을 갈라 센다.
                    mid_change = (g.get('laneF') is not None
                                  and abs(g['laneF'] - round(g['laneF'])) > 0.08)
                    dodging = (obst is not None and 0 <= obst < 8 and st_ > 0.25)
                    if mid_change or dodging:
                        straddle_ok += 1
                    else:
                        straddle += 1
            if g.get('aTurn') in ('L', 'R') and (g.get('aD') or 999) < 40:
                nl = g.get('nl') or 1
                want = 0 if g['aTurn'] == 'L' else nl - 1
                turns.append(abs((g.get('laneF') or 0) - want) <= 0.6)
            lf = g.get('laneF')
            # ★급차로변경 판정에는 '같은 도로'라는 전제가 필요하다.
            #   도로가 바뀌면 차로수가 달라져 laneF 가 재설정되는데, 그걸
            #   '한 번에 여러 차로 이동'으로 오해하면 구간당 37~46회가 찍힌다.
            #   실측으로는 프레임간 최대 변화가 0.83차로(=순차 변경)였다.
            nl_now = g.get('nl')
            if (lanef_prev is not None and lf is not None
                    and nl_prev == nl_now
                    and abs(lf - lanef_prev) > 1.0):
                multi += 1
            nl_prev = nl_now
            # 차로변경 '완료' = 정수 차로가 바뀐 시점
            if lf is not None:
                li = round(lf)
                if lane_base is None: lane_base = li
                elif li != lane_base:
                    lane_chg += 1; lane_base = li
            lanef_prev = lf

        # 정체 감지 — 120초간 진행 없으면 그 구간은 STUCK 으로 끝낸다
        if m - last_m > 5:
            last_m, stall_t = m, time.time()
        elif time.time() - stall_t > 120:
            break

        if m > routeM * 0.97:
            break
        time.sleep(0.25)

    arrived = mmax > routeM * 0.97
    return {
        'from': start, 'to': dest, 'routeM': round(routeM),
        'driven_m': round(mmax), 'arrived': arrived,
        # ★u_5206: 불가항력(정지거리 안에서 튀어나온 무단횡단)은 집계만 하고
        #   사고 점수에서 뺀다. 오너 판단 — "그건 도리가 없다".
        'crashes': sum(v for k, v in crashes.items() if '불가항력' not in k),
        'unavoidable': sum(v for k, v in crashes.items() if '불가항력' in k),
        'types': dict(crashes),
        'samples': n,
        'straddle_pct': round(100 * straddle / max(n, 1), 1),
        'straddle_ok_pct': round(100 * straddle_ok / max(n, 1), 1),
        'offroad_pct': round(100 * offroad / max(n, 1), 1),
        'wrongway_pct': round(100 * wrong / max(n, 1), 1),
        'turn_lane_ok_pct': round(100 * sum(turns) / max(len(turns), 1), 1) if turns else None,
        'turn_samples': len(turns),
        'ped_events': ped_events, 'ped_ok': ped_ok,
        'overtakes': ot_max,
        'turn_L': turn_L, 'turn_R': turn_R,
        'avoid': avoid_n, 'emergency': emerg_n, 'lane_changes': lane_chg,
        'slowdowns': slow_n,
        'avoid_steer': (tel() or {}).get('avoidN', 0),   # u_5223 회피 조향 발동
        'multi_lane_jumps': multi,
        'secs': round(time.time() - t0),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pairs', default='/tmp/pairs.json')
    ap.add_argument('--secs', type=float, default=420)
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--out', default='/tmp/sweep_results.json')
    a = ap.parse_args()

    pairs = json.load(open(a.pairs))
    if a.limit:
        pairs = pairs[:a.limit]
    results = []
    for i, p in enumerate(pairs, 1):
        r = run_one(p['from'], p['to'], a.secs)
        r['i'] = i
        results.append(r)
        print(json.dumps(r, ensure_ascii=False), flush=True)
        json.dump(results, open(a.out, 'w'), ensure_ascii=False, indent=1)

    ok = [r for r in results if not r.get('error')]
    tot_s = sum(r['samples'] for r in ok) or 1
    agg = {
        'runs': len(results), 'route_fail': len(results) - len(ok),
        'arrived': sum(1 for r in ok if r['arrived']),
        'total_crashes': sum(r['crashes'] for r in ok),
        'unavoidable': sum(r.get('unavoidable', 0) for r in ok),
        'zero_crash_runs': sum(1 for r in ok if r['crashes'] == 0),
        'driven_km': round(sum(r['driven_m'] for r in ok) / 1000, 1),
        'straddle_pct': round(sum(r['straddle_pct'] * r['samples'] for r in ok) / tot_s, 1),
        'straddle_ok_pct': round(sum(r.get('straddle_ok_pct', 0) * r['samples'] for r in ok) / tot_s, 1),
        'offroad_pct': round(sum(r['offroad_pct'] * r['samples'] for r in ok) / tot_s, 1),
        'wrongway_pct': round(sum(r['wrongway_pct'] * r['samples'] for r in ok) / tot_s, 1),
        'turn_samples': sum(r['turn_samples'] for r in ok),
        'ped_events': sum(r['ped_events'] for r in ok),
        'ped_ok': sum(r['ped_ok'] for r in ok),
        'overtakes': sum(r['overtakes'] for r in ok),
        'multi_lane_jumps': sum(r['multi_lane_jumps'] for r in ok),
        'turn_L': sum(r.get('turn_L', 0) for r in ok),
        'turn_R': sum(r.get('turn_R', 0) for r in ok),
        'avoid': sum(r.get('avoid', 0) for r in ok),
        'emergency': sum(r.get('emergency', 0) for r in ok),
        'slowdowns': sum(r.get('slowdowns', 0) for r in ok),
        'lane_changes': sum(r.get('lane_changes', 0) for r in ok),
    }
    tn = agg['turn_samples']
    if tn:
        agg['turn_lane_ok_pct'] = round(
            sum((r['turn_lane_ok_pct'] or 0) * r['turn_samples'] for r in ok) / tn, 1)
    ct = collections.Counter()
    for r in ok:
        ct.update(r['types'])
    agg['crash_types'] = dict(ct)
    print(json.dumps({'SUMMARY': agg}, ensure_ascii=False), flush=True)
    json.dump({'results': results, 'summary': agg},
              open(a.out, 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
