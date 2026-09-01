#!/usr/bin/env python3
"""a_361: place bg 0,0,1920,1080 + Google 710,338,500,92. Methods M1-M4. BAN cmd-a, HEX-as-text, 종료."""
import json, subprocess, time
from pathlib import Path

K = "/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol"
OUT = Path("/Users/bumsuklee/git/kong-bot/kaymaps/keynote")
PROTO_A = Path("/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/protocol/a")
PROTO_AR = Path("/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/protocol/ar")
notes = []
t0 = time.time()


def run(a, timeout=90):
    return subprocess.run(a, capture_output=True, text=True, timeout=timeout)


def click(x, y):
    run([K, "--yes", "input", "click", str(int(round(x))), str(int(round(y)))])


def drag(x1, y1, x2, y2):
    run([K, "--yes", "input", "drag",
         str(int(round(x1))), str(int(round(y1))),
         str(int(round(x2))), str(int(round(y2))), "--scale", "1"])


def chord(m, k):
    run([K, "--yes", "input", "chord", m, k])


def text(s):
    run([K, "--yes", "input", "text", s])


def key(n):
    run([K, "--yes", "input", "key", n])


def dump(pid):
    r = run([K, "--json", "see", "--a11y", "--pid", str(pid)], timeout=60)
    if r.returncode != 0:
        return []
    j = json.loads(r.stdout)
    d = j.get("data", j)
    if isinstance(d, list):
        return d
    for v in d.values():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            return v
    return []


def menus(els):
    return [e.get("label") for e in els if e.get("role") == "AXMenuBarItem" and e.get("label")]


def windows(els):
    wins = []
    for e in els:
        if e.get("role") == "AXWindow":
            w, h = e.get("w") or 0, e.get("h") or 0
            wins.append({"label": e.get("label"), "x": e.get("x"), "y": e.get("y"),
                         "w": w, "h": h, "area": w * h})
    wins.sort(key=lambda z: z["area"], reverse=True)
    return wins


def max_doc(wins):
    for w in wins:
        lab = w.get("label") or ""
        if "서체" in lab or "색상" in lab:
            continue
        if (w["w"] or 0) >= 800:
            return w
    return wins[0] if wins else None


def list_left(els):
    out = []
    for e in els:
        lab = (e.get("label") or "").strip()
        cx, cy = e.get("cx") or 0, e.get("cy") or 0
        if cx > 450 or cy < 100 or cy > 900 or not lab:
            continue
        if e.get("role") in ("AXTextField", "AXStaticText", "AXCell"):
            out.append(e)
    seen, uniq = set(), []
    for e in out:
        k = (e.get("label"), round(e.get("cy") or 0, 0))
        if k in seen:
            continue
        seen.add(k)
        uniq.append(e)
    return uniq


def display_w(els):
    mw = max_doc(windows(els)) or {}
    return float(mw.get("w") or 2056)


def on_screen_fields(els, dw):
    """AXTextFields with cx < display width (not off-screen inspector)."""
    out = []
    for e in els:
        if e.get("role") != "AXTextField":
            continue
        cx = e.get("cx") or 0
        if cx <= 0 or cx >= dw - 20:
            continue
        lab = (e.get("label") or "").strip()
        out.append(e)
    return out


def find_label(els, *subs):
    for e in els:
        lab = e.get("label") or ""
        if all(s in lab for s in subs):
            return e
    return None


def set_field(e, val):
    click(e["cx"], e["cy"]); time.sleep(0.2)
    # triple-click select without cmd-a BAN
    click(e["cx"], e["cy"]); time.sleep(0.08)
    click(e["cx"], e["cy"]); time.sleep(0.12)
    key("delete"); time.sleep(0.08)
    text(str(val)); time.sleep(0.12)
    key("return"); time.sleep(0.35)


def ensure_list_on(pid):
    els = dump(pid)
    if list_left(els):
        return els
    click(419, 20); time.sleep(0.35)
    els = dump(pid)
    show = find_label(els, "대상체 목록 보기")
    if show:
        click(show["cx"], show["cy"]); time.sleep(0.5)
        notes.append("list_show")
    els = dump(pid)
    return els


