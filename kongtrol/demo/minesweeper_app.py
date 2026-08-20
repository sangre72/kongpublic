#!/usr/bin/env python3
"""네이티브 지뢰찾기 앱 (Tkinter/Cocoa Aqua) — kongtrol M7 폐루프 데모 대상.
★브라우저 아님(네이티브 데스크톱 앱). 고정 격자/관용 색상으로 kongtrol 픽셀색 인식 대상.
클릭 수신 시 셀을 '열어' 숫자를 드러냄(실제 플레이 반응). --dump 옵션으로 현재 보드 PNG 저장."""
import tkinter as tk
import sys, json, os

CELL = 80
ROWS = COLS = 5
# 0=빈칸, 1~3=숫자(관용 색), M=지뢰. 초기엔 전부 닫힘(N), 클릭 시 open.
SOLUTION = [
    ['1','M','1','0','0'],
    ['1','1','1','0','0'],
    ['0','0','0','0','0'],
    ['0','1','1','1','0'],
    ['0','1','M','1','0'],
]
NUMCOLOR = {'1':'#0000ff','2':'#008000','3':'#ff0000'}


def _geom_file():
    # ★단일 소스: 스크립트가 MS_GEOM_FILE 로 넘긴 경로가 최우선. 없으면 $TMPDIR 기준
    #   SHOTDIR(스크립트의 `${TMPDIR:-/tmp}/kongtrol_play_shots` 와 동일 규칙)로 폴백.
    #   → 앱↔스크립트가 항상 같은 파일을 가리킴(/tmp 하드코딩 제거, 경로 불일치 근본차단).
    env = os.environ.get('MS_GEOM_FILE')
    if env:
        return env
    return os.path.join(_shotdir(), 'app_geom.json')


def _shotdir():
    # 스크립트 SHOTDIR 규칙과 동일: ${TMPDIR:-/tmp}/kongtrol_play_shots.
    # MS_GEOM_FILE 이 주어졌으면 그 디렉토리를 SHOTDIR 로 재사용(완전 일치).
    env = os.environ.get('MS_GEOM_FILE')
    if env:
        return os.path.dirname(env)
    base = os.environ.get('TMPDIR', '/tmp')
    return os.path.join(base, 'kongtrol_play_shots')


