"""연속 주행 자율주행 루프 (u_4745).
- 전진은 끊지 않는다(긴 hold 하나를 깔고 그 위에서 조향만 얹는다)
- 매 프레임 장애물(주차차량·다가오는 차)과 도로를 인식해 목표를 갱신한다
- 모델이 학습한 위험요인(car_x, steer_ms)을 조향 억제에 사용한다
"""
import subprocess, time
import numpy as np
import fastvis, waymo, nav

KT = "/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol"

def bg(k, ms):
    return subprocess.Popen([KT, "input", "key", k, "--hold", str(ms), "--yes"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def obstacles(frame=None):
    """유채색 덩어리 = 다른 차(주차 중이든 주행 중이든). 내 차는 흰색이라 제외된다."""
    a = fastvis.grab() if frame is None else frame
    sat = a.max(axis=2).astype(int) - a.min(axis=2).astype(int)
    return sat > 35

def nearest_ahead(car, obs, reach=260):
    """진행 방향(동쪽) 전방에 장애물이 얼마나 가까운지."""
    if car is None:
        return reach
    x, y = car[0], car[1]
    for d in range(40, reach, 10):
        xs = min(x + d, obs.shape[1] - 1)
        band = obs[max(0, y - 50):y + 50, xs]
        if band.mean() > 0.35:
            return d
    return reach

def run(seconds=12, target_y=300, target_x=790, log=None):
    """연속 전진 + 실시간 인식 조향."""
    hold = int(seconds * 1000)
    p = bg("up", hold)          # ★전진은 한 번 깔고 끝까지 유지
    time.sleep(0.25)
    t0 = time.time()
    best = (0, 0, 0, 0)
    while time.time() - t0 < seconds - 0.4:
        frame = fastvis.grab()
        car = waymo.pos()
        if car:
            x, y, w, h = car
            if x > best[0]:
                best = car
            obs = obstacles(frame)
            gap = nearest_ahead(car, obs)
            dy = y - target_y
            # 모델 학습 결과 반영: x가 클수록(위험) 조향 억제, 조향은 짧게 주고 즉시 뗀다
            in_bay = x > 620 and abs(dy) < 60      # 칸 안 = 조향 말고 계속 전진
            risky = (x > 620 and abs(dy) >= 60) or gap < 80
            if not risky and not in_bay:
                if dy > 25:
                    bg("left", 100)
                elif dy < -25:
                    bg("right", 90)
            if log is not None:
                log.append({"x": x, "y": y, "w": w, "h": h, "gap": gap})
            if x >= target_x:
                break
        time.sleep(0.16)
    try:
        p.terminate()
    except Exception:
        pass
    time.sleep(0.3)
    return best, waymo.pos()
