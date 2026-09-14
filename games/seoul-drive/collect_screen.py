"""화면만으로 수집 — 픽셀 + 라벨을 같은 프레임에서 뽑는다 (2026-09-14).

★db 방식을 버린 이유: 아티팩트 db 는 용량이 차면(run 66개, 'Storage full')
  조용히 죽는다. 실제로 1시간 동안 죽어 있었고 그 사이 모은 42,584프레임이
  라벨 없이 버려졌다. 화면 코드픽셀은 용량 제약이 없고, 픽셀과 라벨이
  같은 프레임에서 나오므로 타임스탬프를 맞출 필요조차 없다.

사용: python3 collect_screen.py <out_dir> <seconds>
"""
import sys, os, time, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from net import preprocess
from decode import decode
import capture as C

def main(out, secs):
    os.makedirs(out, exist_ok=True)
    if C.find_window() is None:
        print('{"err":"no chrome window"}'); return
    C.start_background()
    X, Y, M = [], [], []
    skipped = 0
    t0 = time.time(); secs = float(secs); seq = None
    try:
        while time.time() - t0 < secs:
            f, seq = C.latest(seq)              # 새 프레임만
            if f is None: continue
            # ★f 는 capture 가 주는 BGR. decode 가 내부에서 뒤집으므로 그대로 넘긴다
            #   (예전엔 여기서 한 번 뒤집고 decode 가 또 뒤집어 원위치 = 오판독).
            d = decode(f)
            if d is None:                       # 코드픽셀을 못 읽으면 버린다
                skipped += 1; continue
            X.append(preprocess(f).cpu().numpy().astype(np.float16))
            Y.append([d['steer'], d['thr'], d['brake'], d['rev']])
            M.append([d['v'], d['lane'], 0.0, d['crashes'], d['hold'], d['on_road']])
    finally:
        C.stop_background()
    if not X:
        print(json.dumps({'frames': 0, 'skipped': skipped})); return
    Xa = np.stack(X); Ya = np.array(Y, np.float32); Ma = np.array(M, np.float32)
    np.save(f'{out}/X.npy', (Xa * 255).astype(np.uint8))
    np.save(f'{out}/Y.npy', Ya)
    np.save(f'{out}/M.npy', Ma)
    with open(f'{out}/DONE', 'w') as fh: fh.write('ok')
    on = float((Ma[:, 5] > 0).mean())
    print(json.dumps({
        'frames': len(X), 'skipped': skipped, 'fps': round(len(X)/secs, 1),
        'on_road_pct': round(on*100, 1),
        'lane_median': round(float(np.median(Ma[:, 1])), 2),
        'steer_std': round(float(Ya[:, 0].std()), 3),
        'brake_frames': int((Ya[:, 2] > 0.2).sum()),
        'crash_frames': int((Ma[:, 4] > 0).sum()),
        'out': out}))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
