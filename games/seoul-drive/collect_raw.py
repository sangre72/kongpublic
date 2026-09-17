#!/usr/bin/env python3
"""오드 로우 데이터 수집기 (docs/ODE_data_and_RL_design.md §3, u_5269).

교사(GEOM+teacher.js)가 몰고, 매 틱 '화면 + /tel 스냅샷 + 이벤트' 를 남긴다.
라벨은 여기서 만들지 않는다 — label.py 가 tel.jsonl 에서 생성한다(규칙 바뀌면 재생성).

data/raw/<date>/<NNN_from_to>/
  frames/000123.jpg   256x256 (net.preprocess 와 같은 크롭·리사이즈, JPEG q92)
  tel.jsonl           프레임별 {top, tch, g2, da} 축약 스냅샷
  events.jsonl        사고·복귀·구속·갇힘 발생 시각
  meta.json           경로·결과·품질게이트(accepted)
  labels.npz          label.py 산출

사용: python3 collect_raw.py --pairs /tmp/pairs30.json --secs 100 [--out data/raw/<date>] [--fps 8]
"""
import argparse, hashlib, json, os, subprocess, sys, time, urllib.parse, urllib.request
import numpy as np, cv2
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)
import capture as C
from net import IMG, UI_CROP_TOP
import label as L

TEL = 'http://localhost:8901/tel'
TOP_KEYS = ('prog', 'routeM', 'v', 'cr', 'crk', 'tpN', 'tpPath', 'tpBld', 'blkCenter', 'blkStuck', 'ktDbg', 'loadId')
TCH_KEYS = ('ok', 'st', 'th', 'br', 'gap', 'ped', 'sig', 'sigStop', 'cap')
G2_KEYS = ('aTurn', 'aD', 'fin', 'laneF', 'nl', 'nlat', 'lat', 'roadW', 'o', 'off', 'want', 'aNl')
DA_KEYS = ('vmax', 'gp', 'stall', 'blk', 'cool', 'hold', 'xt')
UNAVOIDABLE = ('불가항력',)   # crk 키에 이 문자열이 있으면 점수 제외(u_5206)


def tel():
    try:
        return json.load(urllib.request.urlopen(TEL, timeout=3))
    except Exception:
        return None


def snap(d):
    top = d.get('top', d); t = d.get('tch') or {}; g = t.get('g2') or {}; da = top.get('da') or {}
    o = {'top': {k: top.get(k) for k in TOP_KEYS}, 'tch': {k: t.get(k) for k in TCH_KEYS},
         'g2': {k: g.get(k) for k in G2_KEYS}, 'da': {k: da.get(k) for k in DA_KEYS}}
    o['top']['kt'] = 1 if top.get('ktDbg') else 0
    return o


def grab_fast():
    """CGWindowListCreateImage 직접 호출(실측 10ms). capture.grab_canvas 는 screencapture CLI 를
       먼저 시도해 0.7초가 걸린다(실측 1.3fps) — 수집기는 CG 경로만 쓴다."""
    if 'rect' not in C._cache and C.find_window() is None: return None
    img = C.CG.CGWindowListCreateImage(C._cache['rect'], C.CG.kCGWindowListOptionOnScreenOnly,
                                       C.CG.kCGNullWindowID, C.CG.kCGWindowImageNominalResolution)
    if img is None:
        if C.find_window() is None: return None
        img = C.CG.CGWindowListCreateImage(C._cache['rect'], C.CG.kCGWindowListOptionOnScreenOnly,
                                           C.CG.kCGNullWindowID, C.CG.kCGWindowImageNominalResolution)
        if img is None: return None
    a = C._to_np(img)
    return a[C._cache['toolbar']:, :, :]


