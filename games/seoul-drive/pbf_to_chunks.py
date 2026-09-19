"""한국 OSM 덤프(pbf) → 게임 청크(1km) 변환 (u_4991).

WHY: Overpass 공개서버는 못 믿는다(실측 2026-09-14: 성공률 1/3, 이후 전면 504).
     오너 판단대로 "미리 받아 두고 필요할 때 불러 쓰는" 방식으로 간다.
     Geofabrik 덤프 한 번(274MB) 받으면 그 뒤로 네트워크가 아예 필요 없다.

출력: <out>/chunks/<i>_<j>.json  (1km 청크 하나당 파일 하나)
      게임은 이 중 3x3 만 읽으면 되므로 전체를 메모리에 올릴 일이 없다.

사용: python3 pbf_to_chunks.py <pbf> <out_dir> [--bbox la0,lo0,la1,lo1]
"""
import sys, os, json, math, time
import osmium

S_LAT, S_LON = 37.4979, 127.0276          # 게임 원점(강남역)
M_PER_DEG_LAT = 111320.0
CHUNK_M = 1000

ROAD = {'motorway','motorway_link','trunk','trunk_link','primary','primary_link',
        'secondary','secondary_link','tertiary','tertiary_link','residential',
        'unclassified','living_street','service'}
LANES_DEF = {'motorway':4,'trunk':3,'primary':3,'secondary':2,'tertiary':2}

def to_xy(lat, lon):
    y = (lat - S_LAT) * M_PER_DEG_LAT
    x = (lon - S_LON) * M_PER_DEG_LAT * math.cos(math.radians(S_LAT))
    return round(x,1), round(-y,1)          # 게임은 y 아래가 +

