"""마이크로 비전 루프: 캡처-판정-클릭을 한 프로세스에서 최소 지연으로 수행.
screencapture 서브프로세스(319ms) 대신 Quartz 직접 캡처(~15ms)를 쓴다."""
import numpy as np, time
import Quartz
import Quartz.CoreGraphics as CG

def grab_rect(x, y, w, h):
    """물리 픽셀 좌표계에서 영역 캡처. Quartz 직접 호출 = 서브프로세스 없음."""
    img = CG.CGWindowListCreateImage(
        CG.CGRectMake(x/2.0, y/2.0, w/2.0, h/2.0),
        CG.kCGWindowListOptionOnScreenOnly, CG.kCGNullWindowID,
        CG.kCGWindowImageDefault)
    if img is None: return None
    W = CG.CGImageGetWidth(img); H = CG.CGImageGetHeight(img)
    bpr = CG.CGImageGetBytesPerRow(img)
    prov = CG.CGImageGetDataProvider(img)
    data = CG.CGDataProviderCopyData(prov)
    buf = np.frombuffer(data, dtype=np.uint8)
    arr = buf[:H*bpr].reshape(H, bpr//4, 4)[:, :W, :]
    return arr[:, :, [2,1,0]].astype(np.int16)   # BGRA -> RGB

def click(x, y):
    """CGEvent 직접 클릭 = kongtrol 서브프로세스(430ms) 없이 즉시."""
    p = CG.CGPointMake(x, y)
    for ev, t in ((CG.kCGEventLeftMouseDown, 1), (CG.kCGEventLeftMouseUp, 0)):
        e = CG.CGEventCreateMouseEvent(None, ev, p, CG.kCGMouseButtonLeft)
        CG.CGEventPost(CG.kCGHIDEventTap, e)
