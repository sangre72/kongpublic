#!/usr/bin/env python3
"""u_5741(b): running class histogram of collected L12 frames + which class is most in surplus.
Classes by nl (lanes per direction): alley nl<=1, two nl==2, arterial nl>=3.
Target = holdout mix ~35/35/30. Prints: "<surplus_class> alley=<n> two=<n> arterial=<n> kept=<n>"."""
import numpy as np, glob, sys
TARGET = {'alley': 0.35, 'two': 0.35, 'arterial': 0.30}
pat = sys.argv[1] if len(sys.argv) > 1 else 'data/dagger_r35*'
c = {'alley': 0, 'two': 0, 'arterial': 0}
for d in sorted(glob.glob(pat)):
    try:
        L = np.load(f'{d}/L.npy').astype(np.float32); Y = np.load(f'{d}/Y.npy').astype(np.float32)
    except Exception: continue
    if L.shape[1] < 12 or len(L) != len(Y): continue
    ok = (L[:, 11] > 0) & (Y[:, 3] > 1.0) & (np.abs(L[:, 0]) <= 2.5) & (np.abs(L[:, 1]) <= 0.7) & (np.abs(L[:, 3:6]) <= 20).all(1)
    nl = L[ok, 7]
    c['alley'] += int((nl <= 1).sum()); c['two'] += int((nl == 2).sum()); c['arterial'] += int((nl >= 3).sum())
kept = sum(c.values())
# surplus = target share - actual share; pick the largest (empty set -> alley, the structurally starved one)
defi = min(TARGET, key=lambda k: TARGET[k] - (c[k] / kept if kept else 0.0)) if kept else 'none'
print(f"{defi} alley={c['alley']} two={c['two']} arterial={c['arterial']} kept={kept}")
