"""db 라벨 + 화면 프레임 → 학습셋(.npz)  (2026-09-14)

라벨은 페이지가 db에 직접 기록한 정확한 값이고(OCR 없음),
픽셀은 파이썬이 screencapture 로 따로 찍는다. 둘을 타임스탬프로 맞춘다.

사용:
  1) orch가 read_db 로 runs/<RUN>/frames 를 모두 받아 labels.json 으로 저장
  2) python3 build_dataset.py labels.json frames_dir out.npz
"""
import sys, json, os, glob
import numpy as np
from PIL import Image

def load_labels(path):
    rows = []
    for doc in json.load(open(path)):
        rows.extend(doc.get('rows', doc.get('data', {}).get('rows', [])))
    rows.sort(key=lambda r: r['t'])
    return rows

def preprocess(img):
    """면적평균으로 84x84 축소.
    ★::k 스트라이드 방식은 폭 2px짜리 차선을 통째로 건너뛴다(실측: 흰 픽셀 764→0).
      면적평균이면 가는 선도 회색으로 남아 신경망이 볼 수 있다."""
    f = np.asarray(img.convert('RGB').resize((168, 168), Image.LANCZOS), dtype=np.float32)
    blk = f.reshape(84, 2, 84, 2, 3).mean(axis=(1, 3))
    return (blk / 255.0).transpose(2, 0, 1)

def main(lab_path, frames_dir, out_path):
    rows = load_labels(lab_path)
    if not rows: print('no labels'); return
    lt = np.array([r['t'] for r in rows])
    files = sorted(glob.glob(os.path.join(frames_dir, '*.png')))
    X, Y, M = [], [], []
    for f in files:
        try: ts = int(os.path.basename(f).split('.')[0])
        except ValueError: continue
        i = int(np.argmin(np.abs(lt - ts)))
        if abs(lt[i] - ts) > 120:      # 120ms 이상 벌어지면 버린다
            continue
        r = rows[i]
        if r.get('hold'):              # 충돌 정지 프레임은 별도 취급
            pass
        X.append(preprocess(Image.open(f)).astype(np.float16))
        Y.append([r['steer'], r['thr'], r['brake'], r['rev']])
        M.append([r['v'], r['lane'], r['obst'], r['cr'], r['hold']])
    if not X: print('no paired frames'); return
    Xa = np.stack(X); Ya = np.array(Y, np.float32); Ma = np.array(M, np.float32)
    np.savez_compressed(out_path, X=Xa, Y=Ya, M=Ma)
    print(json.dumps({'frames': len(X), 'out': out_path,
                      'steer_std': float(Ya[:,0].std()),
                      'thr_mean': float(Ya[:,1].mean()),
                      'brake_frames': int((Ya[:,2] > .2).sum()),
                      'crash_frames': int((Ma[:,4] > 0).sum())}))

if __name__ == '__main__':
    main(*sys.argv[1:4])
