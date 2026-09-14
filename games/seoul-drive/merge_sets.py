"""여러 수집 디렉토리를 하나로 합친다 (u_4975 혼합 학습용).

오너 판단: 밀도별로 모델을 나누지 않고 하나로 간다. 실제 주행은 밀도가 계속
바뀌므로 한 모델이 전부 겪어야 한다.

X 는 크다(레벨당 4.4GB) → 전부 메모리에 올리지 않고 mmap 으로 이어붙인다.
--stride N 으로 N프레임마다 1장만 취해 용량을 줄일 수 있다(연속 프레임은
거의 같은 그림이라 정보량 대비 낭비가 크다).

사용: python3 merge_sets.py <out_dir> <in1> <in2> ... [--stride N]
"""
import sys, os, json
import numpy as np

def main(argv):
    stride = 1
    if '--stride' in argv:
        i = argv.index('--stride'); stride = int(argv[i+1]); argv = argv[:i] + argv[i+2:]
    out, ins = argv[0], argv[1:]
    os.makedirs(out, exist_ok=True)
    metas = []
    tot = 0
    for d in ins:
        Y = np.load(f'{d}/Y.npy'); n = len(Y)
        idx = np.arange(0, n, stride)
        metas.append((d, idx)); tot += len(idx)
    print(json.dumps({'sources': len(ins), 'total_frames': tot, 'stride': stride}), flush=True)

    X0 = np.load(f'{ins[0]}/X.npy', mmap_mode='r')
    Xo = np.lib.format.open_memmap(f'{out}/X.npy', mode='w+',
                                   dtype=X0.dtype, shape=(tot,) + X0.shape[1:])
    Ys, Ms, SRC = [], [], []
    k = 0
    for si, (d, idx) in enumerate(metas):
        X = np.load(f'{d}/X.npy', mmap_mode='r')
        Y = np.load(f'{d}/Y.npy'); M = np.load(f'{d}/M.npy')
        for j0 in range(0, len(idx), 512):          # 512장씩 복사(메모리 상한)
            b = idx[j0:j0+512]
            Xo[k:k+len(b)] = X[b]
            k += len(b)
        Ys.append(Y[idx]); Ms.append(M[idx])
        SRC.append(np.full(len(idx), si, np.int8))
        print(json.dumps({'done': d, 'frames': len(idx)}), flush=True)
    Xo.flush()
    np.save(f'{out}/Y.npy', np.concatenate(Ys))
    np.save(f'{out}/M.npy', np.concatenate(Ms))
    np.save(f'{out}/SRC.npy', np.concatenate(SRC))   # 어느 밀도에서 왔는지(평가용)
    with open(f'{out}/DONE','w') as f: f.write('ok')
    Ma = np.concatenate(Ms); Ya = np.concatenate(Ys)
    print(json.dumps({'merged': tot, 'out': out,
        'on_road_pct': round(float((Ma[:,5]>0.5).mean()*100),1),
        'lane_median': round(float(np.median(Ma[:,1])),2),
        'steer_std': round(float(Ya[:,0].std()),3),
        'crash_frames': int((Ma[:,4]>0).sum())}))

if __name__ == '__main__':
    main(sys.argv[1:])
