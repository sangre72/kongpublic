"""색상 판정기 — 오검출 없이 신호등을 세기 위한 공용 모듈 (2026-09-14 u_4946).

★왜 만들었나: RGB 차이로 '빨강'을 판정했더니 주황 도로(#ff6a00)가 전부 빨간불로
  잡혔다. 실측: 오검출 386px 중 321px(83%)이 주황(Hue 15~45도)이었다.
  해상도 탓이 아니었다 — 색조로 판정하면 84x84 에서도 신호등과 주황이 완벽히 갈린다
  (합성 테스트: 512~84 전 해상도에서 빨강/초록/주황 분리 성공).

판정 기준(HSV):
  빨간불 #ff0000 → Hue   0도
  초록불 #00c000 → Hue 120도
  주황도로 #ff6a00 → Hue  25도   ← 빨강과 25도밖에 안 떨어져 RGB 로는 못 가른다
  채도/명도 문턱을 둬서 회색·연한 색은 아예 제외한다.
"""
import numpy as np

def hsv(a):
    """(H,W,3) uint8 → hue(0~360), sat(0~1), val(0~1)"""
    f = a.astype(np.float32) / 255.0
    r, g, b = f[:, :, 0], f[:, :, 1], f[:, :, 2]
    mx = f.max(2); mn = f.min(2); d = mx - mn
    hue = np.zeros_like(mx)
    i = (mx == r) & (d > 0); hue[i] = ((g - b)[i] / d[i]) % 6
    i = (mx == g) & (d > 0); hue[i] = ((b - r)[i] / d[i]) + 2
    i = (mx == b) & (d > 0); hue[i] = ((r - g)[i] / d[i]) + 4
    hue *= 60
    sat = np.where(mx > 0, d / np.maximum(mx, 1e-6), 0)
    return hue, sat, mx

def masks(a, smin=0.75, vmin=0.65):
    """신호등 빨강/초록 마스크. 주황 도로는 제외된다.

    ★문턱을 높인 이유(실측): smin=0.55 로는 축소 과정에서 배경과 섞인
      흐린 벽돌색(202,72,60)까지 빨강으로 잡혀 프레임당 8px 씩 잡음이 남았다.
      신호등은 순수 #ff0000/#00c000 으로 그려지므로 채도·명도가 매우 높다.
      0.75/0.65 로 올리면 섞인 픽셀은 떨어지고 진짜 신호등만 남는다."""
    hue, sat, val = hsv(a)
    strong = (sat > smin) & (val > vmin)
    red   = strong & ((hue < 12) | (hue > 348))     # 순수 빨강만
    green = strong & (hue > 95) & (hue < 155)
    orange= strong & (hue >= 18) & (hue <= 42)      # 도로 — 참고용
    return red, green, orange

def count(a):
    r, g, o = masks(a)
    return int(r.sum()), int(g.sum()), int(o.sum())
