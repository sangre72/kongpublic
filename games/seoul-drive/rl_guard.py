"""RL collection guardrails (a_5124 T3). All three are measured failure modes.

1. assert_teacher_live — the teacher must be ON or labels FREEZE.
   Measured 2026-09-15: with the teacher idle, /tel returned st=thr=brk=0.000
   unchanged across every sample for minutes. Earlier: 2 unique steer values
   across 278 frames. Constant labels train nothing and fail silently, so we
   abort loudly instead.

2. dedupe_consecutive — 74.1% of stored frames are exact byte-duplicates of the
   PREVIOUS frame (measured on data/final X.npy, first 6000: 4444 consecutive
   identical, 1556 unique). They are consecutive because capture outruns the
   game repaint. A strided/global hash sample shows 0% and misses this entirely.

3. RouteGuard — never overwrite bc_final.pt; never delete data/.
"""
import hashlib, os
import numpy as np

PROTECTED = ('bc_final.pt',)


def assert_teacher_live(samples, min_unique=8, key='st'):
    """samples = list of /tel dicts. Abort if the teacher's output is frozen."""
    vals = [round(float(s.get(key, 0.0)), 4) for s in samples]
    u = len(set(vals))
    if u < min_unique:
        raise SystemExit(
            '[rl_guard] TEACHER FROZEN: only %d unique %s across %d samples '
            '(need >=%d). Labels would be constant — aborting collection.\n'
            '  values seen: %s' % (u, key, len(vals), min_unique, sorted(set(vals))[:12]))
    return u


def dedupe_consecutive(X):
    """Return indices keeping only frames that differ from the previous kept frame."""
    keep, prev = [], None
    for i in range(len(X)):
        h = hashlib.md5(np.ascontiguousarray(X[i]).tobytes()).digest()
        if h != prev:
            keep.append(i); prev = h
    return np.array(keep, dtype=np.int64)


def assert_not_protected(path):
    if os.path.basename(path) in PROTECTED:
        raise SystemExit('[rl_guard] %s is the BC baseline — never overwrite it.'
                         % os.path.basename(path))
    return path
