#!/usr/bin/env python3
"""네이티브 테트리스 앱 (Tkinter) — kongtrol 폐루프/키보드 데모 대상 (a_13).
★브라우저 아님(네이티브 데스크톱 앱). 격자 10x20 + 관용 테트리스 색으로 kongtrol locator 인식 대상.
키보드(enigo 물리키) 조작: Left/Right 이동·Up 회전·Down 소프트드롭·space 하드드롭.
--level 1~5: 낙하속도·초기채움·레벨표시 차등.

★geom/scale 방출·MS_WINPOS·MS_GEOM_FILE 규약 = minesweeper_app.py 와 동일 패턴 재사용(3R).
  (_shotdir·_geom_file·_backing_scale·emit_geometry 구조 동일 — 공통 헬퍼로 추출 여지 있음:
   후속에 demo/_app_common.py 로 빼면 두 앱이 공유 가능. 지금은 앱별 자체 구현 유지.)"""
import tkinter as tk
import sys, json, os, random

COLS, ROWS = 10, 20
CELL = 32
INFO_H = 40  # 상단 레벨 표시 영역 높이(px)
BG = '#101018'       # 보드 배경(진한 남회색)
GRID_LINE = '#303040'
EMPTY = '#181822'    # 빈 셀

# 표준 7테트로미노 + 관용색(가이드라인 컬러).
COLORS = {
    'I': '#00f0f0',  # cyan
    'O': '#f0f000',  # yellow
    'T': '#a000f0',  # purple
    'S': '#00f000',  # green
    'Z': '#f00000',  # red
    'J': '#0000f0',  # blue
    'L': '#f0a000',  # orange
}
# 각 테트로미노의 4x4 상대 좌표(회전 상태 0). (r,c) 오프셋.
SHAPES = {
    'I': [(1, 0), (1, 1), (1, 2), (1, 3)],
    'O': [(0, 1), (0, 2), (1, 1), (1, 2)],
    'T': [(0, 1), (1, 0), (1, 1), (1, 2)],
    'S': [(0, 1), (0, 2), (1, 0), (1, 1)],
    'Z': [(0, 0), (0, 1), (1, 1), (1, 2)],
    'J': [(0, 0), (1, 0), (1, 1), (1, 2)],
    'L': [(0, 2), (1, 0), (1, 1), (1, 2)],
}


def _geom_file():
    # ★단일 소스: MS_GEOM_FILE 우선, 없으면 $TMPDIR 기준 SHOTDIR 폴백(minesweeper_app.py 규약 동일).
    env = os.environ.get('MS_GEOM_FILE')
    if env:
        return env
    return os.path.join(_shotdir(), 'app_geom.json')


def _shotdir():
    # 스크립트 SHOTDIR 규칙과 동일: ${TMPDIR:-/tmp}/kongtrol_play_shots.
    env = os.environ.get('MS_GEOM_FILE')
    if env:
        return os.path.dirname(env)
    base = os.environ.get('TMPDIR', '/tmp')
    return os.path.join(base, 'kongtrol_play_shots')


