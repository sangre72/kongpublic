#!/usr/bin/env python3
"""Axle-anchored silhouette overlay: ref photo vs model ortho render.
Scales model by wheelbase ratio, aligns on front-axle + axle-height (NOT naive stretch-to-box).
Usage: python3 scripts/overlay_ref.py <ref.jpg> <model_ortho.png> <out.png>"""
import sys
from PIL import Image, ImageDraw
import numpy as np
def analyze(path,thr,wthr):
    a=np.array(Image.open(path).convert('L')); mask=a<thr
    cols=np.where(mask.any(axis=0))[0]; x0,x1=cols.min(),cols.max()
    rows=np.where(mask.any(axis=1))[0]; y0,y1=rows.min(),rows.max(); L=x1-x0;Ht=y1-y0
    band=(a[int(y1-0.42*Ht):y1,:]<wthr); cs=band.sum(axis=0)
    fwc=x0+int(np.argmax(cs[x0:x0+L//2])); rwc=x0+L//2+int(np.argmax(cs[x0+L//2:x1]))
    bodymask=(a<thr)&(a>60); top=[]
    for xc in range(x0,x1+1):
        ys=np.where(bodymask[:,xc])[0]; top.append(ys.min() if len(ys) else None)
    return dict(a=a,x0=x0,x1=x1,y1=y1,Ht=Ht,fwc=fwc,rwc=rwc,axle_y=y1-int(0.20*Ht),top=top)
def main(refp,modp,outp):
    ref=analyze(refp,180,70); mod=analyze(modp,195,90)
    scale=(ref['rwc']-ref['fwc'])/(mod['rwc']-mod['fwc'])
    W,H=ref['a'].shape[1],ref['a'].shape[0]
    cv=Image.new('RGB',(W,H),(255,255,255)); dr=ImageDraw.Draw(cv)
    rp=[(ref['x0']+i,ref['top'][i]) for i in range(len(ref['top'])) if ref['top'][i] is not None]
    dr.line(rp,fill=(30,80,220),width=3); dr.line([(ref['x0'],ref['y1']),(ref['x1'],ref['y1'])],fill=(30,80,220),width=2)
    def tf(x,y): return (ref['fwc']+(x-mod['fwc'])*scale, ref['axle_y']+(y-mod['axle_y'])*scale)
    mp=[tf(mod['x0']+i,mod['top'][i]) for i in range(len(mod['top'])) if mod['top'][i] is not None]
    dr.line(mp,fill=(220,40,40),width=3)
    for ax in (ref['fwc'],ref['rwc']): dr.ellipse([ax-6,ref['axle_y']-6,ax+6,ref['axle_y']+6],outline=(30,80,220),width=3)
    dr.text((20,20),"BLUE=ref RED=model (axle-anchored, wheelbase-scaled x%.3f)"%scale,fill=(0,0,0))
    cv.save(outp); print("saved",outp,"scale",round(scale,3))
if __name__=='__main__': main(*sys.argv[1:4])
