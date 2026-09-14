"""학습된 CNN으로 실제 브라우저에서 주행 (2026-09-14).

화면만 보고 조작한다. 교사(T)는 끄고, 키보드로만 차를 몬다 — 사람과 같은 경로.
★검증은 반드시 실제 브라우저에서 한다(시뮬레이터 결과는 인정하지 않음, 오너 지시).

사용: python3 drive_infer.py model.pt [seconds]
"""
import sys, time, json, subprocess
import numpy as np, torch, torch.nn as nn
import os as _os, sys as _sys
_sys.path.insert(0,_os.path.dirname(_os.path.abspath(__file__)))
from net import DriveNet, preprocess
from capture import find_window as _fw, grab_canvas as _gc, start_background as _bgs, stop_background as _bge, latest as _lat
import Quartz as CG
from PIL import Image

DEV = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
KEY = {'up':126,'down':125,'left':123,'right':124}
_down=set()
def key(k,on):
    if on == (k in _down): return
    CG.CGEventPost(CG.kCGHIDEventTap, CG.CGEventCreateKeyboardEvent(None, KEY[k], on))
    (_down.add if on else _down.discard)(k)
def release_all():
    for k in list(_down): key(k,False)


def find_window():
    wl=CG.CGWindowListCopyWindowInfo(CG.kCGWindowListOptionOnScreenOnly|
                                     CG.kCGWindowListExcludeDesktopElements, CG.kCGNullWindowID)
    # ★가장 큰 Chrome 창을 고른다. 제목만 보고 고르면 빈 제목의 보조 창(270x80)이
    #   먼저 잡혀 캡처가 None 을 반환한다(실측).
    best=None; area=0
    for w in wl:
        if 'Chrome' not in str(w.get('kCGWindowOwnerName','')): continue
        b=w.get('kCGWindowBounds') or {}
        a=float(b.get('Width',0))*float(b.get('Height',0))
        if a>area: area=a; best=w.get('kCGWindowNumber')
    return best

def grab(win):
    img=CG.CGWindowListCreateImage(CG.CGRectNull, CG.kCGWindowListOptionIncludingWindow,
                                   win, CG.kCGWindowImageBoundsIgnoreFraming)
    if img is None: return None
    W=CG.CGImageGetWidth(img); H=CG.CGImageGetHeight(img); bpr=CG.CGImageGetBytesPerRow(img)
    buf=np.frombuffer(CG.CGDataProviderCopyData(CG.CGImageGetDataProvider(img)),dtype=np.uint8)
    return buf[:H*bpr].reshape(H,bpr//4,4)[:,:W,[2,1,0]]

def main(model_path, secs=60):
    net=DriveNet().to(DEV); net.load_state_dict(torch.load(model_path, map_location=DEV)); net.eval()
    win=_fw()
    _bgs()          # 캡처 전용 스레드(고정비용 6ms 를 루프 밖으로)
    if not win: print('{"err":"no window"}'); return
    # ★캔버스를 먼저 클릭해 페이지에 키보드 포커스를 준다.
    #   이걸 빼먹어서 모델이 스로틀 0.84를 내보내는데도 차가 안 움직였다(실측: 화면 diff 0.13 = 정지).
    #   수동으로 위 화살표를 눌렀을 땐 diff 8.66 으로 잘 움직였다 — 즉 키 입력 경로는 정상, 포커스가 문제였다.
    subprocess.run(['open','-a','Google Chrome'], capture_output=True); time.sleep(1.2)
    # 합성 클릭은 오히려 포커스를 UI 요소로 빼앗아 키가 안 먹었다(실측: 동일 키 코드가
    # 단독 실행 때는 diff 8.9로 잘 움직였는데 이 루프 안에서만 0.04 = 정지).
    # 창을 앞으로 가져오는 것만으로 충분하다.
    time.sleep(0.4)
    t0=time.time(); n=0; lat=[]
    try:
        while time.time()-t0 < float(secs):
            a,_sq=_lat()
            if a is None: continue
            # ★전처리가 병목이었다(실측 20.5ms, 20ms 예산을 혼자 초과).
            #   4008x2430 을 LANCZOS로 한 번에 줄이는 게 원인.
            #   먼저 8픽셀 간격으로 성글게 줄인 뒤 마무리하면 2.3ms (9배).
            #   ★예전 ::7 스트라이드 버그(차선 764px→0)와 달리 차선이 살아남는 걸 실측 확인:
            #     원본 어두운(차선)픽셀 5.31% → fast 4.97% (LANCZOS 5.20%), 대비 std 44.2 vs 44.5.
            f=preprocess(a, device=DEV)   # 이미 GPU 텐서
            x=f[None]
            s=time.time()
            with torch.no_grad(): o=net(x)[0].cpu().numpy()
            lat.append((time.time()-s)*1000)
            steer,thr,brake=float(o[0]),float(o[1]),float(o[2])
            key('left',  steer < -0.25)
            key('right', steer >  0.25)
            key('down',  brake >  0.35)
            key('up',    brake <= 0.35 and thr > -0.2)
            n+=1
    finally:
        release_all(); _bge()
    print(json.dumps({'frames':n,'infer_ms':round(float(np.mean(lat)),2) if lat else None}))

if __name__=='__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else 60)