def to_frame(canvas_bgr):
    """net.preprocess 와 같은 크롭(UI_CROP_TOP)·리사이즈(256) — 학습·추론 경로와 동일."""
    c = canvas_bgr
    if c.shape[0] > 1000:                       # 레티나 물리해상도면 1/2
        c = cv2.resize(c, (c.shape[1] // 2, c.shape[0] // 2), interpolation=cv2.INTER_AREA)
    c = c[int(round(c.shape[0] * UI_CROP_TOP)):, :, :]
    return cv2.resize(np.ascontiguousarray(c), (IMG, IMG), interpolation=cv2.INTER_AREA)


def gate(meta, rows):
    """품질 게이트(설계 §2.4). 통과 못 하면 accepted=False 로 표시만 하고 지우진 않는다."""
    n = len(rows)
    if n < 50: return False, 'too_few'
    v = np.array([float(r['top'].get('v') or 0) for r in rows])
    stall = float((v < 0.3).mean())
    crk = meta.get('crk') or {}
    bad = {k: c for k, c in crk.items() if not any(u in k for u in UNAVOIDABLE)}
    st = np.array([float(r['tch'].get('st') or 0) for r in rows])
    meta.update({'stall_ratio': round(stall, 3), 'crash_scored': bad,
                 'steer_abs_mean': round(float(np.abs(st).mean()), 3)})
    if stall > 0.30: return False, 'stall>30%'
    if bad: return False, 'crash'
    if meta.get('tpN', 0) > 0: return False, 'teleport'
    if abs(st).mean() > 0.5: return False, 'steer_bias'
    return True, 'ok'


def run_episode(a, b, secs, outd, fps):
    url = 'http://localhost:8901/index.html?go=1&from=' + urllib.parse.quote(a) + '&to=' + urllib.parse.quote(b)
    r = subprocess.run(['bash', f'{BASE}/reload.sh', url, '120'], capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        return {'route': f'{a}>{b}', 'error': 'reload_fail', 'msg': r.stdout[-120:]}
    os.makedirs(f'{outd}/frames', exist_ok=True)
    d0 = tel() or {}; top0 = d0.get('top', d0)
    meta = {'route': f'{a}>{b}', 'routeM': top0.get('routeM'), 'loadId': top0.get('loadId'),
            'mode': 'teacher', 'secs': secs, 't_start': time.time()}
    rows, events = [], []
    seen = set(); dup = noframe = nolabel = 0
    last = {'cr': 0, 'tpN': 0, 'blkCenter': 0, 'blkStuck': 0}
    t0 = time.time(); period = 1.0 / fps; nxt = t0
    with open(f'{outd}/tel.jsonl', 'w', encoding='utf8') as ftel, open(f'{outd}/events.jsonl', 'w', encoding='utf8') as fev:
        while time.time() - t0 < secs:
            now = time.time()
            if now < nxt: time.sleep(min(0.01, nxt - now)); continue
            nxt += period
            d = tel()
            if not d: continue
            s = snap(d); top = s['top']
            for k in last:                                   # 이벤트
                cur = int(top.get(k) or 0)
                if cur > last[k]:
                    ev = {'t': round(now - t0, 2), 'i': len(rows), 'ev': k, 'n': cur, 'crk': top.get('crk')}
                    events.append(ev); fev.write(json.dumps(ev, ensure_ascii=False) + '\n'); last[k] = cur
            if (top.get('prog') or 0) >= 0.97:
                meta['arrived'] = True; break
            if not s['tch'].get('ok', True) or s['tch'].get('st') is None:
                nolabel += 1; continue
            f = grab_fast()
            if f is None: noframe += 1; continue
            h = hashlib.md5(np.ascontiguousarray(f[::8, ::8]).tobytes()).digest()
            if h in seen: dup += 1; continue
            seen.add(h)
            img = to_frame(f)
            cv2.imwrite(f'{outd}/frames/{len(rows):06d}.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 92])
            s['t'] = round(now - t0, 3)
            ftel.write(json.dumps(s, ensure_ascii=False) + '\n'); rows.append(s)
    dl = tel() or {}; topl = dl.get('top', dl)
    meta.update({'frames': len(rows), 'dup': dup, 'noframe': noframe, 'nolabel': nolabel,
                 'driven_m': round((topl.get('prog') or 0) * (topl.get('routeM') or 0)),
                 'cr': topl.get('cr'), 'crk': topl.get('crk'), 'tpN': topl.get('tpN'),
                 'blkCenter': topl.get('blkCenter'), 'blkStuck': topl.get('blkStuck'),
                 'events': len(events), 't_end': time.time()})
    ok, why = gate(meta, rows)
    meta['accepted'] = ok; meta['gate'] = why
    if rows:
        meta['labels'] = L.label_dir(outd)
    json.dump(meta, open(f'{outd}/meta.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pairs', required=True); ap.add_argument('--secs', type=float, default=100)
    ap.add_argument('--out', default=None); ap.add_argument('--fps', type=float, default=8)
    ap.add_argument('--start', type=int, default=0); ap.add_argument('--limit', type=int, default=999)
    a = ap.parse_args()
    outroot = a.out or f'{BASE}/data/raw/{time.strftime("%Y-%m-%d")}'
    os.makedirs(outroot, exist_ok=True)
    pairs = json.load(open(a.pairs))
    tot = acc = 0
    for i, pr in enumerate(pairs[a.start:a.start + a.limit], start=a.start):
        fr, to = (pr['from'], pr['to']) if isinstance(pr, dict) else (pr[0], pr[1])
        outd = f'{outroot}/{i:03d}_{fr}_{to}'
        m = run_episode(fr, to, a.secs, outd, a.fps)
        tot += m.get('frames', 0); acc += m.get('frames', 0) if m.get('accepted') else 0
        print(json.dumps({'i': i, **{k: m.get(k) for k in ('route', 'error', 'frames', 'driven_m', 'cr', 'tpN', 'accepted', 'gate', 'stall_ratio', 'steer_abs_mean')},
                          'reason': (m.get('labels') or {}).get('reason'), 'total_frames': tot, 'accepted_frames': acc}, ensure_ascii=False), flush=True)
    # 커버리지 manifest(설계 §2.3): 도로 유형·회전·reason 분포
    man = {'episodes': 0, 'accepted': 0, 'frames': 0, 'accepted_frames': 0, 'road': {}, 'turn': {}, 'reason': {}}
    for d in sorted(os.listdir(outroot)):
        mp = f'{outroot}/{d}/meta.json'
        if not os.path.exists(mp): continue
        m = json.load(open(mp)); man['episodes'] += 1; man['frames'] += m.get('frames', 0)
        if m.get('accepted'): man['accepted'] += 1; man['accepted_frames'] += m.get('frames', 0)
        for k, v in ((m.get('labels') or {}).get('reason') or {}).items(): man['reason'][k] = man['reason'].get(k, 0) + v
        try:
            for l in open(f'{outroot}/{d}/tel.jsonl', encoding='utf8'):
                g = json.loads(l)['g2']; key = ('oneway' if g.get('o') else 'twoway') + str(int(g.get('nl') or 0))
                man['road'][key] = man['road'].get(key, 0) + 1
                man['turn'][g.get('aTurn') or '?'] = man['turn'].get(g.get('aTurn') or '?', 0) + 1
        except Exception: pass
    json.dump(man, open(f'{outroot}/manifest.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    print(json.dumps({'manifest': man}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
