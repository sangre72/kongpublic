"""지도팩(data6*.js) 오프라인 검증 — 브라우저·GPU 불필요 (2026-09-26 map_fix).

  python3 map_verify.py <current.js> <staged.js> [--report data/map_fixes_2026-09-26.json] [--out result.json]

1) way 수·레코드 수·필드 수(lf/lb/ol/rv/od/lk) 비교
2) way 별 l/o 변화 목록(원인 분류: link-oneway / asym / continuity / other)
3) 차도 겹침 검사: 서로 다른 way 의 도로 레코드가 같은 방향(±20°)으로 간격 < (폭1+폭2)/2 − 1m 이면 겹침 쌍.
   양 팩의 겹침 쌍 수와 '새로 생긴' 쌍을 보고 — 새 쌍에 바뀐 way 가 끼면 FAIL.
"""
import sys, json, math, re, collections
LW = 3.25

def load(path):
    s = open(path, encoding='utf-8').read()
    a = s.index('const CHUNKS=') + 13; b = s.index(';\nconst SIGNALS=')
    ch = json.loads(s[a:b])
    recs = [r for v in ch.values() for r in v['r']]
    return ch, recs, len(s)

class Grid:
    def __init__(self, cell=50.0): self.c = cell; self.g = {}
    def k(self, x, y): return (math.floor(x/self.c), math.floor(y/self.c))
    def add(self, r):
        P = r['p']
        for i in range(len(P)-1):
            (ax, ay), (bx, by) = P[i], P[i+1]
            k0 = self.k(min(ax,bx), min(ay,by)); k1 = self.k(max(ax,bx), max(ay,by))
            for kx in range(k0[0], k1[0]+1):
                for ky in range(k0[1], k1[1]+1): self.g.setdefault((kx,ky), []).append((r, i))
    def near(self, x, y, rad):
        k0 = self.k(x-rad, y-rad); k1 = self.k(x+rad, y+rad); seen = set(); out = []
        for kx in range(k0[0], k1[0]+1):
            for ky in range(k0[1], k1[1]+1):
                for r, i in self.g.get((kx,ky), ()):
                    if (id(r), i) in seen: continue
                    seen.add((id(r), i)); out.append((r, i))
        return out

def segd(p, a, b):
    (px,py),(ax,ay),(bx,by) = p, a, b; L2 = (bx-ax)**2 + (by-ay)**2
    if L2 < 1e-9: return math.hypot(px-ax, py-ay)
    t = max(0.0, min(1.0, ((px-ax)*(bx-ax)+(py-ay)*(by-ay))/L2))
    return math.hypot(ax+(bx-ax)*t-px, ay+(by-ay)*t-py)

def samples(P, step=5.0, margin=4.0):
    out = []; acc = 0.0; total = sum(math.hypot(P[i+1][0]-P[i][0], P[i+1][1]-P[i][1]) for i in range(len(P)-1)); s = margin
    for i in range(len(P)-1):
        (ax,ay),(bx,by) = P[i], P[i+1]; L = math.hypot(bx-ax, by-ay)
        if L < 1e-6: continue
        ang = math.atan2(by-ay, bx-ax)
        while s <= acc+L and s <= total-margin:
            t = (s-acc)/L; out.append((ax+(bx-ax)*t, ay+(by-ay)*t, ang)); s += step
        acc += L
    return out

def overlaps(recs):
    g = Grid()
    for r in recs: g.add(r)
    pairs = {}
    for r in recs:
        wr = r['l'] * LW
        for (sx, sy, ang) in samples(r['p']):
            for q, i in g.near(sx, sy, 20.0):
                if q is r or q['w'] == r['w']: continue
                (ax,ay),(bx,by) = q['p'][i], q['p'][i+1]
                qa = math.atan2(by-ay, bx-ax); da = abs((qa-ang+math.pi) % (2*math.pi) - math.pi); da = min(da, math.pi-da)
                if da >= math.radians(20): continue
                d = segd((sx,sy), (ax,ay), (bx,by)); thr = (wr + q['l']*LW)/2 - 1.0
                if d < thr:
                    key = (min(r['w'], q['w']), max(r['w'], q['w']))
                    if key not in pairs or d < pairs[key][0]: pairs[key] = (round(d,1), round(thr,1), r['n'] or q['n'])
    return pairs

