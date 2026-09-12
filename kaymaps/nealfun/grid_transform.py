"""캡처 픽셀 → 클릭 논리좌표 변환.
★함정(2026-09-12): fastvis.grab() 은 BOARD 영역을 Retina 2배 해상도로 준다.
   캡처 픽셀을 그대로 클릭하면 좌표가 절반쯤 왼쪽/위로 어긋난다.
   반드시 이 변환을 거칠 것. 기준점 = Verify 버튼(a11y로 실좌표를 읽을 수 있는 유일한 요소).
"""
import subprocess
import numpy as np
import fastvis

KT = "/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol"

def verify_logical():
    """a11y 에서 Verify 버튼의 논리 중심좌표."""
    pid = subprocess.run(["pgrep", "-x", "Safari"], capture_output=True, text=True).stdout.split()[0]
    out = subprocess.run([KT, "see", "--a11y", "--pid", pid], capture_output=True, text=True).stdout
    for l in out.splitlines():
        if "Verify" in l and "@(" in l:
            p = l.split("@(")[1].split(")")[0].split(",")
            return int(p[0]), int(p[1])
    return None

def verify_capture():
    """캡처 이미지 안에서 Verify 버튼 중심 픽셀."""
    a = fastvis.grab().astype(int)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    btn = (b > 190) & (b > r + 70) & (b > g + 40)
    ys, xs = np.nonzero(btn)
    m = ys > a.shape[0] * 0.8
    if not m.any():
        return None
    return ((xs[m].min() + xs[m].max()) / 2, (ys[m].min() + ys[m].max()) / 2,
            xs[m].max() - xs[m].min())

def transform():
    """(scale, ox, oy) — 논리좌표 = 캡처픽셀/scale + offset."""
    lg = verify_logical(); cap = verify_capture()
    if not lg or not cap:
        return None
    cx, cy, wpx = cap
    scale = wpx / 85.0                      # Verify 버튼 논리 폭 = 85
    return scale, lg[0] - cx / scale, lg[1] - cy / scale

def to_click(px, py, t=None):
    t = t or transform()
    s, ox, oy = t
    return int(round(px / s + ox)), int(round(py / s + oy))
