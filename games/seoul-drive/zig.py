"""zigzag metric on ALL driving samples (no straight gate): tel_trace2 window [t0,t1]; segments by sw + |Δlat|>0.5 jump + gap>1s; dev = lat − 2s rolling mean; reversals/min with 0.2m hysteresis; amp_p95. usage: zig.py t0 t1"""
import sys,json,numpy as np
t0,t1=float(sys.argv[1]),float(sys.argv[2]); R=[json.loads(l) for l in open('/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp/tel_trace2.jsonl')]
R=[r for r in R if t0<=r['t']<=t1 and isinstance(r.get('lat'),(int,float)) and (r.get('v') or 0)>1.5]
segs=[];cur=[]
for r in R:
    if cur and (r['sw']!=cur[-1]['sw'] or abs(r['lat']-cur[-1]['lat'])>0.5 or r['t']-cur[-1]['t']>1): segs.append(cur); cur=[]
    cur.append(r)
segs.append(cur); devs=[];sc=0;mins=0
for s in segs:
    if len(s)<20: continue
    t=np.array([q['t'] for q in s]); l=np.array([q['lat'] for q in s]); rm=np.array([l[(t>=x-1)&(t<=x+1)].mean() for x in t]); d=l-rm; devs+=list(np.abs(d)); mins+=(t[-1]-t[0])/60; sg=0
    for x in d:
        if x>0.2 and sg<=0: sc+=(sg<0); sg=1
        elif x<-0.2 and sg>=0: sc+=(sg>0); sg=-1
print(json.dumps({'min':round(mins,2),'amp_p95':round(float(np.percentile(devs,95)),3) if devs else None,'rev_min':round(sc/max(mins,1e-6),1)}))
