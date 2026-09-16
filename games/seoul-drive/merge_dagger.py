#!/usr/bin/env python3
"""DAgger 병합 — 원본 BC 데이터 + 모델이 실제로 간 상태의 교사 정답 (a_5170).

★DAgger 의 정의대로 '누적(aggregate)' 한다. 새 라운드 데이터만으로 학습하면
  이전에 잘하던 것을 잊는다(catastrophic forgetting).

★가중치를 왜 이렇게 두나(실측):
  DAgger 프레임은 2,219 vs 원본 21,677 = 9.8배 차이. 그냥 붙이면 원본이 지배해
  '모델이 실제로 가는 상태'가 학습에 거의 안 잡힌다.
  그러나 v2 실패(u_5163)가 보여주듯 소수 데이터를 12배로 불리면 그 데이터의
  편중(여기선 |steer|>0.9 가 72.6%)까지 증폭돼 모델이 통째로 망가진다.
  ⇒ 3배로 제한한다. DAgger 비중 ~23%.

★정지 연출 프레임은 뺀다(u_5163 과 동일 규칙).
"""
import sys, os, numpy as np
BASE = os.path.dirname(os.path.abspath(__file__))

def main(out, rounds):
    Xs, Ys = [], []
    Xb = np.load(f'{BASE}/data/final_uniq/X.npy', mmap_mode='r')
    Yb = np.load(f'{BASE}/data/final_uniq/Y.npy')
    Xs.append(np.asarray(Xb)); Ys.append(Yb[:, :4] if Yb.shape[1] >= 4 else Yb)
    print('final_uniq %d x1' % len(Yb))
    for r in rounds:
        d = f'{BASE}/data/dagger_r{r}'
        X = np.load(f'{d}/X.npy', mmap_mode='r'); Y = np.load(f'{d}/Y.npy')
        keep = ~((Y[:, 2] > 0.5) & (Y[:, 1] < 0.3))       # 정지 연출 제외
        X = np.asarray(X)[keep]; Y = Y[keep]
        REP = 3
        for _ in range(REP):
            Xs.append(X); Ys.append(Y)
        print('dagger_r%s %d (정지제외 후) x%d' % (r, len(Y), REP))
    X = np.concatenate(Xs); Y = np.concatenate(Ys).astype(np.float32)
    os.makedirs(out, exist_ok=True)
    np.save(f'{out}/X.npy', X); np.save(f'{out}/Y.npy', Y)
    open(f'{out}/DONE', 'w').write('ok\n')
    print('합계 %d | thr %.4f | brk>0.5 %.2f%% | |steer|>0.9 %.1f%%'
          % (len(Y), Y[:, 1].mean(), (Y[:, 2] > 0.5).mean() * 100,
             (np.abs(Y[:, 0]) > 0.9).mean() * 100))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
