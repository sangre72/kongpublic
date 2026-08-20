#!/usr/bin/env python3
"""네이티브 지뢰찾기 앱 (pygame/SDL2) — kongtrol M7 폐루프 실마우스클릭 데모 대상.
★Tkinter 대체(ORCH_DECISION#2): Tkinter macOS 는 합성 CGEvent 클릭을 거부하나,
  pygame(SDL2 네이티브 창)은 합성 클릭을 정상 수신(실측 확인). 브라우저 아님(u_10 준수).
고정 격자·관용색으로 kongtrol 픽셀색 인식 대상 + 클릭 시 셀 '열어' 숫자 드러냄(실제 플레이).
geom(창 물리좌표·backing scale)을 app_geom.json 으로 방출 = Tkinter 앱과 동일 규약(3R)."""
import pygame
import sys
import os
import json
import struct
import subprocess

CELL = 80
ROWS = COLS = 5
# 0=빈칸, 1~3=숫자(관용 색), M=지뢰. 초기 전부 닫힘, 클릭 시 open.
SOLUTION = [
    ['1', 'M', '1', '0', '0'],
    ['1', '1', '1', '0', '0'],
    ['0', '0', '0', '0', '0'],
    ['0', '1', '1', '1', '0'],
    ['0', '1', 'M', '1', '0'],
]
# 관용 지뢰찾기 팔레트(Tkinter 앱과 동일 — 인식 로직 공유).
CLOSED = (160, 160, 160)   # 닫힘 회색
OPENED = (240, 240, 240)   # 열림 밝은회색
LINE = (128, 128, 128)     # 격자선
FLAG_BG = (255, 255, 0)    # 깃발 노랑
NUMCOLOR = {'1': (0, 0, 255), '2': (0, 128, 0), '3': (255, 0, 0)}


def _shotdir():
    env = os.environ.get('MS_GEOM_FILE')
    if env:
        return os.path.dirname(env)
    base = os.environ.get('TMPDIR', '/tmp')
    return os.path.join(base, 'kongtrol_play_shots')


def _geom_file():
    return os.environ.get('MS_GEOM_FILE') or os.path.join(_shotdir(), 'app_geom.json')


def _backing_scale(logical_w):
    # 물리 프레임버퍼 폭 / 논리 스크린 폭 = Retina backing scale(screencapture 실측).
    try:
        probe = os.path.join(_shotdir(), '_scale_probe.png')
        os.makedirs(os.path.dirname(probe), exist_ok=True)
        subprocess.run(['screencapture', '-x', '-t', 'png', probe],
                       capture_output=True, timeout=10)
        with open(probe, 'rb') as f:
            f.read(16)
            w = struct.unpack('>I', f.read(4))[0]
        if w and logical_w:
            return round(w / logical_w, 4)
    except Exception as e:
        print(f"[pg] scale probe 실패({e}) → 1.0", flush=True)
    return 1.0


