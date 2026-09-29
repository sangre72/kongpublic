#!/usr/bin/env python3
"""u_5770 RL pivot — SMALLEST target: lane keeping on one straight scoped section.
Model steers ONLY; the rule keeps speed and Layer-1 braking (we never post thr/brake).

Per owner spec:
 (1) ACTION = target lateral offset (the interface the controller already consumes: mode=2 lp),
     continuous, RATE-LIMITED. Not raw steer - raw steer was the u_5757 failure mode.
 (2) STATE  = the pixel input we already use + current speed (same preprocess as every model).
 (3) REWARD = -|e_y| - w*|d lp| + progress, episode ends on off-road/crash. w swept, not guessed.
 (4) INIT   = best existing perception weights (fine-tune, not scratch) - perception already
     reads lanes at IoU .92, so we are learning the CONTROL, not the vision.
 (5) 300s episode harness, page lock, park trap (inherited from the shell wrapper).
 (6) reports model-driving share every episode (u_5769 lesson: a blend is not a result).
"""
import sys, os, json, time, math, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, torch, torch.nn as nn
import urllib.request
from net import DriveNet
import gpu_guard
CTL, TEL = 'http://localhost:8901/ctl', 'http://localhost:8901/tel'
DEV = gpu_guard.require_gpu()
LP_MAX = float(os.environ.get('LP_MAX', '1.5'))   # u_5770: was 3.0 = wider than the lane; policy self-terminated      # action range, metres of lateral offset
ENT_C = float(os.environ.get('ENT_C', '0.01'))   # u_5771 entropy coefficient
LP_RATE = float(os.environ.get('LP_RATE_RL', '2.0')) # m/s rate limit on the commanded offset
def tel():
    try:
        with urllib.request.urlopen(TEL, timeout=4) as r: return json.load(r)
    except Exception: return None
def post(d):
    try:
        req = urllib.request.Request(CTL, data=json.dumps(d).encode(),
                                     headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=4).read()
    except Exception: pass
class Policy(nn.Module):
    """Gaussian over ONE continuous action (target lateral offset), plus a value head.
    Trunk is the perception net's conv stack so we inherit lane reading."""
    def __init__(self, init_path=None, k=5):
        super().__init__()
        self.k = k
        base = DriveNet(out=12, vin=True, vdim=1, in_ch=3 * k)
        if init_path and os.path.exists(init_path):
            sd = torch.load(init_path, map_location='cpu')
            own = base.state_dict()
            ok = {kk: v for kk, v in sd.items() if kk in own and own[kk].shape == v.shape}
            base.load_state_dict(ok, strict=False)
            self.loaded = len(ok)
        else: self.loaded = 0
        self.f = base.f; self.h = base.h
        self.mu = nn.Sequential(nn.Linear(256 + 1, 96), nn.ReLU(), nn.Linear(96, 1), nn.Tanh())
        self.v  = nn.Sequential(nn.Linear(256 + 1, 96), nn.ReLU(), nn.Linear(96, 1))
        self.log_std = nn.Parameter(torch.tensor([-1.0]))
    def feat(self, x, v):
        z = self.h[0:3](self.f(x))
        return torch.cat([z, v.reshape(-1, 1)], 1)
    def forward(self, x, v):
        zc = self.feat(x, v)
        return self.mu(zc) * LP_MAX, self.v(zc)

