#!/usr/bin/env python3
"""u_5751: build a 35/35/30 class-balanced training index from the collected rounds.
The road-deficit phase deliberately over-collected arterial, so the raw pool is skewed
(alley 24760 / two 22322 / arterial 26069). Subsample per class to the target mix, capped by
the scarcest class, and write the chosen (dir, row) pairs so training reads exactly this set.
"""
import numpy as np, glob, json, sys, collections
from train_geo import holdout_mask
TARGET = {'alley': .35, 'two': .35, 'arterial': .30}
pat = sys.argv[1] if len(sys.argv) > 1 else 'data/dagger_r3[56]*'
out = sys.argv[2] if len(sys.argv) > 2 else 'data/train_index_mix.json'
per = collections.defaultdict(list)
for d in sorted(glob.glob(pat)):
    try:
        L = np.load(f'{d}/L.npy').astype(np.float32); Y = np.load(f'{d}/Y.npy').astype(np.float32); Q = np.load(f'{d}/Q.npy')
    except Exception: continue
    if L.shape[1] < 12 or not (len(L) == len(Y) == len(Q)): continue
    ok = (L[:, 11] > 0) & np.isfinite(L[:, :11]).all(1) & (Y[:, 3] > 1.0) & (np.abs(L[:, 0]) <= 2.5) \
         & (np.abs(L[:, 1]) <= 0.7) & (np.abs(L[:, 3:6]) <= 20).all(1) & holdout_mask(Q)
    idx = np.where(ok)[0]
    if not len(idx): continue
    nl = L[idx, 7]
    for k, m in (('alley', nl <= 1), ('two', nl == 2), ('arterial', nl >= 3)):
        for r in idx[m]: per[k].append((d, int(r)))
have = {k: len(v) for k, v in per.items()}
# largest total N such that every class can supply its share
N = min(int(have[k] / TARGET[k]) for k in TARGET)
rng = np.random.default_rng(0)
sel = {}
for k in TARGET:
    want = int(N * TARGET[k])
    pick = rng.choice(len(per[k]), size=want, replace=False)
    sel[k] = [per[k][i] for i in sorted(pick)]
total = sum(len(v) for v in sel.values())
json.dump({k: [[d, r] for d, r in v] for k, v in sel.items()}, open(out, 'w'))
print(json.dumps({'raw': have, 'selected': {k: len(v) for k, v in sel.items()},
                  'total': total, 'mix': {k: round(100 * len(v) / total, 1) for k, v in sel.items()},
                  'out': out}, ensure_ascii=False))