class Game:
    def __init__(self):
        self.opened = [[False] * COLS for _ in range(ROWS)]
        self.flagged = [[False] * COLS for _ in range(ROWS)]
        # 창 위치 = MS_WINPOS("x,y") 환경변수(locator 이동검증). 기본 300,300.
        pos = os.environ.get('MS_WINPOS', '300,300')
        os.environ['SDL_VIDEO_WINDOW_POS'] = pos.strip()
        pygame.init()
        self.w, self.h = COLS * CELL, ROWS * CELL
        # ★always-on-top: locator 자동탐지가 전체화면에서 창을 보려면 최전면 유지 필요
        #   (Tkinter -topmost 대응). SDL_WINDOW_ALWAYS_ON_TOP 플래그.
        flags = 0
        if hasattr(pygame, 'WINDOW_ALWAYS_ON_TOP'):
            flags = pygame.WINDOW_ALWAYS_ON_TOP
        try:
            self.screen = pygame.display.set_mode((self.w, self.h), flags)
        except Exception:
            self.screen = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption("Minesweeper")
        self.font = pygame.font.SysFont('Helvetica', 40, bold=True)
        self.draw()
        self.emit_geometry()

    def draw(self):
        for r in range(ROWS):
            for c in range(COLS):
                x0, y0 = c * CELL, r * CELL
                if self.flagged[r][c]:
                    bg = FLAG_BG
                elif self.opened[r][c]:
                    bg = OPENED
                else:
                    bg = CLOSED
                pygame.draw.rect(self.screen, bg, (x0, y0, CELL, CELL))
                pygame.draw.rect(self.screen, LINE, (x0, y0, CELL, CELL), 1)
                if self.opened[r][c]:
                    v = SOLUTION[r][c]
                    if v in NUMCOLOR:
                        img = self.font.render(v, True, NUMCOLOR[v])
                        rect = img.get_rect(center=(x0 + CELL // 2, y0 + CELL // 2))
                        self.screen.blit(img, rect)
        pygame.display.flip()

    def on_click(self, pos, right=False):
        x, y = pos
        c, r = x // CELL, y // CELL
        if 0 <= r < ROWS and 0 <= c < COLS:
            if right:
                self.flagged[r][c] = not self.flagged[r][c]
                print(f"[pg] RIGHT flag r{r}c{c}", flush=True)
            else:
                self._open_flood(r, c)
                print(f"[pg] LEFT open r{r}c{c} -> {SOLUTION[r][c]} (synthetic click OK)", flush=True)
            self.draw()

    def _open_flood(self, r, c):
        # 실제 지뢰찾기 규칙: 빈칸(0) 을 열면 인접 8칸 자동 확장(flood-fill) → 숫자 경계가
        #   드러나 kongtrol 확정 룰이 진행할 수 있게. 지뢰는 열지 않음.
        if not (0 <= r < ROWS and 0 <= c < COLS) or self.opened[r][c] or SOLUTION[r][c] == 'M':
            return
        self.opened[r][c] = True
        if SOLUTION[r][c] == '0':
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr or dc:
                        self._open_flood(r + dr, c + dc)

    def emit_geometry(self):
        # SDL 창의 실제 위치는 SDL_VIDEO_WINDOW_POS(논리) 기준. Retina scale 로 물리 산출.
        # 논리 스크린 폭: pygame display Info 는 창 크기라 부적합 → screencapture 물리 대비 근사.
        # 논리 좌상단 = MS_WINPOS(요청). SDL 은 대체로 요청 위치 준수(Tkinter 보다 정확).
        pos = os.environ.get('MS_WINPOS', '300,300')
        lx, ly = (int(v) for v in pos.split(','))
        # 논리 스크린 폭 추정: AppKit 없이 — screencapture 물리폭 / 알려진 비율. 여기선
        # 물리폭을 2로 나눠 논리 근사(Retina 2x 관례) 후 scale 재계산은 물리/논리.
        # 더 정확히: probe 물리폭 / (물리폭/2) = 2.0. 실측 scale 로 통일.
        probe_w = self._probe_physical_width()
        logical_screen_w = probe_w // 2 if probe_w else 0  # Retina 2x 관례 근사
        scale = _backing_scale(logical_screen_w) if logical_screen_w else 2.0
        px, py = int(lx * scale), int(ly * scale)
        pw, ph = int(self.w * scale), int(self.h * scale)
        geo = {"logical": [lx, ly, self.w, self.h], "scale": scale,
               "physical": [px, py, pw, ph], "cell_logical": CELL,
               "cell_physical": int(CELL * scale), "rows": ROWS, "cols": COLS,
               "engine": "pygame"}
        gf = _geom_file()
        os.makedirs(os.path.dirname(gf), exist_ok=True)
        tmp = gf + '.tmp'
        with open(tmp, 'w') as f:
            json.dump(geo, f)
        os.replace(tmp, gf)
        print(f"[pg] geometry -> {gf}: {geo}", flush=True)

    def _probe_physical_width(self):
        try:
            probe = os.path.join(_shotdir(), '_scale_probe.png')
            os.makedirs(os.path.dirname(probe), exist_ok=True)
            subprocess.run(['screencapture', '-x', '-t', 'png', probe],
                           capture_output=True, timeout=10)
            with open(probe, 'rb') as f:
                f.read(16)
                return struct.unpack('>I', f.read(4))[0]
        except Exception:
            return 0

    def run(self):
        print(f"[pg] ready native(pygame) minesweeper {self.w}x{self.h} CELL={CELL}", flush=True)
        clock = pygame.time.Clock()
        running = True
        while running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    self.on_click(e.pos, right=(e.button == 3))
            self.draw()
            clock.tick(30)
        pygame.quit()


if __name__ == '__main__':
    # --preopen 은 pygame 데모에선 미사용(실클릭 완주가 목적 — preopen 금지, a_12).
    Game().run()
