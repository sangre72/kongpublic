#!/usr/bin/env python3
# v4 live-eval: capture-timing GATE(poll til 2x identical hash=anim-settled) + v4.pt. auto+curated.
import subprocess,json,re,time,glob,hashlib,sys
from pathlib import Path
import torch,torch.nn as nn
from torchvision import transforms,models
from PIL import Image
D=Path(__file__).parent; DEV="mps" if torch.backends.mps.is_available() else "cpu"
KT="/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol"
CKPT=sys.argv[1] if len(sys.argv)>1 else str(D/"icon_cnn_v4.pt")
TF=transforms.Compose([transforms.Resize((224,224)),transforms.ToTensor(),transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
lbl=json.loads((D/"icon_cnn_labels.json").read_text())
m=models.resnet18(); m.fc=nn.Linear(m.fc.in_features,len(lbl)); m.load_state_dict(torch.load(CKPT,map_location=DEV)); m.to(DEV); m.eval()
def norm(s): return re.sub(r'[^a-z0-9]','',s.lower())
lblnorm={norm(l):l for l in lbl}
def classify(png):
    im=Image.open(png).convert("RGB"); t=TF(im).unsqueeze(0).to(DEV)
    with torch.no_grad(): p=torch.softmax(m(t),1); i=int(p.argmax(1)); return lbl[i],float(p[0,i])
def dock_items():
    dp=subprocess.run(["pgrep","-x","Dock"],capture_output=True,text=True).stdout.split()[0]
    out=subprocess.run([KT,"see","--pid",dp,"--a11y"],capture_output=True,text=True).stdout
    return re.findall(r'AXDockItem\s+@\((\d+),(\d+)\)\s+\[(\d+)x(\d+)\]\s+·\s+(.+)',out)
def cap_stable(x,y,w,h,f,tries=6):
    # GATE: capture until 2 consecutive identical(anim settled), skip bounce/magnify frames
    prev=None
    for _ in range(tries):
        subprocess.run(["screencapture","-x","-R",f"{x-w//2},{y-h//2},{w},{h}",str(f)],capture_output=True)
        if not f.exists(): time.sleep(0.25); continue
        hh=hashlib.md5(f.read_bytes()).hexdigest()
        if hh==prev: return True   # settled
        prev=hh; time.sleep(0.3)
    return f.exists()
SC=Path("/tmp/liveicons_v4"); SC.mkdir(exist_ok=True)
apps={}
for a in glob.glob("/Applications/*.app")+glob.glob("/System/Applications/*.app")+glob.glob("/System/Applications/Utilities/*.app")+glob.glob("/Applications/*/*.app"):
    apps[norm(Path(a).stem)]=a
local=[l for l in lbl if not l.startswith("web_")]
res=[]; hit=tot=0
for cls in local:
    ap=apps.get(norm(cls))
    if not ap: continue
    subprocess.run(["open","-a",ap],capture_output=True); time.sleep(0.9)
    found=None
    for x,y,w,h,name in dock_items():
        if lblnorm.get(norm(name))==cls: found=(int(x),int(y),int(w),int(h)); break
    if not found: continue
    x,y,w,h=found; f=SC/f"{norm(cls)}.png"
    if not cap_stable(x,y,w,h,f): continue
    top1,conf=classify(f); ok=(top1==cls); tot+=1; hit+=ok
    res.append((cls,top1,round(conf,2),ok))
print(f"V4-LIVE-auto trials={tot} hits={hit} acc={hit/tot:.4f}" if tot else "0")
json.dump(res,open(SC/"v4_results.json","w"),ensure_ascii=False)
