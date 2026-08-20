#!/usr/bin/env python3
"""a_349: floating inspector; set 100pt fields 1920x1080; dark fill; Google."""
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
        if "서체" in lab or "색상" in lab or "인스펙터" in lab or "포맷" in lab:
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
    (OUT / "a349_notes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")

def pt_fields(els, max_x=None):
    fields = []
    for e in els:
        if e.get("role") != "AXTextField":
            continue
        lab = e.get("label") or ""
        cx = e.get("cx") or 0
        if max_x is not None and cx >= max_x:
            continue
        if lab.endswith("pt") or "너비" in lab or "높이" in lab or lab in ("100pt", "W", "H"):
            fields.append(e)
    fields.sort(key=lambda e: (e.get("cy") or 0, e.get("cx") or 0))
    return fields

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
        run(["screencapture", "-x", str(OUT / "slide_349.png")])
        write_notes(); return

    for _ in range(2):
        els = dump(pid)
        mw = max_doc(windows(els))
        notes.append("MAX={}".format(mw))
        if mw and (mw["w"] or 0) >= 2000 and (mw["h"] or 0) >= 1200:
            notes.append("FS_ok")
            break
        if mw and (mw["w"] or 0) >= 800:
            click(419, 20); time.sleep(0.5)
            els = dump(pid)
            start = next((e for e in els if e.get("label") == "전체 화면 시작"), None)
            if start:
                click(start["cx"], start["cy"]); time.sleep(1.3)
            else:
                click((mw.get("x") or 0) + 54, (mw.get("y") or 0) + 20); time.sleep(1.3)

    els = dump(pid)
    mw = max_doc(windows(els)) or {}
    wx, wy = mw.get("x") or 0, mw.get("y") or 0
    ww, wh = mw.get("w") or 2056, mw.get("h") or 1290
    c0x, c0y = wx + 300, wy + 130
    c1x, c1y = wx + ww - 360, wy + wh - 50

    objs = list_left(els)
    notes.append("objs_before={}".format([(e.get("label"), e.get("cy")) for e in objs]))
    rects = [e for e in objs if "사각" in (e.get("label") or "") or "직사" in (e.get("label") or "")]
    if not rects:
        notes.append("NO_RECT_insert")
        # 삽입 > 도형 > 직사각형 via menu
        click(310, 20); time.sleep(0.4)  # 삽입
        els = dump(pid)
        shape = next((e for e in els if e.get("label") and "도형" in e.get("label")), None)
        if shape:
            click(shape["cx"], shape["cy"]); time.sleep(0.5)
        else:
            click(340, 90); time.sleep(0.5)
        els = dump(pid)
        rect_m = next((e for e in els if e.get("label") and ("직사" in e.get("label") or "사각" in e.get("label"))), None)
        if rect_m:
            click(rect_m["cx"], rect_m["cy"]); time.sleep(0.6)
            notes.append("inserted_shape_menu")
        else:
            # toolbar shape button common coords
            click(370, 70); time.sleep(0.4)
            click(400, 140); time.sleep(0.5)
            notes.append("inserted_shape_toolbar_guess")
        # click canvas to place
        click((c0x + c1x) / 2, (c0y + c1y) / 2); time.sleep(0.4)
        els = dump(pid)
        rects = [e for e in list_left(els) if "사각" in (e.get("label") or "")]
        notes.append("objs_after_insert={}".format([(e.get("label"), e.get("cy")) for e in list_left(els)]))
    if rects:
        click(rects[0]["cx"], rects[0]["cy"]); time.sleep(0.45)
        notes.append("selected_rect cy={}".format(rects[0].get("cy")))

    # Hide navigator / object list to free space
    for lab_want in ("내비게이터", "대상체 목록"):
        click(419, 20); time.sleep(0.35)
        els = dump(pid)
        it = next((e for e in els if e.get("label") and lab_want in e.get("label")), None)
        if it:
            # if not already hidden, click to hide
            click(it["cx"], it["cy"]); time.sleep(0.5)
            notes.append("toggle_{}".format(lab_want))

    # Open floating inspector
    float_win = None
    for attempt in range(4):
        click(419, 20); time.sleep(0.35)
        els = dump(pid)
        insp = next((e for e in els if e.get("label") and "인스펙터" in e.get("label")), None)
        if insp:
            click(insp["cx"], insp["cy"]); time.sleep(0.8)
            notes.append("inspector_click={},{}".format(insp["cx"], insp["cy"]))
        else:
            click(518, 116); time.sleep(0.8)
            notes.append("inspector_coord attempt={}".format(attempt + 1))
        els = dump(pid)
        wins = windows(els)
        notes.append("windows={}".format(wins))
        for w in wins:
            lab = w.get("label") or ""
            # floating format/inspector panel — not main doc
            if "무제" in lab or ".key" in lab:
                continue
            if (w.get("w") or 0) > 100 and (w.get("h") or 0) > 100:
                if any(k in lab for k in ("포맷", "인스펙터", "정렬", "스타일")) or (w.get("w") or 0) < 600:
                    float_win = w
                    notes.append("float_win={}".format(w))
                    break
        if float_win:
            break
        # also check 100pt fields on-screen
        fields = pt_fields(els, max_x=DISPLAY_W - 5)
        if fields:
            notes.append("onscreen_pt_without_named_win={}".format(
                [(e.get("label"), e.get("cx"), e.get("cy")) for e in fields]))
            break

    els = dump(pid)
    # Prefer on-screen 100pt fields; else any 100pt and log offscreen
    on = pt_fields(els, max_x=DISPLAY_W - 5)
    all_pt = pt_fields(els, max_x=None)
    notes.append("pt_onscreen={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in on]))
    notes.append("pt_all={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in all_pt[:10]]))

    typed = False
    # if off-screen, try drag float window left by dragging title bar
    if not on and all_pt:
        # drag window from first field area leftward
        fx = all_pt[0].get("cx") or 2200
        fy = (all_pt[0].get("cy") or 266) - 160
        drag(fx, fy, 900, fy)
        notes.append("drag_inspector_left {},{} -> 900,{}".format(fx, fy, fy))
        time.sleep(0.5)
        els = dump(pid)
        on = pt_fields(els, max_x=DISPLAY_W - 5)
        all_pt = pt_fields(els, max_x=None)
        notes.append("after_drag_pt_onscreen={}".format(
            [(e.get("label"), e.get("cx"), e.get("cy")) for e in on]))
        notes.append("windows_after_drag={}".format(windows(els)))

    targets = on if on else []
    # need two fields at similar y for W/H — left is width
    if len(targets) >= 2:
        row = [t for t in targets if abs((t.get("cy") or 0) - (targets[0].get("cy") or 0)) < 20]
        row.sort(key=lambda e: e.get("cx") or 0)
        if len(row) >= 2:
            w_f, h_f = row[0], row[1]
        else:
            w_f, h_f = targets[0], targets[1]
        notes.append("type_targets w={} h={}".format(
            (w_f.get("label"), w_f.get("cx"), w_f.get("cy")),
            (h_f.get("label"), h_f.get("cx"), h_f.get("cy"))))
        click(w_f["cx"], w_f["cy"]); time.sleep(0.3)
        chord("cmd", "a"); time.sleep(0.08)
        text("1920"); time.sleep(0.12)
        key("return"); time.sleep(0.35)
        notes.append("typed_1920")
        click(h_f["cx"], h_f["cy"]); time.sleep(0.3)
        chord("cmd", "a"); time.sleep(0.08)
        text("1080"); time.sleep(0.12)
        key("return"); time.sleep(0.35)
        notes.append("typed_1080")
        typed = True
        # leak guard
        els = dump(pid)
        left = list_left(els)
        bad = [e for e in left if (e.get("label") or "") in ("0", "1920", "1080", "202124")]
        if bad:
            notes.append("leak={}".format([(e.get("label"), e.get("cy")) for e in bad]))
            chord("cmd", "z"); time.sleep(0.3)
            notes.append("UNDO_leak")
            typed = False
    else:
        notes.append("NO_ONSCREEN_SIZE_FIELDS_to_type")

    # reselect 사각형 for dark fill
    els = dump(pid)
    rects = [e for e in list_left(els) if "사각" in (e.get("label") or "")]
    if rects:
        click(rects[0]["cx"], rects[0]["cy"]); time.sleep(0.4)
    # style tab / fill swatch — on-screen only
    click(1937, 93); time.sleep(0.3)
    els = dump(pid)
    style = next((e for e in els if e.get("label") == "스타일" and (e.get("cx") or 0) < DISPLAY_W), None)
    if style:
        click(style["cx"], style["cy"]); time.sleep(0.35)
        notes.append("style_tab_on")
    # fill well / color
    fill = next((e for e in els if e.get("label") and "채우기" in e.get("label") and (e.get("cx") or 0) < DISPLAY_W), None)
    if fill:
        click(fill["cx"], fill["cy"]); time.sleep(0.4)
        notes.append("fill_clicked")
    black = next((e for e in els if e.get("label") and any(k in e.get("label") for k in ("검정", "Black"))), None)
    if black and (black.get("cx") or 0) < DISPLAY_W:
        click(black["cx"], black["cy"]); time.sleep(0.3)
        notes.append("black_swatch")
    else:
        # try relative dark swatches on right panel if partially on screen
        for sx, sy in [(DISPLAY_W - 120, 400), (DISPLAY_W - 90, 450), (1800, 420)]:
            if sx < DISPLAY_W:
                click(sx, sy); time.sleep(0.25)
                notes.append("swatch_try {},{}".format(sx, sy))

    # delete junk text (not Google yet)
    els = dump(pid)
    for e in list_left(els):
        if (e.get("label") or "") == "텍스트":
            click(e["cx"], e["cy"]); time.sleep(0.25)
            key("delete"); time.sleep(0.2)
            notes.append("deleted_text")

    # Google
    click(225, 20); time.sleep(0.35)
    click(310, 164); time.sleep(0.7)
    chord("cmd", "a"); time.sleep(0.1)
    text("Google"); time.sleep(0.35)
    gx = (c0x + c1x) / 2
    gy = c0y + (c1y - c0y) * 0.32
    click(gx, gy); time.sleep(0.25)
    drag(gx + 15, gy + 10, gx + 220, gy + 45)
    time.sleep(0.3)

    run(["open", "-a", "Keynote"]); time.sleep(0.35)
    run(["screencapture", "-x", str(OUT / "slide_349.png")])
    els = dump(pid)
    notes.append("typed_size={}".format(typed))
    notes.append("menus_final={}".format(menus(els)))
    notes.append("wins_final={}".format(windows(els)))
    notes.append("objs_final={}".format([(e.get("label"), e.get("cy")) for e in list_left(els)]))
    notes.append("shot={}".format((OUT / "slide_349.png").stat().st_size if (OUT / "slide_349.png").exists() else 0))
    notes.append("ELAPSED={}".format(int(time.time() - t0)))
    write_notes()
    print("DONE")
    for n in notes:
        print(n)

if __name__ == "__main__":
    main()
