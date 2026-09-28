#!/usr/bin/env python3
"""u_5686 전체 지도 감사. 사용: python3 map_audit.py [data/data6.js] [--out data/map_audit_2026-09-27.json]

결함 분류
  A lane_jump    같은 이름·같은 일방성으로 이어지는 조각 사이 차로수 차이 >= 2
  B untagged     lanes 태그 없음(ld=1) → 등급 기본값 추정
  C overlap      같은 이름 평행 차도끼리 간격 < (w1+w2)/2 - 1m (겹쳐 그려짐)
  D mixed_oneway 같은 이름 체인에 일방/양방이 섞임
  E offset_out   주행차로(맨 오른쪽) 오프셋이 도로폭 밖으로 나가는 레코드
출력: 결함별 건수·도로연장 비중, 길이 상위 50, 학습·평가 제외 way 목록, 무결 비중.
"""
import json, math, sys, os
from collections import defaultdict

LANE_M = 3.25

def in_scope_rec(rec):
    """★u_5705 SCOPE: 강남구+송파구 안의 레코드만 감사/집계한다(--scope 로 켠다)."""
    try:
        from scope import in_scope
    except Exception:
        return True
    p = rec.get('p') or []
    if not p: return False
    mid = p[len(p)//2]
    return in_scope(mid[0], mid[1])

def load(path):
    s = open(path, encoding='utf-8').read()
    body = s[s.index('const CHUNKS=') + len('const CHUNKS='):]
    d = 0
    for j, ch in enumerate(body):
        if ch == '{': d += 1
        elif ch == '}':
            d -= 1
            if d == 0: break
    CH = json.loads(body[:j + 1])
    return [r for c in CH.values() for r in (c.get('r') or [])]

def seglen(r):
    p = r.get('p') or []
    return sum(math.hypot(p[i+1][0]-p[i][0], p[i+1][1]-p[i][1]) for i in range(len(p)-1))

def audit(recs):
    for r in recs: r['_len'] = seglen(r)
    total = sum(r['_len'] for r in recs) or 1.0
    by_name = defaultdict(list)
    for r in recs:
        if r.get('n'): by_name[r['n']].append(r)
    D = {k: [] for k in ('lane_jump', 'untagged', 'overlap', 'mixed_oneway', 'offset_out')}

    # B untagged
    for r in recs:
        if r.get('ld'): D['untagged'].append(r)
    # E offset_out : 주행차로 중심이 도로 반폭을 넘는가(일방=전폭 기준, 왕복=내 차도)
    for r in recs:
        l = r.get('l') or 2; half = l * LANE_M / 2
        off = (half - LANE_M / 2) if r.get('o') else ((max(1, l // 2) - 0.5) * LANE_M)
        if abs(off) > half + 0.01: D['offset_out'].append(r)
    # A lane_jump + D mixed_oneway : 같은 이름 안에서 끝점이 맞닿는 조각 쌍
    for nm, rs in by_name.items():
        # ★2026-09-28 수정: 같은 이름 체인에 일방/양방이 섞였다고 **전 조각을 결함으로 세면 과다계상**이다.
        #   실측: 삼성로 31 일방 + 양방 1, 언주로 47 일방 + 양방 2 = 분리 차도에 미태그 토막이 몇 개 낀 정상 형태.
        #   소수쪽(<=25%) 조각만 결함으로 본다. 반반이면 진짜 혼재이므로 전부 센다.
        ones = [r for r in rs if r.get('o')]; twos = [r for r in rs if not r.get('o')]
        if ones and twos:
            minor = twos if len(twos) <= len(ones) else ones
            if len(minor) / max(1, len(rs)) <= 0.25:
                for r in minor: D['mixed_oneway'].append(r)
            else:
                # ★2026-09-28 2차 수정: 반반 체인(88개·92.7km)은 **원본 데이터가 실제로 섞여 있다** —
                #   올림픽로 실측: OSM 에서 oneway=yes 42 · no 7 · 미태그 20. 분리구간과 비분리구간이 공존하는 실제 도로다.
                #   따라서 체인 전체가 아니라 **oneway 미태그(od=1) 조각만** 결함(=추정으로 채운 부분)으로 센다.
                amb = [r for r in rs if r.get('od')]
                for r in amb: D['mixed_oneway'].append(r)
        for i, a in enumerate(rs):
            pa = a.get('p') or []
            if not pa: continue
            for b in rs[i+1:]:
                pb = b.get('p') or []
                if not pb or bool(a.get('o')) != bool(b.get('o')): continue
                touch = any(math.hypot(x[0]-y[0], x[1]-y[1]) < 1.0 for x in (pa[0], pa[-1]) for y in (pb[0], pb[-1]))
                if touch and abs((a.get('l') or 0) - (b.get('l') or 0)) >= 2:
                    D['lane_jump'].append(a); D['lane_jump'].append(b)
    # C overlap : 같은 이름 평행 조각(방향 ±20°) 간격이 폭 합의 절반보다 가까움
    def ang(r):
        p = r.get('p') or []
        if len(p) < 2: return None
        return math.atan2(p[-1][1]-p[0][1], p[-1][0]-p[0][0])
    for nm, rs in by_name.items():
        if len(rs) < 2: continue
        for i, a in enumerate(rs):
            aa = ang(a); pa = a.get('p') or []
            if aa is None: continue
            for b in rs[i+1:]:
                ab = ang(b); pb = b.get('p') or []
                if ab is None: continue
                da = abs(((aa - ab + math.pi) % (2*math.pi)) - math.pi)
                if da > math.radians(20) and abs(da - math.pi) > math.radians(20): continue
                dmin = min((math.hypot(x[0]-y[0], x[1]-y[1]) for x in pa[::3] for y in pb[::3]), default=1e9)
                need = ((a.get('l') or 2) + (b.get('l') or 2)) * LANE_M / 2 - 1.0
                if 0.5 < dmin < need:
                    D['overlap'].append(a); D['overlap'].append(b)
    return D, total

if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'data/data6.js'
    out = sys.argv[sys.argv.index('--out')+1] if '--out' in sys.argv else 'data/map_audit_2026-09-27.json'
    recs = load(src)
    if '--scope' in sys.argv:
        before = len(recs)
        recs = [r for r in recs if in_scope_rec(r)]
        print(json.dumps({'scope': '강남구+송파구', 'records_before': before, 'records_in_scope': len(recs)}, ensure_ascii=False))
    D, total = audit(recs)
    summary = {}
    bad_ids = set()
    for k, rs in D.items():
        uniq = {id(r): r for r in rs}.values()
        ln = sum(r['_len'] for r in uniq)
        summary[k] = {'records': len(uniq), 'length_m': round(ln), 'share_pct': round(100*ln/total, 2)}
        for r in uniq:
            if k != 'untagged': bad_ids.add(r.get('w'))      # untagged 는 추정일 뿐 결함 아님 → 제외목록엔 안 넣음
    clean = {id(r): r for r in recs if not any(r in v for v in ())}   # placeholder, computed below
    badset = set()
    for k, rs in D.items():
        if k == 'untagged': continue
        for r in rs: badset.add(id(r))
    clean_len = sum(r['_len'] for r in recs if id(r) not in badset)
    worst = sorted([r for k in D if k != 'untagged' for r in D[k]], key=lambda r: -r['_len'])
    seen = set(); top = []
    for r in worst:
        if r.get('w') in seen: continue
        seen.add(r.get('w')); top.append({'w': r.get('w'), 'n': r.get('n'), 'l': r.get('l'), 'o': bool(r.get('o')),
                                          'ld': r.get('ld'), 'len_m': round(r['_len'])})
        if len(top) >= 50: break
    res = {'source': src, 'records': len(recs), 'total_length_m': round(total),
           'defects': summary,
           'clean_length_m': round(clean_len), 'clean_pct': round(100*clean_len/total, 2),
           'exclusion_ways': sorted(x for x in bad_ids if x), 'top50_worst': top}
    json.dump(res, open(out, 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k not in ('exclusion_ways', 'top50_worst')}, ensure_ascii=False))
    print(json.dumps({'exclusion_ways': len(res['exclusion_ways']), 'out': out}, ensure_ascii=False))