def ensure_max(pid):
    for _ in range(2):
        els = dump(pid)
        mw = max_doc(windows(els))
        notes.append("MAX={}".format(mw))
        if mw and (mw["w"] or 0) >= 2000 and (mw["h"] or 0) >= 1200:
            notes.append("FS_ok")
            return els
        click(419, 20); time.sleep(0.35)
        els = dump(pid)
        start = find_label(els, "전체 화면 시작")
        if start:
            click(start["cx"], start["cy"]); time.sleep(1.4)
            notes.append("fs_start")
        elif mw:
            click((mw.get("x") or 0) + 54, (mw.get("y") or 0) + 20); time.sleep(1.0)
    return dump(pid)


def m1_slide_bg(pid):
    """M1: slide thumbnail → 배경 well dark if possible (no HEX type)."""
    notes.append("M1_start")
    els = dump(pid)
    # click slide 1 thumbnail left
    thumbs = [e for e in els if e.get("role") in ("AXButton", "AXImage", "AXCell", "AXGroup")
              and (e.get("cx") or 999) < 120 and 80 < (e.get("cy") or 0) < 400]
    # hard click known slide1 area
    click(70, 160); time.sleep(0.4)
    notes.append("slide1_thumb_click")
    # 포맷 → 배경
    els = dump(pid)
    # format radio
    fmt = next((e for e in els if e.get("label") == "포맷" and e.get("role") in
                ("AXRadioButton", "AXButton", "AXCheckBox")), None)
    if fmt and (fmt.get("cx") or 0) < display_w(els):
        click(fmt["cx"], fmt["cy"]); time.sleep(0.4)
        notes.append("fmt_click {},{}".format(fmt.get("cx"), fmt.get("cy")))
    els = dump(pid)
    bg = find_label(els, "배경")
    if bg and (bg.get("cx") or 0) < display_w(els):
        click(bg["cx"], bg["cy"]); time.sleep(0.4)
        notes.append("bg_label {},{}".format(bg.get("cx"), bg.get("cy")))
        # try color well / 현재 채우기
        els = dump(pid)
        well = find_label(els, "현재 채우기") or find_label(els, "채우기")
        if well and (well.get("cx") or 0) < display_w(els):
            click(well["cx"], well["cy"]); time.sleep(0.5)
            notes.append("well_click")
            # pick dark swatch if color panel shows — click dark area of palette without typing HEX
            # BAN type HEX as text
            click(200, 400); time.sleep(0.3)  # speculative dark in color picker
            key("escape"); time.sleep(0.2)
            notes.append("M1_well_dark_attempt")
            return True
        notes.append("M1_no_well_on_screen")
    else:
        notes.append("M1_no_배경_on_screen")
    key("escape"); time.sleep(0.2)
    return False


