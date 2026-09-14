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

    def _put(self, key, kind, obj):
        c = self.ch.setdefault(key, {'r':[],'b':[],'s':[]})
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
            pts = [(n.lat, n.lon) for n in w.nodes if n.location.valid()]
        except Exception:
            return
        if len(pts) < 2: return
        if not self._in(pts[0][0], pts[0][1]): return
        xy = [to_xy(la, lo) for la, lo in pts]
        cx = sum(p[0] for p in xy)/len(xy); cy = sum(p[1] for p in xy)/len(xy)
        k = self._key(cx, cy)
        if hw in ROAD:
            try: lanes = int(t.get('lanes'))
            except (TypeError, ValueError): lanes = LANES_DEF.get(hw, 2)
            self._put(k, 'r', {'n': t.get('name',''), 'l': max(1,min(10,lanes)),
                               'o': t.get('oneway') in ('yes','true','1'), 'p': xy})
            self.nroad += 1
        else:
            self._put(k, 'b', {'n': t.get('name',''), 'p': xy}); self.nbld += 1

    def node(self, n):
        if n.tags.get('highway') != 'traffic_signals': return
        if not n.location.valid() or not self._in(n.location.lat, n.location.lon): return
        x, y = to_xy(n.location.lat, n.location.lon)
        self._put(self._key(x,y), 's', {'x':x,'y':y}); self.nsig += 1

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
                      'roads': h.nroad, 'blds': h.nbld, 'signals': h.nsig,
                      'chunks': len(h.ch)}), flush=True)
    tot = 0
    for k, v in h.ch.items():
        fp = f'{out}/chunks/{k.replace(",","_")}.json'
        b = json.dumps(v, ensure_ascii=False, separators=(',',':')).encode()
        open(fp,'wb').write(b); tot += len(b)
    idx = {k: os.path.getsize(f'{out}/chunks/{k.replace(",","_")}.json') for k in h.ch}
    json.dump(idx, open(f'{out}/index.json','w'))
    print(json.dumps({'written': len(h.ch), 'total_mb': round(tot/1024/1024,1),
                      'avg_kb': round(tot/max(1,len(h.ch))/1024,1), 'out': out}))

if __name__ == '__main__':
    main()
