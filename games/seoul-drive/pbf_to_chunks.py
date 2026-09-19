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
            # 추가 필드(게임이 아직 안 읽음 — 전용 회전차로 등 다음 단계용). 있을 때만 싣는다.
            if tl: rec['tl'] = tl                      # turn:lanes  예: "left|through|through;right"
            if lf is not None: rec['lf'] = lf
            if lb is not None: rec['lb'] = lb
            if wd is not None: rec['wd'] = wd
            if not tagged: rec['ld'] = 1                # lanes 태그 없음 → 도로등급 기본값 사용(검토 대상)
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
                      'roads': h.nroad, 'blds': h.nbld, 'signals': h.nsig, 'stations': getattr(h,'npoi',0),
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
    for k, v in h.ch.items():
        for r in v['r']:
            if not (r['o'] and r.get('ld') and r['n'] in sib): continue
            best = None
            for (x, y) in r['p']:
                for mx, my, l, w in sib[r['n']]:
                    d = math.hypot(mx - x, my - y)
                    if 8 <= d < 40 and (best is None or d < best[0]): best = (d, l, w)   # 4m 짜리는 같은 이름의 연결로/회전차로 — 제외
            if best and best[1] > r['l']:                                            # 넓히기만 한다(본선을 1차로로 줄이는 사고 방지)
                h.fixed.append((r['w'], r['n'], r['l'], best[1], f'sibling {best[2]} @{best[0]:.0f}m'))
                r['l'] = best[1]; r['ls'] = best[2]; nsib += 1
    print(json.dumps({'sibling_lane_fixes': nsib}), flush=True)
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
