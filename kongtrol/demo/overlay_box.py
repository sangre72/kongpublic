#!/usr/bin/env python3
"""overlay_box.py — 전체화면 스샷 위에 locator 탐지 Region 을 빨간 박스로 오버레이.
verify_locator.sh 가 환경변수로 호출: MS_IN(원본 png)·MS_OUT(출력)·MS_BOX("x,y,w,h" 물리)·MS_LABEL.
좌표계: locator region = 물리 프레임버퍼 px. screencapture 전체화면도 물리 px → 좌표 일치."""
import os
from PIL import Image, ImageDraw

inp = os.environ["MS_IN"]
out = os.environ["MS_OUT"]
box = os.environ["MS_BOX"]
label = os.environ.get("MS_LABEL", "")

x, y, w, h = (int(v) for v in box.split(","))
img = Image.open(inp).convert("RGB")
d = ImageDraw.Draw(img)
# 빨간 박스(두께 6px). 탐지 region 사각 테두리.
for t in range(6):
    d.rectangle([x - t, y - t, x + w + t, y + h + t], outline=(255, 0, 0))
# 라벨(박스 위). 폰트 지정 없이 기본.
d.text((x + 4, max(0, y - 22)), f"locator: {label} ({x},{y},{w},{h})", fill=(255, 0, 0))
img.save(out)
print(f"[overlay] {out} box=({x},{y},{w},{h})")
