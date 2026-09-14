"""CNN 비전 자율주행 — 진짜 신경망 버전.

★왜 다시 만들었나(u_4900/4901 오너 지적, 맞는 지적):
  이전 버전은 "광선 11개를 사람이 설계하고, 그 가중치 27개를 튜닝"하는 구조였다.
  그건 상수를 맞춘 룰베이스지 학습된 비전이 아니다. JSON 673바이트로 표현된다는 것
  자체가 증거다. 파라미터가 1000억이면 JSON으로 못 쓴다 — 가중치는 바이너리 텐서다.

이 버전:
  - 입력 = 화면 픽셀 그대로(84x84x3 다운샘플). 사람이 만든 특징 0개.
  - 신경망이 스스로 '무엇을 볼지'를 conv 필터로 학습한다.
  - 출력 = 조향/가속/제동 3채널.
  - 저장 = .pt 바이너리(state_dict). JSON 아님.

학습 방식: CEM(Cross-Entropy Method) — 역전파 없이 정책 탐색.
  게임에 정답 라벨이 없고 보상만 있으므로 강화학습 계열이 맞다.
  DQN/PPO 대비 구현이 단순하고 CPU/MPS에서 안정적이다.

실측(2026-09-14, M-series MPS): 추론 0.27ms/frame — 20ms 예산의 1.4%.
"""
import time, os, math, json
import numpy as np
import torch
import torch.nn as nn
import Quartz.CoreGraphics as CG

DEV = 'mps' if torch.backends.mps.is_available() else 'cpu'
CKPT = os.path.expanduser('~/.kongbot_drive_cnn.pt')

