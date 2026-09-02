"""Image edit service — telegram 자연어 이미지 편집(u_3384~3386, A안).

봇이 refs/에 저장한 이미지 + 유저 자연어 지시 → PIL 편집 연산 수행 → 결과 저장.
연산은 순수 계산(로컬 PIL) — 좌표·색 자동측정 헬퍼 포함(배너 전화번호 편집 u_3380 로직 일반화).

연산 종류(MVP): replace_text_region / erase_region / crop / resize / add_text / blur_region.
자연어→연산 매핑은 orch(호출자)가 판단해 op dict 로 넘긴다(이 모듈=실행 엔진).
"""
from __future__ import annotations

import statistics as _st
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

# 굵은 한글+숫자 지원 폰트(macOS 기본). 없으면 fallback.
_FONT_CANDIDATES = [
    "/Library/Fonts/NotoSansCJKkr-Bold.otf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
]
_JOBS_DIR = Path(__file__).resolve().parents[2] / "jobs" / "image-edits"


def _font(size: int, path: Optional[str] = None) -> ImageFont.FreeTypeFont:
    for fp in ([path] if path else []) + _FONT_CANDIDATES:
        if fp and Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _sample_bg(im: Image.Image, box: tuple[int, int, int, int]) -> tuple[int, int, int]:
    """box 주변(바깥 테두리) 픽셀 최빈 근사색 — 덮개 배경색 자동추정."""
    px = im.load()
    w, h = im.size
    x0, y0, x1, y1 = box
    ring: list[tuple[int, int, int]] = []
    for x in range(max(0, x0 - 4), min(w, x1 + 4)):
        for yy in (max(0, y0 - 4), min(h - 1, y1 + 3)):
            ring.append(px[x, yy][:3])
    for y in range(max(0, y0 - 4), min(h, y1 + 4)):
        for xx in (max(0, x0 - 4), min(w - 1, x1 + 3)):
            ring.append(px[xx, y][:3])
    if not ring:
        return (0, 0, 0)
    return tuple(round(_st.median(c[i] for c in ring)) for i in range(3))  # type: ignore


def _fit_font_to_width(draw, text, target_w, path=None, hi=90) -> ImageFont.FreeTypeFont:
    size = 8
    while size < hi:
        f = _font(size + 1, path)
        bb = draw.textbbox((0, 0), text, font=f)
        if bb[2] - bb[0] >= target_w:
            break
        size += 1
    return _font(size, path)


# ---------- 편집 연산 ----------

def replace_text_region(
    im: Image.Image, box: tuple[int, int, int, int], new_text: str,
    fg: tuple[int, int, int] = (247, 247, 250), bg: Optional[tuple] = None,
    font_path: Optional[str] = None,
) -> Image.Image:
    """box 영역을 bg 로 덮고 new_text 를 box 폭에 맞춰 중앙배치(전화번호 교체 등)."""
    im = im.convert("RGB")
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = box
    bgc = bg or _sample_bg(im, box)
    d.rectangle(box, fill=bgc)
    tw_target = x1 - x0
    f = _fit_font_to_width(d, new_text, tw_target, font_path)
    bb = d.textbbox((0, 0), new_text, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    tx = x0 - bb[0] + (tw_target - tw) // 2
    ty = y0 - bb[1] + ((y1 - y0) - th) // 2
    d.text((tx, ty), new_text, font=f, fill=fg)
    return im


def erase_region(im, box, bg=None) -> Image.Image:
    im = im.convert("RGB")
    d = ImageDraw.Draw(im)
    d.rectangle(box, fill=(bg or _sample_bg(im, box)))
    return im


def crop(im, box) -> Image.Image:
    return im.convert("RGB").crop(box)


def resize(im, w, h) -> Image.Image:
    return im.convert("RGB").resize((int(w), int(h)))


def add_text(im, xy, text, size=32, fg=(255, 255, 255), font_path=None,
             stroke=0, stroke_fill=(0, 0, 0)) -> Image.Image:
    im = im.convert("RGB")
    d = ImageDraw.Draw(im)
    d.text(xy, text, font=_font(size, font_path), fill=fg,
           stroke_width=stroke, stroke_fill=stroke_fill)
    return im


def blur_region(im, box, radius=8) -> Image.Image:
    from PIL import ImageFilter
    im = im.convert("RGB")
    region = im.crop(box).filter(ImageFilter.GaussianBlur(radius))
    im.paste(region, box[:2])
    return im


# ---------- 좌표 헬퍼(자연어 위치어 → box) ----------

def region_by_anchor(im: Image.Image, anchor: str) -> tuple[int, int, int, int]:
    """'우측 하단'/'좌측 상단'/'중앙' 등 위치어 → 대략 box(1/3 그리드)."""
    w, h = im.size
    cx = {"좌": (0, w // 3), "중": (w // 3, 2 * w // 3), "우": (2 * w // 3, w)}
    cy = {"상": (0, h // 3), "중": (h // 3, 2 * h // 3), "하": (2 * h // 3, h)}
    ax = next((k for k in cx if k in anchor), "중")
    ay = next((k for k in cy if k in anchor), "중")
    x0, x1 = cx[ax]
    y0, y1 = cy[ay]
    return (x0, y0, x1, y1)


# ---------- 실행 엔트리 ----------

def run_ops(src_path: str, ops: list[dict], out_name: Optional[str] = None) -> str:
    """ops = [{"op":"replace_text_region","box":[..],"new_text":".."}, ...] 순차 적용 후 저장.

    지원 op: replace_text_region / erase_region / crop / resize / add_text / blur_region.
    반환: 저장경로(jobs/image-edits/).
    """
    im = Image.open(src_path).convert("RGB")
    for o in ops:
        k = o["op"]
        if k == "replace_text_region":
            im = replace_text_region(im, tuple(o["box"]), o["new_text"],
                                     tuple(o.get("fg", (247, 247, 250))),
                                     tuple(o["bg"]) if o.get("bg") else None,
                                     o.get("font_path"))
        elif k == "erase_region":
            im = erase_region(im, tuple(o["box"]), tuple(o["bg"]) if o.get("bg") else None)
        elif k == "crop":
            im = crop(im, tuple(o["box"]))
        elif k == "resize":
            im = resize(im, o["w"], o["h"])
        elif k == "add_text":
            im = add_text(im, tuple(o["xy"]), o["text"], o.get("size", 32),
                          tuple(o.get("fg", (255, 255, 255))), o.get("font_path"),
                          o.get("stroke", 0), tuple(o.get("stroke_fill", (0, 0, 0))))
        elif k == "blur_region":
            im = blur_region(im, tuple(o["box"]), o.get("radius", 8))
        else:
            raise ValueError(f"unknown op: {k}")
    _JOBS_DIR.mkdir(parents=True, exist_ok=True)
    name = out_name or (Path(src_path).stem + "_edited.jpg")
    out = _JOBS_DIR / name
    im.save(out, quality=95)
    return str(out)
