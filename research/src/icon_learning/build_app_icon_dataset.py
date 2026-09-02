#!/usr/bin/env python3
# collect app .icns → png, build ImageFolder dataset(train/val/test) w/ augmentation.
# 1 real icon/app → aug-replicate to N per split(icons deterministic; aug=synthetic variety).
import subprocess, shutil, random
from pathlib import Path
from PIL import Image
import glob, os

random.seed(0)
OUT = Path(__file__).parent / "app_icon_dataset"
RAW = Path(__file__).parent / "app_icon_raw"
for d in (OUT, RAW): shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)

apps = sorted(set(
    glob.glob("/Applications/*.app") + glob.glob("/Applications/*/*.app") +
    glob.glob("/System/Applications/*.app") + glob.glob("/System/Applications/Utilities/*.app") +
    glob.glob(os.path.expanduser("~/Applications/*.app")) +
    glob.glob("/opt/homebrew/Caskroom/*/*/*.app")))
N_TRAIN, N_VAL, N_TEST = 12, 3, 3   # per class, via augmentation

def find_icns(app):
    icon = subprocess.run(["defaults","read",f"{app}/Contents/Info","CFBundleIconFile"],capture_output=True,text=True).stdout.strip()
    if not icon: return None
    if not icon.endswith(".icns"): icon += ".icns"
    p = Path(app)/"Contents"/"Resources"/icon
    return p if p.exists() else None

def aug(img, i):
    im = img.convert("RGB")
    # mild synthetic variety: rotation + brightness (deterministic per i)
    r = (i*37 % 21) - 10           # -10..10 deg
    im = im.rotate(r, resample=Image.BICUBIC, fillcolor=(255,255,255))
    from PIL import ImageEnhance
    b = 0.85 + (i*0.07 % 0.3)
    im = ImageEnhance.Brightness(im).enhance(b)
    return im

n_ok=0
for app in apps:
    name = Path(app).stem.replace(" ","_").replace("/","_")
    icns = find_icns(app)
    if not icns: continue
    # icns→png (largest rep)
    raw_png = RAW/f"{name}.png"
    r = subprocess.run(["sips","-s","format","png","--resampleHeightWidth","256","256",str(icns),"--out",str(raw_png)],capture_output=True)
    if not raw_png.exists(): continue
    try: base = Image.open(raw_png)
    except: continue
    idx=0
    for split,n in (("train",N_TRAIN),("val",N_VAL),("test",N_TEST)):
        cd = OUT/split/name; cd.mkdir(parents=True,exist_ok=True)
        for j in range(n):
            aug(base, idx).save(cd/f"{name}_{split}_{j}.png"); idx+=1
    n_ok+=1

print(f"apps_total={len(apps)} classes_built={n_ok}")
# count
for split in ("train","val","test"):
    cs=list((OUT/split).glob("*")); imgs=sum(len(list(c.glob('*.png'))) for c in cs)
    print(f"{split}: classes={len(cs)} imgs={imgs}")