# ---------- 캡처 ----------
def grab(x, y, w, h):
    img = CG.CGWindowListCreateImage(
        CG.CGRectMake(x/2.0, y/2.0, w/2.0, h/2.0),
        CG.kCGWindowListOptionOnScreenOnly, CG.kCGNullWindowID,
        CG.kCGWindowImageDefault)
    if img is None: return None
    W = CG.CGImageGetWidth(img); H = CG.CGImageGetHeight(img)
    bpr = CG.CGImageGetBytesPerRow(img)
    buf = np.frombuffer(CG.CGDataProviderCopyData(CG.CGImageGetDataProvider(img)),
                        dtype=np.uint8)
    return buf[:H*bpr].reshape(H, bpr//4, 4)[:, :W, [2, 1, 0]]

def find_canvas():
    """상태칩 색으로 캔버스 원점 자동 탐지(창 크기·iframe 변화에 안전)."""
    wide = grab(0, 300, 900, 1100)
    if wide is None: return None
    r = wide[:,:,0].astype(int); g = wide[:,:,1].astype(int); b = wide[:,:,2].astype(int)
    chip = ((abs(r-0x2f)<46)&(abs(g-0x7b)<46)&(abs(b-0xff)<46)) | \
           ((abs(r-0x00)<46)&(abs(g-0xd2)<52)&(abs(b-0x6a)<52)) | \
           ((abs(r-0xff)<46)&(abs(g-0x2d)<52)&(abs(b-0x2d)<52))
    ys, xs = np.nonzero(chip)
    if len(ys) < 30: return None
    top = int(ys.min()); m = ys < top+24
    return (int(xs[m].min()), 300+top)

# ---------- 키 ----------
KEY = {'up':126,'down':125,'left':123,'right':124}
_down = set()
def key(k, on):
    if on == (k in _down): return
    CG.CGEventPost(CG.kCGHIDEventTap, CG.CGEventCreateKeyboardEvent(None, KEY[k], on))
    (_down.add if on else _down.discard)(k)
def release_all():
    for k in list(_down): key(k, False)

# ---------- 신경망 ----------
class DriveNet(nn.Module):
    """화면 → 조작. 사람이 설계한 특징(광선·바닥색) 일절 없음.
       conv 필터가 '도로 가장자리/장애물/내비선'을 스스로 찾아내야 한다."""
    def __init__(self):
        super().__init__()
        self.f = nn.Sequential(
            nn.Conv2d(3, 16, 5, 3), nn.ReLU(),      # 84 -> 27
            nn.Conv2d(16, 32, 3, 2), nn.ReLU(),     # 27 -> 13
            nn.Conv2d(32, 64, 3, 2), nn.ReLU(),     # 13 -> 6
            nn.AdaptiveAvgPool2d(3), nn.Flatten(),
            nn.Linear(64*9, 64), nn.ReLU(),
            nn.Linear(64, 3),                        # steer, throttle, brake
        )
    def forward(self, x):
        return torch.tanh(self.f(x))

def get_flat(m):
    return torch.cat([p.detach().reshape(-1) for p in m.parameters()]).cpu().numpy()

def set_flat(m, v):
    i = 0
    with torch.no_grad():
        for p in m.parameters():
            n = p.numel()
            p.copy_(torch.tensor(v[i:i+n], dtype=p.dtype, device=p.device).view_as(p))
            i += n

# ---------- 한 판 ----------
def preprocess(f):
    """화면 → 신경망 입력.

    ★치명적 결함 수정(2026-09-14 실측): 기존 `f[::7,::7]`는 7픽셀마다 하나만
      뽑는 방식이라 폭 2px인 차선을 통째로 건너뛰었다.
      측정: 원본 흰 픽셀(차선) 764개 → 다운샘플 후 0개.
      즉 신경망은 차선을 한 번도 본 적이 없다. 차선을 못 지킨 게 당연하다.
    → 면적 평균(area-average)으로 줄인다. 가는 선도 회색으로 남아 살아남는다.
    """
    H, W = f.shape[:2]
    k = 7
    h2, w2 = H//k, W//k
    blk = f[:h2*k, :w2*k].reshape(h2, k, w2, k, 3).mean(axis=(1, 3))   # 면적 평균
    s = blk[:84, :84]
    if s.shape[0] < 84 or s.shape[1] < 84:
        s = np.pad(s, ((0, max(0, 84-s.shape[0])), (0, max(0, 84-s.shape[1])), (0, 0)))
    t = torch.from_numpy(np.ascontiguousarray(s)).float().div_(255.)
    return t.permute(2, 0, 1).unsqueeze(0).to(DEV)

def episode(net, box, seconds=25):
    import subprocess
    subprocess.run(['open','-a','Google Chrome'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.4)
    got = find_canvas()
    if got: box = (got[0], got[1], box[2], box[3])
    bx, by, bw, bh = box
    sw, sh = bw//2, bh//2
    t0 = time.time(); frames = 0; inb = 0
    crashes = 0; last = 0.0; moved = 0.0; clears = 0; fails = 0
    prev = None; miss = 0; prog = 0.0; crash_frames = 0
    try:
        while time.time() - t0 < seconds:
            ts = time.time()
            a = grab(bx, by, sw, sh)
            if a is None:
                miss += 1
                if miss > 40: break
                time.sleep(.05); continue
            miss = 0
            f = a.astype(np.int16)
            with torch.no_grad():
                out = net(preprocess(a))[0].cpu().numpy()
            steer, thr, brk = float(out[0]), float(out[1]), float(out[2])
            key('left',  steer < -0.15)
            key('right', steer >  0.15)
            key('down',  brk > 0.35)
            key('up',    thr > 0.0 and brk <= 0.35)
            # 보상 신호는 화면에서만 읽는다(게임 변수 안 씀)
            # ★사고 신호 재설계(u_4913 오너 지적).
            #   기존: 0.8초에 1회만 카운트 → 건물에 붙어 계속 긁혀도 벌점이 거의 안 붙고,
            #   그 사이 moved 보상은 계속 쌓여서 '사고치며 전진'이 이득이 됐다.
            #   → 붉은 화면이 떠 있는 '시간'을 그대로 벌점으로 센다(회전 충돌 = 계속 벌점).
            # ★사고 램프를 본다(u_4914). 전체화면 붉은 번쩍임은 140ms뿐이라
            #   샘플링으로는 120프레임 중 4프레임(3%)만 잡혔다 — 사실상 안 보였다.
            #   게임이 칩 옆에 1.2초간 켜두는 '사고 표시등'을 직접 읽는다.
            # ★검출기 복원(2026-09-14): 전체화면 붉은 오버레이 방식이 실제로 작동했다
            #   (126판에서 사고 1~17건 기록). 140ms/20ms = 7프레임에 걸쳐 보이므로
            #   0.02초 샘플링으로 충분히 잡힌다 — 오너 지적이 옳았다.
            #   내가 새로 만든 '램프' 검출기는 아직 브라우저에 없는 UI를 읽어 0을 냈다.
            red = float(f[:,:,0].mean() - f[:,:,2].mean())
            lamp = f[8:14, 64:70].reshape(-1,3).mean(axis=0)
            lit = (red > 20) or (lamp[0] > 120 and lamp[0] > lamp[1]+60 and lamp[0] > lamp[2]+60)
            if lit:
                crash_frames += 1
                if ts-last > .8:
                    crashes += 1; last = ts
            chip = f[8:14, 8:14].reshape(-1,3).mean(axis=0)   # 칩 사각형 중앙
            if chip[1] > chip[0]+40 and chip[1] > chip[2]+40:
                clears += 1; break
            if chip[0] > chip[1]+60 and chip[0] > chip[2]+60:
                fails += 1; break
            bar = f[8:14, 21:58]                              # 막대 내부(칩과 안 겹치게)
            prog = float(((bar[:,:,0]>150)&(bar[:,:,1]>120)&(bar[:,:,2]<110)).mean())
            small = f[::8, ::8, 1]
            if prev is not None: moved += float(np.abs(small-prev).mean())
            prev = small
            frames += 1
            dt = time.time()-ts
            if dt <= .020: inb += 1
            if dt < .020: time.sleep(.020-dt)
    finally:
        release_all()
    # ★보상 재설계(실측: 123판 전부 prog=0).
    #   moved(화면 흐름량)가 수천 단위라 prog(0~1)를 압도했다.
    #   → 아무 데나 빨리 달리는 게 최적해가 되어 목적지로 갈 이유가 없었다.
    #   목적지 접근을 주 보상으로, 이동량은 보조(정지 방지)로 축소한다.
    # 사고 중 이동은 보상하지 않는다 — 충돌하며 밀고 나가는 전략 차단
    crash_ratio = crash_frames / max(1, frames)
    clean = max(0.0, 1.0 - crash_ratio*2.0)
    score = prog*8000. + moved*0.15*clean - crashes*260. - crash_frames*6. + clears*6000.
    return dict(score=score, prog=round(prog,3), moved=round(moved,1),
                crashes=crashes, crash_frames=crash_frames,
                crash_ratio=round(crash_ratio,3),
                clears=clears, fails=fails, frames=frames,
                budget=round(inb/max(1,frames),3),
                fps=round(frames/max(1e-6,time.time()-t0),1))

# ---------- CEM 학습 ----------
def train(box, iters=12, pop=8, elite=3, seconds=22, sigma=0.25):
    net = DriveNet().to(DEV)
    if os.path.exists(CKPT):
        try:
            net.load_state_dict(torch.load(CKPT, map_location=DEV)); print('resumed', flush=True)
        except Exception: pass
    mu = get_flat(net); n = mu.size
    print(json.dumps({'params': int(n), 'device': DEV}), flush=True)
    best_score = -1e18; stall = 0
    for it in range(iters):
        cands, scores = [], []
        for k in range(pop):
            v = mu + np.random.randn(n).astype(np.float32)*sigma
            set_flat(net, v)
            r = episode(net, box, seconds)
            if r['frames'] < 40:
                r['invalid'] = True
            else:
                cands.append(v); scores.append(r['score'])
            print(json.dumps({'iter': it, 'k': k, **r}, ensure_ascii=False), flush=True)
        if not cands: continue
        idx = np.argsort(scores)[::-1][:elite]
        mu = np.mean([cands[i] for i in idx], axis=0)
        top = float(scores[idx[0]])
        if top > best_score:
            best_score = top
            set_flat(net, mu); torch.save(net.state_dict(), CKPT)
        # ★sigma가 너무 줄면 나쁜 해에서 못 빠져나온다(실측: 0.088에서 14사고 9판 연속).
        #   개선이 없으면 탐색폭을 다시 키운다(간이 재시동).
        if top <= best_score - 1e-9:
            stall += 1
        else:
            stall = 0
        if stall >= 2:
            sigma = min(0.30, sigma*1.6); stall = 0
        else:
            sigma = max(0.12, sigma*0.94)
        print(json.dumps({'iter': it, 'elite_mean': float(np.mean([scores[i] for i in idx])),
                          'best': best_score, 'sigma': round(sigma,3)}), flush=True)
    return best_score

if __name__ == '__main__':
    import sys
    a = sys.argv[1:]
    box = tuple(int(x) for x in a[:4]) if len(a) >= 4 else (15, 367, 1354, 1274)
    mode = a[4] if len(a) > 4 else 'run'
    if mode == 'train':
        train(box, iters=int(a[5]) if len(a) > 5 else 10,
              seconds=float(a[6]) if len(a) > 6 else 22)
    else:
        net = DriveNet().to(DEV)
        if os.path.exists(CKPT):
            net.load_state_dict(torch.load(CKPT, map_location=DEV))
        print(json.dumps(episode(net, box, float(a[5]) if len(a) > 5 else 25),
                         ensure_ascii=False))
