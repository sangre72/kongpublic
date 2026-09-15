"""자율주행 시작 전 브라우저 창 규격화 (u_5078 오너 지시).

WHY: 창 크기가 바뀌면 캔버스 해상도가 바뀌고 코드픽셀 디코더·좌표가 전부 흔들린다.
     실제로 CineBot 작업 후 1800x1189(화면보다 큼)로 남아 측정이 오염됐고,
     탭을 닫자 697x613 으로 찌그러진 적도 있다.
     ⇒ 주행 시작 루틴이 매번 창을 규격 크기로 되돌린다.

크기 근거: 정사각 763x762 가 오너가 확보해둔 규격이다(u_4939). 자율주행 시작 시
     이 해상도로 **강제 변환**한다(u_5089) — 창 크기가 달라지면 캔버스 해상도가 달라지고
     학습/추론 입력 분포가 통째로 바뀌기 때문이다.
"""
import subprocess

# ★정사각 캔버스 763x762 — 오너가 확보해둔 규격(u_4939, u_5089 재지시).
#   capture.py 헤더의 실측 근거: kCGWindowImageNominalResolution 로 논리해상도를 바로 받아
#   28.9ms(35fps) -> 17.9ms(56fps). 픽셀이 1/4 이라 WindowServer 합성 부담이 줄고
#   cv2 1/2 축소 단계가 통째로 사라진다. 품질 저하 없음(신호등 542->540px, 차선 10.82->10.84%).
#   창 높이 = 캔버스 762 + 툴바 75(capture.py:34) = 837.
CANVAS_W, CANVAS_H = 763, 762
TOOLBAR_H = 75
DEFAULT_W, DEFAULT_H = CANVAS_W, CANVAS_H + TOOLBAR_H
ORIGIN_X, ORIGIN_Y = 0, 25


def _osa(script):
    return subprocess.run(['osascript', '-e', script],
                          capture_output=True, text=True).stdout.strip()


def resize(w=DEFAULT_W, h=DEFAULT_H):
    """Chrome 앞창을 규격 크기로 맞춘다.

    ★bounds 는 (x1,y1,x2,y2) 다 — w,h 가 아니라 '오른쪽·아래 좌표'다.
      그래서 y2 = y1 + 원하는높이 로 넣어야 한다. 이걸 놓쳐서 캔버스가
      762 가 아니라 737 로 나왔다(실측).
    """
    _osa('tell application "Google Chrome" to set bounds of front window to '
         '{%d, %d, %d, %d}' % (ORIGIN_X, ORIGIN_Y, ORIGIN_X + w, ORIGIN_Y + h))
    return _osa('tell application "Google Chrome" to get bounds of front window')


def ensure(w=DEFAULT_W, h=DEFAULT_H):
    """리사이즈 + 캔버스가 실제로 잡히는지까지 확인한다."""
    bounds = resize(w, h)
    try:
        import capture
        capture._cache.clear()        # 창이 바뀌었으니 캐시된 rect 를 버린다
        a = capture.grab_canvas()
        shape = None if a is None else a.shape
    except Exception as e:
        shape = 'capture error: %s' % e
    return {'bounds': bounds, 'canvas': shape}


if __name__ == '__main__':
    print(ensure())
