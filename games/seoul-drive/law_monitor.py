#!/usr/bin/env python3
"""실시간 도로교통법 위반 감시 (u_5345).

오너: "주행 실시간 모니터링 하면서 도로 교통법 위반 확인. 실시간 데이터는 문제 기록만
하고 제거해서 용량확보. 위반 사항은 그때그때 문제점 파악해서 조치."

정상 프레임은 버리고 **위반·사고만** 기록한다(용량 확보).

판정 항목(.claude/rules/seoul-drive-workflow.md §5 도로교통법):
  1 차로유지   - 차로 중앙 유지, 차선 물기(정당 사유 없이)
  2 중앙선     - 중앙선 침범
  3 회전차로   - 좌회전=1차로 / 우회전=맨오른쪽 차로에서
  4 유턴       - 1차로에서
  5 역주행
  6 신호       - 적신호 정지선 통과
  7 사고       - 추돌·보행자·건물·차로이탈

사용: python3 law_monitor.py <초> "<출발>><도착>" [--out viol.json]
"""
import json, sys, time, subprocess, urllib.request, urllib.parse, os

BASE = os.path.dirname(os.path.abspath(__file__))
LW, CARW = 3.25, 1.8

def tel():
    try:
        d = json.load(urllib.request.urlopen('http://localhost:8901/tel', timeout=3))
        t = d.get('top', d); ch = d.get('tch') or {}
        return t, ch, (ch.get('g2') or {})
    except Exception:
        return None, None, None

