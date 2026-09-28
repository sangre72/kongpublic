#!/usr/bin/env python3
"""u_5748 summary: amp mean+-sd (primary), sc mean (screening), corner_xt95 MEDIAN + outliers named,
corner_frac, prog parity. MDE at n=3 / 300s for amp = 26%."""
import json,statistics as st,sys,collections
rows=[json.loads(l) for l in open(sys.argv[1],encoding='utf-8')]
G=collections.defaultdict(list)
for x in rows:
    d=x['res']; w=d.get('weave') or {}; c=d.get('corner') or {}; m=c.get('model') or {}
    G[(x['class'],x['stema'])].append(dict(
        amp=w.get('amp_p95'), sc=w.get('sc_min'), xt=m.get('xt_p95'),
        cf=c.get('corner_frac'), prog=(d.get('prog') or 0)*100,
        cr=d.get('crashes'), ck=d.get('crash_types')))
def ms(v):
    v=[z for z in v if z is not None]
    if not v: return None,None
    return st.mean(v), (st.stdev(v) if len(v)>1 else 0.0)
print(f"{'class':9}{'ema':<6}{'n':<3}{'amp mean+-sd':<18}{'sc mean':<9}{'xt med':<8}{'cf med':<8}{'prog':<7}")
for k in sorted(G):
    v=G[k]; am,asd=ms([z['amp'] for z in v]); sm,_=ms([z['sc'] for z in v])
    xts=[z['xt'] for z in v if z['xt'] is not None]; cfs=[z['cf'] for z in v if z['cf'] is not None]
    pm,_=ms([z['prog'] for z in v])
    print(f"{k[0]:9}{k[1]:<6}{len(v):<3}{f'{am:.3f} +-{asd:.3f}':<18}{sm:<9.2f}{(st.median(xts) if xts else 0):<8.2f}{(st.median(cfs) if cfs else 0):<8.3f}{pm:<7.1f}")
    out=[(z['xt'],z['ck'],z['cr']) for z in v if z['xt'] is not None and xts and z['xt']>2*st.median(xts)]
    for o in out: print(f"           ^ OUTLIER xt95={o[0]} crashes={o[2]} {o[1]}")
print()
for cls in sorted(set(k[0] for k in G)):
    a=G.get((cls,'0')); b=G.get((cls,'auto'))
    if not a or not b: continue
    am,asd=ms([z['amp'] for z in a]); bm,bsd=ms([z['amp'] for z in b])
    if am is None or bm is None: continue
    d=100*(bm-am)/am
    print(f"{cls:9} amp {am:.3f} -> {bm:.3f}  = {d:+.1f}%   MDE(n=3)=26%  -> {'DETECTABLE' if abs(d)>=26 else 'within noise (no claim)'}")
