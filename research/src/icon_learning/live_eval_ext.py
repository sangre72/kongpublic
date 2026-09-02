#!/usr/bin/env python3
# EXTENDED live-eval: launch each local-class app→dock→screencapture live icon→classify. 100+ trials.
import subprocess,json,re,time,glob,os
from pathlib import Path
import torch,torch.nn as nn
from torchvision import transforms,models
from PIL import Image
D=Path(__file__).parent; DEV="mps" if torch.backends.mps.is_available() else "cpu"
KT="/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol"
TF=transforms.Compose([transforms.Resize((224,224)),transforms.ToTensor(),transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
lbl=json.loads((D/"icon_cnn_labels.json").read_text())
m=models.resnet18(); m.fc=nn.Linear(m.fc.in_features,len(lbl)); m.load_state_dict(torch.load(D/"icon_cnn_v3.pt",map_location=DEV)); m.to(DEV); m.eval()
def norm(s): return re.sub(r'[^a-z0-9]','',s.lower())
lblnorm={norm(l):l for l in lbl}
def classify(png):
    im=Image.open(png).convert("RGB"); t=TF(im).unsqueeze(0).to(DEV)
    with torch.no_grad(): p=torch.softmax(m(t),1); i=int(p.argmax(1)); return lbl[i],float(p[0,i])
def dock_items():
    dp=subprocess.run(["pgrep","-x","Dock"],capture_output=True,text=True).stdout.split()[0]
    out=subprocess.run([KT,"see","--pid",dp,"--a11y"],capture_output=True,text=True).stdout
    return re.findall(r'AXDockItem\s+@\((\d+),(\d+)\)\s+\[(\d+)x(\d+)\]\s+·\s+(.+)',out)
SC=Path("/tmp/liveicons2"); SC.mkdir(exist_ok=True)
# map local-class → .app path
apps={}
for a in glob.glob("/Applications/*.app")+glob.glob("/System/Applications/*.app")+glob.glob("/System/Applications/Utilities/*.app")+glob.glob("/Applications/*/*.app"):
    apps[norm(Path(a).stem)]=a
local=[l for l in lbl if not l.startswith("web_")]
res=[]; hit=0; tot=0
for cls in local:
    ap=apps.get(norm(cls))
    if not ap: continue
    subprocess.run(["open","-a",ap],capture_output=True); time.sleep(0.8)
    # find in dock by name-match to cls
    found=None
    for x,y,w,h,name in dock_items():
        if norm(name)==norm(cls) or lblnorm.get(norm(name))==cls:
            found=(int(x),int(y),int(w),int(h)); break
    if not found: continue
    x,y,w,h=found
    f=SC/f"{norm(cls)}.png"
    subprocess.run(["screencapture","-x","-R",f"{x-w//2},{y-h//2},{w},{h}",str(f)],capture_output=True)
    if not f.exists(): continue
    top1,conf=classify(f); ok=(top1==cls); tot+=1; hit+=ok
    res.append((cls,top1,round(conf,2),ok))
print(f"EXT-LIVE trials={tot} hits={hit} acc={hit/tot:.4f}" if tot else "0 trials")
json.dump(res,open(SC/"ext_results.json","w"),ensure_ascii=False)
fails=[r for r in res if not r[3]]
print(f"fails={len(fails)}:", [(r[0],r[1]) for r in fails][:15])
