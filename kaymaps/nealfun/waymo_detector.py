"""흰 Waymo(내 차) 전용 검출.
★함정1: autopilot.car_pos()는 분홍/주황 등 남의 차를 추적했다(2026-09-12).
★함정2: 흰색 임계만 쓰면 카드 바깥 페이지 흰 배경과 한 덩어리로 붙는다 →
   반드시 보드(아스팔트) 영역 안에서만 찾는다."""
import fastvis, numpy as np
from scipy import ndimage

# 보드(아스팔트) 영역 — 상단 파란 배너/하단 버튼 줄 제외
TOP, BOT, LEFT, RIGHT = 200, 1090, 15, 915

def pos():
    a = fastvis.grab().astype(int)
    sub = a[TOP:BOT, LEFT:RIGHT]
    r, g, b = sub[:, :, 0], sub[:, :, 1], sub[:, :, 2]
    white = (r > 185) & (g > 185) & (b > 185) & (abs(r - g) < 30) & (abs(g - b) < 30)
    white = ndimage.binary_closing(white, np.ones((9, 9)))   # 회전 시 갈라진 차체를 다시 잇는다
    lab, n = ndimage.label(white)
    if n == 0:
        return None
    best = None
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if len(ys) < 1500:                 # 주차선(가늘고 긴 줄)은 폭이 얇다
            continue
        w = xs.max() - xs.min(); h = ys.max() - ys.min()
        if w < 90 or h < 90:               # 주차선(210x8)·경찰차 흰부분(62x50) 배제
            continue
        if w > 300 or h > 300:
            continue
        if best is None or len(ys) > best[0]:
            best = (len(ys), int(xs.mean()) + LEFT, int(ys.mean()) + TOP, int(w), int(h))
    return best[1:] if best else None
