#!/usr/bin/env python3
"""a_348: bring inspector on-screen OR slide bg fill; Google."""
import json, subprocess, time
from pathlib import Path

K = "/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol"
OUT = Path("/Users/bumsuklee/git/kong-bot/kaymaps/keynote")
DISPLAY_W = 2056
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

def is_keynote(labs):
    s = set(labs or [])
    return ("삽입" in s or "슬라이드" in s) and ("포맷" in s or "편집" in s)

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
        if (w["w"] or 0) >= 800 and (w["h"] or 0) >= 500:
            return w
    return wins[0] if wins else None

def list_left(els):
    out = []
    for e in els:
        lab = (e.get("label") or "").strip()
        cx, cy = e.get("cx") or 0, e.get("cy") or 0
        if cx > 450 or cy < 100 or cy > 900 or not lab:
            continue
        if lab in ("텍스트 상자 삽입", "검색"):
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

def write_notes():
    (OUT / "a348_notes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")

def format_controls(els):
    """Controls that look like format/inspector panel."""
    out = []
    for e in els:
        lab = e.get("label") or ""
        cx = e.get("cx") or 0
        x = e.get("x") or 0
        if any(k in lab for k in ("포맷", "정렬", "스타일", "텍스트", "배경", "채우기", "너비", "높이", "인스펙터")):
            out.append({"label": lab, "role": e.get("role"), "x": x, "cx": cx, "cy": e.get("cy")})
        elif cx > 1600 and e.get("role") in ("AXButton", "AXRadioButton", "AXCheckBox", "AXPopUpButton", "AXTextField"):
            out.append({"label": lab, "role": e.get("role"), "x": x, "cx": cx, "cy": e.get("cy")})
    return out

def onscreen_format(els):
    ctrls = format_controls(els)
    good = [c for c in ctrls if (c.get("x") or 0) < DISPLAY_W - 20 or (c.get("cx") or 0) < DISPLAY_W - 20]
    return good, ctrls