def main():
    cur, stg = sys.argv[1], sys.argv[2]
    rep = None
    if '--report' in sys.argv: rep = json.load(open(sys.argv[sys.argv.index('--report')+1], encoding='utf-8'))
    out = sys.argv[sys.argv.index('--out')+1] if '--out' in sys.argv else None
    chA, A, szA = load(cur); chB, B, szB = load(stg)
    def fld(recs):
        c = collections.Counter()
        for r in recs:
            for k in ('lf','lb','ol','rv','od','lk','oc','ld','tl','pc'):
                if k in r: c[k] += 1
        return dict(c)
    res = {'current': {'file': cur, 'mb': round(szA/1048576,2), 'chunks': len(chA), 'records': len(A), 'ways': len({r['w'] for r in A}), 'fields': fld(A)},
           'staged':  {'file': stg, 'mb': round(szB/1048576,2), 'chunks': len(chB), 'records': len(B), 'ways': len({r['w'] for r in B}), 'fields': fld(B)}}
    wa = {}; wb = {}
    for r in A: wa.setdefault(r['w'], r)
    for r in B: wb.setdefault(r['w'], r)
    res['ways_only_current'] = sorted(set(wa) - set(wb))[:50]; res['ways_only_staged'] = sorted(set(wb) - set(wa))[:50]
    res['ways_only_current_n'] = len(set(wa) - set(wb)); res['ways_only_staged_n'] = len(set(wb) - set(wa))
    linkset = {e['w'] for e in rep['link_oneway']} if rep else set()
    asymset = {e['w'] for e in rep['asym']} if rep else set()
    changes = []
    for w in set(wa) & set(wb):
        a, b = wa[w], wb[w]
        if a['l'] != b['l'] or bool(a['o']) != bool(b['o']) or a.get('lf') != b.get('lf') or a.get('lb') != b.get('lb') or bool(a.get('rv')) != bool(b.get('rv')):
            skipset = {e['w'] for e in rep['link_skipped']} if rep else set()
            if w in linkset: why = 'link-oneway'
            elif w in asymset: why = 'asym'
            elif a.get('ol') and w in skipset: why = 'link-not-flipped(stricter rule)'
            elif a.get('lf') is not None and a.get('lf') == a.get('lb') and b.get('lf') is None and a['l'] == b['l'] and a['o'] == b['o']: why = 'sym-fields-dropped'
            elif b.get('oc') and not a.get('oc'): why = 'continuity'
            else: why = 'other'
            changes.append({'w': w, 'n': a['n'], 'why': why, 'before': {'l': a['l'], 'o': a['o'], 'lf': a.get('lf'), 'lb': a.get('lb')},
                            'after': {'l': b['l'], 'o': b['o'], 'lf': b.get('lf'), 'lb': b.get('lb'), 'rv': b.get('rv')}})
    res['changed_ways_n'] = len(changes); res['changed_by_why'] = dict(collections.Counter(c['why'] for c in changes)); res['changed_ways'] = changes
    res['asym_in_pack'] = sorted({r['w'] for r in B if 'lf' in r and 'lb' in r}); res['asym_in_pack_n'] = len(res['asym_in_pack'])
    res['links_flipped_in_pack'] = sorted({r['w'] for r in B if r.get('ol')}); res['links_flipped_in_pack_n'] = len(res['links_flipped_in_pack'])
    res['links_reversed_in_pack'] = sorted({r['w'] for r in B if r.get('rv')})
    # asym sanity: l == lf+lb, o == False
    bad = [r['w'] for r in B if 'lf' in r and (r['o'] or r['l'] != r['lf'] + r['lb'])]
    res['asym_bad_n'] = len(bad); res['asym_bad'] = bad[:20]
    print('overlap check current...', flush=True); pa = overlaps(A)
    print('overlap check staged...', flush=True); pb = overlaps(B)
    new = {k: v for k, v in pb.items() if k not in pa}; gone = {k: v for k, v in pa.items() if k not in pb}
    touched = linkset | asymset | {c['w'] for c in changes}
    new_touch = {k: v for k, v in new.items() if k[0] in touched or k[1] in touched}
    res['overlap'] = {'pairs_current': len(pa), 'pairs_staged': len(pb), 'new_pairs': len(new), 'gone_pairs': len(gone),
                      'new_pairs_involving_changed_ways': len(new_touch),
                      'new_pairs_list': [{'ways': list(k), 'd': v[0], 'thr': v[1], 'n': v[2]} for k, v in list(new.items())[:40]],
                      'new_pairs_involving_changed_ways_list': [{'ways': list(k), 'd': v[0], 'thr': v[1], 'n': v[2]} for k, v in new_touch.items()]}
    res['PASS'] = (len(new_touch) == 0 and res['asym_bad_n'] == 0)
    if out: json.dump(res, open(out, 'w'), ensure_ascii=False, indent=1)
    summ = {k: res[k] for k in ('current','staged','ways_only_current_n','ways_only_staged_n','changed_ways_n','changed_by_why','asym_in_pack_n','asym_bad_n','links_flipped_in_pack_n','links_reversed_in_pack','overlap','PASS')}
    summ['overlap'] = {k: v for k, v in summ['overlap'].items() if not k.endswith('_list')}
    print(json.dumps(summ, ensure_ascii=False, indent=1))

if __name__ == '__main__':
    main()
