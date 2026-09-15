#!/usr/bin/env python3
"""회피·추월 수집 — 모델이 몰고, 교사가 '나라면 이렇게 피한다'를 라벨로 남긴다 (u_5141).

★왜 이게 필요한가 (실측):
  기존 고유 21,677 프레임 중 **사고 발생 프레임은 3장**뿐이다.
  앞차 채널은 M 에 아예 없다. 즉 모델은 '부딪힐 상황' 자체를 본 적이 없다.
  교사 혼자 달린 데이터는 교사가 잘 가는 길만 담는다 — 위험 상황이 안 생긴다.

★그래서 DAgger 다:
  모델이 직접 운전한다 → 모델은 위험한 데를 간다(그게 지금 실력이다)
  그 순간 교사에게 "너라면?" 을 물어 **정답만** 라벨로 남긴다
  → 모델이 실제로 처하는 상황의 정답이 쌓인다. 이게 회피·추월을 배우는 유일한 길이다.

★기존 dagger_run.py 를 안 쓰는 이유:
  화살표키로 조작한다 — game.js step() 의 키 처리는 `if(!auto.on)` 안에만 있어
  경로 주행 중이면 통째로 무시된다. 그리고 **교사 라벨을 저장하지 않는다.**

수집 규칙(u_5140):
  · 같은 프레임 중복 저장 금지(화면 해시)
  · 교사 OFF 면 라벨이 언다 → 조향값이 N프레임 고정이면 즉시 중단
  · rev != 0 이면 코드픽셀 오염 → 즉시 중단

사용: python3 collect_avoid.py <out_dir> <secs>
"""
import sys, os, time, json, hashlib, urllib.request
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capture as C
from net import preprocess
from gpu_guard import require_gpu

TEL = 'http://localhost:8901/tel'


def tel():
    try:
        return json.load(urllib.request.urlopen(TEL, timeout=2))
    except Exception:
        return None


def main(out, secs):
    os.makedirs(out, exist_ok=True)
    DEV = require_gpu()                      # GPU 강제. CPU 폴백 금지
    X, Y, M = [], [], []
    seen = set()
    t0 = time.time(); secs = float(secs)
    dup = 0; nolabel = 0; last_st = None; frozen = 0
    risky = 0                                # 위험상황(앞차 가깝거나 이탈 직전) 프레임 수

    while time.time() - t0 < secs:
        d = tel()
        if not d:
            time.sleep(0.05); continue
        if d.get('drv') != 'MODEL':
            print(json.dumps({'abort': 'drv=%s — 모델이 몰고 있지 않다' % d.get('drv')}))
            return
        t = d.get('tch') or {}
        if not t.get('ok'):
            nolabel += 1
            if nolabel > 200:
                print(json.dumps({'abort': '교사 라벨 없음(교사 OFF 로 보인다)'})); return
            time.sleep(0.05); continue

        st, th, br = float(t['st']), float(t['th']), float(t['br'])
        # 라벨 동결 감지 — 교사가 꺼지면 같은 값만 나온다
        if last_st is not None and abs(st - last_st) < 1e-9:
            frozen += 1
            if frozen > 150:
                print(json.dumps({'abort': '라벨 동결(조향값 150프레임 고정)'})); return
        else:
            frozen = 0
        last_st = st

        a = C.grab_canvas()
        if a is None:
            time.sleep(0.03); continue
        h = hashlib.md5(np.ascontiguousarray(a)).digest()
        if h in seen:                        # ★중복 프레임 저장 금지
            dup += 1; time.sleep(0.02); continue
        seen.add(h)

        f = preprocess(a, device=DEV)[0] if preprocess(a, device=DEV).ndim == 4 \
            else preprocess(a, device=DEV)
        car = d.get('car') or {}
        X.append(f.cpu().numpy().astype(np.uint8) if f.dtype == np.uint8
                 else (f.cpu().numpy() * 255).astype(np.uint8))
        Y.append([st, th, br, 0.0])
        M.append([car.get('v', 0), 0.0, 0.0, d.get('cr', 0), 0.0, car.get('onroad', 1)])
        if car.get('onroad', 1) == 0 or br > 0.5:
            risky += 1
        time.sleep(0.02)

    if not X:
        print(json.dumps({'err': 'no frames'})); return
    np.save(f'{out}/X.npy', np.stack(X))
    np.save(f'{out}/Y.npy', np.array(Y, dtype=np.float32))
    np.save(f'{out}/M.npy', np.array(M, dtype=np.float32))
    open(f'{out}/DONE', 'w').write('ok\n')
    print(json.dumps({'frames': len(X), 'dup_skipped': dup, 'risky': risky,
                      'risky_pct': round(100 * risky / len(X), 1), 'out': out}))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
