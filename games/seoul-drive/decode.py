"""화면 코드픽셀 → 조작 라벨 디코더 (2026-09-14).

★왜 화면에서 읽나: 아티팩트 db 로 라벨을 보내던 방식은 용량이 차면(run 66개 누적,
  'Storage full') 조용히 죽는다. 실제로 1시간 동안 죽어 있었고 그 사이 수집한
  42,584프레임이 라벨 없이 버려졌다.
  화면에 찍으면 용량 제약이 없고, 픽셀과 라벨이 같은 프레임이라 시간 어긋남도 없다.

레이아웃: 캔버스 좌상단 16px 블록 4개
  블록0 = 고정 마커 (165,90,195)  ← 위치 탐지 + 색 보정 기준
  블록1 = (steer+1)/2, thr, brake
  블록2 = rev, v/20, lane_off/16
  블록3 = crashes, hold, onRoad

★뷰어 합성으로 색이 약간 변형된다(실측 배율 R0.933 G1.044 B0.969).
  마커의 실제 관측색으로 채널별 배율을 역산해 보정한다. 변동은 0.3~0.9 로 매우 안정적.
"""
import numpy as np

MARK = np.array([165, 90, 195], dtype=float)
B = 16

def find_blocks(rgb):
    """캔버스(RGB)에서 코드블록 중심 y 를 찾는다. 못 찾으면 None."""
    d = np.abs(rgb.astype(float) - MARK).sum(2)
    m = d < 60
    ys, xs = np.nonzero(m)
    if len(ys) < 50:
        return None
    top = ys.min()
    sel = ys < top + 20
    if sel.sum() < 50:
        return None
    return int(np.median(ys[sel]))

def decode(rgb):
    """→ dict(steer, thr, brake, rev, v, lane, crashes, hold, on_road) 또는 None"""
    cy = find_blocks(rgb)
    if cy is None:
        return None
    f = rgb.astype(float)
    blocks = [f[cy, i*B + B//2] for i in range(4)]
    scale = np.where(blocks[0] > 8, blocks[0] / MARK, 1.0)   # 마커로 채널 보정
    g = lambda blk, ch: float(np.clip(blk[ch] / max(scale[ch], 1e-6), 0, 255)) / 255.0
    b1, b2, b3 = blocks[1], blocks[2], blocks[3]
    return {
        'steer':   g(b1, 0) * 2 - 1,
        'thr':     g(b1, 1),
        'brake':   g(b1, 2),
        'rev':     g(b2, 0),
        'v':       g(b2, 1) * 20,            # m/s
        'lane':    g(b2, 2) * 16,            # m
        'crashes': int(round(g(b3, 0) * 255)),
        'hold':    1 if g(b3, 1) > 0.5 else 0,
        'on_road': 1 if g(b3, 2) > 0.5 else 0,
    }
