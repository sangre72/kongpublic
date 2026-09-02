#!/usr/bin/env python3
# LIVE icon-eval: screencapture real Dock icons(on-screen rendered), classify v3.pt, pred vs actual dock-name.
# ¬prebuilt-png — genuine live-screen capture. retina: logical→physical ×2.
import subprocess,json,re,sys
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
    with torch.no_grad(): p=torch.softmax(m(t),1); top=torch.topk(p,3)
    return [(lbl[i],float(v)) for v,i in zip(top.values[0],top.indices[0])]
# parse dock items
dp=subprocess.run(["pgrep","-x","Dock"],capture_output=True,text=True).stdout.split()[0]
out=subprocess.run([KT,"see","--pid",dp,"--a11y"],capture_output=True,text=True).stdout
items=re.findall(r'AXDockItem\s+@\((\d+),(\d+)\)\s+\[(\d+)x(\d+)\]\s+·\s+(.+)',out)
SCAP=Path("/tmp/liveicons"); SCAP.mkdir(exist_ok=True)
res=[]; hit=0; total=0
for x,y,w,h,name in items:
    x,y,w,h=int(x),int(y),int(w),int(h)
    name=name.strip()
    # actual label = dock-name→matched class(only apps we have a class for)
    actual=lblnorm.get(norm(name)) or lblnorm.get(norm(name.replace(" ","_")))
    if not actual: continue   # class-unknown, skip(can't score)
    # screencapture icon rect (logical→physical ×2, pad)
    px,py,pw,ph=x-w//2,y-h//2,w,h  # screencapture -R=logical points
    f=SCAP/f"{norm(name)}.png"
    subprocess.run(["screencapture","-x","-R",f"{px},{py},{pw},{ph}",str(f)],capture_output=True)
    if not f.exists(): continue
    preds=classify(f); top1=preds[0][0]; ok=(top1==actual)
    total+=1; hit+=ok
    res.append({"name":name,"actual":actual,"top1":top1,"conf":round(preds[0][1],3),"ok":ok})
print(f"DOCK live trials={total} hits={hit} acc={hit/total:.4f}" if total else "no scorable dock items")
for r in res: print(f"  {'✓' if r['ok'] else '✗'} {r['name']}→{r['top1']}({r['conf']}) [actual={r['actual']}]")
json.dump(res,open(SCAP/"dock_results.json","w"),ensure_ascii=False,indent=2)