class Tetris:
    def __init__(self, level=1):
        self.level = max(1, min(5, level))
        # 낙하속도: 레벨↑ = 간격↓(빠름). L1=600ms ... L5=120ms.
        self.fall_ms = {1: 600, 2: 450, 3: 320, 4: 220, 5: 120}[self.level]
        # 격자: None=빈칸, else=색문자열.
        self.grid = [[None] * COLS for _ in range(ROWS)]
        self._seed_fill()

        self.root = tk.Tk()
        self.root.title("Tetris")
        pos = os.environ.get('MS_WINPOS', '300,200')
        try:
            wx, wy = (int(v) for v in pos.split(','))
        except Exception:
            wx, wy = 300, 200
        self.w = COLS * CELL
        self.h = ROWS * CELL + INFO_H
        self.root.geometry(f"{self.w}x{self.h}+{wx}+{wy}")
        self.root.resizable(False, False)
        self.cv = tk.Canvas(self.root, width=self.w, height=self.h, highlightthickness=0, bg=BG)
        self.cv.pack()

        # 키바인딩: Left/Right 이동·Up 회전·Down 소프트드롭·space 하드드롭.
        self.root.bind('<Left>', lambda e: self.move(-1))
        self.root.bind('<Right>', lambda e: self.move(1))
        self.root.bind('<Up>', lambda e: self.rotate())
        self.root.bind('<Down>', lambda e: self.soft_drop())
        self.root.bind('<space>', lambda e: self.hard_drop())

        self.cur = None
        self.cur_r = 0
        self.cur_c = 0
        self.spawn()
        self.draw()
        self.root.attributes('-topmost', True)
        self.root.lift()

    def _seed_fill(self):
        # ★초기 채움 차등: 레벨↑ = 바닥에 블록 더 쌓임(L1=0줄 ... L5=8줄, 구멍 섞어 현실감).
        fill_rows = {1: 0, 2: 2, 3: 4, 4: 6, 5: 8}[self.level]
        keys = list(COLORS.keys())
        for i in range(fill_rows):
            r = ROWS - 1 - i
            for c in range(COLS):
                # 각 줄에 구멍 2~3개(완성줄 자동삭제 방지) — 시각적 스택.
                if random.random() > 0.25:
                    self.grid[r][c] = random.choice(keys)

    # ── 조각 좌표 계산 ──
    def cells_of(self, shape_cells, base_r, base_c):
        return [(base_r + dr, base_c + dc) for (dr, dc) in shape_cells]

    def valid(self, shape_cells, base_r, base_c):
        for (r, c) in self.cells_of(shape_cells, base_r, base_c):
            if c < 0 or c >= COLS or r >= ROWS:
                return False
            if r >= 0 and self.grid[r][c] is not None:
                return False
        return True

    def spawn(self):
        self.cur_key = random.choice(list(SHAPES.keys()))
        self.cur = list(SHAPES[self.cur_key])
        self.cur_r = 0
        self.cur_c = COLS // 2 - 2
        if not self.valid(self.cur, self.cur_r, self.cur_c):
            # 스폰 불가 = 게임오버 → 보드 상단 일부 비워 계속(데모라 리셋).
            for r in range(4):
                self.grid[r] = [None] * COLS

    # ── 키 액션 ──
    def move(self, dc):
        if self.cur and self.valid(self.cur, self.cur_r, self.cur_c + dc):
            self.cur_c += dc
            self.draw()
            print(f"[app] MOVE {dc:+d} -> c={self.cur_c}", flush=True)

    def rotate(self):
        if not self.cur:
            return
        # 4x4 회전: (r,c) -> (c, 3-r).
        rot = [(c, 3 - r) for (r, c) in self.cur]
        if self.valid(rot, self.cur_r, self.cur_c):
            self.cur = rot
            self.draw()
            print("[app] ROTATE", flush=True)

    def soft_drop(self):
        if self.cur and self.valid(self.cur, self.cur_r + 1, self.cur_c):
            self.cur_r += 1
            self.draw()
            print("[app] SOFT_DROP", flush=True)

    def hard_drop(self):
        if not self.cur:
            return
        while self.valid(self.cur, self.cur_r + 1, self.cur_c):
            self.cur_r += 1
        print("[app] HARD_DROP", flush=True)
        self.lock()

    def lock(self):
        for (r, c) in self.cells_of(self.cur, self.cur_r, self.cur_c):
            if 0 <= r < ROWS and 0 <= c < COLS:
                self.grid[r][c] = self.cur_key
        self.clear_lines()
        self.spawn()
        self.draw()

    def clear_lines(self):
        new = [row for row in self.grid if any(x is None for x in row)]
        cleared = ROWS - len(new)
        for _ in range(cleared):
            new.insert(0, [None] * COLS)
        self.grid = new
        if cleared:
            print(f"[app] CLEAR {cleared} lines", flush=True)

    def tick(self):
        # 자동 낙하(레벨별 속도).
        if self.cur:
            if self.valid(self.cur, self.cur_r + 1, self.cur_c):
                self.cur_r += 1
            else:
                self.lock()
            self.draw()
        self.root.after(self.fall_ms, self.tick)

    # ── 렌더 ──
    def draw(self):
        self.cv.delete('all')
        # 레벨 표시 텍스트(상단).
        self.cv.create_rectangle(0, 0, self.w, INFO_H, fill='#202030', outline='')
        self.cv.create_text(self.w // 2, INFO_H // 2, text=f"TETRIS  LEVEL {self.level}",
                            fill='#ffffff', font=('Helvetica', 16, 'bold'))
        # 격자 + 고정 블록.
        for r in range(ROWS):
            for c in range(COLS):
                x0 = c * CELL
                y0 = INFO_H + r * CELL
                color = self.grid[r][c]
                fill = COLORS[color] if color else EMPTY
                self.cv.create_rectangle(x0, y0, x0 + CELL, y0 + CELL,
                                        fill=fill, outline=GRID_LINE)
        # 현재 낙하 조각.
        if self.cur:
            for (r, c) in self.cells_of(self.cur, self.cur_r, self.cur_c):
                if 0 <= r < ROWS and 0 <= c < COLS:
                    x0 = c * CELL
                    y0 = INFO_H + r * CELL
                    self.cv.create_rectangle(x0, y0, x0 + CELL, y0 + CELL,
                                            fill=COLORS[self.cur_key], outline=GRID_LINE)

    # ── geom/scale 방출 (minesweeper_app.py 패턴 재사용) ──
    def _backing_scale(self):
        import subprocess, struct
        try:
            probe = os.path.join(_shotdir(), '_scale_probe.png')
            os.makedirs(os.path.dirname(probe), exist_ok=True)
            subprocess.run(['screencapture', '-x', '-t', 'png', probe],
                           capture_output=True, timeout=10)
            with open(probe, 'rb') as f:
                f.read(16); w = struct.unpack('>I', f.read(4))[0]
            logical_w = self.root.winfo_screenwidth()
            if w and logical_w:
                return round(w / logical_w, 4)
        except Exception as e:
            print(f"[app] scale probe 실패({e}) → fallback 1.0", flush=True)
        return 1.0

    def emit_geometry(self):
        # 실제 창 물리좌표 + backing scale 방출(kongtrol locator/캡처가 읽음).
        self.root.update_idletasks(); self.root.update()
        lx, ly = self.root.winfo_rootx(), self.root.winfo_rooty()
        lw, lh = self.root.winfo_width(), self.root.winfo_height()
        scale = self._backing_scale()
        px, py = int(lx * scale), int(ly * scale)
        pw, ph = int(lw * scale), int(lh * scale)
        # 격자 원점은 INFO_H(레벨표시) 아래부터 — 물리 오프셋도 반영.
        geo = {"logical": [lx, ly, lw, lh], "scale": scale,
               "physical": [px, py, pw, ph], "cell_logical": CELL,
               "cell_physical": int(CELL * scale), "rows": ROWS, "cols": COLS,
               "info_h_logical": INFO_H, "info_h_physical": int(INFO_H * scale),
               "game": "tetris", "level": self.level}
        gf = _geom_file()
        os.makedirs(os.path.dirname(gf), exist_ok=True)
        tmp = gf + '.tmp'
        with open(tmp, 'w') as f:
            json.dump(geo, f)
        os.replace(tmp, gf)
        print(f"[app] geometry -> {gf}: {geo}", flush=True)

    def run(self):
        self.root.attributes('-topmost', True); self.root.lift()
        # ★enigo 물리키 수신되게 창 포커스(focus_force). 활성화 한계는 상위에서 별도 처리.
        self.root.focus_force()
        self.emit_geometry()
        print(f"[app] ready native tetris {self.w}x{self.h} CELL={CELL} level={self.level}", flush=True)
        self.root.after(self.fall_ms, self.tick)
        self.root.mainloop()


if __name__ == '__main__':
    level = 1
    if '--level' in sys.argv:
        i = sys.argv.index('--level')
        if i + 1 < len(sys.argv):
            try:
                level = int(sys.argv[i + 1])
            except ValueError:
                level = 1
    Tetris(level=level).run()