def judge(t, ch, g):
    """이 프레임의 위반 목록. 정상이면 []."""
    v = []
    nd, rw, o = g.get('nd'), g.get('roadW') or 0, g.get('o')
    nl = g.get('nl') or 1
    laneF = g.get('laneF')
    speed = t.get('v') or 0
    if not rw or nd is None:
        return v

    # ★u_5345 검산: nl 은 '진행방향 차로수'다(왕복 2차로면 nl=1). roadW 는 도로 전체 폭.
    #   그래서 왕복도로에서 half=roadW/2 로 재면 내 차도 밖(반대차선)까지 정상으로 세거나,
    #   반대로 내 차도 기준 이탈을 놓친다. 내 차도 폭 = nl*LW 로 본다.
    #   (초기판: nd=12.40 > half=3.25 같이 도로폭 4배 밖인데 사고 0 인 모순이 이것 때문)
    myhalf = nl * LW if o else nl * LW      # 진행방향 차도 폭(일방=전체, 왕복=절반)
    half = min(rw / 2, myhalf) if myhalf > 0 else rw / 2
    # 1 도로이탈 — 게임 사고판정(차로이탈)과 대조 가능한 수준에서만 본다
    if nd > half + CARW/2:
        v.append(('도로이탈', f'nd={nd:.2f} > myhalf={half:.2f} (roadW={rw} nl={nl} o={o})'))
    # 2 차선 물기
    #   ★u_5345 실측 정정: 기준점이 도로 유형에 따라 다르다.
    #     일방통행 = 도로 왼쪽 가장자리부터 차로가 깔린다(laneOffset 규약) → 가장자리 기준
    #     왕복     = 중앙선(중심선)부터 내 차도 쪽으로 차로가 깔린다 → 중심선 기준
    #   왕복도로에서 가장자리 기준으로 재면 nd=0.29(중앙선에 붙음)가 '차로중앙'으로 계산된다.
    #   ★2026-09-18 추가 정정: roadW = l*LW 이고 왕복은 그 폭을 양방향이 나눠 쓴다.
    #     l=3, o=false 면 nl=floor(3/2)=1 인데 내 차도 폭은 4.875m(=roadW/2)지 3.25m 가 아니다.
    #     즉 왕복 홀수차로에서 '한 차로 폭'이 LW 가 아니다. 게임 laneOffset 규약대로,
    #     차로중앙 기대 위치를 직접 만들어 그것과의 거리로 물기를 판단한다(나눗셈 나머지 금지).
    lane_w = (rw / max(1, nl)) if o else (rw / 2) / max(1, nl)
    # 내 차도 안에서 중앙선(왕복)/왼쪽가장자리(일방) 기준 위치
    pos = nd if not o else (rw/2 - nd)
    k = int(pos // lane_w)
    center = (k + 0.5) * lane_w
    edge = abs(pos - center)                 # 차로중앙에서 벗어난 거리
    straddle = edge > (lane_w - CARW) / 2     # 차폭이 차로를 삐져나오면 물기
    # 3 중앙선/역주행 — nlat 은 중심선 부호거리(양수=정상차선)
    nlat = g.get('nlat')
    if (not o) and nlat is not None and nlat < -0.9:
        v.append(('역주행/중앙선침범', f'nlat={nlat:.2f}'))
    # 4 회전 차로 — 회전 임박(aD 가까움)일 때만 본다
    aTurn, aD, fin = g.get('aTurn'), g.get('aD'), g.get('fin')
    if aTurn in ('L','R','U') and aD is not None and aD < 30 and laneF is not None:
        want = 0 if aTurn in ('L','U') else nl - 1
        if abs(laneF - want) > 0.6:
            nm = {'L':'좌회전','R':'우회전','U':'유턴'}[aTurn]
            v.append((f'{nm} 차로위반', f'laneF={laneF:.2f} want={want} nl={nl} aD={aD}'))
    # 5 차선물기는 '정당 사유'(차로변경중/회피중) 제외 — laneMoving 없으면 무단으로 본다
    if straddle and speed > 1:
        moving = abs((laneF or 0) - (fin if fin is not None else (laneF or 0))) > 0.05
        if not moving:
            v.append(('차선물기(무단)', f'off_center={edge:.2f} lane_w={lane_w:.2f} nd={nd:.2f} rw={rw} nl={nl} o={o} laneF={laneF}'))
    # 6 신호 위반 — 적신호인데 정지선 지나 계속 감
    sig, sigStop = ch.get('sig'), ch.get('sigStop')
    if sig is not None and sigStop is not None and sig < 0 and speed > 2:
        v.append(('신호위반', f'sig={sig} v={speed:.1f}'))
    return v

def main():
    secs = float(sys.argv[1]); pair = sys.argv[2]
    out = sys.argv[sys.argv.index('--out')+1] if '--out' in sys.argv else '/tmp/violations.json'
    a, b = pair.split('>')
    url = ('http://localhost:8901/index.html?go=1&from=' + urllib.parse.quote(a)
           + '&to=' + urllib.parse.quote(b))
    r = subprocess.run(['bash', f'{BASE}/reload.sh', url, '120'], capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        print(json.dumps({'reload_fail': r.stdout[-200:]}, ensure_ascii=False)); return 1

    t0 = time.time()
    viol = []            # 위반만 저장(정상 프레임은 버린다)
    counts = {}
    last_cr, last_tp = 0, 0
    frames = 0
    # 같은 위반이 연속 프레임으로 쏟아지는 것 방지 — 종류별 2초 쿨다운
    last_seen = {}

    while time.time() - t0 < secs:
        t, ch, g = tel()
        if not t: time.sleep(0.3); continue
        frames += 1
        now = round(time.time() - t0, 1)
        m = round((t.get('prog') or 0) * (t.get('routeM') or 0))

        cr = t.get('cr') or 0
        if cr > last_cr:
            e = {'t': now, 'm': m, 'kind': '사고', 'detail': t.get('crk'), 'v': t.get('v'),
                 'g2': {k: g.get(k) for k in ('roadW','nl','laneF','aTurn','aD','lat','o')}}
            viol.append(e); counts['사고'] = counts.get('사고',0)+1
            print(json.dumps(e, ensure_ascii=False), flush=True); last_cr = cr

        tp = t.get('tpN') or 0
        if tp > last_tp:
            e = {'t': now, 'm': m, 'kind': '경로복귀', 'detail': {'tpPath': t.get('tpPath'), 'blkStuck': t.get('blkStuck'), 'blkCenter': t.get('blkCenter')}}
            viol.append(e); counts['경로복귀'] = counts.get('경로복귀',0)+1
            print(json.dumps(e, ensure_ascii=False), flush=True); last_tp = tp

        for kind, detail in judge(t, ch, g):
            if now - last_seen.get(kind, -9) < 2.0: continue
            last_seen[kind] = now
            e = {'t': now, 'm': m, 'kind': kind, 'detail': detail, 'v': round(t.get('v') or 0,1)}
            viol.append(e); counts[kind] = counts.get(kind,0)+1
            print(json.dumps(e, ensure_ascii=False), flush=True)

        if (t.get('prog') or 0) > 0.97: break
        time.sleep(0.25)

    t, ch, g = tel(); t = t or {}
    summary = {'route': pair, 'secs': secs, 'frames_seen': frames,
               'driven_m': round((t.get('prog') or 0)*(t.get('routeM') or 0)),
               'violations': counts, 'total_violations': len(viol),
               'cr': t.get('cr'), 'crk': t.get('crk'), 'tpN': t.get('tpN')}
    json.dump({'summary': summary, 'violations': viol}, open(out,'w',encoding='utf8'),
              ensure_ascii=False, indent=1)
    print(json.dumps({'SUMMARY': summary}, ensure_ascii=False), flush=True)
    return 0

if __name__ == '__main__':
    sys.exit(main())
