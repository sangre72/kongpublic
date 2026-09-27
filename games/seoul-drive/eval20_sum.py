"""eval20 pass check: avoidable 0 ∧ offroad(차로이탈) 0 ∧ weave sc ≤6/min ∧ amp_p95 ≤0.35 ∧ tp ≤1/route ∧ handover ≤2/min. usage: eval20_sum.py <tag>"""
import sys,json,numpy as np
T='/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp'; tag=sys.argv[1]; R=[json.loads(l) for l in open(f'{T}/eval20_{tag}.jsonl')]; R=[r for r in R if r.get('res')]
av=off=tp=0; amps=[]; scs=[]; hand=[]; prog=[]
for r in R:
    d=r['res']; ct=d.get('crash_types') or {}; av+=d['crashes']-sum(v for k,v in ct.items() if '불가항력' in k); off+=sum(v for k,v in ct.items() if '이탈' in k); tp+=d['tpN']; hand.append(60*d['handovers']/max(d['secs'],1)); prog.append(100*(d['prog'] or 0))
    w=d.get('weave')
    if w and w.get('min',0)>=0.2: amps.append(w['amp_p95']); scs.append(w['sc_min'])
res={'routes':len(R),'avoidable':av,'offroad':off,'tp_per_route':round(tp/max(len(R),1),2),'weave_amp_p95_med':round(float(np.median(amps)),3) if amps else None,'weave_sc_med':round(float(np.median(scs)),1) if scs else None,'handover_per_min_med':round(float(np.median(hand)),2),'prog_mean':round(float(np.mean(prog)),1)}
lawv=sum(1 for r in R if any(int(((r.get('res') or {}).get('law') or {}).get(k) or 0)>0 for k in ('turnLane','straddle','center','signal','solid'))); res['law_fail_routes']=lawv; res['law_sum']={k:sum(int(((r.get('res') or {}).get('law') or {}).get(k) or 0) for r in R) for k in ('turnLane','straddle','center','signal','solid')}
res['PASS']=bool(lawv==0 and av==0 and off==0 and tp/max(len(R),1)<=1 and (res['weave_sc_med'] is not None and res['weave_sc_med']<=6) and (res['weave_amp_p95_med'] is not None and res['weave_amp_p95_med']<=0.35) and res['handover_per_min_med']<=2)
print(json.dumps(res,ensure_ascii=False))
