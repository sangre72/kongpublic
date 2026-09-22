#!/usr/bin/env python3
"""ScreenCaptureKit 창 캡처(u_5532 GPU 상주 파이프라인 1단계, 2026-09-22). Chrome 게임 창을 SCStream 으로 받아 BGRA 프레임을 콜백으로 전달.
사용: python3 sck_capture.py [초=5]  → fps·프레임당 ms 측정. 모듈로: start(cb, fps=60) / stop(). cb(np.uint8 HxWx4, t)."""
import sys, time, threading, objc, numpy as np
import ScreenCaptureKit as SC, CoreMedia as CM, Quartz as CG
from Foundation import NSObject, NSRunLoop, NSDate
import capture as C

_state = {'stream': None, 'n': 0, 't0': 0.0, 'cb': None, 'shape': None, 'last': 0.0}

class _Out(NSObject):
    def stream_didOutputSampleBuffer_ofType_(self, stream, sbuf, otype):
        if otype != 0: return   # 0 = screen
        try:
            pb = CM.CMSampleBufferGetImageBuffer(sbuf)
            if pb is None: return
            CG.CVPixelBufferLockBaseAddress(pb, 1)
            try:
                w = CG.CVPixelBufferGetWidth(pb); h = CG.CVPixelBufferGetHeight(pb); bpr = CG.CVPixelBufferGetBytesPerRow(pb)
                base = CG.CVPixelBufferGetBaseAddress(pb)
                buf = base.as_buffer(bpr * h) if hasattr(base, 'as_buffer') else base
                arr = np.frombuffer(buf, dtype=np.uint8, count=bpr * h).reshape(h, bpr // 4, 4)[:, :w, :]
                _state['n'] += 1; _state['last'] = time.time(); _state['shape'] = arr.shape
                if _state['cb']: _state['cb'](arr, _state['last'])
            finally:
                CG.CVPixelBufferUnlockBaseAddress(pb, 1)
        except Exception as e:
            _state['err'] = repr(e)

def _shareable():
    box = {}
    ev = threading.Event()
    def done(content, err): box['c'] = content; box['e'] = err; ev.set()
    SC.SCShareableContent.getShareableContentWithCompletionHandler_(done)
    t0 = time.time()
    while not ev.is_set() and time.time() - t0 < 10:
        NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.05))
    if box.get('e') is not None: raise RuntimeError(str(box['e']))
    return box.get('c')

def start(cb=None, fps=60, scale=1):
    C.find_window(); wid = C._cache.get('wid')
    content = _shareable()
    win = next((w for w in content.windows() if w.windowID() == wid), None)
    if win is None: raise RuntimeError('chrome window not in shareable content (permission?)')
    f = SC.SCContentFilter.alloc().initWithDesktopIndependentWindow_(win)
    cfg = SC.SCStreamConfiguration.alloc().init()
    fr = win.frame(); cfg.setWidth_(int(fr.size.width * scale)); cfg.setHeight_(int(fr.size.height * scale))
    cfg.setMinimumFrameInterval_(CM.CMTimeMake(1, fps)); cfg.setPixelFormat_(1111970369)   # 'BGRA'
    cfg.setQueueDepth_(3); cfg.setShowsCursor_(False)
    st = SC.SCStream.alloc().initWithFilter_configuration_delegate_(f, cfg, None)
    out = _Out.alloc().init(); _state['out'] = out
    ok, err = st.addStreamOutput_type_sampleHandlerQueue_error_(out, 0, None, None)
    if not ok: raise RuntimeError(str(err))
    ev = threading.Event(); box = {}
    def started(e): box['e'] = e; ev.set()
    st.startCaptureWithCompletionHandler_(started)
    t0 = time.time()
    while not ev.is_set() and time.time() - t0 < 10:
        NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.05))
    if box.get('e') is not None: raise RuntimeError(str(box['e']))
    _state['stream'] = st; _state['cb'] = cb; _state['n'] = 0; _state['t0'] = time.time()
    return (int(fr.size.width), int(fr.size.height))

def pump(sec):
    NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(sec))

def stop():
    st = _state.get('stream')
    if st: st.stopCaptureWithCompletionHandler_(lambda e: None); _state['stream'] = None

if __name__ == '__main__':
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 5
    lat = []
    def cb(arr, t): lat.append(time.time() - t)
    sz = start(cb)
    t0 = time.time()
    while time.time() - t0 < secs: pump(0.1)
    n = _state['n']; stop()
    print({'window': sz, 'frames': n, 'fps': round(n / secs, 1), 'shape': _state.get('shape'), 'err': _state.get('err')})
