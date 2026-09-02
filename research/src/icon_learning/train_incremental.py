#!/usr/bin/env python3
# warm-start: load old ckpt backbone(transfer), expand fc→new num_classes, train combined. verify no-forget.
import json,time,sys
from pathlib import Path
import torch,torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets,transforms,models
D=Path(__file__).parent
DEV="mps" if torch.backends.mps.is_available() else "cpu"
DATA=D/"icon_dataset_v2"; OLD=D/"icon_cnn_v3.pt"; NEW=D/"icon_cnn_v4.pt"; LBL=D/"icon_cnn_labels.json"
TF=transforms.Compose([transforms.Resize((224,224)),transforms.ToTensor(),transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
TTF=transforms.Compose([transforms.Resize((224,224)),transforms.RandomRotation(8),transforms.ColorJitter(0.12,0.12),transforms.ToTensor(),transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
tr=datasets.ImageFolder(DATA/"train",TTF); va=datasets.ImageFolder(DATA/"val",TF)
ncls=len(tr.classes)
m=models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
# warm-start backbone from old ckpt(skip fc dim-mismatch)
if OLD.exists():
    old=torch.load(OLD,map_location="cpu")
    m.fc=nn.Linear(m.fc.in_features,old["fc.weight"].shape[0])
    m.load_state_dict(old); print(f"warm-start: loaded old backbone({old['fc.weight'].shape[0]}-cls)")
m.fc=nn.Linear(m.fc.in_features,ncls)  # expand head→new
m=m.to(DEV)
tl=DataLoader(tr,32,shuffle=True); vl=DataLoader(va,32)
opt=torch.optim.Adam(m.parameters(),1e-3); sch=torch.optim.lr_scheduler.CosineAnnealingLR(opt,8)
cc=[0]*ncls
for _,l in tr.samples: cc[l]+=1
w=torch.tensor([sum(cc)/(ncls*c) for c in cc],dtype=torch.float32).to(DEV)
crit=nn.CrossEntropyLoss(weight=w)
LBL.write_text(json.dumps(tr.classes,indent=2))
t0=time.time()
for e in range(8):
    m.train()
    for im,l in tl:
        im,l=im.to(DEV),l.to(DEV); opt.zero_grad(); loss=crit(m(im),l); loss.backward(); opt.step()
    m.eval(); c=t=0
    with torch.no_grad():
        for im,l in vl:
            im,l=im.to(DEV),l.to(DEV); c+=(m(im).argmax(1)==l).sum().item(); t+=l.size(0)
    print(f"ep{e+1}/8 val_acc={c/t:.4f}"); sch.step()
    tp=NEW.with_suffix(".pt.tmp"); torch.save(m.state_dict(),tp); tp.replace(NEW)
print(f"done {time.time()-t0:.0f}s classes={ncls} labels={len(json.loads(LBL.read_text()))} ckpt-dim={ncls}")
