"""DAgger 수집 — 모델이 운전, 교사는 정답만 기록 (2026-09-14 강화 단계).

WHY: 교사 혼자 달린 데이터는 '교사가 잘 가는 길'만 담겨 있다.
     모델은 거기 없던 상황(차선 살짝 벗어남, 사고 직전)에서 무너지는데,
     그 상황의 정답이 데이터에 없으니 아무리 더 모아도 안 고쳐진다.
     → 모델이 직접 운전하게 두고, 그때그때 교사에게 "너라면?"을 물어 라벨로 남긴다.

★반드시 포그라운드로 실행(백그라운드면 키가 게임에 안 들어감 — 실측).
사용: python3 dagger_run.py <model.pt> <out_dir> <seconds>
"""
import sys, os, time, json
import numpy as np, torch, torch.nn as nn
import os as _os, sys as _sys
_sys.path.insert(0,_os.path.dirname(_os.path.abspath(__file__)))
from net import DriveNet, preprocess
from capture import find_window as _fw, grab_canvas as _gc, start_background as _bgs, stop_background as _bge, latest as _lat
import Quartz as CG
from PIL import Image

# ★a_5124 T3: 조용한 CPU 폴백 금지(.claude/rules/gpu-mandatory.md).
#   예전 코드는 mps 가 없으면 말없이 cpu 로 떨어져, 느린 학습을 '정상'으로 착각하게 했다.
from gpu_guard import require_gpu, assert_on_gpu
DEV = require_gpu()


KEY = {'up':126,'down':125,'left':123,'right':124}
_d = set()
def key(k, on):
    if on == (k in _d): return
    CG.CGEventPost(CG.kCGHIDEventTap, CG.CGEventCreateKeyboardEvent(None, KEY[k], on))
    (_d.add if on else _d.discard)(k)

def pick():
    wl = CG.CGWindowListCopyWindowInfo(
        CG.kCGWindowListOptionOnScreenOnly | CG.kCGWindowListExcludeDesktopElements,
        CG.kCGNullWindowID)
    best = None; area = 0
    for w in wl:
        if 'Chrome' not in str(w.get('kCGWindowOwnerName','')): continue
        b = w.get('kCGWindowBounds') or {}
        a = float(b.get('Width',0))*float(b.get('Height',0))
        if a > area: area = a; best = w.get('kCGWindowNumber')
    return best

def grab(win):
    img = CG.CGWindowListCreateImage(CG.CGRectNull, CG.kCGWindowListOptionIncludingWindow,
                                     win, CG.kCGWindowImageBoundsIgnoreFraming)
    if img is None: return None
    W = CG.CGImageGetWidth(img); H = CG.CGImageGetHeight(img)
    bpr = CG.CGImageGetBytesPerRow(img)
    b = np.frombuffer(CG.CGDataProviderCopyData(CG.CGImageGetDataProvider(img)), dtype=np.uint8)
    return b[:H*bpr].reshape(H, bpr//4, 4)[:, :W, [2,1,0]]

def main(model_path, out, secs):
    os.makedirs(out, exist_ok=True)
    net = DriveNet().to(DEV)
    net.load_state_dict(torch.load(model_path, map_location=DEV)); net.eval()
    win = _fw()
    _bgs()
    _sq = None
    if not win: print('{"err":"no window"}'); return
    X, T = [], []
    t0 = time.time(); secs = float(secs); n = 0
    try:
        while time.time() - t0 < secs:
            a, _sq = _lat(_sq)   # 새 프레임만(중복 수집 방지)
            if a is None: continue
            f = preprocess(a, device=DEV)
            x = f[None]
            with torch.no_grad(): o = net(x)[0].cpu().numpy()
            st, th, br = float(o[0]), float(o[1]), float(o[2])
            # 모델이 운전한다
            key('left', st < -0.25); key('right', st > 0.25)
            key('down', br > 0.35);  key('up', br <= 0.35 and th > -0.2)
            X.append(f.cpu().numpy().astype(np.float16))
            T.append(int(time.time()*1000))
            n += 1
    finally:
        for k in list(_d): key(k, False)
        _bge()
    np.savez_compressed(f'{out}/frames.npz', X=np.stack(X), T=np.array(T, dtype=np.int64))
    print(json.dumps({'frames': n, 'fps': round(n/secs,1), 'out': out}))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
