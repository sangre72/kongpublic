#!/usr/bin/env python3
"""a_5612 D2 학습기(2026-09-24): X.npy(256) + S.npy(픽셀 클래스, 255=무시) → SegNet. CE(ignore 255, 클래스 가중 = 1/√빈도 정규화) + soft dice(클래스 1..11), 광도 증강만.
사용: python3 train_seg.py 'data/dagger_r27*' ode_seg1.pt [--epochs 10] [--init prev.pt] [--seed 0]
필터: v>1m/s, 이벤트 ±3s 제외, 홀드아웃 청크+이웃 제외. 검증 = 10% 분할 mIoU(클래스별). 저장 = SegNet state_dict."""
import sys, os, glob, json, numpy as np, torch, torch.nn.functional as F
from seg_net import SegNet, NCLS
from train_geo import holdout_mask
from train_stage import augment, AUG
import gpu_guard
DEV = gpu_guard.require_gpu(); BS = int(os.environ.get('BS', '16'))
def load(dirs):
    parts = []
    for d in dirs:
        try: X = np.load(f'{d}/X.npy', mmap_mode='r'); S = np.load(f'{d}/S.npy', mmap_mode='r'); Yf = np.load(f'{d}/Y.npy'); Q = np.load(f'{d}/Q.npy')
        except Exception as e: print(json.dumps({'skip': d, 'why': str(e)[:60]}), flush=True); continue
        if not (len(X) == len(S) == len(Yf) == len(Q)): print(json.dumps({'skip': d, 'why': 'shape'}), flush=True); continue
        ok = (Yf[:, 3] > 1.0) & holdout_mask(Q)
        ev = np.where((np.diff(Q[:, 1]) > 0) | (np.diff(Q[:, 2]) > 0))[0] + 1
        for e in ev: ok &= ~(np.abs(Q[:, 3] - Q[e, 3]) <= 3.0)
        idx = np.where(ok)[0]
        if len(idx): parts.append((X, S, idx)); print(json.dumps({'dir': d.split('/')[-1], 'total': len(X), 'kept': int(len(idx))}), flush=True)
    return parts
def take(parts, gids, off):
    xs, ss = [], []
    for g in gids:
        p = int(np.searchsorted(off, g, side='right') - 1); loc = parts[p][2][g - off[p]]; xs.append(parts[p][0][loc]); ss.append(parts[p][1][loc])
    return torch.from_numpy(np.stack(xs)).float().div_(255.).to(DEV), torch.from_numpy(np.stack(ss).astype(np.int64)).to(DEV)
def iou(conf):   # conf[ncls,ncls] 행=정답 열=예측
    tp = np.diag(conf); return tp / np.maximum(1, conf.sum(0) + conf.sum(1) - tp)
def evaluate(net, parts, off, ids):
    net.eval(); conf = np.zeros((NCLS, NCLS), np.int64)
    with torch.no_grad():
        for s in range(0, len(ids), BS):
            xb, sb = take(parts, ids[s:s + BS], off); p = net(xb).argmax(1); m = sb != 255
            conf += np.bincount((sb[m] * NCLS + p[m]).cpu().numpy(), minlength=NCLS * NCLS).reshape(NCLS, NCLS)
    net.train(); return iou(conf), conf
def main():
    import argparse; ap = argparse.ArgumentParser(); ap.add_argument('dirs'); ap.add_argument('out'); ap.add_argument('--epochs', type=int, default=10); ap.add_argument('--init', default=None); ap.add_argument('--seed', type=int, default=0); a = ap.parse_args()
    rng = np.random.default_rng(a.seed); torch.manual_seed(a.seed)
    parts = load([d for p in a.dirs.split(',') for d in sorted(glob.glob(p))])
    if not parts: print(json.dumps({'error': 'no frames'})); return
    off = np.cumsum([0] + [len(i) for _, _, i in parts]); n = int(off[-1]); print(json.dumps({'frames': n}), flush=True)
    idx = rng.permutation(n); cut = int(n * 0.9); tr, va = idx[:cut], idx[cut:]
    hist = np.zeros(NCLS, np.int64)
    for g in tr[:2000]: p = int(np.searchsorted(off, g, side='right') - 1); s = parts[p][1][parts[p][2][g - off[p]]]; hist += np.bincount(s[s != 255].ravel(), minlength=NCLS)
    freq = hist / max(1, hist.sum()); cw = 1.0 / np.sqrt(np.maximum(freq, 1e-4)); cw = cw / cw.mean(); cw_t = torch.tensor(cw, dtype=torch.float32, device=DEV)
    print(json.dumps({'class_pct': [round(100 * f, 2) for f in freq], 'class_w': [round(float(c), 2) for c in cw]}), flush=True)
    net = SegNet().to(DEV); gpu_guard.assert_on_gpu(net)
    if a.init: net.load_state_dict(torch.load(a.init, map_location=DEV)); print(json.dumps({'init': a.init}), flush=True)
    opt = torch.optim.Adam(net.parameters(), 1e-3 if not a.init else 4e-4, weight_decay=1e-4); best = -1.0
    for ep in range(a.epochs):
        rng.shuffle(tr); tot = 0.0; nb = 0
        for s in range(0, len(tr), BS):
            xb, sb = take(parts, tr[s:s + BS], off)
            if AUG: xb = augment(xb)
            lo = net(xb); ce = F.cross_entropy(lo, sb, weight=cw_t, ignore_index=255)
            pr = lo.softmax(1); m = (sb != 255).float(); oh = F.one_hot(sb.clamp(max=NCLS - 1), NCLS).permute(0, 3, 1, 2).float() * m[:, None]
            inter = (pr * oh).sum((0, 2, 3))[1:]; den = (pr * m[:, None]).sum((0, 2, 3))[1:] + oh.sum((0, 2, 3))[1:]
            dice = 1 - (2 * inter + 1) / (den + 1); loss = ce + dice.mean()
            opt.zero_grad(); loss.backward(); opt.step(); tot += float(loss); nb += 1
        io, _ = evaluate(net, parts, off, va); miou_l = float(np.mean(io[1:9][hist[1:9] > 0])); rep = {'ep': ep, 'train': round(tot / max(1, nb), 4), 'val_miou_lanes': round(miou_l, 3), 'iou_line': round(float(io[9]), 3), 'iou_opp': round(float(io[10]), 3), 'iou_x': round(float(io[11]), 3), 'iou': [round(float(v), 2) for v in io]}
        print(json.dumps(rep), flush=True)
        if miou_l > best: best = miou_l; torch.save(net.state_dict(), a.out)
    print(json.dumps({'done': a.out, 'best_val_miou_lanes': round(best, 3)}), flush=True)
if __name__ == '__main__': main()
