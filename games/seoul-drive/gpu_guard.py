"""GPU 사용 강제 (u_5100 오너 지시: "gpu 사용하라고 몇번이 이야기해야해. 하네스로 묶어").

★이건 선택이 아니다. 모델 추론은 반드시 GPU(MPS)에서 돈다.
  CPU 로 조용히 떨어지면 느린 채로 '되는 것처럼' 보이고, 그 상태로 측정한
  수치가 전부 오염된다. 그래서 확인이 아니라 **강제**다 — 안 되면 죽는다.

실측(2026-09-15, 이 기계):
  MPS 추론 0.26 ms/frame   (256x256 DriveNet, weight·input 모두 mps:0)
  MPS matmul 2000x2000 x50 = 204.9ms / CPU = 284.5ms

사용:
  from gpu_guard import require_gpu
  DEV = require_gpu()          # mps 아니면 SystemExit
"""
import sys


def require_gpu(allow_cpu_env='ALLOW_CPU'):
    """MPS 장치를 돌려준다. 못 쓰면 즉시 종료한다(조용한 CPU 폴백 금지)."""
    import os
    import torch
    if torch.backends.mps.is_available():
        return torch.device('mps')
    if os.environ.get(allow_cpu_env) == '1':
        print('[gpu_guard] WARNING: %s=1 — CPU 로 진행(측정치 신뢰 불가)' % allow_cpu_env,
              file=sys.stderr)
        return torch.device('cpu')
    raise SystemExit(
        '[gpu_guard] GPU(MPS) 를 쓸 수 없다. 중단한다.\n'
        '  mps.is_available()=%s  mps.is_built()=%s  torch=%s\n'
        '  CPU 로 강행하려면 ALLOW_CPU=1 (측정치는 신뢰하지 말 것).'
        % (torch.backends.mps.is_available(), torch.backends.mps.is_built(),
           torch.__version__))


def assert_on_gpu(*tensors_or_modules):
    """입력/가중치가 실제로 GPU 에 있는지 확인한다. 하나라도 cpu 면 종료."""
    import torch
    for i, o in enumerate(tensors_or_modules):
        if isinstance(o, torch.nn.Module):
            p = next(o.parameters(), None)
            dev = None if p is None else p.device
        else:
            dev = getattr(o, 'device', None)
        if dev is not None and dev.type != 'mps':
            raise SystemExit('[gpu_guard] #%d 이 %s 에 있다. GPU 아니면 중단.' % (i, dev))
    return True
