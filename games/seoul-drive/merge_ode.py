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
    # ★수집 중 '정지' 연출 프레임은 제외한다(u_5163).
    #   커리큘럼은 차를 일부러 세우거나 밀어냈다 — 그 순간의 급제동은
    #   '상황 대처'가 아니라 연출이다. 실측: 이탈복구 21.2% / 정지출발 19.7% 가
    #   brake>0.5 인데 원본은 0.5% 다. 이걸 증폭하면 오드가 '서 있기'를 배운다
    #   (오드 v2 실주행 thr=0.109 brake=0.790, 진행률 0.0).
    #   배우게 하려는 건 '어떻게 돌아오는가(조향)'이지 '어떻게 서는가'가 아니다.
    def drop_stall(X, Y, M):
        keep = ~((Y[:, 2] > 0.5) & (Y[:, 1] < 0.3))     # 급제동+저스로틀 = 정지 연출
        return X[keep], Y[keep], M[keep]

    parts = []
    base = load(f'{BASE}/data/final_uniq')
    if base: parts.append(('final_uniq', base, 1))

    # 커리큘럼은 희소하므로 3배 반복해서 비중을 올린다
    for d in sorted(glob.glob(f'{BASE}/data/ode_*')):
        p = load(d)
        if p and len(p[1]) > 0:
            p = drop_stall(np.asarray(p[0]), p[1], p[2])
            name = os.path.basename(d)
            # ★결손이 심한 구간일수록 더 많이 반복한다(u_5158 실측).
            #   3배 균일로는 좌:우 = 1:17.6 에 머물렀다(원래 1:94).
            #   좌회전·이탈복구는 오드가 못 하는 바로 그 동작이라 가중치를 더 준다.
            # ★가중치를 낮춘다(u_5162 실패 분석).
            #   12배로 불렸더니 커리큘럼의 '제동 편중'까지 12배가 됐다.
            #   실측 brake>0.5 비율: 기존 0.5% / 이탈복구 21.2% / 정지출발 19.7%
            #   합치니 7.2%, 스로틀 평균도 0.812 -> 0.643 으로 하락.
            #   결과: 오드 v2 가 실주행에서 thr=0.109 brake=0.790 -> 안 움직임
            #   (진행률 0.0, 사고 17). 새 상황 자체는 배웠다
            #   (그 데이터 조향 상관 v1 0.079 -> v2 0.863).
            #   문제는 양이 아니라 '제동까지 같이 증폭한 것'이다.
            rep = {'ode_left': 4, 'ode_recover': 3,
                   'ode_overtake': 3, 'ode_lanechg': 3, 'ode_stopgo': 1}.get(name, 2)
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
