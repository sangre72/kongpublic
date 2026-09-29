#!/usr/bin/env python3
"""u_5773 BASELINE FIRST: score the RULE on perturbation RECOVERY, before any training.
Episodes start from a commanded perturbed pose (the ?pgrid= placement already built in u_5763).
Reward = recovery speed + post-recovery stability - overshoot penalty; departure/crash terminates.
If the rule's recovery is already tight, there is no headroom and we stop instead of repeating
the u_5772 cycle (where we trained on a task the rule already solved)."""
import sys, os, json, time, urllib.request
import numpy as np
TEL = 'http://localhost:8901/tel'
REC_EY = 0.2          # recovered when |e_y| < this
HOLD = 20             # frames of stability scored after recovery
W_OVER = 1.0          # overshoot penalty weight
def tel():
    try:
        with urllib.request.urlopen(TEL, timeout=4) as r: return json.load(r)
    except Exception: return None
def ey_of(d):
    g = d.get('geo') or {}
    v = g.get('ey')
    return abs(float(v)) if isinstance(v, (int, float)) else None
def sgn_ey(d):
    g = d.get('geo') or {}
    v = g.get('ey')
    return float(v) if isinstance(v, (int, float)) else 0.0
def run_episode(last_n, max_s=12.0, dt=0.05):
    """Wait for a perturbation to fire, then score the recovery."""
    # u_5774 ROOT CAUSE: keying on pgOn re-entered the SAME live perturbation once pghold was long
    #   enough to span several calls - 13 scored "episodes" came from only 3 real triggers, all
    #   reporting the same cell. An episode is one TRIGGER, so wait for pgN to advance.
    t0 = time.time(); start = None; cur_n = last_n
    while time.time() - t0 < 40.0:
        d = tel()
        if d is not None:
            n = int(d.get('pgN') or 0)
            if n > last_n and d.get('pgOn'):
                start = d; cur_n = n; break
        time.sleep(0.03)
    if start is None: return None, last_n
    # u_5773 fix: pgOn flips true on the frame the displacement is APPLIED, so sampling immediately
    #   can read ey before it lands (measured: 4 of 9 episodes reported ey0 ~0.0 and "recovered" in
    #   0.06s - those are not recoveries, they are reads of the pre-displacement pose). Wait for the
    #   offset to actually appear, and skip the episode if it never does.
    for _ in range(20):
        time.sleep(0.03)
        d2 = tel()
        if d2 and (ey_of(d2) or 0) > 0.15: start = d2; break
    ey0 = ey_of(start) or 0.0
    if ey0 < 0.15: return None, cur_n   # u_5773: 0.25 rejected valid small-offset cells; 0.15 keeps them
    cell = start.get('pgCell')
    t_start = time.time(); rec_t = None; overshoot = 0.0; s0 = sgn_ey(start)
    post = []; prev = start
    while time.time() - t_start < max_s:
        time.sleep(dt)
        cur = tel()
        if not cur: continue
        e = ey_of(cur)
        if e is None: continue
        # u_5774 ROOT CAUSE #2: a bare cr-delta counts ANY crash in the window - pedestrian
        #   bul-ga-hang-ryeok and counter resets included. Measured: episodes labelled "crashed"
        #   had SMALLER starting offsets (0.583m) than recovered ones (1.043m), the opposite of a
        #   real departure mechanism, inflating failure 27-36% -> 63.1%. Only count a crash that
        #   is a DEPARTURE the perturbation plausibly caused: the car must be leaving the lane.
        cr = int(cur.get('cr') or 0) - int(prev.get('cr') or 0)
        _kinds = cur.get('crk') or {}
        _blame = any(('이탈' in k) or ('침범' in k) for k in _kinds)
        if cr > 0 and _blame and e > 1.0:
            return dict(cell=cell, ey0=round(ey0,3), rec_t=None, crashed=1, mean_r=-10.0), cur_n
        s = sgn_ey(cur)
        if rec_t is None:
            if s0 != 0 and np.sign(s) != np.sign(s0) and abs(s) > REC_EY:
                overshoot = max(overshoot, abs(s))       # crossed past centre before settling
            if e < REC_EY: rec_t = time.time() - t_start
        else:
            post.append(e)
            if len(post) >= HOLD: break
        prev = cur
    if rec_t is None:
        return dict(cell=cell, ey0=round(ey0,3), rec_t=None, crashed=0,
                    mean_r=round(-(ey0) - W_OVER*overshoot - 5.0, 3)), cur_n
    stab = float(np.mean(post)) if post else 0.0
    r = -(rec_t) - stab - W_OVER*overshoot
    return dict(cell=cell, ey0=round(ey0,3), rec_t=round(rec_t,2), overshoot=round(overshoot,3),
                stab=round(stab,3), crashed=0, mean_r=round(r,3)), cur_n
def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    out = []
    last_n = -1
    d0 = tel()
    if d0 is not None: last_n = int(d0.get('pgN') or 0)
    for i in range(n):
        e, last_n = run_episode(last_n)
        if e is None:
            print(json.dumps({'ep': i, 'skip': 'no perturbation fired'}), flush=True); continue
        e['ep'] = i; out.append(e); print(json.dumps(e, ensure_ascii=False), flush=True)
    if out:
        rt = [o['rec_t'] for o in out if o.get('rec_t') is not None]
        print(json.dumps({'RULE_baseline': True, 'eps': len(out),
                          'mean_r': round(float(np.mean([o['mean_r'] for o in out])), 3),
                          'recovered': len(rt), 'failed': len(out)-len(rt),
                          'rec_t_mean': round(float(np.mean(rt)), 2) if rt else None,
                          'rec_t_p50': round(float(np.median(rt)), 2) if rt else None,
                          'rec_t_p90': round(float(np.percentile(rt, 90)), 2) if rt else None,
                          'overshoot_mean': round(float(np.mean([o.get('overshoot',0) for o in out])), 3)},
                         ensure_ascii=False), flush=True)
if __name__ == '__main__': main()