class App:
    def __init__(self, dump=None, preopen=None):
        self.opened = [[False]*COLS for _ in range(ROWS)]
        self.flagged = [[False]*COLS for _ in range(ROWS)]
        # ★preopen: 초기에 열어둘 셀 목록(실제 플레이 진행 상태 = 숫자 드러난 보드).
        #   합성입력(가짜 클릭)이 아니라 상태 시드 → 권한 없이도 "플레이 중" 화면 재현.
        for (r, c) in (preopen or []):
            if 0 <= r < ROWS and 0 <= c < COLS:
                self.opened[r][c] = True
        self.root = tk.Tk()
        self.root.title("Minesweeper")
        # ★창 위치 = MS_WINPOS 환경변수("x,y")로 지정 가능(locator 검증: 창 이동 케이스). 기본 300,300.
        pos = os.environ.get('MS_WINPOS', '300,300')
        try:
            wx, wy = (int(v) for v in pos.split(','))
        except Exception:
            wx, wy = 300, 300
        self.root.geometry(f"{COLS*CELL}x{ROWS*CELL}+{wx}+{wy}")
        self.root.resizable(False, False)
        self.cv = tk.Canvas(self.root, width=COLS*CELL, height=ROWS*CELL, highlightthickness=0)
        self.cv.pack()
        self.cv.bind('<Button-1>', self.on_left)
        self.cv.bind('<Button-2>', self.on_right)
        self.cv.bind('<Button-3>', self.on_right)
        self.draw()
        self.root.attributes('-topmost', True)
        self.root.lift()
        if dump:
            self.root.update_idletasks(); self.root.update()
            self.dump_png(dump)
            self.root.destroy()

    def draw(self):
        self.cv.delete('all')
        for r in range(ROWS):
            for c in range(COLS):
                x0, y0 = c*CELL, r*CELL
                if self.flagged[r][c]:
                    bg = '#ffff00'  # 깃발=노랑
                elif self.opened[r][c]:
                    bg = '#f0f0f0'  # 열림=밝은회색
                else:
                    bg = '#a0a0a0'  # 닫힘=회색(160,160,160)
                self.cv.create_rectangle(x0, y0, x0+CELL, y0+CELL, fill=bg, outline='#808080')
                if self.opened[r][c]:
                    v = SOLUTION[r][c]
                    if v in NUMCOLOR:
                        self.cv.create_text(x0+CELL//2, y0+CELL//2, text=v,
                                            fill=NUMCOLOR[v], font=('Helvetica', 28, 'bold'))

    def on_left(self, e):
        c, r = e.x//CELL, e.y//CELL
        if 0 <= r < ROWS and 0 <= c < COLS:
            self.opened[r][c] = True
            print(f"[app] LEFT open r{r}c{c} -> {SOLUTION[r][c]} (synthetic input OK)", flush=True)
            self.draw()

    def on_right(self, e):
        c, r = e.x//CELL, e.y//CELL
        if 0 <= r < ROWS and 0 <= c < COLS:
            self.flagged[r][c] = not self.flagged[r][c]
            print(f"[app] RIGHT flag r{r}c{c}", flush=True)
            self.draw()

    def dump_png(self, path):
        # 현재 캔버스를 PostScript→PNG 대신, 격자 상태를 PIL 없이 직접 PNG 인코딩은 복잡.
        # 대신 Tk 캔버스 postscript 저장(벡터) → 여기선 상태를 텍스트로도 남김.
        ps = path.replace('.png', '.ps')
        self.cv.postscript(file=ps, colormode='color')
        print(f"[app] board postscript saved: {ps}", flush=True)

    def _backing_scale(self):
        # 물리 프레임버퍼 폭 / 논리 스크린 폭 = Retina backing scale.
        # screencapture 로 전체화면 1장 찍어 실제 px 폭 확인(가장 신뢰 가능한 실측).
        # ★probe 저장 위치 = geom 파일과 동일 SHOTDIR(/tmp 하드코딩 제거, 단일 소스).
        import subprocess, struct
        try:
            probe = os.path.join(_shotdir(), '_scale_probe.png')
            os.makedirs(os.path.dirname(probe), exist_ok=True)
            subprocess.run(['screencapture', '-x', '-t', 'png', probe],
                           capture_output=True, timeout=10)
            with open(probe, 'rb') as f:
                f.read(16); w = struct.unpack('>I', f.read(4))[0]  # IHDR width
            logical_w = self.root.winfo_screenwidth()
            if w and logical_w:
                return round(w / logical_w, 4)
        except Exception as e:
            print(f"[app] scale probe 실패({e}) → fallback 논리=물리(1.0)", flush=True)
        return 1.0

    def emit_geometry(self):
        # ★근본: 요청좌표(+300+300)가 아니라 [실제 창 물리좌표]를 산출해 파일로 출력.
        #   Tkinter winfo_rootx/rooty = 논리(pt). Retina scale = 물리px/pt.
        #   kongtrol xcap 캡처는 물리px 기준 → 이 값을 넘겨야 격자가 정확히 맞음.
        self.root.update_idletasks(); self.root.update()
        lx, ly = self.root.winfo_rootx(), self.root.winfo_rooty()   # 논리 좌상단
        lw, lh = self.root.winfo_width(), self.root.winfo_height()
        # ★scale = [물리 프레임버퍼 px] / [Tkinter 논리 px]. winfo_fpixels 는 Retina 에서 1.0 오답
        #   → screencapture 로 실제 캡처 크기(물리) 얻어 논리 screenwidth 로 나눠 정확 산출.
        scale = self._backing_scale()
        px, py = int(lx*scale), int(ly*scale)
        pw, ph = int(lw*scale), int(lh*scale)
        geo = {"logical": [lx, ly, lw, lh], "scale": scale,
               "physical": [px, py, pw, ph], "cell_logical": CELL,
               "cell_physical": int(CELL*scale), "rows": ROWS, "cols": COLS}
        gf = _geom_file()
        os.makedirs(os.path.dirname(gf), exist_ok=True)
        # ★원자적 쓰기: temp 에 쓴 뒤 rename → 스크립트 폴링이 반쪽 파일 읽는 경합 방지.
        tmp = gf + '.tmp'
        with open(tmp, 'w') as f: json.dump(geo, f)
        os.replace(tmp, gf)
        print(f"[app] geometry -> {gf}: {geo}", flush=True)

    def run(self):
        # ★HUMAN-ONLY-IO(ORCH_DECISION): 앱은 스스로 활성화하지 않음(pyobjc·NSApp 금지).
        #   창을 전면에 올리기만(topmost·lift). key window 획득은 kongtrol 이 [사람처럼 창을
        #   좌클릭 1회] 해서 얻는다(사람이 창을 눌러 활성화하는 것과 동일).
        self.root.attributes('-topmost', True); self.root.lift()
        self.emit_geometry()
        print(f"[app] ready native minesweeper {COLS*CELL}x{ROWS*CELL} CELL={CELL}", flush=True)
        self.root.mainloop()

if __name__ == '__main__':
    dump = None
    if '--dump' in sys.argv:
        i = sys.argv.index('--dump')
        dump = sys.argv[i+1] if i+1 < len(sys.argv) else '/tmp/ms_board.png'
    # --preopen "r,c;r,c;..." : 초기 오픈 셀(실제 플레이 진행 화면)
    preopen = []
    if '--preopen' in sys.argv:
        i = sys.argv.index('--preopen')
        if i+1 < len(sys.argv):
            for pair in sys.argv[i+1].split(';'):
                if ',' in pair:
                    r, c = pair.split(','); preopen.append((int(r), int(c)))
    App(dump=dump, preopen=preopen).run() if not dump else App(dump=dump, preopen=preopen)
