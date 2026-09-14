"""ScreenCaptureKit 캡처 백엔드 (2026-09-14 u_4946).

capture.py 와 **같은 인터페이스**를 제공한다 — find_window / grab_canvas /
start_background / stop_background / latest.
그래서 drive_infer·dagger_run·fast_capture 는 import 한 줄만 바꾸면 된다.
카메라(camera.py)로 갈 때도 같은 인터페이스를 지키면 코드가 그대로 돈다.

왜 SCK 인가:
  CGWindowListCreateImage 는 '요청→합성→복사→반환' 왕복이라 픽셀 수와 무관하게
  고정비용 ~6ms 가 든다(실측: 8x8 만 캡처해도 5.96ms). 100fps(10ms) 예산의 60%다.
  SCK 는 구독 방식이라 왕복이 없고, IOSurface(GPU 버퍼)를 그대로 넘겨 복사도 없다.
  width/height 를 설정에 넣으면 시스템이 축소까지 해준다.

★주의: 비동기 콜백이라 첫 프레임까지 시간이 걸린다. start_background() 가 기다린다.
"""
import threading, time
import numpy as np
import objc, Quartz as CG
import ScreenCaptureKit as SCK
import CoreMedia
import Quartz as CoreVideo   # CVPixelBuffer* 는 pyobjc 에서 Quartz 아래 있다
from Foundation import NSObject

_st = {'stream': None, 'frame': None, 'seq': 0, 'run': False, 'err': None}

class _Out(NSObject):
    """SCStreamOutput — 프레임이 올 때마다 호출된다."""
    def stream_didOutputSampleBuffer_ofType_(self, stream, sbuf, otype):
        if otype != SCK.SCStreamOutputTypeScreen:
            return
        try:
            px = CoreMedia.CMSampleBufferGetImageBuffer(sbuf)
            if px is None: return
            CoreVideo.CVPixelBufferLockBaseAddress(px, 1)
            try:
                w = CoreVideo.CVPixelBufferGetWidth(px)
                h = CoreVideo.CVPixelBufferGetHeight(px)
                bpr = CoreVideo.CVPixelBufferGetBytesPerRow(px)
                base = CoreVideo.CVPixelBufferGetBaseAddress(px)
                buf = (base.as_buffer(h * bpr) if hasattr(base, 'as_buffer')
                       else memoryview(base))
                a = np.frombuffer(buf, dtype=np.uint8, count=h*bpr)
                a = a.reshape(h, bpr // 4, 4)[:, :w, :3]      # BGRA → BGR view
                _st['frame'] = np.ascontiguousarray(a)
                _st['seq'] += 1
            finally:
                CoreVideo.CVPixelBufferUnlockBaseAddress(px, 1)
        except Exception as e:
            _st['err'] = str(e)

def find_window(title_hint='드라이브'):
    """가장 큰 Chrome 창의 window id. capture.py 와 동일한 규칙."""
    wl = CG.CGWindowListCopyWindowInfo(
        CG.kCGWindowListOptionOnScreenOnly | CG.kCGWindowListExcludeDesktopElements,
        CG.kCGNullWindowID)
    best, area = None, 0
    for w in wl:
        if 'Chrome' not in str(w.get('kCGWindowOwnerName', '')): continue
        b = w.get('kCGWindowBounds') or {}
        a = float(b.get('Width', 0)) * float(b.get('Height', 0))
        if a > area: area, best = a, w.get('kCGWindowNumber')
    return best

def start_background(width=None, height=None, fps=120, toolbar=75):
    """width/height 를 안 주면 창 논리크기를 그대로 쓴다.
    ★안 주면 SCK 가 임의 크기(실측 480x1005)로 줘서 화면이 잘린다."""
    """SCK 스트림 시작. 실패하면 False 를 돌려주므로 호출측이 폴백할 수 있다."""
    if _st['run']: return True
    wid = find_window()
    if wid is None: return False
    if width is None or height is None:      # 창 논리크기를 기본값으로
        wl = CG.CGWindowListCopyWindowInfo(
            CG.kCGWindowListOptionOnScreenOnly | CG.kCGWindowListExcludeDesktopElements,
            CG.kCGNullWindowID)
        for w in wl:
            if w.get('kCGWindowNumber') == wid:
                b = w.get('kCGWindowBounds') or {}
                width  = width  or int(b.get('Width', 0))
                height = height or int(b.get('Height', 0))
    _st['toolbar'] = toolbar
    done = {'content': None}
    def handler(content, err):
        done['content'] = content
    SCK.SCShareableContent.getShareableContentWithCompletionHandler_(handler)
    for _ in range(100):
        if done['content'] is not None: break
        time.sleep(0.03)
    content = done['content']
    if content is None: return False
    target = None
    for w in content.windows():
        if int(w.windowID()) == int(wid): target = w; break
    if target is None: return False
    filt = SCK.SCContentFilter.alloc().initWithDesktopIndependentWindow_(target)
    cfg = SCK.SCStreamConfiguration.alloc().init()
    if width:  cfg.setWidth_(int(width))
    if height: cfg.setHeight_(int(height))
    cfg.setMinimumFrameInterval_(CoreMedia.CMTimeMake(1, int(fps)))
    cfg.setShowsCursor_(False)
    # ★픽셀 포맷을 BGRA 로 명시(2026-09-14 실측).
    #   기본값이 '420v'(YUV 4:2:0) 라 bytesPerRow=768(1바이트/픽셀)이 나오고,
    #   BGRA(4바이트/픽셀)로 가정해 읽으면 폭이 763→192 로 잘린다.
    cfg.setPixelFormat_(0x42475241)          # 'BGRA'
    cfg.setQueueDepth_(3)
    out = _Out.alloc().init()
    stream = SCK.SCStream.alloc().initWithFilter_configuration_delegate_(filt, cfg, None)
    ok, err = stream.addStreamOutput_type_sampleHandlerQueue_error_(
        out, SCK.SCStreamOutputTypeScreen, None, None)
    if not ok: return False
    _st.update(stream=stream, out=out, run=True)
    stream.startCaptureWithCompletionHandler_(lambda e: None)
    for _ in range(150):                 # 첫 프레임 대기
        if _st['frame'] is not None: return True
        time.sleep(0.02)
    return _st['frame'] is not None

def stop_background():
    if _st.get('stream'):
        try: _st['stream'].stopCaptureWithCompletionHandler_(lambda e: None)
        except Exception: pass
    _st.update(stream=None, run=False)

def grab_canvas():
    f = _st['frame']
    if f is None: return None
    return f[_st.get('toolbar', 75):, :, :]

def latest(min_seq=None):
    if min_seq is not None:
        while _st['run'] and _st['seq'] <= min_seq:
            time.sleep(0.001)
    return grab_canvas(), _st['seq']
