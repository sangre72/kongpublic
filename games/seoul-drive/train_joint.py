#!/usr/bin/env python3
"""u_5801 (2): ey + epsi jointly weighted, sweep the weighting, report BOTH held-out MAEs.
loss = (1-w)*|ey_err| + w*|epsi_err|  (both in normalised units, as the net emits them)."""
import os, sys, json, glob, math, argparse
import numpy as np, torch, gpu_guard
from net import DriveNet
import train_geo as TG
DEV = gpu_guard.require_gpu(); BS = TG.BS
def mae(net, dirs, bs=64):
    te=ty=0.0; c=0
    for d in dirs:
        pl=TG.load([d])
        if not pl: continue
        X,Y,V,W=pl
        for i in range(0,len(Y),bs):
            ids=np.arange(i,min(i+bs,len(Y)))
            xb,yb,vb,_=TG.batch(X,Y,V,W,ids)
            with torch.no_grad(): o=net(xb,vb,raw=True)
            te+=float(torch.abs(o[:,1]-yb[:,1]).sum())*float(TG.SCALE[1])
            ty+=float(torch.abs(o[:,0]-yb[:,0]).sum())*float(TG.SCALE[0]); c+=len(ids)
    return (math.degrees(te/c), ty/c, c)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('train_glob'); ap.add_argument('--holdout',required=True)
    ap.add_argument('--init',default='models/ode_geo_wide.pt'); ap.add_argument('--k',type=int,default=5)
    ap.add_argument('--epochs',type=int,default=8); ap.add_argument('--w',type=float,required=True)
    ap.add_argument('--out',required=True); ap.add_argument('--seed',type=int,default=0)
    a=ap.parse_args(); TG.KSTACK=a.k
    rng=np.random.default_rng(a.seed); torch.manual_seed(a.seed)
    ho=[l.strip() for l in open(a.holdout) if l.strip()]
    tr=[d for d in sorted(glob.glob(a.train_glob)) if d not in set(ho)]
    got=TG.load(tr); X,Y,V,W=got; n=len(X)
    net=DriveNet(out=12,vin=True,vdim=1,in_ch=3*a.k).to(DEV)
    sd=torch.load(a.init,map_location=DEV); own=net.state_dict()
    ok={k:v for k,v in sd.items() if k in own and own[k].shape==v.shape}
    if len(ok)!=len(own): raise SystemExit(json.dumps({'FATAL':'ckpt mismatch','loaded':len(ok),'expected':len(own)}))
    net.load_state_dict(ok,strict=False)
    b=mae(net,ho); print(json.dumps({'w':a.w,'baseline':{'epsi_deg':round(b[0],3),'ey_m':round(b[1],4)}}),flush=True)
    opt=torch.optim.Adam(net.parameters(),5e-4,weight_decay=1e-4)
    best=(1e9,None)
    for ep in range(a.epochs):
        net.train(); perm=rng.permutation(n)
        for i in range(0,len(perm),BS):
            ids=np.sort(perm[i:i+BS]); xb,yb,vb,wb=TG.batch(X,Y,V,W,ids,train=True)
            opt.zero_grad(); o=net(xb,vb,raw=True)
            l=(((1-a.w)*torch.abs(o[:,0]-yb[:,0]) + a.w*torch.abs(o[:,1]-yb[:,1]))*wb).mean()
            l.backward(); opt.step()
        net.eval(); e,y,c=mae(net,ho)
        sc=(1-a.w)*(y/0.3516)+a.w*(e/2.749)
        if sc<best[0]: best=(sc,(e,y)); torch.save(net.state_dict(),a.out)
        print(json.dumps({'w':a.w,'ep':ep+1,'epsi_deg':round(e,3),'ey_m':round(y,4)}),flush=True)
    print(json.dumps({'w':a.w,'done':a.out,'best_epsi_deg':round(best[1][0],3),'best_ey_m':round(best[1][1],4)}),flush=True)
if __name__=='__main__': main()
