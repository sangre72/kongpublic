#!/usr/bin/env python3
"""오드 강화학습 (PPO) — u_5172 오너 지시 "학습하는 방향으로 진행해".

★왜 BC 를 접고 RL 인가 (이 세션 실측 근거):
  · BC 는 교사를 복제할 뿐 넘어설 수 없다. 지금 교사조차 11,372m 를 못 간다.
  · v6~v14 까지 9개를 만들었는데 전부 v5 보다 못했다. 가중치·데이터구성·
    보조목표를 다 바꿔봤지만 BC 틀 안에서는 개선이 안 나왔다.
  · 오드(20%)가 교사(24~27%)보다 조향이 안정적이다 — 복제할 대상이
    이미 한계다.

★보상 재조정(reward.py, 실측 기반):
  기존 W_PROGRESS=100 이면 완주해도 -2180 점, 정지는 0 점이라
  PPO 가 '안 움직이기'를 배운다. 3000 으로 올려 완주 +2720 > 정지 0.

★행동공간: 연속 3차원(steer, thr, brake). 가우시안 정책.
  bc_final.pt(=ode_v5.pt 계열)에서 파인튜닝한다 — 밑바닥부터는
  측정 61.5 에피소드/시간 기준 162시간이 걸린다.

사용: python3 ppo.py --init ode_v5.pt --iters 50 --steps 512
"""
import argparse, json, os, time, sys
import numpy as np
import torch, torch.nn as nn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gpu_guard, reward as R, capture as C
from net import DriveNet
from dagger import preprocess, post

DEV = gpu_guard.require_gpu()
TEL = 'http://localhost:8901/tel'


def tel():
    import urllib.request
    try:
        return json.load(urllib.request.urlopen(TEL, timeout=3))
    except Exception:
        return None


def reset_episode():
    """★소프트리셋은 prog=1.0 고착 시 안 풀린다(실측). ?go=1 새로고침만 확실하다.
       그냥 새로고침하면 wpLen=0 이 되어 진행률이 영영 안 오른다."""
    import subprocess
    here = os.path.dirname(os.path.abspath(__file__))
    subprocess.run(['bash', here + '/reload.sh',
                    'http://localhost:8901/index.html?go=1'],
                   capture_output=True, timeout=120)
    for _ in range(40):
        time.sleep(1)
        d = tel()
        if d and (d.get('wpLen') or 0) > 100 and not d.get('parked'):
            post({'on': 1, 'force': 1})
            return d
    return tel()


class Policy(nn.Module):
    """BC 가중치를 그대로 쓰는 평균 + 학습되는 로그표준편차 + 가치함수."""
    def __init__(self, backbone, out=3):
        super().__init__()
        self.net = backbone
        self.log_std = nn.Parameter(torch.full((out,), -1.2))
        self.v = nn.Sequential(nn.Linear(128 * 6 * 6, 128), nn.ReLU(), nn.Linear(128, 1))

    def feat(self, x):
        return self.net.f(x).flatten(1)

    def forward(self, x):
        mu = self.net(x)[:, :3]
        return mu, self.log_std.exp().clamp(0.02, 0.5), self.v(self.feat(x)).squeeze(-1)


def act(pol, frame):
    x = preprocess(frame, device=DEV)[None]
    with torch.no_grad():
        mu, std, val = pol(x)
    dist = torch.distributions.Normal(mu, std)
    a = dist.sample()
    lp = dist.log_prob(a).sum(-1)
    a0 = a[0].cpu().numpy()
    return (float(np.clip(a0[0], -1, 1)),
            float(np.clip(a0[1], 0, 1)),
            float(np.clip(a0[2], 0, 1))), float(lp), float(val)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--init', default='ode_v5.pt')
    ap.add_argument('--iters', type=int, default=30)
    ap.add_argument('--steps', type=int, default=512)
    ap.add_argument('--out', default='ode_rl.pt')
    a = ap.parse_args()

    ck = torch.load(a.init, map_location=DEV)
    out = [v for k, v in ck.items() if k.endswith('.weight')][-1].shape[0]
    bb = DriveNet(out=out).to(DEV); bb.load_state_dict(ck)
    pol = Policy(bb).to(DEV)
    gpu_guard.assert_on_gpu(pol)
    opt = torch.optim.Adam(pol.parameters(), 3e-5)

    print(json.dumps({'init': a.init, 'W_PROGRESS': R.W_PROGRESS}), flush=True)
    R_ = 11372.0
    best = -1e9

    for it in range(a.iters):
        d0 = reset_episode()
        if not d0:
            print(json.dumps({'iter': it, 'abort': 'no telemetry'}), flush=True); break
        prev, t0 = d0, time.time()
        X, A, LP, VL, RW = [], [], [], [], []
        ep_r = 0.0; m0 = (prev.get('prog') or 0) * R_

        for _ in range(a.steps):
            f = C.grab_canvas()
            if f is None:                      # 사고 오버레이 등 — 데이터 아님
                time.sleep(0.02); continue
            (st, th, br), lp, val = act(pol, f)
            post({'on': 1, 'force': 1, 'steer': st, 'thr': th, 'brake': br})
            time.sleep(0.05)
            cur = tel()
            if not cur:
                continue
            r, _ = R.step_reward(prev, cur, 0.05)
            X.append(f); A.append([st, th, br]); LP.append(lp); VL.append(val); RW.append(r)
            ep_r += r; prev = cur

        if len(X) < 32:
            print(json.dumps({'iter': it, 'skip': 'too few steps', 'n': len(X)}), flush=True)
            continue

        # ---- GAE 없이 단순 리턴(구현 위험 최소화) ----
        rets = np.zeros(len(RW), np.float32); run = 0.0
        for i in reversed(range(len(RW))):
            run = RW[i] + 0.99 * run; rets[i] = run
        rets_t = torch.tensor(rets, device=DEV)
        vals_t = torch.tensor(VL, dtype=torch.float32, device=DEV)
        adv = rets_t - vals_t
        adv = (adv - adv.mean()) / (adv.std() + 1e-6)
        old_lp = torch.tensor(LP, dtype=torch.float32, device=DEV)
        acts = torch.tensor(np.array(A), dtype=torch.float32, device=DEV)

        for _ in range(4):                       # PPO epoch
            idx = np.random.permutation(len(X))
            for s in range(0, len(idx), 64):
                b = idx[s:s+64]
                xb = torch.stack([preprocess(X[i], device=DEV) for i in b])
                mu, std, v = pol(xb)
                dist = torch.distributions.Normal(mu, std)
                lp = dist.log_prob(acts[b]).sum(-1)
                ratio = (lp - old_lp[b]).exp()
                l_pi = -torch.min(ratio * adv[b],
                                  ratio.clamp(0.8, 1.2) * adv[b]).mean()
                l_v = ((v - rets_t[b]) ** 2).mean()
                loss = l_pi + 0.5 * l_v - 0.001 * dist.entropy().sum(-1).mean()
                opt.zero_grad(); loss.backward()
                nn.utils.clip_grad_norm_(pol.parameters(), 0.5)
                opt.step()

        dm = (prev.get('prog') or 0) * R_ - m0
        print(json.dumps({'iter': it, 'reward': round(ep_r, 1), 'dist_m': round(dm),
                          'crashes': prev.get('cr'), 'steps': len(X),
                          'secs': round(time.time() - t0, 1)}), flush=True)
        if ep_r > best:
            best = ep_r
            torch.save(pol.net.state_dict(), a.out)   # 주행에 쓸 건 backbone 뿐


if __name__ == '__main__':
    main()
