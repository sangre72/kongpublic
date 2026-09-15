#!/usr/bin/env python3
"""오드 v2 학습셋 병합 — 결손 구간 가중 균형 (u_5140/5144).

기존 final_uniq(21,677) 는 우회전 10,142 / 좌회전 108 로 94배 쏠려 있다.
커리큘럼(ode_*)은 부족한 상황만 모은 것이라 양이 적다 — 그냥 붙이면 기존이 지배한다.
그래서 **부족한 구간을 반복 샘플링(oversample)** 해서 비율을 맞춘다.

사용: python3 merge_ode.py <out_dir>
"""
import sys, os, glob
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))


def load(d):
    try:
        return (np.load(f'{d}/X.npy', mmap_mode='r'),
                np.load(f'{d}/Y.npy'), np.load(f'{d}/M.npy'))
    except Exception:
        return None


def main(out):
    parts = []
    base = load(f'{BASE}/data/final_uniq')
    if base: parts.append(('final_uniq', base, 1))

    # 커리큘럼은 희소하므로 3배 반복해서 비중을 올린다
    for d in sorted(glob.glob(f'{BASE}/data/ode_*')):
        p = load(d)
        if p and len(p[1]) > 0:
            name = os.path.basename(d)
            # ★결손이 심한 구간일수록 더 많이 반복한다(u_5158 실측).
            #   3배 균일로는 좌:우 = 1:17.6 에 머물렀다(원래 1:94).
            #   좌회전·이탈복구는 오드가 못 하는 바로 그 동작이라 가중치를 더 준다.
            rep = {'ode_left': 12, 'ode_recover': 12,
                   'ode_overtake': 8, 'ode_lanechg': 8, 'ode_stopgo': 6}.get(name, 3)
            parts.append((name, p, rep))

    if not parts:
        print('no data'); return

    Xs, Ys = [], []
    print('%-16s %8s %6s' % ('구간', '프레임', '배수'))
    for name, (X, Y, M), rep in parts:
        print('%-16s %8d %6d' % (name, len(Y), rep))
        for _ in range(rep):
            Xs.append(np.asarray(X)); Ys.append(Y)

    X = np.concatenate(Xs); Y = np.concatenate(Ys)
    os.makedirs(out, exist_ok=True)
    np.save(f'{out}/X.npy', X); np.save(f'{out}/Y.npy', Y)
    open(f'{out}/DONE', 'w').write('ok\n')
    L = (Y[:, 0] < -0.3).sum(); R = (Y[:, 0] > 0.3).sum()
    print('\n합계 %d 프레임 | 좌 %d 우 %d (비율 1:%.1f)' % (len(Y), L, R, R / max(1, L)))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else f'{BASE}/data/ode_v2')
