#!/usr/bin/env python3
"""u_5775 BASELINE FIRST: per-channel perception error on MODEL-DRIVEN states vs RULE-DRIVEN states.
Reuses train_geo's load()/SCALE/filter verbatim so the numbers are comparable to the u_5762 2.69x.
Input stays pixels (X.npy); truth is the /tel geometry recorded in L.npy. Offline, deterministic."""
import sys, os, json, glob
import numpy as np, torch
import gpu_guard
from net import DriveNet
import train_geo as TG

DEV = gpu_guard.require_gpu()
TG.KSTACK = int(os.environ.get('KSTACK','1'))   # must match the checkpoint's in_ch/3
CH = ['ey','epsi','k0','lc10','lc20','lc40','li','nl','lw','dl','dr']

def episodes_of(dirs):
    n = 0
    for d in dirs:
        p = os.path.join(d, 'episodes.json')
        if os.path.exists(p):
            try:
                e = json.load(open(p)); n += len(e) if isinstance(e, list) else 1
            except Exception: n += 1
    return n

def err_of(dirs, net, tag, bs=64):
    plan = TG.load(dirs)
    if not plan: return None
    # Reuse train_geo.batch verbatim: it applies zoom() and indexes Y/V/W by the SAME ids as X.
    # Reimplementing the decode risks a silent mismatch that would corrupt the comparison.
    X, Y, V, W = plan                            # load() -> (LazyX, Y, V, W), global ids
    tot = np.zeros(11); cnt = 0
    for i in range(0, len(Y), bs):
        ids = np.arange(i, min(i + bs, len(Y)))
        xb, yb, vb, _ = TG.batch(X, Y, V, W, ids)
        with torch.no_grad(): o = net(xb, vb)
        e = (torch.abs(o[:, :11] - yb[:, :11]).cpu().numpy() * TG.SCALE[:11])
        tot += e.sum(0); cnt += len(ids)
    if not cnt: return None
    return dict(tag=tag, frames=cnt, episodes=episodes_of(dirs),
                mae={c: round(float(v), 4) for c, v in zip(CH, tot / cnt)})

def main():
    w = sys.argv[1]
    onpol = sorted(glob.glob(sys.argv[2])); rule = sorted(glob.glob(sys.argv[3]))
    net = DriveNet(out=12, vin=True, vdim=1, in_ch=3 * TG.KSTACK).to(DEV)
    sd = torch.load(w, map_location=DEV); own = net.state_dict()
    ok = {k: v for k, v in sd.items() if k in own and own[k].shape == v.shape}
    # u_5776 STANDING CHECK: a PARTIAL load is silent and produces plausible-looking but bogus
    #   numbers. ode_lp30cn.pt is an 11-output train_lp model: it loaded 15 of 20 tensors and gave
    #   an entirely fictitious ey ratio before this assert existed. Never trust a checkpoint whose
    #   tensor count does not match the architecture.
    if len(ok) != len(own):
        miss = sorted(set(own) - set(ok))
        raise SystemExit(json.dumps({'FATAL': 'checkpoint/arch mismatch', 'weights': w,
                                     'loaded': len(ok), 'expected': len(own),
                                     'missing': miss[:8],
                                     'hint': 'wrong model family or wrong KSTACK (in_ch/3)'}))
    net.load_state_dict(ok, strict=False); net.eval()
    gpu_guard.assert_on_gpu(net)
    print(json.dumps({'weights': w, 'loaded': len(ok), 'of': len(own)}), flush=True)
    a = err_of(onpol, net, 'model_driven'); b = err_of(rule, net, 'rule_driven')
    for r in (a, b):
        if r: print(json.dumps(r, ensure_ascii=False), flush=True)
    if a and b:
        ratio = {c: round(a['mae'][c] / b['mae'][c], 3) if b['mae'][c] else None for c in CH}
        print(json.dumps({'ratio_model_over_rule': ratio}, ensure_ascii=False), flush=True)

if __name__ == '__main__': main()
