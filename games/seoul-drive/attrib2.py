"""attribution v2 on ALL-sample car lateral reversals (zig events from tel_trace2, seg by sw/jump/gap, 2s rolling mean, 0.2m hyst).
cause per reversal: (a) <1.5s after handover(npz hand) (b) commanded lp20 change >0.5m within ±0.3s(npz raw col2) (c) lane-target(laneF/off) flip <1.5s before (d) other.
usage: attrib2.py <run_log> <tag>"""
import sys,json,glob,datetime,numpy as np
T='/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp'; log,tag=sys.argv[1],sys.argv[2]; td=datetime.date.today()
R=[json.loads(l) for l in open(f'{T}/tel_trace2.jsonl')]; npz=sorted(glob.glob(f'{T}/tr/{tag}_*.npz'))
tot={'a':0,'b':0,'c':0,'d':0}; H=0; runs=0
starts=[l for l in open(log) if l.startswith('===')]
for i,line in enumerate(starts):
    hms=line.split('(')[1].split(')')[0]; h,m,s=map(int,hms.split(':')); t0=datetime.datetime(td.year,td.month,td.day,h,m,s).timestamp()+5
    W=[r for r in R if t0<=r['t']<=t0+92 and isinstance(r.get('lat'),(int,float)) and (r.get('v') or 0)>1.5]
    if i>=len(npz) or len(W)<50: continue
    z=np.load(npz[i]); hand=z['hand']; raw=z['raw']; ht=hand[:,0] if len(hand) else np.array([]); rt=raw[1:,0] if len(raw)>1 else np.array([]); rj=np.abs(np.diff(raw[:,2])) if len(raw)>1 else np.array([])
    lf=[(r['t'],r.get('off')) for r in W]; flips=[lf[k][0] for k in range(1,len(lf)) if lf[k][1] is not None and lf[k-1][1] is not None and abs(lf[k][1]-lf[k-1][1])>1.0]
    segs=[];cur=[]
    for r in W:
        if cur and (r['sw']!=cur[-1]['sw'] or abs(r['lat']-cur[-1]['lat'])>0.5 or r['t']-cur[-1]['t']>1): segs.append(cur); cur=[]
        cur.append(r)
    segs.append(cur); ev=[]
    for sg_ in segs:
        if len(sg_)<20: continue
        t=np.array([q['t'] for q in sg_]); l=np.array([q['lat'] for q in sg_]); rm=np.array([l[(t>=x-1)&(t<=x+1)].mean() for x in t]); d=l-rm; sg=0
        for k,x in enumerate(d):
            if x>0.2 and sg<=0: (sg<0) and ev.append(t[k]); sg=1
            elif x<-0.2 and sg>=0: (sg>0) and ev.append(t[k]); sg=-1
    c={'a':0,'b':0,'c':0,'d':0}
    for e in ev:
        if len(ht) and np.any((e-ht>=0)&(e-ht<1.5)): c['a']+=1
        elif len(rt) and np.any((np.abs(rt-e)<=0.3)&(rj>0.5)): c['b']+=1
        elif any(0<=e-f<1.5 for f in flips): c['c']+=1
        else: c['d']+=1
    n=max(1,sum(c.values())); runs+=1; H+=len(hand)
    for k in c: tot[k]+=c[k]
    print(tag,'run%d'%(i+1),'reversals',sum(c.values()),' '.join('%s%.0f%%'%(k,100*v/n) for k,v in c.items()),'handovers',len(hand),'laneflips',len(flips))
n=max(1,sum(tot.values())); print(json.dumps({'tag':tag,'runs':runs,'reversals':sum(tot.values()),'pct':{k:round(100*v/n,1) for k,v in tot.items()},'handovers':H}))
