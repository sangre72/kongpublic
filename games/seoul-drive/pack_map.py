"""청크 파일들 → 게임이 읽는 data6.js 한 개로 묶기 (u_5009).

WHY: 아티팩트는 파일 하나로 배포된다. 서울 전체(1,281청크 48MB)를 통째로 넣을 수는 없다.
     그래서 '주행 반경'을 정해 그 안만 담되, 용량의 70% 를 차지하는 건물을
     먼 구역에서는 빼는 식으로 조절한다(도로·신호는 전부 유지 — 경로탐색에 필요).

사용: python3 pack_map.py [--radius 8] [--bld-radius 5] [--out data6.js]
"""
import sys, os, json, glob

SRC = 'games/seoul-drive/data/seoul/chunks'
def arg(name, default):
    if name in sys.argv:
        return sys.argv[sys.argv.index(name)+1]
    return default

def main():
    R    = int(arg('--radius', 8))        # 도로를 담을 반경(km)
    BR   = int(arg('--bld-radius', 5))    # 건물까지 담을 반경(km)
    out  = arg('--out', 'games/seoul-drive/data/data6.js')

    chunks, nroad, nbld, nsig = {}, 0, 0, 0
    for f in sorted(glob.glob(SRC + '/*.json')):
        k = os.path.basename(f)[:-5]
        i, j = (int(v) for v in k.split('_'))
        if abs(i) > R or abs(j) > R:
            continue
        v = json.load(open(f, encoding='utf-8'))
        r = v.get('r', []); b = v.get('b', []); sg = v.get('s', [])
        if abs(i) > BR or abs(j) > BR:
            b = []                         # 먼 구역은 건물 생략(용량)
        chunks[f'{i},{j}'] = {'r': r, 'b': b}
        nroad += len(r); nbld += len(b); nsig += len(sg)

    # 신호등은 게임이 SIGNALS 전역에서 읽는다(buildSignals)
    sigs = []
    for f in sorted(glob.glob(SRC + '/*.json')):
        k = os.path.basename(f)[:-5]
        i, j = (int(v) for v in k.split('_'))
        if abs(i) > R or abs(j) > R:
            continue
        for s in json.load(open(f, encoding='utf-8')).get('s', []):
            sigs.append({'x': s['x'], 'y': s['y']})

    body = ('const CHUNKS=' + json.dumps(chunks, ensure_ascii=False, separators=(',', ':')) + ';\n'
            + 'const SIGNALS=' + json.dumps(sigs, separators=(',', ':')) + ';\n'
            # ROADS/BLDS 는 CHUNKS 가 없을 때의 폴백이지만, 선언 자체가 없으면
            # collectRoads 의 참조에서 ReferenceError 가 난다(실측). 빈 배열로 둔다.
            + 'const ROADS=[];const BLDS=[];const POI=[];const XWALK=[];\n')
    open(out, 'w', encoding='utf-8').write(body)
    print(json.dumps({'chunks': len(chunks), 'roads': nroad, 'blds': nbld,
                      'signals': len(sigs), 'mb': round(len(body.encode())/1024/1024, 2),
                      'radius_km': R, 'bld_radius_km': BR, 'out': out}))

if __name__ == '__main__':
    main()
