#!/usr/bin/env python3
# web classes: train=SimpleIcons svg, REAL-test=SuperTinyIcons SAME-brand DISTINCT svg(diff artwork/style).
import subprocess,glob,os
from pathlib import Path
from PIL import Image,ImageEnhance
OUT=Path(__file__).parent/"icon_dataset_v2"
DL=Path("/Users/bumsuklee/.claude/jobs/c58bf0a2/tmp/webicons")
def svg2png(svg,out):
    qd=Path("/tmp/qlw2"); qd.mkdir(exist_ok=True)
    subprocess.run(["qlmanage","-t","-s","256","-o",str(qd),svg],capture_output=True)
    p=qd/(Path(svg).name+".png")
    return p if p.exists() else None
def norm(img,i=0):
    im=img.convert("RGB").resize((224,224))
    if i>0: im=im.rotate((i*23%15)-7,resample=Image.BICUBIC,fillcolor=(255,255,255)); im=ImageEnhance.Brightness(im).enhance(0.9+(i*0.05%0.2))
    return im
def norml(s): return s.lower().replace(" ","").replace("-","").replace("_","").replace(".","")
si={norml(Path(f).stem):f for f in glob.glob(str(DL/"si/icons/*.svg"))}
sti={norml(Path(f).stem):f for f in glob.glob(str(DL/"sti/images/svg/*.svg"))}
common=sorted(set(si)&set(sti))  # brands in BOTH → train=SI, real-test=STI(distinct)
n=0
for b in common:
    tr=svg2png(si[b],None); te=svg2png(sti[b],None)
    if not tr or not te: continue
    name=f"web_{b}"
    try: bt=Image.open(tr); be=Image.open(te)
    except: continue
    cd=OUT/"train"/name; cd.mkdir(parents=True,exist_ok=True)
    for k in range(6): norm(bt,k).save(cd/f"t{k}.png")
    vd=OUT/"val"/name; vd.mkdir(parents=True,exist_ok=True); norm(bt).save(vd/"v0.png")
    sd=OUT/"test"/name; sd.mkdir(parents=True,exist_ok=True); norm(be).save(sd/"s0.png")  # DISTINCT source
    n+=1
print(f"web_classes(SI∩STI distinct-test)={n}")
for sp in ("train","val","test"):
    cs=list((OUT/sp).glob("*")); print(f"{sp}: classes={len(cs)}")
