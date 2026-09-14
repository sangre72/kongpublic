"""화면 캡처 — 공용 모듈 (2026-09-14 u_4939 CPU/GPU 경합 대응).

★핵심: kCGWindowImageNominalResolution 으로 캡처하면 Retina 2배를 건너뛰고
  논리 해상도(763x762)로 바로 받는다. 픽셀이 1/4 이라
    - WindowServer 합성 부담이 줄고
    - cv2 로 1/2 줄이는 단계가 통째로 사라진다
  실측(실제 주행 루프): 28.9ms(35fps) → 17.9ms(56fps)
  품질은 사실상 동일: 신호등 542→540px, 차선 10.82→10.84%, 오차 1.04→1.16

  WindowServer 가 CPU 1위(48.6%)였던 것이 단서였다 — CGWindowListCreateImage 는
  매 호출마다 WindowServer 합성을 거치므로, 받는 픽셀을 줄이는 게 가장 직접적이다.
"""
import threading, time
import numpy as np
import Quartz as CG

_cache = {}

def find_window(title_hint='드라이브'):
    """가장 큰 Chrome 창. 제목으로만 찾으면 빈 제목 보조창(270x80)이 잡혀 캡처가 None 이 된다."""
    wl = CG.CGWindowListCopyWindowInfo(
        CG.kCGWindowListOptionOnScreenOnly | CG.kCGWindowListExcludeDesktopElements,
        CG.kCGNullWindowID)
    best, area, bounds = None, 0, None
    for w in wl:
        if 'Chrome' not in str(w.get('kCGWindowOwnerName', '')): continue
        b = w.get('kCGWindowBounds') or {}
        a = float(b.get('Width', 0)) * float(b.get('Height', 0))
        if a > area:
            area, best, bounds = a, w.get('kCGWindowNumber'), b
    if best is not None:
        _cache['wid'] = best
        _cache['rect'] = CG.CGRectMake(bounds['X'], bounds['Y'], bounds['Width'], bounds['Height'])
        _cache['toolbar'] = 75          # 논리해상도 기준 툴바 높이(레티나의 절반)
    return best

def _to_np(img):
    W = CG.CGImageGetWidth(img); H = CG.CGImageGetHeight(img)
    bpr = CG.CGImageGetBytesPerRow(img)
    d = np.frombuffer(CG.CGDataProviderCopyData(CG.CGImageGetDataProvider(img)), dtype=np.uint8)
    # ★[2,1,0] 팬시 인덱싱은 복사를 만든다(0.6ms). [:, :W, :3] 는 view(0ms).
    #   BGR→RGB 는 GPU 에서 flip 으로 처리한다(net.preprocess).
    return d[:H*bpr].reshape(H, bpr//4, 4)[:, :W, :3]

def grab_canvas():
    """게임 캔버스만 (툴바 제외) 논리해상도로 반환. 실패시 None."""
    if 'rect' not in _cache and find_window() is None:
        return None
    img = CG.CGWindowListCreateImage(
        _cache['rect'], CG.kCGWindowListOptionOnScreenOnly,
        CG.kCGNullWindowID, CG.kCGWindowImageNominalResolution)
    if img is None:
        if find_window() is None: return None
        img = CG.CGWindowListCreateImage(
            _cache['rect'], CG.kCGWindowListOptionOnScreenOnly,
            CG.kCGNullWindowID, CG.kCGWindowImageNominalResolution)
        if img is None: return None
    a = _to_np(img)
    return a[_cache['toolbar']:, :, :]


# ───────────────────────── 백그라운드 캡처 (u_4942 100fps 목표) ─────────────────
#  CGWindowListCreateImage 는 픽셀 수와 무관하게 고정비용 ~6ms 다
#  (실측: 8x8 만 캡처해도 5.96ms). 순차로 돌면 여기서 루프가 막힌다.
#  → 캡처를 전용 스레드로 돌리고 추론은 '최신 프레임'을 즉시 쓴다.
#  실측: 순차 60fps → 추론루프 478fps, 실제 새 화면 70fps.
#  ※추론이 캡처보다 빠르므로 같은 프레임을 다시 보는 경우가 생긴다(85%).
#    주행 판단에는 문제 없다(화면이 안 바뀌었으면 같은 판단이 맞다).
#    단 학습 데이터 수집에는 중복이 쌓이므로 seq 번호로 새 프레임만 받을 것.
_bg = {'frame': None, 'seq': 0, 'run': False, 'th': None}

def clear_selection():
    """캔버스 빈 곳을 한 번 클릭해 텍스트 전체선택을 푼다.

    ★2026-09-14 u_4957: 화면이 파랗게 보여 '뷰어가 오버레이를 씌운다'고 오진했다.
      실제로는 페이지가 전체선택(Cmd+A)된 상태의 선택 하이라이트였다.
      선택을 풀면 색편향(B-R)이 +47 → +2 로 중립이 된다.
      이 상태로 수집하면 학습 데이터 전체가 파랗게 물든다.
    """
    try:
        import Quartz as _Q
        if 'rect' not in _cache and find_window() is None:
            return False
        r = _cache['rect']
        x = float(r.origin.x) + float(r.size.width) * 0.5
        y = float(r.origin.y) + float(r.size.height) * 0.6
        pt = _Q.CGPointMake(x, y)
        for down in (True, False):
            ev = _Q.CGEventCreateMouseEvent(
                None,
                _Q.kCGEventLeftMouseDown if down else _Q.kCGEventLeftMouseUp,
                pt, _Q.kCGMouseButtonLeft)
            _Q.CGEventPost(_Q.kCGHIDEventTap, ev)
        time.sleep(0.25)
        return True
    except Exception:
        return False

def start_background():
    """캡처 전용 스레드 시작. 이미 돌고 있으면 무시."""
    if _bg['run']:
        return
    if 'rect' not in _cache and find_window() is None:
        return
    clear_selection()          # 선택 하이라이트가 남아 있으면 화면이 파랗게 물든다
    _bg['run'] = True
    def _loop():
        while _bg['run']:
            f = grab_canvas()
            if f is not None:
                _bg['frame'] = f
                _bg['seq'] += 1
            else:
                time.sleep(0.05)
                find_window()
    _bg['th'] = threading.Thread(target=_loop, daemon=True)
    _bg['th'].start()
    for _ in range(40):           # 첫 프레임 대기
        if _bg['frame'] is not None: break
        time.sleep(0.02)

def stop_background():
    _bg['run'] = False
    if _bg['th']: _bg['th'].join(timeout=1.0)
    _bg['th'] = None

def latest(min_seq=None):
    """최신 프레임. min_seq 를 주면 그보다 새 프레임이 나올 때까지 기다린다
       (학습 데이터 수집처럼 중복이 곤란할 때 사용)."""
    if min_seq is None:
        return _bg['frame'], _bg['seq']
    while _bg['run'] and _bg['seq'] <= min_seq:
        time.sleep(0.001)
    return _bg['frame'], _bg['seq']
