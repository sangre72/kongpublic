"""교사 시범주행 화면 수집 (2026-09-14, 256 입력 + 백그라운드 캡처).

라벨은 페이지가 artifact db 에 직접 기록하고, 여기서는 픽셀만 모은다.
타임스탬프로 나중에 짝을 맞춘다(build_dataset2.py).

★latest(min_seq) 로 '새 프레임만' 받는다 — 추론 루프는 같은 프레임을
  다시 봐도 되지만 학습 데이터에 중복이 쌓이면 안 된다.

사용: python3 fast_capture.py <out_dir> <seconds>
"""
import sys, os, time, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from net import preprocess
import capture as C

def main(out, secs):
    os.makedirs(out, exist_ok=True)
    if C.find_window() is None:
        print('{"err":"no chrome window"}'); return
    C.start_background()
    buf, idx = [], []
    t0 = time.time(); secs = float(secs); seq = None
    try:
        while time.time() - t0 < secs:
            f, seq = C.latest(seq)          # 새 프레임만
            if f is None: continue
            buf.append(preprocess(f).cpu().numpy().astype(np.float16))
            idx.append(int(time.time() * 1000))
    finally:
        C.stop_background()
    if not buf:
        print('{"frames":0}'); return
    # ★압축 저장 금지(2026-09-14): 256x256 float16 수만 장을 savez_compressed 로
    #   저장하면 205MB 를 쥐어짜느라 수십 초가 걸리고, 그동안 파일이 불완전해
    #   뒤따르는 파이프라인이 BadZipFile 로 죽는다. 무압축 .npy 로 바로 쓴다.
    #   (uint8 로 저장해 용량도 절반 — 학습때 /255 하면 된다)
    X = (np.stack(buf) * 255).astype(np.uint8)
    np.save(f'{out}/X.npy', X)
    np.save(f'{out}/T.npy', np.array(idx, dtype=np.int64))
    with open(f'{out}/DONE', 'w') as fh: fh.write('ok')      # 완료 표식
    print(json.dumps({'frames': len(buf), 'fps': round(len(buf)/secs, 1), 'out': out}))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
