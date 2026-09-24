#!/usr/bin/env python3
"""오드(DriveNet .pt) → CoreML .mlpackage (u_5532 GPU 상주 파이프라인용, 2026-09-22).
사용: python3 to_coreml.py ode_v2.pt out.mlpackage   — 입력 img(1,3,256,256 float 0~1, preprocess 크롭 후), v(1,1 = 속도/30)
★깨진 tensorflow 가 coremltools import 를 막으므로 sys.modules 로 차단한다. 검증: torch 출력과 비교, ms/frame 출력."""
import sys, os, time; sys.modules['tensorflow'] = None
import coremltools as ct, torch, numpy as np
from net import DriveNet, vdim_of
src, dst = sys.argv[1], sys.argv[2]
sd = torch.load(src, map_location='cpu'); out = sd[list(sd)[-1]].shape[0]
if os.environ.get('BEV') == '1':   # C: BevNet(3×64×64 로짓)
    from train_bev import BevNet
    net = BevNet(); net.load_state_dict(sd); net.eval(); x = torch.rand(1, 3, 256, 256); v = torch.rand(1, 1)
    class _B(torch.nn.Module):
        def __init__(s, n): super().__init__(); s.n = n
        def forward(s, x, v): return s.n(x)
    net = _B(net).eval()
if os.environ.get('BEV') != '1':
    net = DriveNet(out=out, vin=any(k.startswith('hv.') for k in sd), in_ch=int(sd['f.0.weight'].shape[1]), vdim=vdim_of(sd)); net.load_state_dict(sd); net.eval()
    x = torch.rand(1, net.in_ch if hasattr(net, 'in_ch') else 3, 256, 256); v = torch.rand(1, vdim_of(sd))
if os.environ.get('RAW') == '1':   # a_5598 기하 헤드: 활성화(tanh/sigmoid) 없이 로짓 그대로 내보낸다(train_geo raw=True 와 일치)
    class _Raw(torch.nn.Module):
        def __init__(s, n): super().__init__(); s.n = n
        def forward(s, x, v): return s.n(x, v, raw=True)
    net = _Raw(net).eval()
tr = torch.jit.trace(net, (x, v))
# ★CU: env CU=ALL|CPU_AND_GPU|CPU_ONLY (2026-09-23 a_5577). ANE 컴파일(E5RT MILCompilerForANE) 실패 시 CPU_AND_GPU 로 자동 폴백.
CU = os.environ.get('CU', 'ALL')
def conv(cu):
    return ct.convert(tr, inputs=[ct.TensorType(name='img', shape=x.shape), ct.TensorType(name='v', shape=v.shape)], compute_units=getattr(ct.ComputeUnit, cu), minimum_deployment_target=ct.target.macOS15)
try:
    m = conv(CU); m.save(dst); m.predict({'img': x.numpy(), 'v': v.numpy()})
except Exception as e:
    if CU == 'CPU_AND_GPU': raise
    print({'ane_fail': str(e)[:160], 'fallback': 'CPU_AND_GPU'}); CU = 'CPU_AND_GPU'
    m = conv(CU); m.save(dst)
    m = ct.models.MLModel(dst, compute_units=ct.ComputeUnit.CPU_AND_GPU)
ref = net(x, v).detach().numpy(); o = m.predict({'img': x.numpy(), 'v': v.numpy()}); k = list(o)[0]
t = time.time()
for _ in range(50): m.predict({'img': x.numpy(), 'v': v.numpy()})
print({'out': dst, 'cu': CU, 'max_abs_diff': float(np.abs(o[k].ravel() - ref.ravel()).max()), 'ms_per_frame': round((time.time() - t) / 50 * 1000, 2)})
