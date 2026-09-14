"""fast_capture .npz + db 라벨 → 학습셋 (2026-09-14).

fast_capture 는 이미 84x84 float16 로 줄여서 frames.npz 에 쌓아둔다(PNG 인코딩 제거).
여기서는 타임스탬프로 라벨과 짝만 맞춘다.

사용: python3 build_dataset2.py labels.json run_dir out.npz
"""
import sys, json
import numpy as np

def main(lab_path, run_dir, out_path):
    rows = []
    for doc in json.load(open(lab_path)):
        rows.extend(doc.get('rows', []))
    rows.sort(key=lambda r: r['t'])
    lt = np.array([r['t'] for r in rows])

    import os
    if os.path.exists(f'{run_dir}/X.npy'):      # 새 포맷(무압축 uint8)
        X = np.load(f'{run_dir}/X.npy', mmap_mode='r')
        T = np.load(f'{run_dir}/T.npy')
    else:
        d = np.load(f'{run_dir}/frames.npz')
        X, T = d['X'], d['T']

    keepX, Y, M = [], [], []
    for i in range(len(T)):
        j = int(np.argmin(np.abs(lt - T[i])))
        if abs(int(lt[j]) - int(T[i])) > 120:   # 120ms 넘게 벌어지면 버린다
            continue
        r = rows[j]
        keepX.append(np.asarray(X[i], dtype=np.float16) / np.float16(255))  # 이미 (3,256,256)
        Y.append([r['steer'], r['thr'], r['brake'], r['rev']])
        M.append([r['v'], r['lane'], r['obst'], r['cr'], r['hold']])
    if not keepX:
        print('{"frames":0,"err":"no pairs"}'); return
    Xa = np.stack(keepX); Ya = np.array(Y, np.float32); Ma = np.array(M, np.float32)
    np.savez_compressed(out_path, X=Xa, Y=Ya, M=Ma)
    print(json.dumps({'frames': int(len(Xa)), 'out': out_path,
                      'steer_std': round(float(Ya[:,0].std()), 4),
                      'steer_min': round(float(Ya[:,0].min()), 3),
                      'steer_max': round(float(Ya[:,0].max()), 3),
                      'brake_frames': int((Ya[:,2] > .2).sum()),
                      'crash_frames': int((Ma[:,4] > 0).sum())}))

if __name__ == '__main__':
    main(*sys.argv[1:4])
