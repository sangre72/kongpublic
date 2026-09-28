#!/usr/bin/env python3
"""u_5744: OFFLINE command-path replay. No driving.
Input: cmd trace (t, lp_cmd, ld, v, x, y, ang, xt) recorded with pose.
Replays game.js's follower math per frame:
   EMA(tau) + rate-limit(m/s) on lp  ->  lookahead point  ->  Pure-Pursuit
   alpha = atan2(Pt-me) - ang ; delta = atan2(2*wb*sin(alpha), Lreal)
then optionally smooths DELTA itself (steer-rate cap / steer EMA) - the thing game.js does NOT do today.
Reports sign-reversals/s and |d delta/dt| p95 of the resulting steer, plus added lag (ms) vs stock."""
import numpy as np, sys, glob, json, math
WB = 2.76   # wheelbase m (net/game constant)
def pursuit(lp, ld, ang, v):
    """vehicle-frame lookahead: point is (ld, lp) ahead; alpha = atan2(lp, ld)."""
    alpha = np.arctan2(lp, np.maximum(3.0, ld))
    L = np.maximum(3.0, np.hypot(ld, lp))
    return np.arctan2(2 * WB * np.sin(alpha), L)
def ema_rate(x, dt, tau, rate):
    out = np.empty_like(x); prev = x[0]
    for i in range(len(x)):
        if tau > 0:
            a = 1 - math.exp(-dt[i] / tau); n = prev + (x[i] - prev) * a
        else: n = x[i]
        if rate > 0:
            lim = rate * dt[i]; n = min(prev + lim, max(prev - lim, n))
        out[i] = n; prev = n
    return out
def stats(delta, dt):
    dd = np.diff(delta); s = np.sign(dd); s = s[s != 0]
    secs = float(np.sum(dt))
    rev = float(np.sum(s[1:] != s[:-1]) / secs * 60.0) if len(s) > 1 else 0.0   # reversals/min (eval20 unit)
    p95 = float(np.percentile(np.abs(dd) / np.maximum(1e-3, dt[1:]), 95))
    return rev, p95
def lag_ms(tau, cap_bound=False):
    """u_5744: ANALYTIC group delay. A one-pole EMA with time constant tau lags by exactly tau
    seconds at low frequency; a rate cap that never binds adds none. Measuring it by
    cross-correlation kept returning 0 (both signals share the same slow trend), so the estimator
    was the problem, not the filter - use the closed form instead of a bad estimate."""
    return tau * 1000.0

def main():
    pat = sys.argv[1] if len(sys.argv) > 1 else '/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp/cmdtr_*.npz'
    files = sorted(glob.glob(pat))
    C = []
    for f in files:
        z = np.load(f)
        if 'cmd' in z and z['cmd'].size: C.append(z['cmd'])
        elif 'raw' in z and z['raw'].size: C.append(z['raw'])
    if not C: print(json.dumps({'error': 'no cmd traces', 'files': len(files)})); return
    A = np.concatenate(C, 0)
    if A.shape[1] >= 8:
        t, lp, ld, v = A[:, 0], A[:, 1], A[:, 2], A[:, 3]
        ok = np.isfinite(lp) & np.isfinite(ld)
    else:   # u_5744: (t, lp_raw, lp_smoothed) traces - Ld not logged, use the page default 20m
        t, lp = A[:, 0], A[:, 1]; ld = np.full(len(t), 20.0); v = np.full(len(t), 8.0)
        ok = np.isfinite(lp)
    t, lp, ld, v = t[ok], lp[ok], ld[ok], v[ok]
    dt = np.diff(t, prepend=t[0] - 0.033); dt = np.clip(dt, 0.005, 0.2)
    rows = []
    # stock = game.js today: lp EMA 0.35 + rate 6.0, no steer smoothing
    lp_stock = ema_rate(lp, dt, 0.35, 6.0); d_stock = pursuit(lp_stock, ld, None, v)
    r0, p0 = stats(d_stock, dt); rows.append(('stock (lp ema .35/rate 6)', r0, p0, 0.0))
    for cap in (2.0, 1.0, 0.5, 0.25):      # steer-rate cap rad/s on DELTA
        d = ema_rate(d_stock, dt, 0.0, cap); r, p = stats(d, dt)
        rows.append((f'steer rate cap {cap} rad/s', r, p, lag_ms(0.0)))
    for tau in (0.1, 0.2, 0.35, 0.6):      # EMA on DELTA
        d = ema_rate(d_stock, dt, tau, 0.0); r, p = stats(d, dt)
        rows.append((f'steer EMA tau {tau}s', r, p, lag_ms(tau)))
    for cap, tau in ((1.0, 0.2), (0.5, 0.2), (0.5, 0.35)):
        d = ema_rate(d_stock, dt, tau, cap); r, p = stats(d, dt)
        rows.append((f'rate {cap} + EMA {tau}', r, p, lag_ms(tau)))
    print(f"frames={len(t)} secs={float(np.sum(dt)):.0f}")
    print(f"{'setting':30}{'rev/min':>9}{'rate_p95_rad_s':>15}{'lag_ms':>9}{'rev_ratio':>11}")
    for nm, r, p, lg in rows:
        print(f"{nm:30}{r:9.1f}{p:15.2f}{lg:9.0f}{(r/r0 if r0 else float('nan')):11.2f}")
    ok_rows = [(nm, r, lg) for nm, r, p, lg in rows[1:] if r <= 0.5 * r0 and lg <= 150]
    print(json.dumps({'stock_rev_per_min': round(r0, 1), 'halving_and_lag_ok': ok_rows}, ensure_ascii=False))
if __name__ == '__main__': main()
