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
    """코드블록 중심 y 를 찾는다. 못 찾으면 None.

    ★2026-09-14 u_4969 재작성. 예전 구현은 '마커색에 가까운 픽셀 중 가장 위'를
      골랐는데, 허용오차를 넓히자 브라우저 툴바(보라 계열)가 먼저 걸려서
      엉뚱한 행을 읽었다(steer=1.00/brake=1.00 같은 불가능한 값이 나옴).
      마커는 반드시 캔버스 좌상단 x=0..15 에 16px 로 있고 그 오른쪽으로
      블록 3개가 이어지므로, 그 구조 자체를 검사해서 확정한다.
    """
    # ★2026-09-14 u_4971 속도: 전체 프레임(2.6M px)을 float 로 올리면 26ms 가 든다.
    #   블록은 항상 캔버스 좌상단 x=0..15 에 있으므로 그 열만 본다(2.6M → 4만 px).
    #   실측 25.87ms → 0.5ms.
    f = rgb[:, :7 * B, :].astype(np.float32)   # ★블록5(주행가능공간, u_5028)까지 포함
    H = f.shape[0]
    col = np.abs(f[:, :B, :] - MARK).sum(2).mean(1)   # x=0..15 평균 거리
    cand = np.nonzero(col < 110)[0]
    if len(cand) == 0:
        return None
    # 연속 구간으로 묶어 16px 이상인 것만 후보로
    runs, s0 = [], cand[0]
    for a, b in zip(cand, cand[1:]):
        if b != a + 1:
            runs.append((s0, a)); s0 = b
    runs.append((s0, cand[-1]))
    for a, b in runs:
        if b - a + 1 < 10:
            continue
        cy = (a + b) // 2
        # 오른쪽 3블록이 마커와 '다른' 색이어야 진짜 코드블록이다
        # (툴바처럼 균일한 띠면 4칸이 전부 같은 색 → 탈락)
        blocks = [f[cy, k * B + B // 2] for k in range(4)]
        if max(np.abs(blocks[k] - blocks[0]).sum() for k in (1, 2, 3)) < 12:
            continue
        return int(cy)
    return None

def decode(rgb, bgr=True):
    """bgr=True(기본): capture._to_np 가 주는 BGR 버퍼를 그대로 받는다.

    ★2026-09-14 u_4969 실사고: capture._to_np 는 성능을 위해 채널을 뒤집지 않고
      BGR view 를 그대로 돌려준다(주석에 명시, net.preprocess 가 GPU 에서 flip).
      decode 는 그걸 RGB 로 가정해 읽고 있었다 → 마커 (165,90,195) 가
      (195,90,165) 로 보여 거리 69 로 탐지 실패, 어쩌다 잡혀도 R/B 가 뒤바뀐
      값(crashes 가 on_road 자리로)을 읽었다. 화면 실측(파란 4번 블록)과
      캡처값(빨강)이 정반대인 것으로 확정.
    """
    if bgr:
        rgb = rgb[:, :, ::-1]
    return _decode_rgb(rgb)   # find_blocks 도 이 RGB 버퍼를 받는다


def _decode_rgb(rgb):
    """→ dict(steer, thr, brake, rev, v, lane, crashes, hold, on_road) 또는 None"""
    cy = find_blocks(rgb)
    if cy is None:
        return None
    # ★u_4971 속도: 전체 프레임 astype(float) 가 5.6ms. 실제로 쓰는 건 4픽셀뿐이다.
    blocks = [rgb[cy, i*B + B//2].astype(np.float64) for i in range(7)]
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
        # ★주행 평가용(u_5016) — 방향/경로진행률/자율주행 여부
        'heading': g(blocks[4], 0) * 2 * np.pi,   # rad
        'progress': g(blocks[4], 1),              # 0~1
        'auto': 1 if g(blocks[4], 2) > 0.5 else 0,
        # ★주행가능공간(u_5028) — 좌/우로 도로가 몇 m 남았나. 학습 보조목표.
        'free_l': g(blocks[5], 0) * 8,            # m
        'free_r': g(blocks[5], 1) * 8,            # m
        # ★경로가 도로 위인가(u_5036)
        'wp_onroad': g(blocks[6], 0),             # 0~1 비율
        'wp_n': int(round(g(blocks[6], 1) * 255)),
        'wp_first_ok': 1 if g(blocks[6], 2) > 0.5 else 0,
    }
