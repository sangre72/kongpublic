#!/usr/bin/env python3
# add web-icons(Simple Icons sample) as classes into existing app_icon_dataset. svg→png(cairosvg)→aug.
import subprocess, random, glob, os
from pathlib import Path
from PIL import Image, ImageEnhance
random.seed(1)
OUT = Path(__file__).parent / "app_icon_dataset"
DL = Path("/Users/bumsuklee/.claude/jobs/c58bf0a2/tmp/webicons")
N_TRAIN,N_VAL,N_TEST = 12,3,3
SAMPLE = 200
def aug(img,i):
    im=img.convert("RGB"); r=(i*37%21)-10
    im=im.rotate(r,resample=Image.BICUBIC,fillcolor=(255,255,255))
    im=ImageEnhance.Brightness(im).enhance(0.85+(i*0.07%0.3)); return im
svgs = sorted(glob.glob(str(DL/"si/icons/*.svg")))
random.shuffle(svgs); svgs=svgs[:SAMPLE]
n=0
for svg in svgs:
    name="web_"+Path(svg).stem.replace(" ","_").replace("/","_").replace(".","_")
    qd=Path("/tmp/qlwic"); qd.mkdir(exist_ok=True)
    subprocess.run(["qlmanage","-t","-s","256","-o",str(qd),svg],capture_output=True)
    tmp=qd/(Path(svg).name+".png")
    if not tmp.exists(): continue
    try: base=Image.open(tmp)
    except: continue
    idx=0
    for split,k in (("train",N_TRAIN),("val",N_VAL),("test",N_TEST)):
        cd=OUT/split/name; cd.mkdir(parents=True,exist_ok=True)
        for j in range(k): aug(base,idx).save(cd/f"{name}_{split}_{j}.png"); idx+=1
    n+=1
print(f"web_classes_added={n}")
for split in ("train","val","test"):
    cs=list((OUT/split).glob("*")); print(f"{split}: classes={len(cs)}")
