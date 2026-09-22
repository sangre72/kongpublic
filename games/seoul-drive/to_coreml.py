#!/usr/bin/env python3
"""오드(DriveNet .pt) → CoreML .mlpackage (u_5532 GPU 상주 파이프라인용, 2026-09-22).
사용: python3 to_coreml.py ode_v2.pt out.mlpackage   — 입력 img(1,3,256,256 float 0~1, preprocess 크롭 후), v(1,1 = 속도/30)
★깨진 tensorflow 가 coremltools import 를 막으므로 sys.modules 로 차단한다. 검증: torch 출력과 비교, ms/frame 출력."""
import sys, time; sys.modules['tensorflow'] = None
import coremltools as ct, torch, numpy as np
from net import DriveNet
src, dst = sys.argv[1], sys.argv[2]
sd = torch.load(src, map_location='cpu'); out = sd[list(sd)[-1]].shape[0]
net = DriveNet(out=out, vin=any(k.startswith('hv.') for k in sd), in_ch=int(sd['f.0.weight'].shape[1])); net.load_state_dict(sd); net.eval()
x = torch.rand(1, net.in_ch if hasattr(net, 'in_ch') else 3, 256, 256); v = torch.rand(1, 1)
tr = torch.jit.trace(net, (x, v))
m = ct.convert(tr, inputs=[ct.TensorType(name='img', shape=x.shape), ct.TensorType(name='v', shape=v.shape)], compute_units=ct.ComputeUnit.ALL, minimum_deployment_target=ct.target.macOS15)
m.save(dst)
ref = net(x, v).detach().numpy(); o = m.predict({'img': x.numpy(), 'v': v.numpy()}); k = list(o)[0]
t = time.time()
for _ in range(50): m.predict({'img': x.numpy(), 'v': v.numpy()})
print({'out': dst, 'max_abs_diff': float(np.abs(o[k].ravel() - ref.ravel()).max()), 'ms_per_frame': round((time.time() - t) / 50 * 1000, 2)})
