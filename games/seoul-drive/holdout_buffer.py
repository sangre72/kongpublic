#!/usr/bin/env python3
"""u_5750: training-eligibility rule. Replaces the +/-1 chunk buffer, which excluded a 3x3 km
neighbourhood per holdout cell and removed 70% of in-scope roads (two 103->10, arterial 30->10).

Rule: a road may be used for TRAINING iff
  (1) it is >= R metres from every holdout cell centre (R=1000m default; the adjacent-cell
      diagonal is 707m, so 1000m keeps more than one cell of separation), AND
  (2) its NAME does not appear inside any holdout cell - a same-named road continuing into a
      test cell is the same road, so distance alone would not catch it.
Measured at R=1000m: (2) excludes 0 additional roads, i.e. (1) already subsumes it. Kept as a
permanent guard so a future R change cannot silently reintroduce name leakage.
The holdout/test set itself is unchanged - this only governs what TRAINING may draw.
"""
import json, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
R_DEFAULT = float(os.environ.get('HOLDOUT_R', '1000'))
def _holdout():
    return [tuple(k) for k in json.load(open(os.path.join(HERE, 'data/holdout_chunks.json')))['chunks']]
def holdout_names(roads):
    H = _holdout()
    ck = lambda r: (math.floor(r['x'] / 1000), math.floor(r['y'] / 1000))
    return {r['n'] for r in roads if r.get('n') and ck(r) in H}
def train_eligible(r, names=None, R=None):
    H = _holdout(); R = R_DEFAULT if R is None else R
    d = min(math.hypot(r['x'] - (h[0] * 1000 + 500), r['y'] - (h[1] * 1000 + 500)) for h in H)
    if d < R: return False
    if names and r.get('n') in names: return False
    return True
