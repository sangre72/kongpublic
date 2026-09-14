"""순수 비전 자율주행 — 사물 인식 금지 버전.

★오너 규약(u_4873/4874, 철저히 지킬 것):
  1. "로직으로 주행하는건 금지" → 게임 내부 좌표·변수 접근 0. 입력은 화면 픽셀뿐.
  2. ★"다가오는 차량, 사람, 사물 등 모든걸 보면 안 돼, 이건 금지"
     → 코드가 '이건 차다/사람이다/장애물이다'라고 **분류하지 않는다**.
       색·채도로 물체를 지목하는 규칙(예: sat>55 = 다른 차) = 전부 삭제했다.
     → 눈은 '내가 지금 가는 방향이 내가 달려온 바닥과 얼마나 같은가'만 본다.
       무엇이 막았는지는 끝내 모른다. 부딪혀 봐야(벌점) 안다.
  3. 학습은 '마주치는 상황'에서만 일어난다. 사고=벌, 목적지 도달=클리어(보상).

실측(2026-09-14, 이 머신 / 크롬 677x637 캔버스):
  캡처 1/2축소 10.9ms, 캡처+판정 14.5ms → 20ms 예산 내. 초당 50프레임.
"""
import time, json, os, math, random
import numpy as np
import Quartz.CoreGraphics as CG

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

# ---------- 키(CGEvent) ----------
KEY = {'up': 126, 'down': 125, 'left': 123, 'right': 124}
_down = set()
def key(k, on):
    if on == (k in _down): return
    CG.CGEventPost(CG.kCGHIDEventTap, CG.CGEventCreateKeyboardEvent(None, KEY[k], on))
    (_down.add if on else _down.discard)(k)
def release_all():
    for k in list(_down): key(k, False)

