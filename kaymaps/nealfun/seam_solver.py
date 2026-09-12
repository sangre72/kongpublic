"""타일 회전 퍼즐 = 경로(그림) 연속성 맞추기 (u_4764).
핵심: 이웃한 두 타일의 '맞닿는 변'의 픽셀 프로파일이 서로 이어져야 한다.
눈으로 '이어져 보인다'는 무의미(레시피 TRAP c) — 변 프로파일 차이를 수치로 재서 최소인 회전을 고른다.
"""
import subprocess, time
import numpy as np
import fastvis

KT = "/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol"
S, OX, OY = 1.965, 763.8, 159.8
CX = [(19, 309), (319, 609), (619, 909)]
CY = [(208, 499), (509, 800), (809, 1100)]
BAND = 10                      # 변에서 몇 px 를 프로파일로 볼지

def click_xy(i, j):
    px = (CX[j][0] + CX[j][1]) // 2
    py = (CY[i][0] + CY[i][1]) // 2
    return int(round(px / S + OX)), int(round(py / S + OY))

def rotate(i, j, n=1):
    x, y = click_xy(i, j)
    for _ in range(n):
        subprocess.run([KT, "input", "click", str(x), str(y), "--yes"], capture_output=True)
        time.sleep(0.85)

def tile(a, i, j):
    y0, y1 = CY[i]; x0, x1 = CX[j]
    return a[y0:y1, x0:x1]

def edges(a, i, j):
    """타일의 4변 프로파일(그레이). 길이를 통일해 비교 가능하게 한다."""
    t = tile(a, i, j).astype(float).mean(axis=2)
    n = min(t.shape[0], t.shape[1])
    def rs(v):
        idx = np.linspace(0, len(v) - 1, n)
        return np.interp(idx, np.arange(len(v)), v)
    return {
        "T": rs(t[:BAND, :].mean(axis=0)),
        "B": rs(t[-BAND:, :].mean(axis=0)),
        "L": rs(t[:, :BAND].mean(axis=1)),
        "R": rs(t[:, -BAND:].mean(axis=1)),
    }

def seam_cost(a):
    """보드 전체 이음새 불일치 총합. 작을수록 그림이 이어진다."""
    E = {(i, j): edges(a, i, j) for i in range(3) for j in range(3)}
    c = 0.0
    for i in range(3):
        for j in range(3):
            if j < 2:                                   # 좌우 이웃: 내 R 과 옆 L
                c += np.abs(E[(i, j)]["R"] - E[(i, j + 1)]["L"]).mean()
            if i < 2:                                   # 상하 이웃: 내 B 와 아래 T
                c += np.abs(E[(i, j)]["B"] - E[(i + 1, j)]["T"]).mean()
    return float(c)

def solve(rounds=3, log=print):
    """각 타일을 0~3회 돌려보고 전체 이음새 비용이 최소가 되는 회전을 고정한다."""
    for r in range(rounds):
        improved = False
        for i in range(3):
            for j in range(3):
                base = seam_cost(fastvis.grab())
                best_n, best_c = 0, base
                for n in range(1, 4):
                    rotate(i, j, 1)
                    c = seam_cost(fastvis.grab())
                    if c < best_c - 0.2:
                        best_c, best_n = c, n
                rotate(i, j, (4 - 3 + best_n) % 4)      # 최적 회전으로 맞춤
                if best_n:
                    improved = True
                    log(f"  r{i}c{j}: {base:.1f} -> {best_c:.1f} (회전 {best_n})")
        log(f"round {r}: cost={seam_cost(fastvis.grab()):.1f}")
        if not improved:
            break
