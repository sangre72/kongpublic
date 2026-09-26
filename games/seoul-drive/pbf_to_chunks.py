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
# ★2026-09-26 지도 결함 수정 플래그(기본 ON). --no-asym / --no-link-oneway 로 끈다(비교 실험용).
#   asym : 왕복도로 lanes:forward≠lanes:backward 를 lf/lb 로 싣는다(게임은 c=(lb−lf)·LW/2 로 중앙선을 옮겨야 한다, cases/map_fix_2026-09-26.md).
#   link : *_link 연결로(oneway 미태그)를 양 끝이 일방 차도에 닿으면 일방으로 본다(방향 검사·겹침 검사 포함).
OPT = {'asym': True, 'link': True}
LW = 3.25                                  # 차로폭(m) — 게임 LANE_M 과 같아야 한다
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
        self.asym = []                          # (A) 비대칭 왕복도로 목록(보고용)

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
            if lanes is None:
                lanes = LANES_DEF.get(hw, 2)
                # ★2026-09-19 u_5434 실측(서소문로 1424068313, oneway=no·lanes 없음): 왕복도로에 홀수 기본값(primary 3)이 붙으면
                #   방향당 1.5차로 → 1차로 중심이 중앙선 1.63m 옆(여유 0.7m) = '중앙선 주행'으로 보인다. 왕복 미태그는 짝수로.
                if not oneway and lanes % 2 == 1: lanes += 1
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
            # ★(A) 2026-09-26 비대칭 왕복도로(남대문로 218923156/424940172 = forward 5 / backward 3). 지금까지 총 8 을 4/4 로
            #   그려 중앙선이 OSM 축에 놓였다(실제 중앙선은 (lb−lf)·LW/2 = −3.25m 옆) → 한쪽 차도의 차로가 반대 차도를 물었다(오너 관측).
            #   한쪽만 태그돼 있으면 나머지 = lanes − 그쪽. 양쪽을 알면 lanes 태그로 취급(ld 아님 → 뒤의 형제/병합 규칙이 폭을 못 건드린다).
            #   싣는 건 비대칭일 때만(lf≠lb). 없으면 게임은 대칭으로 본다(하위호환).
            asym = None
            if OPT['asym'] and not oneway:
                if lf is None and lb is not None and lanes is not None and lanes - lb >= 1: lf = lanes - lb
                if lb is None and lf is not None and lanes is not None and lanes - lf >= 1: lb = lanes - lf
                if lf is not None and lb is not None and lf >= 1 and lb >= 1:
                    tagged = True; lanes = lf + lb
                    if lf + lb > 10:                       # 레코드 'l' 상한 10 과 맞춘다(소공로 383097722 7+4=11). 큰 쪽을 깎고 보고서에 남긴다.
                        lf0, lb0 = lf, lb
                        while lf + lb > 10:
                            if lf >= lb: lf -= 1
                            else: lb -= 1
                        lanes = lf + lb
                        self.fixed.append((w.id, t.get('name',''), lf0 + lb0, lanes, f'asym cap10 {lf0}/{lb0}->{lf}/{lb}'))
                    if lf != lb:
                        asym = (lf, lb)
                        self.asym.append({'w': w.id, 'n': t.get('name',''), 'hc': hw, 'l': lanes, 'lf': lf, 'lb': lb,
                                          'c_m': round((lb - lf) * LW / 2, 2)})
            tl = t.get('turn:lanes') or t.get('turn:lanes:forward')
            wd = _i('width')
            # 'w' = OSM way id (a_5046). 회전제한 테이블(data/seoul/restrictions.json)의
            # 키가 "<from_way>|<via_node>|<to_way>" 라서, 이 id 없이는 청크 도로와 제한을
            # 이어붙일 수 없다(cf ar_5034 Q3).
            # 'nd' = [첫 노드 id, 끝 노드 id] (a_5053). 회전제한 키의 via 는 '노드 id' 라
            # way id 만으로는 조회가 안 된다. 교차로는 두 way 가 끝점 노드를 공유하는
            # 지점이므로 끝점 두 개만 있으면 via 판정이 된다.
            rec = {'n': t.get('name',''), 'l': max(1,min(10,lanes)), 'o': oneway, 'p': xy, 'hc': hw,
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
                    if OPT['asym']:
                        if asym: r2['lf'], r2['lb'] = asym
                    else:
                        if lf is not None: r2['lf'] = lf
                        if lb is not None: r2['lb'] = lb
                    if wd is not None: r2['wd'] = wd
                    if not tagged: r2['ld'] = 1
                    # ★2026-09-26: 조각에도 od/lk 를 싣는다. 빠져 있어서 청크 경계를 넘는 way 는 일방 연속성·연결로 규칙 대상에서 통째로 빠졌다.
                    if not oneway_tagged: r2['od'] = 1
                    if hw.endswith('_link'): r2['lk'] = 1
                    self._put(pk, 'r', r2)
                self.nroad += 1
                self.nsplit = getattr(self, 'nsplit', 0) + 1
                return
            # 추가 필드(게임이 아직 안 읽음 — 전용 회전차로 등 다음 단계용). 있을 때만 싣는다.
            if tl: rec['tl'] = tl                      # turn:lanes  예: "left|through|through;right"
            if OPT['asym']:
                if asym: rec['lf'], rec['lb'] = asym   # (A) 비대칭 왕복만. 대칭·일방은 싣지 않는다(없음 = 대칭)
            else:
                if lf is not None: rec['lf'] = lf
                if lb is not None: rec['lb'] = lb
            if wd is not None: rec['wd'] = wd
            if not tagged: rec['ld'] = 1                # lanes 태그 없음 → 도로등급 기본값 사용(검토 대상)
            if not oneway_tagged: rec['od'] = 1         # oneway 태그 없음(왕복 기본값) → 연속성 규칙 검토 대상
            if hw.endswith('_link'): rec['lk'] = 1     # 연결로(램프) 표시 — 일방 추론 대상(2026-09-26 u_5648/orch 승인)
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

class _Grid:
    """도로 선분 격자 색인(셀 = cell m). near(x,y,rad) → (rec, 선분 i) 목록. 연결로 규칙의 전수 스캔(1,500×30만 점)을 대체한다."""
    def __init__(self, cell):
        self.c = cell; self.g = {}
    def _k(self, x, y): return (math.floor(x / self.c), math.floor(y / self.c))
    def add(self, r):
        P = r['p']
        for i in range(len(P) - 1):
            (ax, ay), (bx, by) = P[i], P[i+1]
            k0 = self._k(min(ax, bx), min(ay, by)); k1 = self._k(max(ax, bx), max(ay, by))
            for kx in range(k0[0], k1[0] + 1):
                for ky in range(k0[1], k1[1] + 1):
                    self.g.setdefault((kx, ky), []).append((r, i))
    def near(self, x, y, rad):
        k0 = self._k(x - rad, y - rad); k1 = self._k(x + rad, y + rad); seen = set(); out = []
        for kx in range(k0[0], k1[0] + 1):
            for ky in range(k0[1], k1[1] + 1):
                for r, i in self.g.get((kx, ky), ()):
                    if (id(r), i) in seen: continue
                    seen.add((id(r), i)); out.append((r, i))
        return out

def _segd(p, a, b):
    """점 p 에서 선분 ab 까지 거리와 매개변수 t."""
    (px, py), (ax, ay), (bx, by) = p, a, b; L2 = (bx-ax)**2 + (by-ay)**2
    if L2 < 1e-9: return math.hypot(px-ax, py-ay), 0.0
    t = max(0.0, min(1.0, ((px-ax)*(bx-ax) + (py-ay)*(by-ay)) / L2))
    return math.hypot(ax + (bx-ax)*t - px, ay + (by-ay)*t - py), t

def _samples(P, step, margin):
    """점열 P 를 따라 step m 간격 표본 (x, y, 진행각). 양 끝 margin m 은 제외."""
    out = []; acc = 0.0; total = sum(math.hypot(P[i+1][0]-P[i][0], P[i+1][1]-P[i][1]) for i in range(len(P)-1))
    s = margin
    for i in range(len(P)-1):
        (ax, ay), (bx, by) = P[i], P[i+1]; L = math.hypot(bx-ax, by-ay)
        if L < 1e-6: continue
        ang = math.atan2(by-ay, bx-ax)
        while s <= acc + L and s <= total - margin:
            t = (s - acc) / L; out.append((ax + (bx-ax)*t, ay + (by-ay)*t, ang)); s += step
        acc += L
    if not out and len(P) >= 2:
        mx = sum(p[0] for p in P) / len(P); my = sum(p[1] for p in P) / len(P)
        out.append((mx, my, math.atan2(P[-1][1]-P[0][1], P[-1][0]-P[0][0])))
    return out

def main():
    pbf, out = sys.argv[1], sys.argv[2]
    if '--no-asym' in sys.argv: OPT['asym'] = False
    if '--no-link-oneway' in sys.argv: OPT['link'] = False
    report = sys.argv[sys.argv.index('--report')+1] if '--report' in sys.argv else f'{out}/map_fixes.json'
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
            if r['o'] or not r.get('od') or not r['n'] or r['n'] not in ends or 'lb' in r: continue   # lb 있음 = 방향별 차로 태그 = 진짜 왕복
            def _nb(pt):   # ★2026-09-26 straddle 실측(사평대로 219837933 2way-4 사이 3차로 일방, 서소문로 480233462): 차로수가 달라도 양끝이 같은 이름 일방에 닿으면 연속(차로수는 이웃 최소값)
                for x, y, q in ends[r['n']]:
                    if q is not r and math.hypot(x - pt[0], y - pt[1]) < 1.0: return q
                return None
            a_, b_ = _nb(r['p'][0]), _nb(r['p'][-1])
            if a_ is not None and b_ is not None and a_ is not b_:
                l0 = r['l']; r['o'] = True; r['oc'] = 1; ncont += 1
                if r.get('ld'): r['l'] = min(a_['l'], b_['l'])
                h.fixed.append((r['w'], r['n'], l0, r['l'], f'oneway-continuity {a_["w"]}/{b_["w"]}'))
    print(json.dumps({'oneway_continuity_fixes': ncont}), flush=True)
    # ★2026-09-26 straddle 실측(강남대로 472042765 ld-3 ↔ 523141074 tagged-5 맞닿음): 태그 없는 일방 조각이 같은 이름의 태그된 일방 조각과 끝점(1m)을 공유하면 그 차로수를 잇는다(이어지는 도로의 폭 계단 제거).
    tagged = {}
    for k, v in h.ch.items():
        for r in v['r']:
            if r['o'] and not r.get('ld') and r['n']:
                for pt in (r['p'][0], r['p'][-1]): tagged.setdefault(r['n'], []).append((pt[0], pt[1], r))
    ncont2 = 0
    for k, v in h.ch.items():
        for r in v['r']:
            if not (r['o'] and r.get('ld') and r['n'] in tagged): continue
            nb = [q for pt in (r['p'][0], r['p'][-1]) for x, y, q in tagged[r['n']] if math.hypot(x - pt[0], y - pt[1]) < 1.0 and q.get('hc') == r.get('hc')]   # 같은 도로등급끼리만(같은 이름의 이면도로·연결로 과폭 방지)
            if not nb: continue
            to = max(q['l'] for q in nb)
            if to != r['l']:
                h.fixed.append((r['w'], r['n'], r['l'], to, f'continuation {nb[0]["w"]}')); r['l'] = to; ncont2 += 1
    print(json.dumps({'continuation_lane_fixes': ncont2}), flush=True)
    # ★2026-09-26 straddle 실측(사평대로 219837933: oneway 미태그·lanes 미태그 primary 가 3+3 일방 사이 → 기본 4 = 방향당 2 → 3차로에서 2차로로 계단 → 차선 물기;
    #   서소문로 480233462 oneway=no·lanes 미태그 ↔ 3차로 일방): 양방향(lanes 미태그) 조각의 끝점이 같은 이름 일방 조각과 맞닿으면 방향당 차로수를 그 일방 차로수로 본다(총 = 2×).
    nmerge = 0
    for k, v in h.ch.items():
        for r in v['r']:
            if r['o'] or not r.get('ld') or not r['n'] or r['n'] not in ends: continue
            nb = [q for pt in (r['p'][0], r['p'][-1]) for x, y, q in ends[r['n']] if math.hypot(x - pt[0], y - pt[1]) < 1.0 and q.get('hc') == r.get('hc') and r.get('hc') in ('primary', 'secondary', 'tertiary', 'trunk')]   # 같은 등급(간선급)끼리만
            if not nb: continue
            to = min(8, 2 * max(q['l'] for q in nb))
            if to > r['l']:
                h.fixed.append((r['w'], r['n'], r['l'], to, f'twoway-merge {nb[0]["w"]}')); r['l'] = to; nmerge += 1
    print(json.dumps({'twoway_merge_lane_fixes': nmerge}), flush=True)
    # ★(B) 2026-09-26 u_5648: *_link 연결로가 oneway 미태그면 양방향 2차로로 그려져 대교차로에 가짜 양방향 도로·삼각 포장면이 생긴다
    #   (서소문로/통일로 1214479814). 규칙: 연결로(lk)·oneway 미태그·길이 3~300m 이고 양 끝점이 각각 서로 다른 일방 way 의 점(1m)에 닿으면 일방으로 본다.
    #   방향 검사: 끝점에서 닿은 일방 차도의 진행방향과 연결로의 첫/끝 선분 방향의 cos. 둘 다 >0.15 = 그린 방향 그대로, 둘 다 <−0.15 = 거꾸로
    #   그려짐 → 점열을 뒤집어 싣는다(rv:1). 섞이거나 직각이면 보류(방향을 못 정한다).
    #   겹침 검사: 연결로 가운데 구간(양 끝 min(5m, L/3) 제외)을 2m 간격으로 표본 → 닿은 두 차도를 뺀 모든 도로에 대해 같은 방향(±20°)이고
    #   간격 < (두 폭 합)/2 − 1m 이면 보류(겹침 생성 금지 — 형제 차로 상한 규칙과 같은 기준). 판정마다 보고서에 남긴다.
    nlink = 0; nlink_skip = 0; nlink_rev = 0; nlink_dq = 0; h.links = []; h.link_skip = []
    if OPT['link']:
        grid = _Grid(50.0)
        for k, v in h.ch.items():
            for r in v['r']: grid.add(r)
        def _touch(pt, r):
            best = None
            for q, i in grid.near(pt[0], pt[1], 1.5):
                if q is r or not q['o'] or q['w'] == r['w']: continue
                Q = q['p']
                for j in (i, ):
                    d, t = _segd(pt, Q[j], Q[j+1])
                    if d < 1.0 and (best is None or d < best[0]): best = (d, q, j)
            return best
        for k, v in h.ch.items():
            for r in v['r']:
                if r['o'] or not r.get('lk') or not r.get('od'): continue
                P = r['p']; L = sum(math.hypot(P[i+1][0]-P[i][0], P[i+1][1]-P[i][1]) for i in range(len(P)-1))
                if L > 300 or L < 3: continue
                a_, b_ = _touch(P[0], r), _touch(P[-1], r)
                if a_ is None or b_ is None:
                    h.link_skip.append({'w': r['w'], 'n': r['n'], 'hc': r.get('hc'), 'L': round(L), 'why': 'end not on oneway', 'pc': r.get('pc')}); continue
                if a_[1]['w'] == b_[1]['w']:
                    h.link_skip.append({'w': r['w'], 'n': r['n'], 'hc': r.get('hc'), 'L': round(L), 'why': f'both ends on same way {a_[1]["w"]}'}); continue
                def _cos(seg, q, j):
                    Q = q['p']; ux, uy = Q[j+1][0]-Q[j][0], Q[j+1][1]-Q[j][1]; vx, vy = seg
                    nu = math.hypot(ux, uy); nv = math.hypot(vx, vy)
                    return (ux*vx + uy*vy) / (nu*nv) if nu > 1e-6 and nv > 1e-6 else 0.0
                c0 = _cos((P[1][0]-P[0][0], P[1][1]-P[0][1]), a_[1], a_[2])
                c1 = _cos((P[-1][0]-P[-2][0], P[-1][1]-P[-2][1]), b_[1], b_[2])
                # 방향 판정: 뚜렷한 끝(|cos|≥0.15)이 하나라도 있으면 그걸 따른다. 두 끝이 서로 반대면 모순 → 보류.
                #   두 끝 다 직각(분리대 사이 횡단 연결로, 서소문로/통일로 1214479814 L17 cos −0.06/−0.04)이면 그린 방향 유지 + dq:1(방향 미검증).
                sg = [c for c in (c0, c1) if abs(c) >= 0.15]
                if sg and any(c > 0 for c in sg) and any(c < 0 for c in sg):
                    h.link_skip.append({'w': r['w'], 'n': r['n'], 'hc': r.get('hc'), 'L': round(L), 'why': f'direction contradictory cos {c0:.2f}/{c1:.2f}', 'a': a_[1]['w'], 'b': b_[1]['w']}); continue
                rev = bool(sg) and sg[0] < 0; dq = not sg
                # 겹침 검사(가운데 구간 표본)
                m = min(5.0, L/3); overlap = None; dmin = 1e9
                for (sx, sy, ang) in _samples(P, 2.0, m):
                    for q, i in grid.near(sx, sy, 20.0):
                        if q is r or q['w'] in (r['w'], a_[1]['w'], b_[1]['w']): continue
                        (ax, ay), (bx, by) = q['p'][i], q['p'][i+1]
                        d, t = _segd((sx, sy), (ax, ay), (bx, by))
                        qa = math.atan2(by-ay, bx-ax); da = abs((qa - ang + math.pi) % (2*math.pi) - math.pi); da = min(da, math.pi - da)
                        if da < math.radians(20):
                            if d < dmin: dmin = d
                            if d < (r['l'] + q['l']) * LW / 2 - 1.0: overlap = (q, d); break
                    if overlap: break
                if overlap:
                    nlink_skip += 1
                    h.link_skip.append({'w': r['w'], 'n': r['n'], 'hc': r.get('hc'), 'L': round(L), 'why': f'overlap {overlap[0]["w"]} d={overlap[1]:.1f}m', 'a': a_[1]['w'], 'b': b_[1]['w']})
                    h.fixed.append((r['w'], r['n'], r['l'], r['l'], f'link-oneway SKIP overlap {overlap[0]["w"]} d{overlap[1]:.1f}')); continue
                if rev:
                    r['p'] = list(reversed(r['p'])); r['nd'] = [r['nd'][1], r['nd'][0]]; r['rv'] = 1; nlink_rev += 1
                if dq: r['dq'] = 1; nlink_dq += 1
                r['o'] = True; r['ol'] = 1; nlink += 1
                h.links.append({'w': r['w'], 'n': r['n'], 'hc': r.get('hc'), 'l': r['l'], 'L': round(L), 'a': a_[1]['w'], 'b': b_[1]['w'],
                                'cos': [round(c0, 2), round(c1, 2)], 'reversed': rev, 'dir_unverified': dq, 'min_sep_m': (round(dmin, 1) if dmin < 1e8 else None),
                                'before': {'o': False}, 'after': {'o': True, 'rv': int(rev), 'dq': int(dq)}})
                h.fixed.append((r['w'], r['n'], r['l'], r['l'], f'link-oneway {a_[1]["w"]}/{b_[1]["w"]} L{L:.0f}' + (' REV' if rev else '')))
    print(json.dumps({'link_oneway_fixes': nlink, 'link_oneway_reversed': nlink_rev, 'link_oneway_dir_unverified': nlink_dq, 'link_oneway_skipped_overlap': nlink_skip,
                      'link_oneway_skipped_total': len(h.link_skip)}), flush=True)
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
    # ★2026-09-26 (A)/(B) 보고서: 비대칭 왕복도로·연결로 일방화(전후·판정 근거·보류 사유). 검토 가능하게 way id 단위로.
    asym_by_w = {}
    for a in h.asym: asym_by_w.setdefault(a['w'], a)
    rep = {'date': time.strftime('%Y-%m-%d %H:%M'), 'pbf': pbf, 'bbox': bbox, 'opt': OPT, 'formula': {'LW': LW,
           'center_offset_m': 'c = (lb - lf) * LW / 2  (OSM 축에서, 진행방향 오른쪽 +)',
           'forward_lane_k_center': 'c + (k + 0.5) * LW', 'backward_lane_k_center': 'c - (k + 0.5) * LW'},
           'counts': {'asym_ways': len(asym_by_w), 'asym_records': len(h.asym), 'link_oneway': nlink, 'link_oneway_reversed': nlink_rev, 'link_oneway_dir_unverified': nlink_dq,
                      'link_skipped_overlap': nlink_skip, 'link_skipped_total': len(h.link_skip), 'lane_fixes_total': len(h.fixed)},
           'asym': [{'w': a['w'], 'n': a['n'], 'hc': a['hc'], 'before': {'l': a['l'], 'lf': a['l'] // 2, 'lb': a['l'] // 2, 'note': 'symmetric approx'},
                     'after': {'l': a['l'], 'lf': a['lf'], 'lb': a['lb'], 'c_m': a['c_m']}} for a in asym_by_w.values()],
           'link_oneway': h.links, 'link_skipped': h.link_skip}
    json.dump(rep, open(report, 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({'map_fixes_report': report, **rep['counts']}))

if __name__ == '__main__':
    main()
