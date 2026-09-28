#!/usr/bin/env python3
"""u_5742: route/geographic coverage of collected L12 rounds.
Prints: pairs=<n> chunks=<n> bbox=<w>x<h>km area=<pct>% of scope
pairs come from the run logs (start>dest), chunks/bbox from Q.npy frame positions."""
import numpy as np, glob, sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scope import scope_bbox_m
pat = sys.argv[1] if len(sys.argv) > 1 else 'data/dagger_r35*'
# u_5743: count EVERY l12 round log. Per-run counting understated the set (3/3/0 vs the true 18/5/4):
#   the training set is all r35xx rounds, so coverage must be measured over all of them, not one run.
logs = sys.argv[2] if len(sys.argv) > 2 else os.environ.get('COVLOG', '/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp/l12_*.log')
pairs = set()
for f in sorted(set(sum((glob.glob(g) for g in logs.split()), []))):
    try:
        for ln in open(f, encoding='utf-8', errors='ignore'):
            m = re.match(r'^=== r\d+ (.+?) turns=', ln)
            if m: pairs.add(m.group(1).strip())
    except Exception: pass
xs = []; ys = []
for d in sorted(glob.glob(pat)):
    try: Q = np.load(f'{d}/Q.npy')
    except Exception: continue
    if Q.ndim < 2 or Q.shape[1] < 6: continue
    xs.append(Q[:, 4] / 6.0); ys.append(Q[:, 5] / 6.0)
if not xs:
    print('pairs=%d chunks=0 bbox=0x0km area=0.0%%' % len(pairs)); raise SystemExit
x = np.concatenate(xs); y = np.concatenate(ys)
ck = set(zip(np.floor(x / 1000).astype(int), np.floor(y / 1000).astype(int)))
bb = scope_bbox_m(); sw = (bb[2] - bb[0]) / 1000.0; sh = (bb[3] - bb[1]) / 1000.0
w = (x.max() - x.min()) / 1000.0; h = (y.max() - y.min()) / 1000.0
# u_5743: distinct ROADS PER CLASS is the coverage metric that matters (pair count can rise without
#   buying diversity by re-pairing the same scarce-class roads). Roads = both endpoints of each pair.
import json as _j
_cls = _j.load(open('data/scope_road_class.json'))
_roads = set()
for pr in pairs:
    for side in pr.split('>'):
        n = side.strip()
        if n: _roads.add(n)
_per = {'alley': 0, 'two': 0, 'arterial': 0}
for n in _roads:
    c = _cls.get(n)
    if c in _per: _per[c] += 1
print('roads alley=%d two=%d arterial=%d | pairs=%d chunks=%d bbox=%.1fx%.1fkm area=%.1f%%'
      % (_per['alley'], _per['two'], _per['arterial'], len(pairs), len(ck), w, h, 100.0 * (w * h) / (sw * sh)))
