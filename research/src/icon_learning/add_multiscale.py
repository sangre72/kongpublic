#!/usr/bin/env python3
# augment EXISTING v2 train set: each source icon → degraded @multi-res(16..512 downscale then upscale-224).
# teaches small-icon degradation. test set UNCHANGED(distinct-source real held-out).
import glob
from pathlib import Path
from PIL import Image
D=Path(__file__).parent; OUT=D/"icon_dataset_v2"
SCALES=[16,24,32,48,64,128,256,512]
def degrade(img,s):
    im=img.convert("RGB")
    small=im.resize((s,s),Image.BILINEAR)      # downscale(lose detail)
    return small.resize((224,224),Image.BILINEAR)  # upscale to model-input(blur artifacts)
n=0
for cd in (OUT/"train").glob("*"):
    srcs=list(cd.glob("t*.png"))
    if not srcs: continue
    base=Image.open(srcs[0])
    for s in SCALES:
        degrade(base,s).save(cd/f"ms_{s}.png")
    n+=1
print(f"multiscale-augmented classes={n} scales={SCALES}")
imgs=sum(len(list(c.glob('*.png'))) for c in (OUT/'train').glob('*'))
print(f"train imgs now={imgs}")
