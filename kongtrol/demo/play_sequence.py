#!/usr/bin/env python3
"""kongtrol 지뢰찾기 실제 플레이 시퀀스 — 단계별 보드 PNG 생성.
각 단계 = kongtrol 폐루프가 판단한 액션(open/flag)을 보드에 반영한 상태.
render_board.py 의 PNG 인코더 재사용."""
import sys, subprocess, os, json
sys.path.insert(0, os.path.dirname(__file__))
import render_board as rb

SOL = [[1,'M',1,0,0],[1,1,1,0,0],[0,0,0,0,0],[0,1,1,1,0],[0,1,'M',1,0]]
ROWS=COLS=5
BIN = sys.argv[1]
# ★SHOTDIR 단일 소스: 스크립트 SHOTDIR 규칙과 동일($TMPDIR 우선, /tmp 하드코딩 폴백만).
OUT = sys.argv[2] if len(sys.argv)>2 else os.path.join(
    os.environ.get('TMPDIR', '/tmp'), 'kongtrol_play_shots')
os.makedirs(OUT, exist_ok=True)

opened=[[False]*COLS for _ in range(ROWS)]
flagged=[[False]*COLS for _ in range(ROWS)]
# 초기: 첫 클릭이 안전한 0-영역(우하단)을 열면 실제 지뢰찾기처럼 flood-fill 로 넓게 열림.
# SOL 상 지뢰=(0,1),(4,2). 우측·하단 0 지대를 시드 → kongtrol 이 경계 숫자로 flag/open 연쇄 판단.
def flood_open(sr, sc):
    stack=[(sr,sc)]
    while stack:
        r,c=stack.pop()
        if not(0<=r<ROWS and 0<=c<COLS) or opened[r][c] or SOL[r][c]=='M': continue
        opened[r][c]=True
        if SOL[r][c]==0:  # 빈칸이면 8방 확장(관용 지뢰찾기 규칙)
            for dr in(-1,0,1):
                for dc in(-1,0,1):
                    stack.append((r+dr,c+dc))
flood_open(2,4)  # 첫 클릭 = 안전한 0 지대 → 넓게 열림

shots=[]
for step in range(8):
    img=f"{OUT}/step_{step:02d}.png"
    rb.render(SOL, opened, flagged, img)
    # kongtrol 이 이 보드를 인식→판단
    res=subprocess.run([BIN,"--yes","game","minesweeper","--image",img,
                        "--cell","80","--rows","5","--cols","5","--cycles","1","--sense-only"],
                       capture_output=True,text=True)
    line=[l for l in res.stdout.splitlines() if l.startswith("cycle")]
    action=line[0].split("·")[-1].strip() if line else "no-decision"
    print(f"step {step}: {action}  -> {img}", flush=True)
    shots.append(img)
    # 판단 반영: flag rXcY 면 그 셀 깃발, open 이면 열기
    import re
    m=re.search(r'(flag|open) r(\d+)c(\d+)', action)
    if not m:
        print(f"  (확정 수 없음 — 플레이 종료 @ step {step})", flush=True)
        break
    kind,r,c=m.group(1),int(m.group(2)),int(m.group(3))
    if kind=='flag': flagged[r][c]=True
    else: opened[r][c]=True
    # 다음 스텝: 안전지역도 조금 더 열어 진행감(0 주변 자동확장 흉내)
    if kind=='open':
        for (nr,nc) in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]:
            if 0<=nr<ROWS and 0<=nc<COLS and SOL[nr][nc]!='M':
                opened[nr][nc]=True

print(f"\nSHOTS: {len(shots)}장 저장 @ {OUT}", flush=True)