def m2_rect_size_fields(pid):
    """M2: select 사각형 → 포맷 정렬 fields 너비/높이/X/Y if on-screen."""
    notes.append("M2_start")
    els = ensure_list_on(pid)
    rects = [e for e in list_left(els) if "사각" in (e.get("label") or "")]
    if not rects:
        notes.append("M2_no_rect")
        return False
    click(rects[0]["cx"], rects[0]["cy"]); time.sleep(0.4)
    notes.append("M2_sel_rect")
    # unlock if present
    els = dump(pid)
    un = next((e for e in els if e.get("label") == "잠금 해제" and (e.get("cx") or 0) < 400), None)
    if un:
        click(un["cx"], un["cy"]); time.sleep(0.35)
        notes.append("M2_unlock")
    # format + arrange
    els = dump(pid)
    dw = display_w(els)
    fmt = next((e for e in els if e.get("label") == "포맷" and e.get("role") in
                ("AXRadioButton", "Button", "AXButton", "AXCheckBox") and (e.get("cx") or 0) < dw), None)
    if fmt:
        click(fmt["cx"], fmt["cy"]); time.sleep(0.35)
    els = dump(pid)
    # 정렬 tab only if on-screen (BAN click 2284 정렬)
    arr = next((e for e in els if e.get("label") == "정렬" and (e.get("cx") or 0) < dw - 50
                and e.get("role") in ("AXRadioButton", "AXButton", "AXCheckBox", "AXTab", "AXStaticText")), None)
    if arr:
        click(arr["cx"], arr["cy"]); time.sleep(0.4)
        notes.append("M2_정렬 {},{}".format(arr.get("cx"), arr.get("cy")))
    else:
        notes.append("M2_정렬_offscreen_skip")
    els = dump(pid)
    dw = display_w(els)
    # fields with labels 너비/높이 or pt values on-screen
    labeled = []
    for e in els:
        lab = (e.get("label") or "")
        cx = e.get("cx") or 0
        if cx <= 0 or cx >= dw - 20:
            continue
        if e.get("role") != "AXTextField":
            continue
        if any(k in lab for k in ("너비", "높이", "W", "H")) or lab.endswith("pt"):
            labeled.append(e)
    notes.append("M2_fields={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in labeled[:12]]))
    # Prefer y~266 for w/h, y~346 for x/y pattern from prior scripts — only if cx < dw
    wh = sorted([e for e in labeled if 240 < (e.get("cy") or 0) < 300], key=lambda e: e.get("cx") or 0)
    xy = sorted([e for e in labeled if 320 < (e.get("cy") or 0) < 380], key=lambda e: e.get("cx") or 0)
    ok = False
    if len(wh) >= 2:
        set_field(wh[0], 1920); set_field(wh[1], 1080)
        notes.append("M2_set_WH_1920_1080")
        ok = True
    if len(xy) >= 2:
        set_field(xy[0], 0); set_field(xy[1], 0)
        notes.append("M2_set_XY_0_0")
        ok = True
    if not ok:
        # any two smallest pt as size
        pts = sorted([e for e in labeled if (e.get("label") or "").endswith("pt")],
                     key=lambda e: float((e.get("label") or "9999pt").replace("pt", "") or 9999))
        if len(pts) >= 2 and float((pts[0].get("label") or "999").replace("pt", "") or 999) < 500:
            set_field(pts[0], 1920); set_field(pts[1], 1080)
            notes.append("M2_set_small_pts")
            ok = True
    notes.append("M2_ok={}".format(ok))
    return ok


def m3_insert_rect_drag(pid):
    """M3: 삽입>도형>직사각형 then drag handles toward full slide."""
    notes.append("M3_start")
    els = dump(pid)
    ins = next((e for e in els if e.get("role") == "AXMenuBarItem" and e.get("label") == "삽입"), None)
    if not ins:
        notes.append("M3_no_삽입"); return False
    click(ins["cx"], ins["cy"]); time.sleep(0.4)
    els = dump(pid)
    shape = next((e for e in els if e.get("label") == "도형"), None)
    if shape:
        click(shape["cx"], shape["cy"]); time.sleep(0.5)
        notes.append("M3_도형 {},{}".format(shape.get("cx"), shape.get("cy")))
        els = dump(pid)
        rect = next((e for e in els if e.get("label") and "직사각" in e.get("label")), None)
        if not rect:
            # first shape in palette approx
            rect = next((e for e in els if e.get("label") == "사각형" or (e.get("role") == "AXButton" and "사각" in (e.get("label") or ""))), None)
        if rect:
            click(rect["cx"], rect["cy"]); time.sleep(0.6)
            notes.append("M3_직사각 {},{}".format(rect.get("cx"), rect.get("cy")))
        else:
            # click palette position near submenu
            click((shape.get("cx") or 340) + 80, (shape.get("cy") or 188) + 40); time.sleep(0.6)
            notes.append("M3_palette_fallback")
    else:
        notes.append("M3_no_도형"); key("escape"); return False
    # drag SE from center stamp toward BR of canvas; NW toward TL
    # canvas approx for MAX window
    els = dump(pid)
    mw = max_doc(windows(els)) or {"x": 0, "y": 39, "w": 2056, "h": 1290}
    # approximate slide content area
    c0x, c0y = 400, 180
    c1x, c1y = min(1900, (mw.get("x") or 0) + (mw.get("w") or 2000) - 80), min(1200, (mw.get("y") or 0) + (mw.get("h") or 1200) - 80)
    # assume new rect near center
    cx, cy = 1100, 700
    for i in range(3):
        drag(cx + 40 + i * 10, cy + 40 + i * 10, c1x, c1y)
        time.sleep(0.4)
        notes.append("M3_SE_drag_{}".format(i + 1))
    for i in range(2):
        drag(cx - 40, cy - 40, c0x, c0y)
        time.sleep(0.4)
        notes.append("M3_NW_drag_{}".format(i + 1))
    notes.append("M3_done")
    return True


def m4_google(pid):
    """M4: 삽입 텍스트 상자 Google; size/pos fields if on-screen else drag."""
    notes.append("M4_start")
    els = dump(pid)
    ins = next((e for e in els if e.get("role") == "AXMenuBarItem" and e.get("label") == "삽입"), None)
    if not ins:
        notes.append("M4_no_삽입"); return False
    click(ins["cx"], ins["cy"]); time.sleep(0.4)
    els = dump(pid)
    tb = next((e for e in els if e.get("label") == "텍스트 상자"), None)
    if not tb:
        notes.append("M4_no_textbox"); key("escape"); return False
    click(tb["cx"], tb["cy"]); time.sleep(0.5)
    # place near target screen approx of slide 710,338
    # map: slide origin ~ canvas TL; rough screen (400+710*scale) — use click 1000,450 then type
    click(1000, 450); time.sleep(0.35)
    text("Google"); time.sleep(0.35)
    notes.append("M4_typed_Google")
    # try fields
    els = dump(pid)
    dw = display_w(els)
    # 정렬 tab if on-screen
    arr = next((e for e in els if e.get("label") == "정렬" and (e.get("cx") or 0) < dw - 50
                and e.get("role") in ("AXRadioButton", "AXButton", "AXCheckBox")), None)
    if arr:
        click(arr["cx"], arr["cy"]); time.sleep(0.35)
    els = dump(pid)
    labeled = [e for e in els if e.get("role") == "AXTextField" and (e.get("cx") or 0) < dw - 20
               and ((e.get("label") or "").endswith("pt") or any(k in (e.get("label") or "") for k in ("너비", "높이")))]
    wh = sorted([e for e in labeled if 240 < (e.get("cy") or 0) < 300], key=lambda e: e.get("cx") or 0)
    xy = sorted([e for e in labeled if 320 < (e.get("cy") or 0) < 380], key=lambda e: e.get("cx") or 0)
    notes.append("M4_fields WH={} XY={}".format(
        [(e.get("label"), e.get("cx")) for e in wh[:4]],
        [(e.get("label"), e.get("cx")) for e in xy[:4]]))
    if len(wh) >= 2:
        set_field(wh[0], 500); set_field(wh[1], 92)
        notes.append("M4_set_500_92")
    if len(xy) >= 2:
        set_field(xy[0], 710); set_field(xy[1], 338)
        notes.append("M4_set_710_338")
    else:
        # drag text box origin toward ~710,338 screen-mapped
        # rough: drag from current to 900,420
        drag(1000, 450, 900, 420)
        time.sleep(0.35)
        notes.append("M4_drag_place")
    notes.append("M4_done")
    return True


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    run(["open", "-a", "Keynote"]); time.sleep(0.8)
    pr = run(["pgrep", "-x", "Keynote"])
    if pr.returncode != 0:
        notes.append("NO_PID"); return
    pid = pr.stdout.strip().split()[0]
    notes.append("PID {}".format(pid))

    ensure_max(pid)
    ensure_list_on(pid)
    notes.append("objs0={}".format([(e.get("label"), e.get("cy")) for e in list_left(dump(pid))]))

    m1 = m1_slide_bg(pid)
    m2 = m2_rect_size_fields(pid)
    m3 = m3_insert_rect_drag(pid)
    m4 = m4_google(pid)
    notes.append("methods_ok M1={} M2={} M3={} M4={}".format(m1, m2, m3, m4))

    els = dump(pid)
    notes.append("objs_final={}".format([(e.get("label"), e.get("cy")) for e in list_left(els)]))
    notes.append("wins_final={}".format(windows(els)))
    # dump pt fields for ar
    dw = display_w(els)
    pts = [(e.get("label"), e.get("cx"), e.get("cy")) for e in els
           if e.get("role") == "AXTextField" and (e.get("cx") or 0) < dw
           and ((e.get("label") or "").endswith("pt") or any(k in (e.get("label") or "") for k in ("너비", "높이")))]
    notes.append("fields_on_screen={}".format(pts[:20]))

    shot = OUT / "slide_361.png"
    run(["open", "-a", "Keynote"]); time.sleep(0.25)
    run(["screencapture", "-x", str(shot)])
    if shot.exists():
        run(["cp", str(shot), str(PROTO_A / "slide_361.png")])
        run(["cp", str(shot), str(PROTO_AR / "slide_361.png")])
        notes.append("shot={}".format(shot.stat().st_size))
    notes.append("ELAPSED={}".format(int(time.time() - t0)))
    (OUT / "a361_notes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")
    print("DONE")
    for n in notes:
        print(n)


if __name__ == "__main__":
    main()
