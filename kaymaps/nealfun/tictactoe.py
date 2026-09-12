"""틱택토: 보드 판독 + 최적수(미니맥스). 레시피 LVL6 전략을 코드로 고정."""
import subprocess, time
import numpy as np
import fastvis

KT = "/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol"
S, OX, OY = 1.965, 763.8, 159.8
CX = [(22, 311), (319, 609), (617, 906)]      # 실측(연회색 셀 영역)
CY = [(206, 495), (503, 793), (801, 1090)]    # 실측

def toclick(px, py):
    return int(round(px / S + OX)), int(round(py / S + OY))

def read():
    """보드 판독: 'O'=빨간 동그라미, 'X'=파란 표식, '.'=빈칸."""
    a = fastvis.grab().astype(int)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    red = (r > 150) & (r > g + 60) & (r > b + 60)
    blue = (b > 130) & (b > r + 50) & (b > g + 30)
    bd = []
    for i in range(3):
        row = []
        for j in range(3):
            y0, y1 = CY[i]; x0, x1 = CX[j]
            ro = red[y0:y1, x0:x1].mean()
            bl = blue[y0:y1, x0:x1].mean()
            row.append('O' if ro > 0.01 else ('X' if bl > 0.01 else '.'))
        bd.append(row)
    return bd

LINES = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]

def winner(f):
    for a_, b_, c_ in LINES:
        if f[a_] != '.' and f[a_] == f[b_] == f[c_]:
            return f[a_]
    return None

def best_move(f, me):
    """미니맥스 — 지지 않는 수를 고른다."""
    opp = 'O' if me == 'X' else 'X'
    def mm(bd, turn):
        w = winner(bd)
        if w == me: return 1, None
        if w == opp: return -1, None
        empty = [i for i, v in enumerate(bd) if v == '.']
        if not empty: return 0, None
        scores = []
        for i in empty:
            nb = bd[:]; nb[i] = turn
            s, _ = mm(nb, opp if turn == me else me)
            scores.append((s, i))
        return (max(scores) if turn == me else min(scores))
    return mm(f, me)[1]

def play_cell(idx):
    i, j = divmod(idx, 3)
    px = (CX[j][0] + CX[j][1]) // 2
    py = (CY[i][0] + CY[i][1]) // 2
    x, y = toclick(px, py)
    subprocess.run([KT, "input", "click", str(x), str(y), "--yes"], capture_output=True)
    return x, y
