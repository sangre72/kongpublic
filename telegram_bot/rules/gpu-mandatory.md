# GPU 사용 필수 (MUST — u_5100, 2026-09-15)

> **모델 추론·학습은 반드시 GPU(MPS)에서 돈다. CPU 폴백 금지.**
> 오너 지적: "gpu 사용하라고 몇번이 이야기해야해. 이것도 필수 조항으로 적어. 하네스로 묶어"

## 왜 확인이 아니라 강제인가
`torch.device('mps' if available else 'cpu')` 같은 조용한 폴백은 최악이다.
느린 채로 **되는 것처럼 보이고**, 그 상태로 잰 수치가 전부 오염된다.
실패는 시끄러워야 한다 — 못 쓰면 죽는다.

## 하네스
`games/seoul-drive/gpu_guard.py`
```python
from gpu_guard import require_gpu, assert_on_gpu
DEV = require_gpu()          # mps 아니면 SystemExit
assert_on_gpu(net)           # 가중치가 실제로 GPU 인지
assert_on_gpu(x)             # 입력 텐서도 GPU 인지
```
- `require_gpu()` — MPS 없으면 즉시 종료. `ALLOW_CPU=1` 일 때만 경고 후 진행(측정치 신뢰 불가).
- `assert_on_gpu()` — device.type != 'mps' 면 종료. **선언만 믿지 말고 실제 텐서를 본다.**

## 적용 대상
모델을 올리거나 추론/학습하는 모든 스크립트. 새 스크립트 작성 시 기본 포함.
현재 적용: `model_drive.py`(추론 루프).

## 실측 (2026-09-15, 이 기계)
```
MPS 추론          0.26 ms/frame   (256x256 DriveNet)
MPS matmul 2000^2 x50   204.9 ms
CPU matmul 2000^2 x50   284.5 ms
```

## 점검
`python3 -c "import torch;print(torch.backends.mps.is_available())"` → True 여야 한다.
추론이 느리면 **먼저 device 를 의심**한다: 가중치·입력 둘 다 `mps:0` 인지 실제로 찍어본다.
