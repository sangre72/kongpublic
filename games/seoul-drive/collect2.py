"""교사 시범주행 → 학습데이터 수집 (화면 전용판, 2026-09-14).

★왜 collect.py를 못 쓰나:
  기존 수집기는 AppleScript로 Chrome 탭에 JS를 실행해 교사 조작값을 받아왔다.
  그러나 (1) Chrome은 기본적으로 AppleScript JS 실행을 막고,
       (2) 아티팩트는 샌드박스 iframe 안이라 상위 탭에서 __teach 가 보이지 않는다.
  실측에서 둘 다 실패했다.

★대신: 교사가 스스로 주행하면서 자기 조작값을 캔버스에 숫자로 찍는다.
  여기서는 화면만 캡처해서 (픽셀, 조작값)을 얻는다 — 사람이 보는 것과 같은 경로.
  readout 형식:  KB v=45 st=0.00 th=1.00 cr=0 ln=4.9
"""
import time, os, json, subprocess, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cnn_drive as C

OUT = os.path.expanduser('~/kongbot_drive_data')
os.makedirs(OUT, exist_ok=True)

# 화면 좌표(물리픽셀). 1100폭 리사이즈 기준 좌표 × (4112/1100).
K = 4112/1100.0
RO = tuple(int(v*K) for v in (5, 412, 230, 430))     # readout 영역
CANVAS = tuple(int(v*K) for v in (5, 95, 360, 440))  # 게임 캔버스 영역

_GLYPH = {}
def _glyphs():
    """readout 폰트의 숫자/기호 템플릿을 최초 1회 학습한다."""
    return _GLYPH

def parse_readout(img):
    """readout 크롭(RGB ndarray) → dict. 초록 글자만 남겨 이진화 후 열 단위 분해."""
    a = img.astype(int)
    m = (np.abs(a - np.array([0x7C, 0xFF, 0x9E])).sum(2) < 150)
    if m.sum() < 20: return None
    return m

def shot(path):
    subprocess.run(['screencapture', '-x', path], check=True)
    return Image.open(path).convert('RGB')
