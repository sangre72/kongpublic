"""a_5588 addendum2/3: weave sign-change attribution. usage: attrib.py <npz glob>
sign-change = dev(lat − 2s rolling mean, within 1s-gap segments) crossing ±0.1m hysteresis.
cause: (a) within 1.5s after a handover event  (b) raw lp20 frame-to-frame jump >0.5m within ±0.3s  (c) other."""
import sys,glob,json,numpy as np
tot={'a':0,'b':0,'c':0}; runs=0; hand_tot=0; sc_tot=0; secs=0
for f in sorted(glob.glob(sys.argv[1])):
    z=np.load(f); wv=z['wv']; hand=z['hand']; raw=z['raw']; runs+=1
    if len(wv)<40: print(f.split('/')[-1],'wv',len(wv),'hand',len(hand),'raw',len(raw),'(too few wv)'); continue
    tw=wv[:,0]; lw=wv[:,1]; secs+=tw[-1]-tw[0]
    # segments by gap>1s
    br=np.where(np.diff(tw)>1.0)[0]+1; segs=np.split(np.arange(len(tw)),br)
    ev=[]
    for idx in segs:
        if len(idx)<20: continue
        t=tw[idx]; l=lw[idx]; rm=np.array([l[(t>=x-1)&(t<=x+1)].mean() for x in t]); dev=l-rm; sg=0
        for i,x in enumerate(dev):
            if x>0.1 and sg<=0: (sg<0) and ev.append(t[i]); sg=1
            elif x<-0.1 and sg>=0: (sg>0) and ev.append(t[i]); sg=-1
    ht=hand[:,0] if len(hand) else np.array([]); rt=raw[:,0] if len(raw) else np.array([]); rj=np.abs(np.diff(raw[:,1])) if len(raw)>1 else np.array([]); rjt=rt[1:] if len(raw)>1 else np.array([])
    c={'a':0,'b':0,'c':0}
    for e in ev:
        if len(ht) and np.any((e-ht>=0)&(e-ht<1.5)): c['a']+=1
        elif len(rjt) and np.any((np.abs(rjt-e)<=0.3)&(rj>0.5)): c['b']+=1
        else: c['c']+=1
    n=max(1,sum(c.values())); sc_tot+=sum(c.values()); hand_tot+=len(hand)
    for k in c: tot[k]+=c[k]
    print(f.split('/')[-1],'sc',sum(c.values()),'a%.0f%% b%.0f%% c%.0f%%'%(100*c['a']/n,100*c['b']/n,100*c['c']/n),'handovers',len(hand),'raw_jump>0.5 frac %.3f'%(float((rj>0.5).mean()) if len(rj) else 0),'wv_s %.0f'%(tw[-1]-tw[0]))
n=max(1,sum(tot.values())); print(json.dumps({'runs':runs,'sign_changes':sum(tot.values()),'pct':{k:round(100*v/n,1) for k,v in tot.items()},'handovers':hand_tot,'wv_secs':round(secs)}))