def main():
    run(["open", "-a", "Keynote"]); time.sleep(1.0)
    pr = run(["pgrep", "-x", "Keynote"])
    if pr.returncode != 0:
        notes.append("NO_PID"); write_notes(); return
    pid = pr.stdout.strip().split()[0]
    notes.append("PID {}".format(pid))

    for _ in range(3):
        els = dump(pid)
        if is_keynote(menus(els)):
            break
        run(["open", "-a", "Keynote"]); time.sleep(0.9)
    else:
        notes.append("FAIL_app")
        run(["screencapture", "-x", str(OUT / "slide_348.png")])
        write_notes(); return

    for _ in range(2):
        els = dump(pid)
        mw = max_doc(windows(els))
        notes.append("MAX={}".format(mw))
        if mw and (mw["w"] or 0) >= 2000 and (mw["h"] or 0) >= 1200:
            notes.append("FS_ok")
            break
        if mw and (mw["w"] or 0) >= 800:
            click(419, 20); time.sleep(0.55)
            els = dump(pid)
            start = next((e for e in els if e.get("label") == "전체 화면 시작"), None)
            if start:
                click(start["cx"], start["cy"]); time.sleep(1.4)
                notes.append("fs_start")
            else:
                click((mw.get("x") or 0) + 54, (mw.get("y") or 0) + 20); time.sleep(1.4)

    els = dump(pid)
    mw = max_doc(windows(els)) or {}
    wx, wy = mw.get("x") or 0, mw.get("y") or 0
    ww, wh = mw.get("w") or 2056, mw.get("h") or 1290
    c0x, c0y = wx + 300, wy + 130
    c1x, c1y = wx + ww - 360, wy + wh - 50
    notes.append("objs_before={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in list_left(els)]))

    # 보기 > 인스펙터 — job coords 518,116 or menu
    insp_ok = False
    for attempt in range(3):
        click(419, 20); time.sleep(0.45)  # 보기 menubar approx
        els = dump(pid)
        insp = next((e for e in els if e.get("label") and "인스펙터" in e.get("label")), None)
        if insp:
            click(insp["cx"], insp["cy"]); time.sleep(0.7)
            notes.append("inspector_menu_click={},{}".format(insp["cx"], insp["cy"]))
        else:
            # job hint 518,116
            click(518, 116); time.sleep(0.7)
            notes.append("inspector_coord_518_116 attempt={}".format(attempt + 1))
        # also try hide navigator to free space
        if attempt == 1:
            els = dump(pid)
            nav = next((e for e in els if e.get("label") and "내비게이터" in e.get("label")), None)
            if nav:
                click(nav["cx"], nav["cy"]); time.sleep(0.5)
                notes.append("navigator_toggle")
        els = dump(pid)
        good, allc = onscreen_format(els)
        notes.append("format_ctrls_sample={}".format(allc[:15]))
        notes.append("onscreen_format_n={}".format(len(good)))
        if good:
            insp_ok = True
            notes.append("INSPECTOR_ON_SCREEN")
            break
    notes.append("insp_ok={}".format(insp_ok))

    method = None
    # Method A: empty canvas + slide background fill
    empty_x = (c0x + c1x) / 2
    empty_y = (c0y + c1y) / 2 + 80  # slightly below center to avoid tiny shapes
    click(empty_x, empty_y); time.sleep(0.45)
    notes.append("clicked_empty_canvas {},{}".format(empty_x, empty_y))
    # open 포맷 for slide
    click(1937, 93); time.sleep(0.3)
    els = dump(pid)
    # find 배경 / 슬라이드 외관 / fill well on-screen
    bg_cands = []
    for e in els:
        lab = e.get("label") or ""
        cx = e.get("cx") or 0
        if cx >= DISPLAY_W - 10:
            continue
        if any(k in lab for k in ("배경", "슬라이드 외관", "채우기", "색상")):
            bg_cands.append(e)
    notes.append("bg_cands={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in bg_cands[:12]]))
    well = None
    for e in bg_cands:
        lab = e.get("label") or ""
        if "배경" in lab or "채우기" in lab:
            well = e
            break
    if not well and bg_cands:
        well = bg_cands[0]
    if well:
        click(well["cx"], well["cy"]); time.sleep(0.55)
        notes.append("clicked_bg_well={},{}".format(well["cx"], well["cy"]))
        els = dump(pid)
        # dark swatch — look for black/dark color wells or known swatch coords
        swatches = [e for e in els if e.get("role") in ("AXButton", "AXImage", "AXColorWell", "AXGroup")
                    and (e.get("cx") or 0) < DISPLAY_W - 10
                    and (e.get("cy") or 0) > 200]
        # try labeled black / 검정
        black = next((e for e in els if e.get("label") and any(k in e.get("label") for k in ("검정", "Black", "검은"))), None)
        if black and (black.get("cx") or 0) < DISPLAY_W:
            click(black["cx"], black["cy"]); time.sleep(0.4)
            notes.append("clicked_black_label")
            method = "A_bg_black_label"
        else:
            # open color picker area near well, pick dark swatch row
            # common: after fill click, palette appears — click near well lower-left dark
            wx_ = well.get("cx") or 1800
            wy_ = well.get("cy") or 400
            if wx_ >= DISPLAY_W:
                wx_ = DISPLAY_W - 80
            # try a few dark swatch positions relative to panel
            for sx, sy in [(wx_ - 40, wy_ + 80), (wx_ - 20, wy_ + 120), (DISPLAY_W - 100, 450), (DISPLAY_W - 80, 500)]:
                if sx < DISPLAY_W - 5:
                    click(sx, sy); time.sleep(0.35)
                    notes.append("swatch_try {},{}".format(sx, sy))
            method = "A_bg_swatch_tries"
    else:
        notes.append("NO_BG_WELL_onscreen")

    # Method B if A didn't establish — drag SE handle of 사각형
    if method is None or method.startswith("A"):
        # still try B to enlarge/darken rect as backup if still tiny
        els = dump(pid)
        rects = [e for e in list_left(els) if "사각" in (e.get("label") or "")]
        if rects:
            r = rects[0]
            click(r["cx"], r["cy"]); time.sleep(0.5)
            notes.append("selected_rect_for_B cy={}".format(r.get("cy")))
            # SE handle: a few px outside bottom-right of tiny black box
            # use canvas center estimate of tiny shape ~100pt around center
            cx = (c0x + c1x) / 2
            cy = (c0y + c1y) / 2
            # assume postage stamp ~80px — SE just outside
            for i in range(3):
                se_x, se_y = cx + 45 + i * 5, cy + 45 + i * 5
                drag(se_x, se_y, c1x - 15, c1y - 15)
                notes.append("drag_SE_handle_{} {},{} -> {},{}".format(i + 1, se_x, se_y, c1x - 15, c1y - 15))
                time.sleep(0.5)
                # reselect rect only
                els = dump(pid)
                rects = [e for e in list_left(els) if "사각" in (e.get("label") or "")]
                if rects:
                    click(rects[0]["cx"], rects[0]["cy"]); time.sleep(0.35)
            if method is None:
                method = "B_se_drag"
            else:
                method = method + "+B_se_drag"

    # Delete leftover 텍스트
    els = dump(pid)
    texts = [e for e in list_left(els) if (e.get("label") or "") == "텍스트"]
    notes.append("texts_before_delete={}".format([(e.get("cy")) for e in texts]))
    for e in texts:
        click(e["cx"], e["cy"]); time.sleep(0.3)
        run([K, "--yes", "input", "key", "delete"]); time.sleep(0.25)
        notes.append("deleted_text cy={}".format(e.get("cy")))

    # Google
    click(225, 20); time.sleep(0.35)
    click(310, 164); time.sleep(0.7)
    chord("cmd", "a"); time.sleep(0.1)
    text("Google"); time.sleep(0.35)
    gx = (c0x + c1x) / 2
    gy = c0y + (c1y - c0y) * 0.32
    click(gx, gy); time.sleep(0.25)
    drag(gx + 15, gy + 10, gx + 220, gy + 45)
    time.sleep(0.35)

    run(["open", "-a", "Keynote"]); time.sleep(0.35)
    run(["screencapture", "-x", str(OUT / "slide_348.png")])
    els = dump(pid)
    notes.append("method={}".format(method))
    notes.append("menus_final={}".format(menus(els)))
    notes.append("wins_final={}".format(windows(els)))
    notes.append("objs_final={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in list_left(els)]))
    notes.append("shot={}".format((OUT / "slide_348.png").stat().st_size if (OUT / "slide_348.png").exists() else 0))
    notes.append("ELAPSED={}".format(int(time.time() - t0)))
    write_notes()
    print("DONE")
    for n in notes:
        print(n)

if __name__ == "__main__":
    main()
