#!/usr/bin/env python3
"""실주행 조건에서 오드를 측정한다 (u_5171).

★왜 이 스크립트가 따로 필요한가 — 두 번의 오보고가 여기서 나왔다:

1) 교사만 켜고(teach=1, 모델 off) 재면 차가 안 움직인다.
   이 게임은 교사가 '라벨'만 만들고 실제 가속·조향은 모델이 한다.
   정지 상태에서는 목표점이 안 변하니 조향이 안정적으로 보여서
   '직진 74%, 포화 19%' 같은 수치가 나온다. 실주행은 15%/61% 였다.

2) reset:1 로 리셋하면 auto.wp(경로)가 통째로 지워진다(game.js 571행).
   경로가 없으면 출발 핸들러가 'nowp' 로 즉시 반환하고,
   __parked 는 auto.on 일 때만 풀리므로(1670행) 차가 영영 주차 상태로 남는다.
   ⇒ rst 카운터로 __softReset() 을 부른다(dagger.py 와 같은 방식).

★판정은 이동거리로 한다. cross(차로이탈)·포화율은 보조지표일 뿐이다.
  실제로 cross 를 5.68→3.22m 로 줄인 수정이 이동거리를 685→420m 로
  악화시켰다. 지표를 목표로 삼으면 목적과 반대로 간다.

사용: python3 measure_drive.py [초] [라벨]
"""
import urllib.request,json,time,numpy as np,statistics as st,sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import torch, capture as C
from net import DriveNet
from dagger import preprocess, post
import gpu_guard; dev=gpu_guard.require_gpu()
_ck = torch.load(sys.argv[3] if len(sys.argv) > 3 else 'ode_v5.pt', map_location=dev)
# ★출력 차원은 체크포인트에서 읽는다. lane_off 보조목표를 쓴 모델은 out=4 라
#   out=3 으로 고정하면 로드가 실패한다(주행에는 앞 3개만 쓴다).
_out = [v for k, v in _ck.items() if k.endswith('.weight')][-1].shape[0]
net = DriveNet(out=_out).to(dev); net.load_state_dict(_ck); net.eval()
# ★rst 카운터로 소프트리셋 — reset:1 은 auto.wp 를 지워버려 경로가 사라지고
# 차가 parked 로 남는다(__parked 는 auto.on 일 때만 풀린다). dagger.py 와 같은 방식.
_rst=int(time.time())
post({'on':1,'force':1,'rst':_rst}); time.sleep(1)
post({'on':1,'force':1,'rst':_rst+1}); time.sleep(4)
sts=[];rows=[];p0=None;pmax=0
t0=time.time()
while time.time()-t0<float(sys.argv[1] if len(sys.argv)>1 else 60):
    try:
        d=json.load(urllib.request.urlopen('http://localhost:8901/tel',timeout=3))
        t=d.get('tch') or {}
        p=(d.get('prog') or 0)*11372
        if p0 is None: p0=p
        pmax=max(pmax,p)
        f=C.grab_canvas()
        if f is not None:
            x=preprocess(f,device=dev)[None]
            with torch.no_grad(): o=net(x)[0].cpu().numpy()
            post({'on':1,'force':1,'steer':float(o[0]),'thr':float(o[1]),'brake':float(o[2])})
        if t.get('ok'):
            sts.append(float(t['st']))
            if t.get('g2') and t.get('ct') is not None:
                rows.append((float(t['ct']),t['g2'],float(d.get('v') or 0)))
    except Exception: pass
a=np.array(sts)
print('%s: %d샘플 속도%.1f | 직진%.0f%% 포화%.0f%% | cross%.2f off%.2f | 이동 %.0fm'%(
  sys.argv[2] if len(sys.argv)>2 else '?',len(a),
  st.mean(r[2] for r in rows) if rows else 0,
  100*(abs(a)<0.2).mean(),100*(abs(a)>=0.99).mean(),
  st.mean(abs(r[0]) for r in rows) if rows else 0,
  st.mean(abs(r[1]['off']) for r in rows) if rows else 0, pmax-p0))
