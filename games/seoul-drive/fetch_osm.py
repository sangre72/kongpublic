"""OSM → 게임 청크(1km) 다운로더 (u_4990).

WHY: data6.js 에는 강남 80청크(6.5x7.5km)만 있었다. 그 밖으로 나가면 빈 공간이다.
     청크 스트리밍(3x3)은 이미 구현돼 있으므로, 데이터만 넓히면 어디든 달릴 수 있다.

★Overpass 공개서버는 불안정하다(실측: overpass-api.de 1/3 성공, 미러 2곳 0/3).
  그래서 (1) 타일 단위로 나눠 받고 (2) 실패하면 재시도하며 (3) 받은 건 즉시
  디스크에 저장해 중단 후 이어받기가 되게 한다. 통째로 한 번에 받으면 반드시 실패한다.

사용:
  python3 fetch_osm.py <region> [--out DIR]
  region = seoul | gyeonggi | <la0,lo0,la1,lo1>
"""
import sys, os, json, time, math, gzip, urllib.request, urllib.parse, urllib.error

EP = ['https://overpass-api.de/api/interpreter',
      'https://overpass.kumi.systems/api/interpreter']
TILE = 0.018          # 위도 약 2km — 실측: 5km 타일은 건물까지 넣으면 504 로 계속 실패했다
CHUNK_M = 1000        # 게임 청크 크기(m)

BOX = {
    'seoul':    (37.4130, 126.7645, 37.7150, 127.1830),
    'gyeonggi': (36.8930, 126.2620, 38.2850, 127.8700),
}

def q_for(la0, lo0, la1, lo1):
    return f"""[out:json][timeout:90];
(way["highway"~"^(motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|secondary_link|tertiary|tertiary_link|residential|unclassified|living_street|service)$"]({la0},{lo0},{la1},{lo1});
 way["building"]({la0},{lo0},{la1},{lo1});
 node["highway"="traffic_signals"]({la0},{lo0},{la1},{lo1}););
out geom;"""

def fetch(la0, lo0, la1, lo1, tries=6):
    q = q_for(la0, lo0, la1, lo1)
    for t in range(tries):
        ep = EP[t % len(EP)]
        try:
            req = urllib.request.Request(ep, data=urllib.parse.urlencode({'data': q}).encode(),
                                         headers={'User-Agent': 'seoul-drive/1.0'})
            return urllib.request.urlopen(req, timeout=180).read()
        except urllib.error.HTTPError as e:
            # ★429(Too Many Requests) = 서버가 '천천히 하라'는 뜻이다. 실측으로
            #   동시에 두 작업을 돌렸을 때 바로 429 가 떴다. 길게 쉬어야 풀린다.
            #   504(Gateway Timeout) = 쿼리가 무거운 것 → 짧게 쉬고 재시도.
            wait = 60 if e.code == 429 else 5 + t * 8
            print(json.dumps({'retry': t + 1, 'code': e.code, 'wait': wait}), flush=True)
            time.sleep(wait)
        except Exception as e:
            wait = 5 + t * 8
            print(json.dumps({'retry': t + 1, 'err': type(e).__name__, 'wait': wait}), flush=True)
            time.sleep(wait)
    return None

def main():
    region = sys.argv[1]
    out = 'games/seoul-drive/data/osm'
    if '--out' in sys.argv:
        out = sys.argv[sys.argv.index('--out') + 1]
    os.makedirs(out, exist_ok=True)
    if region in BOX:
        la0, lo0, la1, lo1 = BOX[region]
    else:
        la0, lo0, la1, lo1 = [float(x) for x in region.split(',')]

    lat_tiles = math.ceil((la1 - la0) / TILE)
    lon_step = TILE / math.cos(math.radians((la0 + la1) / 2))
    lon_tiles = math.ceil((lo1 - lo0) / lon_step)
    total = lat_tiles * lon_tiles
    print(json.dumps({'region': region, 'tiles': total,
                      'grid': f'{lat_tiles}x{lon_tiles}'}), flush=True)

    done = ok = 0
    for i in range(lat_tiles):
        for j in range(lon_tiles):
            done += 1
            a0 = la0 + i * TILE; a1 = min(la1, a0 + TILE)
            o0 = lo0 + j * lon_step; o1 = min(lo1, o0 + lon_step)
            fp = f'{out}/t_{i:03d}_{j:03d}.json.gz'
            if os.path.exists(fp):          # 이어받기
                ok += 1; continue
            raw = fetch(a0, o0, a1, o1)
            if raw is None:
                print(json.dumps({'tile': [i, j], 'FAIL': True, 'done': done, 'total': total}), flush=True)
                continue
            with gzip.open(fp, 'wb') as f:
                f.write(raw)
            ok += 1
            print(json.dumps({'tile': [i, j], 'kb': round(len(raw) / 1024),
                              'done': done, 'total': total, 'ok': ok}), flush=True)
            time.sleep(2)
    print(json.dumps({'finished': True, 'ok': ok, 'total': total, 'out': out}))

if __name__ == '__main__':
    main()