def reward(prev, cur, w, dlp):
    """-(|e_y|) - w*|d lp| + progress ; terminate on off-road or crash. All from /tel."""
    g = cur.get('geo') or {}
    ey = g.get('ey')
    ey = abs(float(ey)) if isinstance(ey, (int, float)) else 2.0
    dprog = (float(cur.get('prog') or 0) - float(prev.get('prog') or 0)) * 100.0
    cr = int(cur.get('cr') or 0) - int(prev.get('cr') or 0)
    # u_5770 fix: /tel has no 'offroad' key (measured None), so the old test reduced to ey>2.5.
    #   With LP_MAX=3.0 the policy could command itself out of bounds and self-terminate in ~11
    #   steps, which teaches nothing. Use the game's own lane-departure counter, and keep an ey
    #   guard well outside the action range.
    _crk = cur.get('crk') or {}
    _dep = sum(v for k, v in _crk.items() if '이탈' in str(k)) if isinstance(_crk, dict) else 0
    _pdep = prev.get('_dep', 0)
    off = 1 if (_dep > _pdep or ey > 3.5) else 0
    cur['_dep'] = _dep
    r = -ey - w * abs(dlp) + 3.0 * dprog
    done = bool(cr > 0 or off)
    if done: r -= 10.0
    return r, done
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--init', default=None); ap.add_argument('--out', default='ode_rl_lat.pt')
    ap.add_argument('--iters', type=int, default=20); ap.add_argument('--steps', type=int, default=250)
    ap.add_argument('--w', type=float, default=0.5); ap.add_argument('--k', type=int, default=5)
    ap.add_argument('--lr', type=float, default=3e-5)
    a = ap.parse_args()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import capture as C   # module-level grab_canvas(), not a class
    from net import preprocess
    pol = Policy(a.init, a.k).to(DEV); gpu_guard.assert_on_gpu(pol)
    # u_5771: log_std needs its OWN lr. Measured: at lr 3e-5, four updates cap log_std movement at
    #   0.00012 => std changes by 0.01%. It was never 'pinned by a bug' - it was rate-limited. The
    #   policy gradient is healthy (~2.2 after return normalisation) so only the std lr is raised.
    _std_lr = float(os.environ.get('STD_LR', '1e-2'))
    _others = [p_ for n_, p_ in pol.named_parameters() if n_ != 'log_std']
    opt = torch.optim.Adam([{'params': _others, 'lr': a.lr},
                            {'params': [pol.log_std], 'lr': _std_lr}])
    print(json.dumps({'init': a.init, 'loaded_tensors': pol.loaded, 'w': a.w,
                      'action': 'lateral_offset', 'lp_max': LP_MAX, 'lp_rate': LP_RATE}), flush=True)
    best = -1e9
    ROUTE = (os.environ.get('RL_FROM', ''), os.environ.get('RL_TO', ''))
    def reset_episode():
        """u_5770 fix2: the loop never reset between iterations, so every episode STARTED wherever
        the previous one crashed (measured: page idling at ey=-1.385 with the car stopped). One bad
        ending then poisoned all later iterations - that is the w=0.1 collapse (10 of 15 episodes
        died in <=1 step). Reload the route per episode so each starts from a clean pose."""
        post({'on': 0, 'force': 0, 'tgt': 0, 'mode': 1, 'lp': 0.0, 'vT': -1})
        import subprocess
        url = 'http://localhost:8901/index.html?go=1&lab=1'
        if ROUTE[0] and ROUTE[1]: url += f'&from={ROUTE[0]}&to={ROUTE[1]}'
        try:
            subprocess.run(['bash', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reload.sh'),
                            url, '90'], capture_output=True, text=True, timeout=120)
        except Exception: pass
        for _ in range(40):
            d = tel()
            if d and float(d.get('v') or 0) > 0.5: return d
            time.sleep(0.5)
        return tel()

    for it in range(a.iters):
        d0 = reset_episode()
        if not d0:
            print(json.dumps({'iter': it, 'abort': 'no telemetry'}), flush=True); break
        prev = d0; buf_x = []; buf_v = []; buf_a = []; buf_lp = []; buf_r = []; buf_val = []
        ep_r = 0.0; lp_cmd = 0.0; drive_n = 0; tot_n = 0; t_last = time.time()
        fbuf = []
        for _ in range(a.steps):
            f = C.grab_canvas()
            if f is None: time.sleep(0.02); continue
            x = preprocess(f, device=DEV)[None]
            fbuf.append(x); fbuf[:] = fbuf[-a.k:]
            while len(fbuf) < a.k: fbuf.insert(0, fbuf[0])
            xin = torch.cat(fbuf, 1)
            vnow = float(prev.get('v') or 0.0)
            vt = torch.tensor([[vnow / 30.0]], dtype=torch.float32, device=DEV)
            with torch.no_grad():
                mu, val = pol(xin, vt)
                std = pol.log_std.exp()
                act = torch.normal(mu, std)
                logp = (-0.5 * ((act - mu) / std) ** 2 - pol.log_std - 0.5 * math.log(2 * math.pi)).sum()
            raw = float(act.item())
            now = time.time(); dt = max(1e-3, now - t_last); t_last = now
            lim = LP_RATE * dt
            new_cmd = max(lp_cmd - lim, min(lp_cmd + lim, raw))   # (1) rate-limited
            dlp = new_cmd - lp_cmd; lp_cmd = new_cmd
            # model steers only; speed + Layer-1 stay with the rule (no thr/brake posted)
            post({'on': 1, 'force': 1, 'tgt': 1, 'mode': 2, 'lp': lp_cmd, 'ld': -1, 'vT': -1})
            tot_n += 1; drive_n += 1
            time.sleep(0.05)
            cur = tel()
            if not cur: continue
            r, done = reward(prev, cur, a.w, dlp)
            buf_x.append(xin.detach().cpu()); buf_v.append(vt.detach().cpu()); buf_a.append(raw)
            buf_lp.append(float(logp.item())); buf_r.append(r); buf_val.append(float(val.item()))
            ep_r += r; prev = cur
            if done: break
        post({'on': 0, 'force': 0, 'tgt': 0, 'mode': 1, 'lp': 0.0, 'vT': -1})
        n = len(buf_x)
        if n < 32:
            print(json.dumps({'iter': it, 'skip': 'few steps', 'n': n}), flush=True); continue
        R = np.zeros(n, np.float32); acc = 0.0
        for i in range(n - 1, -1, -1): acc = buf_r[i] + 0.99 * acc; R[i] = acc
        # u_5771 ROOT CAUSE of the flat curve: returns reach -110 (250 steps x ~-1.2, gamma .99), so
        #   the value head starting near 0 gives an initial value loss ~6700. That term dominated the
        #   update - measured policy grad norm 115-605 vs log_std grad 0.10-0.26 (~1000x). Neither the
        #   policy nor the std could move. Normalise returns so the value loss is O(1).
        Rt = torch.tensor(R, device=DEV)
        r_mu, r_sd = Rt.mean(), Rt.std() + 1e-6
        Rt = (Rt - r_mu) / r_sd
        Vt = torch.tensor(buf_val, dtype=torch.float32, device=DEV)
        adv = Rt - Vt; adv = (adv - adv.mean()) / (adv.std() + 1e-6)
        X = torch.cat(buf_x).to(DEV); V = torch.cat(buf_v).to(DEV)
        A = torch.tensor(buf_a, dtype=torch.float32, device=DEV).unsqueeze(1)
        OLD = torch.tensor(buf_lp, dtype=torch.float32, device=DEV)
        gn_pi = []; gn_std = []
        for _ in range(4):
            mu, val = pol(X, V); std = pol.log_std.exp()
            lp_new = (-0.5 * ((A - mu) / std) ** 2 - pol.log_std - 0.5 * math.log(2 * math.pi)).sum(1)
            ratio = (lp_new - OLD).exp()
            l_pi = -torch.min(ratio * adv, ratio.clamp(0.8, 1.2) * adv).mean()
            l_v = ((val.squeeze(1) - Rt) ** 2).mean()
            # u_5771: entropy bonus (was absent). Also record grad norms so a pinned std is visible.
            ent = (0.5 + 0.5 * math.log(2 * math.pi) + pol.log_std).sum()
            loss = l_pi + 0.5 * l_v - ENT_C * ent
            opt.zero_grad(); loss.backward()
            _gp = torch.nn.utils.clip_grad_norm_([p_ for n_, p_ in pol.named_parameters() if n_ != 'log_std'], 1.0)
            _gs = float(pol.log_std.grad.norm()) if pol.log_std.grad is not None else 0.0
            gn_pi.append(float(_gp)); gn_std.append(_gs)
            opt.step()
        g = prev.get('geo') or {}
        out = dict(iter=it, n=n, ep_r=round(ep_r, 1), mean_r=round(ep_r / n, 3),
                   ey_end=(round(abs(float(g['ey'])), 3) if isinstance(g.get('ey'), (int, float)) else None),
                   prog=round(float(prev.get('prog') or 0) * 100, 1),
                   drive_share=round(drive_n / max(1, tot_n), 3), std=round(float(pol.log_std.exp().item()), 4),
                   gn_pi=round(float(np.mean(gn_pi)), 4) if gn_pi else None, gn_std=round(float(np.mean(gn_std)), 6) if gn_std else None)
        if ep_r > best: best = ep_r; torch.save(pol.state_dict(), a.out); out['saved'] = True
        print(json.dumps(out), flush=True)
    print(json.dumps({'done': a.out, 'best_ep_r': round(best, 1)}), flush=True)
if __name__ == '__main__': main()
