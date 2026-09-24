"""u_5605 merge planner(2026-09-24): 프레임마다 조향하지 않고 ① PLAN @2Hz(0.5s 중앙값 e_y·e_psi → 차로중심까지 부드러운 횡 프로파일, 길이 max(20m, 3s·v))
② EXECUTE: 앞점 = 계획 프로파일 위 Ld 앞 점 + 도로 곡률 ff(½κL²), 변화율 상한, 0 으로 수렴 ③ HOLD: |e_y|<0.3∧|e_psi|<2° 가 1s 이상 → κ ff 만(동결), 편차 0.5s 지속시에만 해제.
출력은 gpu_drive mode=2 의 lp(차 기준 20m 앞 횡오프셋, m). 오프라인 재생(offline_gate)과 동일 코드."""
import math, collections
class MergePlanner:
    def __init__(self, ld=20.0, rate=1.5, plan_hz=2.0, win=0.5):
        self.ld = ld; self.rate = rate; self.dt_plan = 1.0 / plan_hz; self.win = win
        self.buf = collections.deque(); self.t_plan = None; self.plan = None   # plan = (t0, ey0, epsi0, Lm)
        self.hold = False; self.in_t = None; self.out_t = None; self.lp_prev = None; self.t_prev = None; self.hold_n = 0
    def _median(self):
        ey = sorted(b[1] for b in self.buf); ep = sorted(b[2] for b in self.buf); k = len(ey) // 2
        return ey[k], ep[k]
    def step(self, t, ey, epsi, k0, v, shift=0.0):
        self.buf.append((t, ey, epsi))
        while self.buf and t - self.buf[0][0] > self.win: self.buf.popleft()
        eym, epm = self._median()
        inb = abs(eym) < 0.3 and abs(epm) < math.radians(2.0)
        if self.hold:
            if not inb: self.out_t = self.out_t or t; self.hold = not (t - self.out_t >= 0.5)
            else: self.out_t = None
            if not self.hold: self.plan = None; self.t_plan = None
        else:
            if inb: self.in_t = self.in_t or t; self.hold = (t - self.in_t >= 1.0)
            else: self.in_t = None
        ff = 0.5 * k0 * self.ld * self.ld
        if self.hold: lp = ff + shift; self.hold_n += 1
        else:
            if self.plan is None or (t - self.t_plan) >= self.dt_plan:
                Lm = max(20.0, 3.0 * max(v, 0.0)); self.plan = (t, eym, epm, Lm, max(v, 1.0)); self.t_plan = t
            t0, ey0, ep0, Lm, v0 = self.plan
            s = v0 * (t - t0)   # 계획 시작 후 진행 거리(m)
            def prof(x):   # 남은 횡오차 비율(코사인 수렴, 0..1)
                u = min(max(x / Lm, 0.0), 1.0); return 0.5 * (1.0 + math.cos(math.pi * u))
            # 앞점(Ld 앞)의 차로중심 대비 계획 횡위치: 차 기준 = (계획 위치 − 현재 위치) − 헤딩 성분
            y_now = ey0 * prof(s); y_ahead = ey0 * prof(s + self.ld)
            lp = ff - y_now + y_ahead   # 앞점 = 계획상 현재 오차(−y_now, 프레임 잡음 대신 계획값) + Ld 앞 잔여오차(y_ahead→0) + 곡률 ff ; 2Hz 재계획 사이엔 매끈
            lp += shift
        if self.lp_prev is not None and self.t_prev is not None:
            dmax = self.rate * max(t - self.t_prev, 1e-3); lp = max(self.lp_prev - dmax, min(self.lp_prev + dmax, lp))
        self.lp_prev = lp; self.t_prev = t
        return lp, self.hold

class MergePlannerKF:
    """u_5606: 매 프레임(28~32fps). 상태 (e_y, e_psi) 운동학 예측(자전거 모델: e_psi += (yaw_rate − v·κ_road)·dt, e_y += v·sin(e_psi)·dt)
    → 헤드 추정으로 보정(상보 이득 g), 혁신 게이트 |est−pred|>0.5m 또는 >5° 는 기각(33ms 에 물리적으로 불가). 매 프레임 필터 상태로 병합 프로파일 재계획.
    HOLD: |e_y|<0.3∧|e_psi|<2° ≥1s → κ ff 만, 편차 ≥0.5s 지속시 해제. 변화율 상한."""
    def __init__(self, ld=20.0, rate=1.5, g_y=0.25, g_psi=0.4):
        self.ld = ld; self.rate = rate; self.g_y = g_y; self.g_psi = g_psi
        self.ey = None; self.ep = None; self.t_prev = None; self.lp_prev = None
        self.hold = False; self.in_t = None; self.out_t = None; self.hold_n = 0; self.rej = 0; self.n = 0; self.rej_run = 0; self.k0f = None
    def step(self, t, ey_m, ep_m, k0, v, yaw_rate=None, shift=0.0):
        import math
        self.n += 1
        self.k0f = k0 if self.k0f is None else self.k0f + 0.1 * (k0 - self.k0f); k0 = self.k0f   # 곡률 ff 는 저역(0.1) — 헤드 κ 잡음이 hold 중 명령을 흔들지 않게
        if self.ey is None: self.ey, self.ep, self.t_prev = ey_m, ep_m, t
        else:
            dt = max(1e-3, min(0.2, t - self.t_prev)); self.t_prev = t
            yr = yaw_rate if yaw_rate is not None else v * k0   # 관측 없으면 도로를 따라간다고 가정
            self.ep += (yr - v * k0) * dt; self.ey += v * math.sin(self.ep) * dt          # 예측
            if abs(ey_m - self.ey) <= 0.5 and abs(ep_m - self.ep) <= math.radians(5.0):   # 혁신 게이트
                self.ey += self.g_y * (ey_m - self.ey); self.ep += self.g_psi * (ep_m - self.ep); self.rej_run = 0
            else:
                self.rej += 1; self.rej_run += 1
                if self.rej_run >= 5: self.ey, self.ep, self.rej_run = ey_m, ep_m, 0   # 5프레임 연속 기각 = 예측 발산 → 측정으로 재초기화
        eyf, epf = self.ey, self.ep
        inb = abs(eyf) < 0.3 and abs(epf) < math.radians(2.0)
        if self.hold:
            if not inb: self.out_t = self.out_t or t; self.hold = not (t - self.out_t >= 0.5)
            else: self.out_t = None
        else:
            if inb: self.in_t = self.in_t or t; self.hold = (t - self.in_t >= 1.0)
            else: self.in_t = None
        ff = 0.5 * k0 * self.ld * self.ld
        if self.hold: lp = ff + shift; self.hold_n += 1
        else:
            Lm = max(20.0, 3.0 * max(v, 0.0)); u = min(self.ld / Lm, 1.0); y_ahead = eyf * 0.5 * (1.0 + math.cos(math.pi * u))
            lp = ff - eyf + y_ahead + shift   # 매 프레임 재계획: 현재 필터 오차에서 Lm 안에 0 으로 수렴하는 프로파일의 Ld 앞 점
        if self.lp_prev is not None: dmax = self.rate * max(1e-3, min(0.2, t - (self.t_lp if hasattr(self, 't_lp') else t))); lp = max(self.lp_prev - dmax, min(self.lp_prev + dmax, lp))
        self.lp_prev = lp; self.t_lp = t
        return lp, self.hold
