"""도로명·건물명 → 검색 인덱스 (u_5003).

오너 요구(u_4984): "한글이든 영문이든 주소든 지명이든 특징적인 상호든 다 가게"
지금 맵에 이미 재료가 다 있다 — 도로명 1,507종, 건물명 1,900종.
인덱스만 만들면 부분일치 검색이 된다(예상 93KB, 맵 2.3MB 대비 4%).

출력: games/seoul-drive/data/search.js  (const SEARCH=[{n,x,y,k}, ...])
  n=이름  x,y=게임좌표  k=종류(road|bld|poi)
"""
import re, json, sys

SRC = 'games/seoul-drive/data/data6.js'
OUT = 'games/seoul-drive/data/search.js'

def load(path, var):
    s = open(path, encoding='utf-8').read()
    m = re.search(var + r'\s*=\s*', s)
    if not m: return None
    i = s.index('{' if var == 'CHUNKS' else '[', m.end())
    d, _ = json.JSONDecoder().raw_decode(s[i:])
    return d

def main():
    ch = load(SRC, 'CHUNKS') or {}
    poi = load(SRC, 'POI') or []
    seen = {}
    def add(name, x, y, kind):
        n = (name or '').strip()
        if not n or n.replace('-', '').replace('.', '').isdigit():
            return                                   # 번지수만 있는 건 검색 의미 없음
        key = (n, kind)
        if key in seen: return                       # 같은 이름은 첫 위치만
        seen[key] = {'n': n, 'x': round(x, 1), 'y': round(y, 1), 'k': kind}

    for v in ch.values():
        for r in v.get('r', []):
            p = r.get('p') or []
            if len(p) < 2: continue
            mid = p[len(p)//2]
            add(r.get('n'), mid[0], mid[1], 'road')
        for b in v.get('b', []):
            p = b.get('p') or []
            if not p: continue
            cx = sum(q[0] for q in p)/len(p); cy = sum(q[1] for q in p)/len(p)
            add(b.get('n'), cx, cy, 'bld')
    for p in poi:
        add(p.get('n'), p.get('x', 0), p.get('y', 0), 'poi')

    rows = list(seen.values())
    rows.sort(key=lambda r: r['n'])
    body = json.dumps(rows, ensure_ascii=False, separators=(',', ':'))
    open(OUT, 'w', encoding='utf-8').write('const SEARCH=' + body + ';\n')
    kinds = {}
    for r in rows: kinds[r['k']] = kinds.get(r['k'], 0) + 1
    print(json.dumps({'entries': len(rows), 'by_kind': kinds,
                      'kb': round(len(body.encode())/1024, 1), 'out': OUT},
                     ensure_ascii=False))

if __name__ == '__main__':
    main()
