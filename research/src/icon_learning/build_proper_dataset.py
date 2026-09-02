#!/usr/bin/env python3
# PROPER: train/val = size-reps {128,256,512}, REAL-test = DISTINCT size-reps {16,32,64,1024}.
# genuinely-distinct instances(diff resolution rendering, ¬aug-of-same). tests real generalization.
import subprocess, shutil, glob, os
from pathlib import Path
from PIL import Image, ImageEnhance
OUT=Path(__file__).parent/"icon_dataset_v2"
shutil.rmtree(OUT,ignore_errors=True)
TRAIN_SIZES=["128x128","128x128@2x","256x256","256x256@2x","512x512"]  # 256@2x=512
TEST_SIZES=["16x16","16x16@2x","32x32","32x32@2x"]  # distinct small reps (@2x adds more)
def load_reps(app):
    icns=subprocess.run(["defaults","read",f"{app}/Contents/Info","CFBundleIconFile"],capture_output=True,text=True).stdout.strip()
    if not icns: return {}
    if not icns.endswith(".icns"): icns+=".icns"
    p=Path(app)/"Contents"/"Resources"/icns
    if not p.exists(): return {}
    iset=Path("/tmp/icv2")/Path(app).stem.replace(" ","_"); shutil.rmtree(iset,ignore_errors=True)
    subprocess.run(["iconutil","-c","iconset",str(p),"-o",str(iset)+".iconset"],capture_output=True)
    d=Path(str(iset)+".iconset")
    reps={}
    if d.exists():
        for f in d.glob("icon_*.png"):
            key=f.stem.replace("icon_","")
            reps[key]=f
    return reps
def norm(img,i=0):
    im=img.convert("RGB").resize((224,224))
    if i>0:  # mild aug for train-count only
        im=im.rotate((i*23%15)-7,resample=Image.BICUBIC,fillcolor=(255,255,255))
        im=ImageEnhance.Brightness(im).enhance(0.9+(i*0.05%0.2))
    return im
apps=sorted(set(glob.glob("/Applications/*.app")+glob.glob("/Applications/*/*.app")+glob.glob("/System/Applications/*.app")+glob.glob("/System/Applications/Utilities/*.app")+glob.glob(os.path.expanduser("~/Applications/*.app"))))
n_local=0; n_notest=0
for app in apps:
    name=Path(app).stem.replace(" ","_").replace("/","_")
    reps=load_reps(app)
    tr=[reps[s] for s in TRAIN_SIZES if s in reps]
    te=[reps[s] for s in TEST_SIZES if s in reps]
    if not tr or not te:  # need BOTH distinct train+test reps
        n_notest+=1; continue
    # train: real reps + aug to reach ~12
    cd=OUT/"train"/name; cd.mkdir(parents=True,exist_ok=True)
    idx=0
    for rp in tr:
        try: b=Image.open(rp)
        except: continue
        for k in range(3): norm(b,idx if k else 0).save(cd/f"t{idx}.png"); idx+=1
    # val: 1 real rep
    vd=OUT/"val"/name; vd.mkdir(parents=True,exist_ok=True)
    try: norm(Image.open(tr[0])).save(vd/"v0.png")
    except: pass
    # REAL test: distinct small reps, NO aug
    sd=OUT/"test"/name; sd.mkdir(parents=True,exist_ok=True)
    j=0
    for rp in te:
        try: norm(Image.open(rp)).save(sd/f"s{j}.png"); j+=1
        except: pass
    n_local+=1
print(f"local_classes={n_local} skipped_no-distinct-reps={n_notest}")
for sp in ("train","val","test"):
    cs=list((OUT/sp).glob("*")); print(f"{sp}: classes={len(cs)} imgs={sum(len(list(c.glob('*.png'))) for c in cs)}")
