#!/usr/bin/env python3
"""u_5204/u_5205 — 스테이지 결과 1줄(JSON) → 텔레그램 한글 보고문."""
import sys, json

d = json.loads(sys.stdin.read())

if 'SUMMARY' in d:
    s = d['SUMMARY']
    print(
        "■ 전체 완료 요약\n"
        "구간 %s개 (경로실패 %s) · 도착 %s · 누적 %skm\n"
        "사고 %s건 (무사고 구간 %s개) %s%s\n\n"
        "[법규]\n무단 차선물기 %s%% (정당한 회피·차로변경 %s%% 별도)\n도로이탈 %s%% · 중앙선침범 %s%%\n"
        "회전차로 준수 %s%% (표본 %s)\n\n"
        "[이벤트 합계]\n"
        "좌회전 %s회 · 우회전 %s회\n"
        "차로변경 %s회 (급변경 %s회)\n"
        "회피 %s회 · 돌발상황 대처 %s회 · 서행 %s회\n"
        "추월 %s회\n"
        "보행자 조우 %s회 중 감속 %s회" % (
            s['runs'], s['route_fail'], s['arrived'], s['driven_km'],
            s['total_crashes'], s['zero_crash_runs'], s.get('crash_types') or '',
            ('  ※불가항력 %s건 제외' % s['unavoidable']) if s.get('unavoidable') else '',
            s['straddle_pct'], s.get('straddle_ok_pct', 0), s['offroad_pct'], s['wrongway_pct'],
            s.get('turn_lane_ok_pct'), s['turn_samples'],
            s.get('turn_L', 0), s.get('turn_R', 0),
            s.get('lane_changes', 0), s['multi_lane_jumps'],
            s.get('avoid', 0), s.get('emergency', 0), s.get('slowdowns', 0),
            s['overtakes'], s['ped_events'], s['ped_ok']))

elif d.get('error'):
    print("[%s구간] %s → %s\n경로 생성 실패 (지도 구석이거나 이름 중복)"
          % (d['i'], d['from'], d['to']))

else:
    ok = '도착' if d['arrived'] else '시간상한'
    print(
        "[%s구간] %s → %s\n"
        "%s · %sm / %sm · %dm%ds\n"
        "사고 %s건 %s%s\n\n"
        "[법규]\n무단 차선물기 %s%% (정당한 회피·차로변경 %s%% 별도)\n이탈 %s%% · 중앙선 %s%%\n"
        "회전차로 준수 %s%% (표본 %s)\n\n"
        "[이벤트]\n"
        "좌회전 %s회 · 우회전 %s회\n"
        "차로변경 %s회 (급변경 %s회)\n"
        "회피 %s회 · 돌발상황 대처 %s회 · 서행 %s회\n"
        "추월 %s회\n"
        "보행자 조우 %s회 중 감속 %s회" % (
            d['i'], d['from'], d['to'],
            ok, d['driven_m'], d['routeM'], d['secs'] // 60, d['secs'] % 60,
            d['crashes'], d['types'] or '',
            ('  ※불가항력 %s건 제외' % d['unavoidable']) if d.get('unavoidable') else '',
            d['straddle_pct'], d.get('straddle_ok_pct', 0), d['offroad_pct'], d['wrongway_pct'],
            d.get('turn_lane_ok_pct'), d['turn_samples'],
            d.get('turn_L', 0), d.get('turn_R', 0),
            d.get('lane_changes', 0), d['multi_lane_jumps'],
            d.get('avoid', 0), d.get('emergency', 0), d.get('slowdowns', 0),
            d['overtakes'], d['ped_events'], d['ped_ok']))
