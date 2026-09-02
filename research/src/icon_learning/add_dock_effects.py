#!/usr/bin/env python3
# dock-effect aug: simulate live-dock rendering(magnify-scale-jitter, running-dot overlay, motion-blur, crop-offset).
# applied to train icons → model robust to live-screen dock artifacts.
import glob,random
from pathlib import Path
from PIL import Image,ImageFilter,ImageDraw
random.seed(3)
D=Path(__file__).parent; OUT=D/"icon_dataset_v2"
def dockify(img,i):
    im=img.convert("RGB").resize((224,224))
    r=random.Random(i)
    # 1. magnify-scale jitter(dock hover zoom 0.85-1.3) then re-fit
    sc=r.uniform(0.82,1.28); s=int(224*sc)
    im2=im.resize((s,s),Image.BILINEAR)
    if s>=224:
        off=(s-224)//2; ox=off+r.randint(-off,off) if off else 0; oy=off+r.randint(-off,off) if off else 0
        im=im2.crop((ox,oy,ox+224,oy+224))
    else:
        bg=Image.new("RGB",(224,224),(245,245,245)); bg.paste(im2,((224-s)//2,(224-s)//2)); im=bg
    # 2. motion-blur(launch bounce)
    if r.random()<0.5: im=im.filter(ImageFilter.GaussianBlur(r.uniform(0.5,2.2)))
    # 3. crop-offset(imperfect icon-rect capture)
    dx,dy=r.randint(-14,14),r.randint(-14,14)
    im=im.transform((224,224),Image.AFFINE,(1,0,dx,0,1,dy),fillcolor=(245,245,245))
    # 4. running-dot overlay(bottom-center indicator)
    if r.random()<0.5:
        d=ImageDraw.Draw(im); cx=112+r.randint(-6,6)
        d.ellipse([cx-5,210,cx+5,220],fill=(90,90,90))
    return im
n=0
for cd in (OUT/"train").glob("*"):
    srcs=[p for p in cd.glob("*.png") if not p.name.startswith("de_")]
    if not srcs: continue
    base=Image.open(srcs[0])
    for k in range(6): dockify(base,n*10+k).save(cd/f"de_{k}.png")
    n+=1
print(f"dock-effect-aug classes={n}")
print(f"train imgs={sum(len(list(c.glob('*.png'))) for c in (OUT/'train').glob('*'))}")