# ---------- 눈 ----------
class Eye:
    """사물을 찾지 않는다. 단 하나만 판단한다:
       '이 픽셀이 내가 방금 달려온 바닥과 비슷한가?'
       기준 바닥색은 주행하면서 **스스로 갱신**한다(사전 지식 없음)."""

    def __init__(self, box, scale=2):
        self.bx, self.by, self.bw, self.bh = box
        self.sw, self.sh = self.bw // scale, self.bh // scale
        self.cx = self.sw // 2
        self.cy = int(self.sh * 0.60)          # 내 차 위치(화면 하단 중앙)
        self.ground = None                      # 학습되는 바닥 기준색
        self.tol = 13.0   # ★실측 조정: 30이면 화면 83%가 '도로'로 잡혀 광선이 전부 뚫림

    def look(self):
        a = grab(self.bx, self.by, self.sw, self.sh)
        if a is None: return None
        f = a.astype(np.int16)
        # 내 차 바로 아래 = 지금 달리고 있는 바닥. 이것이 유일한 '정답 샘플'.
        # ★사고 중에는 바닥색을 배우지 않는다(2026-09-14 실측 사고):
        #   충돌하면 화면 전체가 붉게 덮이는데, 그걸 계속 학습하면
        #   기준 바닥색이 붉은색([71,39,39])이 되어 '온 화면이 도로'로 보인다.
        #   그러면 광선이 전부 1.0(뻥 뚫림)이 되어 벽에 박힌 채 탈출 불가.
        red_flash = float(f[:, :, 0].mean() - f[:, :, 2].mean())
        # ★기준 바닥 = '차 아래'가 아니라 '화면에서 가장 흔한 넓은 표면'.
        #   주차칸/공터에서 출발하면 차 아래가 도로가 아니므로 엉뚱한 색을 배운다
        #   (실측: [21,24,30] = 페이지 배경색을 도로로 오학습 → 직진만 하다 건물 충돌).
        #   가장 넓게 깔린 면 = 도로/지면. 무엇인지는 여전히 모른다(분류 아님).
        if red_flash < 18:
            # ★np.unique(axis=0)는 60만 픽셀에서 150ms+ 걸려 예산을 깬다(실측 6.4fps).
            #   대신 성글게 샘플링 + 색을 정수 하나로 접어 bincount — 1ms 미만.
            band = f[int(self.sh*0.25):int(self.sh*0.95):4, ::4]
            q = (band // 16).astype(np.int32)
            code = (q[:, :, 0] << 8) | (q[:, :, 1] << 4) | q[:, :, 2]
            top = np.bincount(code.ravel()).argmax()
            m = np.array([(top >> 8) & 15, (top >> 4) & 15, top & 15], float)*16 + 8
            self.ground = m if self.ground is None else self.ground*0.88 + m*0.12
        if self.ground is None: return None
        # '바닥과 같은가' = 색 거리. 무엇인지는 묻지 않는다.
        d = np.abs(f - self.ground).sum(axis=2)
        return dict(same=d < self.tol*3, frame=f)

    def nav(self, v):
        """★내비 미니맵을 '눈으로' 읽는다(u_4893).
           우상단 원 안의 초록 경로선이 어느 방향으로 뻗는지만 본다.
           좌표를 넘겨받는 게 아니라 픽셀에서 각도를 추정한다.
           반환: -1(좌) ~ +1(우), 없으면 0.0"""
        f = v['frame']
        H, W = f.shape[:2]
        R = 54
        cx, cy = int(min(W - R - 10, W*0.72)), R + 12   # 게임과 동일 규칙
        y0, y1 = max(0, cy-R), min(H, cy+R)
        x0, x1 = max(0, cx-R), min(W, cx+R)
        if y1 <= y0 or x1 <= x0: return 0.0, 0.0
        sub = f[y0:y1, x0:x1]
        gmask = (sub[:,:,1] > 130) & (sub[:,:,1] > sub[:,:,0].astype(int)+55) \
                                   & (sub[:,:,1] > sub[:,:,2].astype(int)+35)
        ys, xs = np.nonzero(gmask)
        if len(ys) < 6: return 0.0, 0.0
        # 차(원 중앙) 기준 위쪽 절반에서 경로가 치우친 방향
        ccx, ccy = (x1-x0)/2.0, (y1-y0)/2.0
        dx = (xs - ccx); dy = (ys - ccy)
        upper = dy < 2                   # 진행방향(위쪽) 구간만
        if upper.sum() < 4: upper = np.ones_like(dy, bool)
        bias = float(np.clip(dx[upper].mean() / max(1.0, R*0.6), -1, 1))
        amount = float(min(1.0, len(ys)/220.0))
        return bias, amount

    def rays(self, v, n=11):
        """부채꼴 광선: 각 방향으로 '바닥이 이어지는 거리'만 잰다.
           막힌 이유(차·사람·건물·인도)는 구분하지 않는다 — 구분 자체가 금지."""
        same = v['same']; H, W = same.shape
        maxr = int(min(H, W) * 0.45)
        out = []
        for i in range(n):
            th = -math.pi/2 + (i - (n-1)/2) * (math.pi / (n*1.5))
            dx, dy = math.cos(th), math.sin(th)
            # ★내 차 자체(및 주차칸 바닥)는 '바닥이 아님'으로 잡힌다.
            #   그대로 재면 모든 광선이 즉시 0이 되어 아무것도 못 본다(실측 0.02).
            #   차체를 지나간 뒤(첫 바닥 픽셀)부터 거리를 잰다.
            start = None
            for d in range(4, maxr, 2):
                x = int(self.cx + dx*d); y = int(self.cy + dy*d)
                if not (0 <= x < W and 0 <= y < H): break
                if same[y, x]: start = d; break
            if start is None:
                out.append(0.0); continue
            hit = maxr
            for d in range(start, maxr, 2):
                x = int(self.cx + dx*d); y = int(self.cy + dy*d)
                if not (0 <= x < W and 0 <= y < H): hit = d; break
                if not same[y, x]: hit = d; break
            out.append((hit - start) / maxr)
        return np.array(out)

# ---------- 정책 ----------
class Policy:
    """가중치만 있다. if문 규칙표가 아니다.
       입력 = 광선 11개 + **현재 속도** → 출력 = 조향/가속/제동.

       ★속도-조향 결합(u_4886): 사람은 빠를수록 핸들을 덜 꺾는다.
         이 관계를 규칙으로 박지 않고 **학습 파라미터로 둔다**:
           steer = base_steer * (1 / (1 + k_v * speed))
         k_v 가 크면 고속에서 조향 억제(안정), 작으면 고속에서도 확 꺾음(전복·이탈).
         커브·유턴 진입 속도도 같은 원리로 v_curve 가 결정한다.
         무엇이 맞는지는 사고 벌점이 가르친다."""
    PATH = os.path.expanduser('~/.kongbot_drive_policy.json')
    KEYS = ('w_steer','w_go','brake_th','k_v','v_curve','v_max')

    def __init__(self, n=11):
        self.n = n
        self.w_steer = np.linspace(-1, 1, n)
        self.w_go    = np.zeros(n); self.w_go[n//2] = 1.0
        self.brake_th = 0.26
        self.w_nav   = 0.25   # 내비 추종 강도(학습됨)
        self.k_v     = 0.9      # 속도에 따른 조향 감쇠(학습됨)
        self.v_curve = 0.45     # 전방이 굽었을 때 목표속도 비율(학습됨)
        self.v_max   = 0.85     # 직선 목표속도 비율(학습됨)
        self.gen, self.best = 0, -1e9
        self.load()

    def act(self, rays, speed=0.0, nav=0.0):
        """speed = 0~1 로 정규화된 현재 속도(화면 흐름량으로 추정)."""
        # ★조향은 '좌우 불균형'이다(2026-09-14 실측 수정).
        #   이전엔 가중합을 rays.sum()으로 나눠 값이 항상 0.00~0.06이었고,
        #   키 입력 임계 0.15를 한 번도 넘지 못해 차가 영원히 직진만 했다.
        #   → 변이를 줘도 행동이 안 바뀌어 학습이 정체(사고 22~24 고정).
        n = len(rays); h = n // 2
        left = float(rays[:h].mean()); right = float(rays[h+1:].mean())
        steer = (right - left) * 3.0 + float((self.w_steer * rays).mean())
        # ★내비가 가리키는 방향으로 끌린다. 가중치 w_nav 자체가 학습 대상 —
        #   너무 크면 도로를 무시하고 목적지로 직진(충돌), 작으면 영영 못 감.
        steer = steer + self.w_nav * nav
        fwd   = float((self.w_go * rays).sum() / max(1e-6, self.w_go.sum()))
        # ★속도가 높을수록 조향 억제 — 계수 k_v 자체가 학습 대상
        steer = steer / (1.0 + self.k_v * max(0.0, speed))
        # ★굽은 정도에 따라 목표속도를 낮춘다 — v_curve 도 학습 대상
        bend  = abs(steer)
        target = self.v_max * (1.0 - (1.0 - self.v_curve) * min(1.0, bend * 2.2))
        brake = (fwd < self.brake_th) or (speed > target + 0.12)
        acc   = 0.0 if brake else min(1.0, max(0.0, (target - speed) * 2.0))
        return steer, acc, brake

    def mutate(self, scale=0.14):
        p = Policy(self.n)
        p.w_steer = self.w_steer + np.random.randn(self.n)*scale
        p.w_go    = np.abs(self.w_go + np.random.randn(self.n)*scale)
        p.brake_th = float(np.clip(self.brake_th + np.random.randn()*0.05, .1, .6))
        p.w_nav    = float(np.clip(self.w_nav + np.random.randn()*0.12, 0.0, 1.5))
        p.k_v      = float(np.clip(self.k_v + np.random.randn()*0.25, 0.0, 4.0))
        p.v_curve  = float(np.clip(self.v_curve + np.random.randn()*0.08, 0.05, 1.0))
        p.v_max    = float(np.clip(self.v_max + np.random.randn()*0.08, 0.2, 1.0))
        p.gen, p.best = self.gen + 1, self.best
        return p

    def save(self):
        json.dump({'w_steer': self.w_steer.tolist(), 'w_go': self.w_go.tolist(),
                   'brake_th': self.brake_th, 'w_nav': self.w_nav, 'k_v': self.k_v,
                   'v_curve': self.v_curve, 'v_max': self.v_max,
                   'gen': self.gen, 'best': self.best}, open(self.PATH, 'w'))
    def load(self):
        if not os.path.exists(self.PATH): return
        try:
            d = json.load(open(self.PATH))
            self.w_steer = np.array(d['w_steer']); self.w_go = np.array(d['w_go'])
            self.brake_th = d['brake_th']
            self.w_nav   = d.get('w_nav', self.w_nav)
            self.k_v     = d.get('k_v', self.k_v)
            self.v_curve = d.get('v_curve', self.v_curve)
            self.v_max   = d.get('v_max', self.v_max)
            self.gen = d.get('gen', 0); self.best = d.get('best', -1e9)
        except Exception: pass

# ---------- 한 판(에피소드) ----------
def find_canvas():
    """★캡처 박스 자동탐지(2026-09-14): 좌표를 손으로 넣었다가 창 크기·iframe
       변화로 엉뚱한 영역을 읽어 판정이 계속 틀렸다.
       상태칩(좌상단 파란 사각형)을 화면에서 찾아 캔버스 원점을 역산한다."""
    wide = grab(0, 300, 900, 1100)
    if wide is None: return None
    r = wide[:, :, 0].astype(int); g_ = wide[:, :, 1].astype(int); b_ = wide[:, :, 2].astype(int)
    # 상태칩 색 = #2f7bff(주행) / #00d26a(클리어) / #ff2d2d(실패) 중 하나
    chip = ((abs(r-0x2f) < 46) & (abs(g_-0x7b) < 46) & (abs(b_-0xff) < 46)) | \
           ((abs(r-0x00) < 46) & (abs(g_-0xd2) < 52) & (abs(b_-0x6a) < 52)) | \
           ((abs(r-0xff) < 46) & (abs(g_-0x2d) < 52) & (abs(b_-0x2d) < 52))
    ys, xs = np.nonzero(chip)
    if len(ys) < 30: return None
    top = int(ys.min()); m = ys < top + 24
    x0 = int(xs[m].min()); y0 = top
    # 칩 좌상단이 캔버스 (12,12) → 원점 역산 (실측 보정: 원점=칩좌표 그대로가 맞음)
    return (x0, 300 + y0)

def focus_chrome():
    """캡처 전 Chrome을 최전면으로. 백그라운드면 CGWindowListCreateImage가 None을 준다."""
    import subprocess
    subprocess.run(['open','-a','Google Chrome'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.6)

def episode(box, seconds, pol, scale=2):
    """보상 = 오래 굴러간 거리 − 사고 벌점. 목적지 도달 = 클리어 보너스.
       사고는 '화면이 붉게 번쩍'하는 것으로만 안다(게임이 주는 유일한 신호)."""
    focus_chrome()
    got = find_canvas()
    if got: box = (got[0], got[1], box[2], box[3])
    eye = Eye(box, scale)
    t0 = time.time(); frames = 0; inb = 0
    crashes = 0; last = 0; moved = 0.0
    clears = 0; fails = 0; prog = 0.0; flow = 0.0; stuck_f = 0; miss = 0
    prev = None
    try:
        while time.time() - t0 < seconds:
            ts = time.time()
            v = eye.look()
            if v is None:
                miss += 1
                if miss > 40: break        # 지속 실패만 중단
                time.sleep(0.05); continue
            miss = 0
            rays = eye.rays(v)
            # 속도 추정: 화면이 흐른 양(옵티컬 플로 대용) — 게임 변수 아님
            speed_est = min(1.0, flow / 12.0)
            nav_bias, nav_amt = eye.nav(v)
            steer, acc, brake = pol.act(rays, speed_est, nav_bias)
            # ★끼임 탈출: 화면이 전혀 흐르지 않으면(= 못 움직임) 후진으로 뺀다.
            #   무엇에 막혔는지는 여전히 모른다. '안 움직인다'는 사실만 쓴다.
            if flow < 0.35: stuck_f += 1
            else: stuck_f = 0
            if stuck_f > 25:
                key('up', False); key('left', False); key('right', False)
                key('down', True)
                if stuck_f > 60: stuck_f = 0
            else:
                key('left',  steer < -0.035)   # ★실측 신호폭(±0.07)에 맞춘 임계
                key('right', steer >  0.035)
                key('up',    acc > 0.04 and not brake)
                key('down',  bool(brake))
            f = v['frame']
            # 사고 신호: 붉은 오버레이(게임이 화면 전체를 붉게 덮음)
            red = float(f[:, :, 0].mean() - f[:, :, 2].mean())
            if red > 24 and ts - last > 0.8:
                crashes += 1; last = ts
            # ★상태칩 읽기(u_4882 3번) — 게임 변수를 받지 않고 '화면을 본다'.
            #   좌상단 10x10 = 파랑(주행) / 초록(클리어) / 빨강(실패)
            chip = f[8:14, 8:14].reshape(-1, 3).mean(axis=0)
            r_, g_, b_ = chip
            if g_ > r_ + 40 and g_ > b_ + 40:
                clears += 1; break                    # 클리어 → 이 판 종료
            if r_ > g_ + 60 and r_ > b_ + 60:
                fails += 1; break                     # 실패 → 이 판 종료
            # 노란 막대 길이 = 목적지 근접도(0~1). 보상에 쓴다.
            bar = f[8:14, 21:58]
            prog = float(((bar[:, :, 0] > 150) & (bar[:, :, 1] > 120) &
                          (bar[:, :, 2] < 110)).mean())
            # 전진량: 화면이 얼마나 흘렀는가(옵티컬 플로 대용)
            small = f[::8, ::8, 1]
            if prev is not None:
                flow = float(np.abs(small - prev).mean())
                moved += flow
            prev = small
            frames += 1
            dt = time.time() - ts
            if dt <= 0.020: inb += 1
            if dt < 0.020: time.sleep(0.020 - dt)
    finally:
        release_all()
    # 보상: 목적지 근접(주), 이동량(보조), 사고 벌점, 클리어 보너스
    score = prog*4000.0 + moved - crashes*220.0 + clears*3000.0
    return dict(score=score, prog=round(prog, 3), moved=round(moved, 1),
                crashes=crashes, clears=clears, fails=fails, frames=frames,
                budget=round(inb/max(1, frames), 3),
                fps=round(frames/max(1e-6, time.time()-t0), 1))

def train(box, rounds=8, seconds=18, scale=2):
    """세대 학습: 부모 정책을 변이시켜 더 높은 점수면 채택."""
    best = Policy(); res0 = episode(box, seconds, best, scale)
    best.best = res0['score']; best.save()
    log = [dict(gen=best.gen, **res0)]
    print(json.dumps(log[-1], ensure_ascii=False), flush=True)
    for _ in range(rounds):
        cand = best.mutate()
        r = episode(box, seconds, cand, scale)
        # ★프레임이 거의 없는 판은 무효(창 포커스 이탈 등) — 0점이 최고점으로 둔갑하는 것 방지
        if r['frames'] < 40:
            log.append(dict(gen=cand.gen, kept=False, invalid=True, **r))
            print(json.dumps(log[-1], ensure_ascii=False), flush=True)
            continue
        keep = r['score'] > best.best
        if keep:
            cand.best = r['score']; best = cand; best.save()
        log.append(dict(gen=cand.gen, kept=keep, **r))
        print(json.dumps(log[-1], ensure_ascii=False), flush=True)
    return log

if __name__ == '__main__':
    import sys
    a = sys.argv[1:]
    box = tuple(int(x) for x in a[:4]) if len(a) >= 4 else (2, 366, 1354, 1274)
    mode = a[4] if len(a) > 4 else 'run'
    if mode == 'train':
        train(box, rounds=int(a[5]) if len(a) > 5 else 6,
              seconds=float(a[6]) if len(a) > 6 else 15)
    else:
        print(json.dumps(episode(box, float(a[5]) if len(a) > 5 else 20, Policy()),
                         ensure_ascii=False))
