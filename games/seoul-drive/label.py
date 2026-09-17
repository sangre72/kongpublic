#!/usr/bin/env python3
"""오드 자동 라벨러 (docs/ODE_data_and_RL_design.md §4). 로우 tel.jsonl → 라벨.

라벨은 로우에 굽지 않는다. 규칙이 바뀌면 이 파일만 고치고 재생성한다:
  python3 label.py data/raw/<date>/<episode>      # labels.npz 갱신

산출(labels.npz):
  Y      (N,3) float32  steer thr brake          — 교사 지령(tch.st/th/br). 최상위 brk/st(적용값) 아님
  NAV    (N,7) float32  [S,L,R,U onehot, aD/200, fin/nl, laneF/nl]
  REASON (N,)  int8     아래 REASONS 인덱스
  STATE  (N,4) float32  [v/17, nlat/10, lat/10, o]
  OK     (N,)  bool     라벨 정합 통과(결손 없음·교사 ok)
"""
import json, sys, numpy as np

REASONS = ['none', 'lead', 'ped', 'signal', 'turn_prep', 'lane_change', 'avoid', 'overtake', 'kturn', 'stall']
TURNS = {'S': 0, 'L': 1, 'R': 2, 'U': 3}


def stop_dist(v):
    """정지거리 = 공주 0.7s + 제동 a=4.0 (rules/ode-teacher-todo B1). 모든 거리는 속도의 함수."""
    return v * 0.7 + v * v / 8.0


def reason_of(row):
    """왜 그 행동인가 — tch/g2/da 로 결정론적으로. 우선순위 = 위험 순."""
    t, g, top = row.get('tch') or {}, row.get('g2') or {}, row.get('top') or {}
    v = float(top.get('v') or 0)
    ped = t.get('ped'); gap = t.get('gap'); sig = t.get('sig')
    sd = stop_dist(v) + 4.0
    if top.get('kt'): return 'kturn'
    if ped is not None and ped < 1e8 and ped < sd * 1.5: return 'ped'
    if sig is not None and sig < sd * 1.5: return 'signal'
    if gap is not None and gap < sd: return 'lead'
    if float(t.get('br') or 0) > 0.3 and v < 0.5: return 'stall'
    fin, lf = g.get('fin'), g.get('laneF')
    if fin is not None and lf is not None and abs(float(fin) - float(lf)) > 0.3:
        return 'turn_prep' if g.get('aTurn') in ('L', 'R', 'U') and (g.get('aD') or 999) < 250 else 'lane_change'
    return 'none'


def label_row(row):
    t, g, top = row.get('tch') or {}, row.get('g2') or {}, row.get('top') or {}
    ok = bool(t.get('ok', True)) and t.get('st') is not None and g.get('nl') is not None
    y = [float(t.get('st') or 0), float(t.get('th') or 0), float(t.get('br') or 0)]
    nl = max(1.0, float(g.get('nl') or 1))
    turn = TURNS.get(g.get('aTurn'), 0)
    nav = [0, 0, 0, 0, min(1.0, float(g.get('aD') or 200) / 200.0),
           float(g.get('fin') if g.get('fin') is not None else g.get('laneF') or 0) / nl,
           float(g.get('laneF') or 0) / nl]
    nav[turn] = 1
    state = [float(top.get('v') or 0) / 17.0, float(g.get('nlat') or 0) / 10.0,
             float(g.get('lat') or 0) / 10.0, 1.0 if g.get('o') else 0.0]
    return y, nav, REASONS.index(reason_of(row)), state, ok


def label_dir(d):
    rows = [json.loads(l) for l in open(f'{d}/tel.jsonl', encoding='utf8')]
    Y, NAV, R, ST, OK = [], [], [], [], []
    for r in rows:
        y, nav, rs, st, ok = label_row(r)
        Y.append(y); NAV.append(nav); R.append(rs); ST.append(st); OK.append(ok)
    np.savez(f'{d}/labels.npz', Y=np.array(Y, np.float32), NAV=np.array(NAV, np.float32),
             REASON=np.array(R, np.int8), STATE=np.array(ST, np.float32), OK=np.array(OK, bool))
    hist = {REASONS[i]: int((np.array(R) == i).sum()) for i in range(len(REASONS))}
    return {'n': len(rows), 'ok': int(sum(OK)), 'reason': hist,
            'steer_abs_mean': round(float(np.abs(np.array(Y)[:, 0]).mean()), 3) if rows else None}


if __name__ == '__main__':
    for d in sys.argv[1:]:
        print(json.dumps({'dir': d, **label_dir(d)}, ensure_ascii=False))
