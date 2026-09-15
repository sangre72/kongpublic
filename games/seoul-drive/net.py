"""주행 신경망 정의 (2026-09-14 u_4935: 256 입력).

WHY 256:
  84x84 로 뭉개면 신호등이 4~5픽셀만 남아 빨강/초록 구분이 사실상 불가능했다
  (학습셋 실측: 빨간불 프레임당 평균 0.3px). 해상도별 실측 결과 —
      84 → 빨강 7px   / 합계 2.50ms
     128 → 빨강 62px  / 합계 2.78ms
     256 → 빨강 324px / 합계 3.03ms
  256 이 84 보다 겨우 0.5ms 비싸다. 캡처 7.9ms 를 더해도 11ms 로 20ms 예산 안.
  ⇒ 압축할 이유가 없다. 3D 로 갈 때도 이 해상도가 기준이 된다.

★AdaptiveAvgPool2d 는 MPS 에서 입력이 출력의 배수가 아니면 터진다.
  그래서 stride conv 를 더 쌓고 마지막에 global average pool 을 쓴다(입력크기 무관).
"""
import torch, torch.nn as nn

IMG = 256          # 입력 한 변
# ★a_5112 P2: 상단 UI 패널(#nav)이 차지하는 비율. 캔버스 763px 기준 180px = 0.236.
#   이 값만큼 위에서 잘라내고 256 으로 리사이즈한다(학습·추론 공통 경로).
UI_CROP_TOP = 0.236

class DriveNet(nn.Module):
    """out=3 이면 steer/thr/brake 만. out=5 면 뒤 2개가 주행가능공간(좌/우 여유).

    ★왜 보조출력인가(u_5028): 오너 지적 — "다닐 수 있는 길과 없는 길이 구분이
      안 돼 있나". 실제로 그랬다. 라벨이 steer/thr/brake 3개뿐이라 8.5만 프레임
      내내 '핸들 흉내'만 배웠고, '도로 위에 있어야 한다'는 한 번도 안 가르쳤다.
      좌/우 여유거리를 같이 맞히게 하면, 특징추출부가 '도로 경계'를 표현하도록
      강제된다(auxiliary task). 추론 때는 앞의 3개만 쓰면 되므로 비용은 0에 가깝다.
      색 대비 실측: 도로 vs 인도 = 80(구분 쉬움), 인도 vs 건물 = 16.8(안 구분되지만
      둘 다 '못 가는 곳'이라 문제되지 않는다)."""
    def __init__(self, out=3):
        super().__init__()
        self.f = nn.Sequential(
            nn.Conv2d(3, 16, 5, 2), nn.ReLU(),
            nn.Conv2d(16, 32, 3, 2), nn.ReLU(),
            nn.Conv2d(32, 64, 3, 2), nn.ReLU(),
            nn.Conv2d(64, 96, 3, 2), nn.ReLU(),
            nn.Conv2d(96, 128, 3, 2), nn.ReLU())
        # ★u_5170: global average pool 을 걷어냈다.
        #   왜: mean(dim=(2,3)) 은 '어디에' 무엇이 있는지를 평균으로 뭉갠다.
        #   앞차가 8m 앞에 있는지 길이 비었는지는 순수하게 공간 정보라서,
        #   평균을 내면 표현 자체가 불가능하다. 실측으로 확인됐다 —
        #   제동 프레임 예측 0.505 vs 비제동 0.476(재현율 12.8%). 손실함수를
        #   아무리 고쳐도 안 올라간 이유가 이것이었다.
        #   256 입력 → conv 5단(stride 2) → 6x6 격자가 남는다. 이걸 그대로 편다.
        self.h = nn.Sequential(nn.Flatten(), nn.Linear(128 * 6 * 6, 256), nn.ReLU(),
                               nn.Dropout(0.1), nn.Linear(256, 96), nn.ReLU(),
                               nn.Linear(96, out))

    def forward(self, x):
        return torch.tanh(self.h(self.f(x)))

def preprocess(canvas_rgb, size=IMG, device=None, bgr=True):
    """캔버스(H,W,3 uint8) → (3,size,size) float32 0~1 (device 텐서).

    ★캡처를 kCGWindowImageNominalResolution 으로 바꾼 뒤(capture.py 참고)
      입력이 이미 논리해상도(687x763)라 cv2 로 1/2 줄이는 단계가 필요 없다.
      큰 입력(레티나 1374x1526)이 들어오면 예전처럼 cv2 AREA /2 를 먼저 태운다.

    ★왜 antialias=True 인가: bilinear/nearest 단독은 '샘플링'이라 탭 사이에
      떨어진 2px 차선을 통째로 건너뛴다(예전 ::7 스트라이드로 차선 764px→0 사고와
      같은 원리). 면적 적분 계열은 흐려질지언정 위치가 보존된다.
      신경망은 임계값이 아니라 연속값을 보므로 후자가 맞다.

    ★MPS 주의: F.adaptive_avg_pool2d 는 입력이 출력의 배수가 아니면 터진다
      (pytorch#96056). align_corners=False 필수.
      uint8 로 올린 뒤 GPU 에서 float 변환해야 전송량이 1/4.
    """
    import torch
    import torch.nn.functional as F
    import numpy as _np
    c = canvas_rgb
    if c.shape[0] > size * 3:          # 레티나 등 큰 입력이면 정수배 고속경로로 먼저 축소
        import cv2
        c = cv2.resize(c, (c.shape[1] // 2, c.shape[0] // 2), interpolation=cv2.INTER_AREA)
    # ★a_5112 P2: 상단 UI 패널(#nav)을 입력에서 잘라낸다.
    #   패널을 넓힌 뒤(u_5096) 캔버스 위 ~24%를 덮었고, 그 결과 같은 모델·같은 코드인데
    #   입력만 바뀌어 steer corr 가 학습프레임 0.992 → 라이브 0.011 로 무너졌다.
    #   실측 행밝기: 0~180행 0.87~0.97(패널) / 180행 이후 ~0.75(게임화면).
    #   학습·추론 '양쪽' 경로가 이 함수를 쓰므로 여기서 자르면 둘이 항상 일치하고,
    #   앞으로 UI 를 어떻게 고쳐도 모델 입력은 영향을 받지 않는다.
    c = c[int(round(c.shape[0] * UI_CROP_TOP)):, :, :]
    dev = device if device is not None else (
        'mps' if torch.backends.mps.is_available() else 'cpu')
    # ★capture.grab_canvas() 는 BGR view 를 준다(팬시 인덱싱 복사를 피하려고).
    #   채널 뒤집기는 GPU 에서 flip 으로 — CPU 복사 0.6ms 를 아낀다.
    t = torch.from_numpy(_np.ascontiguousarray(c)).to(dev)
    if bgr: t = torch.flip(t, dims=[2])
    t = t.permute(2, 0, 1)[None].float().div_(255)
    o = F.interpolate(t, size=(size, size), mode='bilinear',
                      align_corners=False, antialias=True)
    return o[0]
