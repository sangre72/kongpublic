#!/usr/bin/env python3
"""a_350: 삽입>도형>직사각형 menu only; SE handle drag; Google."""
import json, subprocess, time
from pathlib import Path

K = "/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol"
OUT = Path("/Users/bumsuklee/git/kong-bot/kaymaps/keynote")
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
    (OUT / "a350_notes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")

def find_label(els, *subs):
    for e in els:
        lab = e.get("label") or ""
        if all(s in lab for s in subs):
            return e
    return None

def insert_rect_menu(pid):
    """삽입 menubar → 도형 → 직사각형. BAN toolbar."""
    for attempt in range(2):
        # click menubar 삽입
        els = dump(pid)
        ins = next((e for e in els if e.get("role") == "AXMenuBarItem" and e.get("label") == "삽입"), None)
        if ins:
            click(ins["cx"], ins["cy"]); time.sleep(0.55)
            notes.append("menu_삽입={},{}".format(ins["cx"], ins["cy"]))
        else:
            # approximate menubar 삽입
            click(280, 20); time.sleep(0.55)
            notes.append("menu_삽입_coord")
        els = dump(pid)
        notes.append("after_삽입_labels={}".format(
            [e.get("label") for e in els if e.get("role") in ("AXMenuItem", "AXMenu") and e.get("label")][:25]))
        shape = next((e for e in els if e.get("label") == "도형" or (e.get("label") or "").startswith("도형")), None)
        if shape:
            click(shape["cx"], shape["cy"]); time.sleep(0.55)
            notes.append("menu_도형={},{}".format(shape["cx"], shape["cy"]))
        else:
            # job hint 310,188
            click(310, 188); time.sleep(0.55)
            notes.append("menu_도형_coord_310_188")
        els = dump(pid)
        notes.append("after_도형_labels={}".format(
            [e.get("label") for e in els if e.get("role") in ("AXMenuItem",) and e.get("label")][:30]))
        rect = next((e for e in els if e.get("label") and ("직사" in e.get("label") or e.get("label") == "사각형")), None)
        if rect:
            click(rect["cx"], rect["cy"]); time.sleep(0.7)
            notes.append("menu_직사각형={},{}".format(rect["cx"], rect["cy"]))
        else:
            # job hint 492,188
            click(492, 188); time.sleep(0.7)
            notes.append("menu_직사각형_coord_492_188")
        time.sleep(0.4)
        els = dump(pid)
        objs = list_left(els)
        notes.append("objs_after_insert_try{}={}".format(attempt + 1,
            [(e.get("label"), e.get("cy")) for e in objs]))
        if any("사각" in (e.get("label") or "") for e in objs):
            return True
        # dismiss menus
        run([K, "--yes", "input", "key", "escape"]); time.sleep(0.3)
    return False

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
        run(["screencapture", "-x", str(OUT / "slide_350.png")])
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

    # restore object list: 보기 > 대상체 목록
    click(419, 20); time.sleep(0.4)
    els = dump(pid)
    ol = next((e for e in els if e.get("label") and "대상체 목록" in e.get("label")), None)
    if ol:
        click(ol["cx"], ol["cy"]); time.sleep(0.55)
        notes.append("toggle_대상체_목록={},{}".format(ol["cx"], ol["cy"]))
    else:
        notes.append("no_대상체_목록_menu")

    els = dump(pid)
    notes.append("objs_before={}".format([(e.get("label"), e.get("cy")) for e in list_left(els)]))
    has_rect = any("사각" in (e.get("label") or "") for e in list_left(els))
    if not has_rect:
        ok = insert_rect_menu(pid)
        notes.append("insert_ok={}".format(ok))
        # place on canvas if needed
        click((c0x + c1x) / 2, (c0y + c1y) / 2); time.sleep(0.4)
        # ensure list visible again
        click(419, 20); time.sleep(0.3)
        els = dump(pid)
        ol = next((e for e in els if e.get("label") and "대상체 목록" in e.get("label")), None)
        if ol:
            click(ol["cx"], ol["cy"]); time.sleep(0.4)

    els = dump(pid)
    objs = list_left(els)
    notes.append("objs_mid={}".format([(e.get("label"), e.get("cy")) for e in objs]))
    rects = [e for e in objs if "사각" in (e.get("label") or "")]
    if rects:
        click(rects[0]["cx"], rects[0]["cy"]); time.sleep(0.5)
        notes.append("selected_rect cy={}".format(rects[0].get("cy")))
        # SE handle: slightly outside BR of new default shape (~center postage)
        cx = (c0x + c1x) / 2
        cy = (c0y + c1y) / 2
        for i in range(3):
            se_x, se_y = cx + 50 + i * 8, cy + 50 + i * 8
            drag(se_x, se_y, c1x - 20, c1y - 20)
            notes.append("drag_SE_{} {},{} -> {},{}".format(i + 1, se_x, se_y, c1x - 20, c1y - 20))
            time.sleep(0.5)
            els = dump(pid)
            rects = [e for e in list_left(els) if "사각" in (e.get("label") or "")]
            if rects:
                click(rects[0]["cx"], rects[0]["cy"]); time.sleep(0.3)
        notes.append("objs_after_drag={}".format(
            [(e.get("label"), e.get("cy")) for e in list_left(dump(pid))]))
    else:
        notes.append("NO_RECT_after_menu")

    # dark swatch if fill on-screen
    els = dump(pid)
    fill = next((e for e in els if e.get("label") and "채우기" in e.get("label") and (e.get("cx") or 0) < 2050), None)
    if fill:
        click(fill["cx"], fill["cy"]); time.sleep(0.4)
        notes.append("fill_clicked")
        black = next((e for e in els if e.get("label") and "검정" in e.get("label")), None)
        if black:
            click(black["cx"], black["cy"]); time.sleep(0.3)
            notes.append("black")
    else:
        notes.append("fill_skip_offscreen")

    # Google
    click(225, 20); time.sleep(0.35)
    # 삽입>텍스트 상자 via menu not toolbar if possible
    els = dump(pid)
    ins = next((e for e in els if e.get("role") == "AXMenuBarItem" and e.get("label") == "삽입"), None)
    if ins:
        click(ins["cx"], ins["cy"]); time.sleep(0.4)
        els = dump(pid)
        tb = next((e for e in els if e.get("label") and "텍스트" in e.get("label")), None)
        if tb:
            click(tb["cx"], tb["cy"]); time.sleep(0.5)
            notes.append("menu_텍스트_상자")
        else:
            click(310, 164); time.sleep(0.5)
    else:
        click(310, 164); time.sleep(0.5)
    chord("cmd", "a"); time.sleep(0.1)
    text("Google"); time.sleep(0.35)
    gx = (c0x + c1x) / 2
    gy = c0y + (c1y - c0y) * 0.32
    click(gx, gy); time.sleep(0.25)
    drag(gx + 15, gy + 10, gx + 220, gy + 45)
    time.sleep(0.3)

    run(["open", "-a", "Keynote"]); time.sleep(0.35)
    run(["screencapture", "-x", str(OUT / "slide_350.png")])
    els = dump(pid)
    notes.append("menus_final={}".format(menus(els)))
    notes.append("wins_final={}".format(windows(els)))
    notes.append("objs_final={}".format([(e.get("label"), e.get("cy")) for e in list_left(els)]))
    notes.append("shot={}".format((OUT / "slide_350.png").stat().st_size if (OUT / "slide_350.png").exists() else 0))
    notes.append("ELAPSED={}".format(int(time.time() - t0)))
    write_notes()
    print("DONE")
    for n in notes:
        print(n)

if __name__ == "__main__":
    main()
