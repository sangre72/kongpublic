"""자율주행 시작 전 브라우저 창 규격화 (u_5078 오너 지시).

WHY: 창 크기가 바뀌면 캔버스 해상도가 바뀌고 코드픽셀 디코더·좌표가 전부 흔들린다.
     실제로 CineBot 작업 후 1800x1189(화면보다 큼)로 남아 측정이 오염됐고,
     탭을 닫자 697x613 으로 찌그러진 적도 있다.
     ⇒ 주행 시작 루틴이 매번 창을 규격 크기로 되돌린다.

크기 근거(실측 2026-09-15): 1728x1017 캔버스 81.0fps / 720x560 캔버스 91.4fps.
     작은 쪽이 13% 빠르고 디코더도 정상이라 기본값은 작은 쪽.
"""
import subprocess

DEFAULT_W, DEFAULT_H = 720, 660      # 오너가 쓰던 크기
ORIGIN_X, ORIGIN_Y = 0, 25


def _osa(script):
    return subprocess.run(['osascript', '-e', script],
                          capture_output=True, text=True).stdout.strip()


def resize(w=DEFAULT_W, h=DEFAULT_H):
    """Chrome 앞창을 규격 크기로 맞추고 실제 bounds 를 돌려준다."""
    _osa('tell application "Google Chrome" to set bounds of front window to '
         '{%d, %d, %d, %d}' % (ORIGIN_X, ORIGIN_Y, w, h))
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