class Conv(osmium.SimpleHandler):
    def __init__(self, bbox=None):
        super().__init__()
        self.ch = {}
        self.bbox = bbox
        self.nroad = self.nbld = self.nsig = 0
        self.fixed = []                         # 차로수를 보정한 way 목록(보고용)

    def _put(self, key, kind, obj):
        c = self.ch.setdefault(key, {'r':[],'b':[],'s':[],'p':[]})
        c[kind].append(obj)

    def _key(self, x, y):
        return f'{math.floor(x/CHUNK_M)},{math.floor(y/CHUNK_M)}'

    def _in(self, lat, lon):
        if not self.bbox: return True
        a0,o0,a1,o1 = self.bbox
        return a0 <= lat <= a1 and o0 <= lon <= o1

    def way(self, w):
        t = w.tags
        hw = t.get('highway'); bl = t.get('building')
        if hw not in ROAD and bl is None: return
        try:
            # 노드 id 도 같이 모은다(a_5053). location 무효인 노드를 거르므로 좌표와
            # id 를 반드시 같은 루프에서 뽑아야 인덱스가 어긋나지 않는다.
            kept = [(n.lat, n.lon, n.ref) for n in w.nodes if n.location.valid()]
        except Exception:
            return
        if len(kept) < 2: return
        pts = [(la, lo) for la, lo, _ in kept]
        if not self._in(pts[0][0], pts[0][1]): return
        xy = [to_xy(la, lo) for la, lo in pts]
        cx = sum(p[0] for p in xy)/len(xy); cy = sum(p[1] for p in xy)/len(xy)
        k = self._key(cx, cy)
        if hw in ROAD:
            oneway = t.get('oneway') in ('yes','true','1')
            oneway_tagged = t.get('oneway') is not None
            def _i(k):
                try: return int(str(t.get(k)).split(';')[0])
                except (TypeError, ValueError): return None
            lanes = _i('lanes'); lf = _i('lanes:forward'); lb = _i('lanes:backward')
            tagged = lanes is not None
            if lanes is None: lanes = LANES_DEF.get(hw, 2)
            # ★2026-09-19 u_5418/u_5419 실측: 통일로 way 773066532 등 4건이 lanes=8·oneway=yes 로 태그돼
            #   있다(원본 pbf 확인). 서울에 편도 8차로 일방 차도는 없다 — 도로 전체 차로수를 한쪽 차도에
            #   단 것이다. 게임은 이걸 그대로 26m 도로로 그려 1차로가 실제 차도 밖 6m 에 찍혔고, 경로가
            #   4~5차로를 사선으로 가로질렀다(오너 스크린샷). 규칙: 일방통행에 lanes:forward 가 있으면
            #   그것, 없고 7차로 이상이면 절반. 보정한 way 는 전부 보고서에 남긴다.
            if oneway:
                if lf is not None and lf < lanes: self.fixed.append((w.id, t.get('name',''), lanes, lf, 'lanes:forward')); lanes = lf
                elif lanes >= 7: self.fixed.append((w.id, t.get('name',''), lanes, lanes//2, 'oneway>=7 halved')); lanes = lanes//2
            elif lf is not None and lb is not None and lf+lb != lanes:
                self.fixed.append((w.id, t.get('name',''), lanes, lf+lb, 'forward+backward')); lanes = lf+lb
            tl = t.get('turn:lanes') or t.get('turn:lanes:forward')
            wd = _i('width')
            # 'w' = OSM way id (a_5046). 회전제한 테이블(data/seoul/restrictions.json)의
            # 키가 "<from_way>|<via_node>|<to_way>" 라서, 이 id 없이는 청크 도로와 제한을
            # 이어붙일 수 없다(cf ar_5034 Q3).
            # 'nd' = [첫 노드 id, 끝 노드 id] (a_5053). 회전제한 키의 via 는 '노드 id' 라
            # way id 만으로는 조회가 안 된다. 교차로는 두 way 가 끝점 노드를 공유하는
            # 지점이므로 끝점 두 개만 있으면 via 판정이 된다.
            rec = {'n': t.get('name',''), 'l': max(1,min(10,lanes)), 'o': oneway, 'p': xy,
                   'w': w.id, 'nd': [kept[0][2], kept[-1][2]]}
            # ★2026-09-19 스윕 10·11구간 실측(언주로 218448824, 57점 ≈1km): way 를 무게중심 청크 하나에만 넣어
            #   옆 청크를 지나는 부분이 로컬 그래프에서 사라졌다(전역 라우터는 알고 있어 경로는 그리로 감 →
            #   onRoad/교사가 '도로 없음' → 도로이탈 13~19회 루프, 두 구간이 같은 좌표에서). 청크 경계에서
            #   way 를 조각내 각 청크에 자기 조각을 넣는다. 조각은 경계점을 공유해 그래프가 이어진다.
            pieces = []; cur = [xy[0]]; ck = self._key(*xy[0])
            for q in xy[1:]:
                k2 = self._key(*q)
                cur.append(q)
                if k2 != ck:
                    pieces.append((ck, cur)); cur = [q]; ck = k2
            if len(cur) >= 2: pieces.append((ck, cur))
            if len(pieces) > 1:
                for idx, (pk, pp) in enumerate(pieces):
                    r2 = dict(rec); r2['p'] = pp
                    r2['nd'] = [kept[0][2] if idx == 0 else None, kept[-1][2] if idx == len(pieces)-1 else None]
                    r2['pc'] = idx                      # 조각 번호(진단용)
                    if tl: r2['tl'] = tl
                    if lf is not None: r2['lf'] = lf
                    if lb is not None: r2['lb'] = lb
                    if wd is not None: r2['wd'] = wd
                    if not tagged: r2['ld'] = 1
                    self._put(pk, 'r', r2)
                self.nroad += 1
                self.nsplit = getattr(self, 'nsplit', 0) + 1
                return
            # 추가 필드(게임이 아직 안 읽음 — 전용 회전차로 등 다음 단계용). 있을 때만 싣는다.
            if tl: rec['tl'] = tl                      # turn:lanes  예: "left|through|through;right"
            if lf is not None: rec['lf'] = lf
            if lb is not None: rec['lb'] = lb
            if wd is not None: rec['wd'] = wd
            if not tagged: rec['ld'] = 1                # lanes 태그 없음 → 도로등급 기본값 사용(검토 대상)
            if not oneway_tagged: rec['od'] = 1         # oneway 태그 없음(왕복 기본값) → 연속성 규칙 검토 대상
            self._put(k, 'r', rec)
            self.nroad += 1
        else:
            self._put(k, 'b', {'n': t.get('name',''), 'p': xy}); self.nbld += 1

    def node(self, n):
        t = n.tags
        if not n.location.valid() or not self._in(n.location.lat, n.location.lon): return
        x, y = to_xy(n.location.lat, n.location.lon)
        if t.get('highway') == 'traffic_signals':
            self._put(self._key(x,y), 's', {'x':x,'y':y}); self.nsig += 1; return
        # ★2026-09-19: 역 이름 목적지(강남역→시청역 = 오너 성공기준). 지하철·철도역은 railway=station 노드이고
        #   이름에 '역'이 없다(시청·강남·신촌). 예전 검색인덱스에만 '시청역'이 있었고 지도엔 없어서 재추출 후
        #   경로가 아예 안 잡혔다. POI 로 싣고 '역' 붙인 별칭도 같이 넣는다.
        if t.get('railway') == 'station' and t.get('name'):
            nm = t.get('name'); k = t.get('station') or 'station'
            self._put(self._key(x,y), 'p', {'n': nm, 'x': x, 'y': y, 'k': 'station'})
            if not nm.endswith('역'):
                self._put(self._key(x,y), 'p', {'n': nm+'역', 'x': x, 'y': y, 'k': 'station'})
            self.npoi = getattr(self, 'npoi', 0) + 1

def main():
    pbf, out = sys.argv[1], sys.argv[2]
    bbox = None
    if '--bbox' in sys.argv:
        bbox = [float(v) for v in sys.argv[sys.argv.index('--bbox')+1].split(',')]
    os.makedirs(f'{out}/chunks', exist_ok=True)
    t0 = time.time()
    h = Conv(bbox)
    h.apply_file(pbf, locations=True, idx='flex_mem')
    print(json.dumps({'parsed_s': round(time.time()-t0),
                      'roads': h.nroad, 'blds': h.nbld, 'signals': h.nsig, 'stations': getattr(h,'npoi',0), 'split_ways': getattr(h,'nsplit',0),
                      'chunks': len(h.ch)}), flush=True)
    # ★2026-09-19 스윕 10·11구간 실측(언주로 218448824): lanes 태그 없는 일방 차도가 기본값 3(9.75m)으로 그려졌는데
    #   16m 옆의 같은 이름 반대편 차도(908696520)는 lanes=4. 두 구간이 정확히 같은 좌표(1104.7,-1005.2)에서
    #   도로이탈했다. 규칙: 태그 없는 일방(ld) way 는 40m 안 같은 이름의 태그된 일방 way 차로수를 물려받는다.
    sib = {}
    for k, v in h.ch.items():
        for r in v['r']:
            if r['o'] and 'ld' not in r and r['n']:
                mx = sum(x for x, _ in r['p']) / len(r['p']); my = sum(y for _, y in r['p']) / len(r['p'])
                sib.setdefault(r['n'], []).append((mx, my, r['l'], r['w']))
    nsib = 0
    # ★청크 경계 분할 뒤엔 한 way 가 여러 조각이다 — 상속은 way 단위로(조각마다 다르면 3/3/4/3 처럼 폭이 들쭉날쭉).
    byw = {}
    for k, v in h.ch.items():
        for r in v['r']:
            if r['o'] and r.get('ld') and r['n'] in sib: byw.setdefault(r['w'], []).append(r)
    for wid, recs in byw.items():
        best = None
        for r in recs:
            for (x, y) in r['p']:
                for mx, my, l, w in sib[r['n']]:
                    d = math.hypot(mx - x, my - y)
                    if 8 <= d < 40 and (best is None or d < best[0]): best = (d, l, w)   # 4m 짜리는 같은 이름의 연결로/회전차로 — 제외
        if not best: continue
        # ★2026-09-19 실측(신촌로 1006160948 3→4 @10m): 형제와의 간격보다 넓어지면 두 차도가 겹쳐
        #   경로/최근접 도로 판정이 뒤섞인다(스윕 신촌역 회귀). 폭 ≤ 간격−1m 로 상한.
        cap = int((best[0] - 1.0) // 3.25)
        to = min(best[1], cap)
        if to > recs[0]['l']:
            h.fixed.append((wid, recs[0]['n'], recs[0]['l'], to, f'sibling {best[2]} @{best[0]:.0f}m' + (f' cap{cap}' if to < best[1] else '') + f' x{len(recs)}'))
            for r in recs: r['l'] = to; r['ls'] = best[2]
            nsib += 1
    print(json.dumps({'sibling_lane_fixes': nsib}), flush=True)
    # ★2026-09-19 u_5434 "중앙선 주행" 실측(서소문로 1424068313, 176m): oneway 태그 없는 토막이 앞뒤 같은 이름의 일방 사이에서
    #   왕복으로 모델링돼 실제 없는 중앙선이 그려졌다. 규칙: od(태그 없음) way 의 양쪽 끝점이 각각 같은 이름의 일방 way 끝점과
    #   맞닿고(1m) 그 이웃들의 차로수가 같으면 일방으로 본다(연속성). 보고서에 남긴다.
    ends = {}   # (name) -> list of (x,y,rec)
    for k, v in h.ch.items():
        for r in v['r']:
            if r['o'] and r['n']:
                for pt in (r['p'][0], r['p'][-1]): ends.setdefault(r['n'], []).append((pt[0], pt[1], r))
    ncont = 0
    for k, v in h.ch.items():
        for r in v['r']:
            if r['o'] or not r.get('od') or not r['n'] or r['n'] not in ends: continue
            def _nb(pt):
                for x, y, q in ends[r['n']]:
                    if q is not r and math.hypot(x - pt[0], y - pt[1]) < 1.0 and q['l'] == r['l']: return q
                return None
            a_, b_ = _nb(r['p'][0]), _nb(r['p'][-1])
            if a_ is not None and b_ is not None and a_ is not b_:
                r['o'] = True; r['oc'] = 1; ncont += 1
                h.fixed.append((r['w'], r['n'], r['l'], r['l'], f'oneway-continuity {a_["w"]}/{b_["w"]}'))
    print(json.dumps({'oneway_continuity_fixes': ncont}), flush=True)
    tot = 0
    for k, v in h.ch.items():
        fp = f'{out}/chunks/{k.replace(",","_")}.json'
        b = json.dumps(v, ensure_ascii=False, separators=(',',':')).encode()
        open(fp,'wb').write(b); tot += len(b)
    idx = {k: os.path.getsize(f'{out}/chunks/{k.replace(",","_")}.json') for k in h.ch}
    json.dump(idx, open(f'{out}/index.json','w'))
    print(json.dumps({'written': len(h.ch), 'total_mb': round(tot/1024/1024,1),
                      'avg_kb': round(tot/max(1,len(h.ch))/1024,1), 'out': out}))
    # 차로수 보정 보고서 — 뭘 고쳤는지 남긴다(추측 금지, 검토 가능하게)
    json.dump([{'w':w,'n':n,'from':a,'to':b,'why':why} for w,n,a,b,why in h.fixed],
              open(f'{out}/lane_fixes.json','w'), ensure_ascii=False, indent=1)
    print(json.dumps({'lane_fixes': len(h.fixed), 'report': f'{out}/lane_fixes.json'}))

if __name__ == '__main__':
    main()
