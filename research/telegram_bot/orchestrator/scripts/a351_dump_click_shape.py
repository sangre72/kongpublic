#!/usr/bin/env python3
"""a_351: maximize; 삽입→dump-click 도형→dump-click 직사각형 only."""
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
    (OUT / "a351_notes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")

def find_menu_item(els, exact=None, contains=None):
    """Prefer AXMenuItem from open menu dump."""
    cands = []
    for e in els:
        lab = e.get("label") or ""
        role = e.get("role") or ""
        if role not in ("AXMenuItem", "AXMenuButton", "AXButton", "AXStaticText", "AXCell"):
            # also allow menuitem-like
            if role not in ("AXMenuItem",):
                if role != "AXMenuItem" and role not in ("AXMenuItem",):
                    pass
        if exact and lab == exact:
            cands.append(e)
        elif contains and contains in lab:
            cands.append(e)
    # prefer AXMenuItem
    menuish = [e for e in cands if e.get("role") == "AXMenuItem"]
    if menuish:
        return menuish[0]
    return cands[0] if cands else None

def insert_once(pid):
    els = dump(pid)
    ins = next((e for e in els if e.get("role") == "AXMenuBarItem" and e.get("label") == "삽입"), None)
    if not ins:
        notes.append("NO_MENUBAR_삽입")
        return False
    click(ins["cx"], ins["cy"]); time.sleep(0.6)
    notes.append("click_삽입_dump={},{}".format(ins["cx"], ins["cy"]))
    els = dump(pid)
    items = [(e.get("label"), e.get("role"), e.get("cx"), e.get("cy")) for e in els
             if e.get("label") and e.get("role") in ("AXMenuItem", "AXMenu")]
    notes.append("dump_after_삽입={}".format(items[:30]))
    shape = find_menu_item(els, exact="도형") or find_menu_item(els, contains="도형")
    if not shape:
        notes.append("NO_도형_in_dump")
        run([K, "--yes", "input", "key", "escape"]); time.sleep(0.2)
        return False
    # BAN toolbar: require y typically menubar dropdown (cy < 400) or role menu item
    notes.append("도형_hit label={} role={} cx={} cy={}".format(
        shape.get("label"), shape.get("role"), shape.get("cx"), shape.get("cy")))
    click(shape["cx"], shape["cy"]); time.sleep(0.65)
    els = dump(pid)
    items2 = [(e.get("label"), e.get("role"), e.get("cx"), e.get("cy")) for e in els
              if e.get("label") and e.get("role") in ("AXMenuItem", "AXMenu")]
    notes.append("dump_after_도형={}".format(items2[:40]))
    rect = find_menu_item(els, exact="직사각형") or find_menu_item(els, contains="직사")
    if not rect:
        # re-open 도형 from THIS dump if present
        shape2 = find_menu_item(els, exact="도형") or find_menu_item(els, contains="도형")
        if shape2:
            click(shape2["cx"], shape2["cy"]); time.sleep(0.55)
            notes.append("reclick_도형={},{}".format(shape2["cx"], shape2["cy"]))
            els = dump(pid)
            notes.append("dump_after_도형2={}".format(
                [(e.get("label"), e.get("cx"), e.get("cy")) for e in els
                 if e.get("role") == "AXMenuItem" and e.get("label")][:40]))
            rect = find_menu_item(els, exact="직사각형") or find_menu_item(els, contains="직사")
    if not rect:
        notes.append("NO_직사각형_in_dump")
        run([K, "--yes", "input", "key", "escape"]); time.sleep(0.2)
        return False
    notes.append("직사각형_hit label={} role={} cx={} cy={}".format(
        rect.get("label"), rect.get("role"), rect.get("cx"), rect.get("cy")))
    click(rect["cx"], rect["cy"]); time.sleep(0.75)
    return True

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
        run(["screencapture", "-x", str(OUT / "slide_351.png")])
        write_notes(); return

    # Maximize / FS if small
    for _ in range(3):
        els = dump(pid)
        mw = max_doc(windows(els))
        notes.append("MAX={}".format(mw))
        display_w = 2056
        if mw and (mw["w"] or 0) >= display_w - 80 and (mw["h"] or 0) >= 1200:
            notes.append("FS_ok")
            break
        click(419, 20); time.sleep(0.5)
        els = dump(pid)
        start = next((e for e in els if e.get("label") == "전체 화면 시작"), None)
        if start:
            click(start["cx"], start["cy"]); time.sleep(1.5)
            notes.append("fs_start={},{}".format(start["cx"], start["cy"]))
        else:
            # green traffic / maximize
            if mw:
                click((mw.get("x") or 0) + 54, (mw.get("y") or 0) + 20); time.sleep(1.2)
                notes.append("max_btn_try")

    els = dump(pid)
    mw = max_doc(windows(els)) or {}
    wx, wy = mw.get("x") or 0, mw.get("y") or 0
    ww, wh = mw.get("w") or 2056, mw.get("h") or 1290
    c0x, c0y = wx + 300, wy + 130
    c1x, c1y = wx + ww - 360, wy + wh - 50
    notes.append("objs_before={}".format([(e.get("label"), e.get("cy")) for e in list_left(els)]))

    ok = insert_once(pid)
    notes.append("insert1={}".format(ok))
    if not ok:
        ok = insert_once(pid)
        notes.append("insert2={}".format(ok))

    # click canvas center to place if needed
    click((c0x + c1x) / 2, (c0y + c1y) / 2); time.sleep(0.4)
    # object list
    click(419, 20); time.sleep(0.35)
    els = dump(pid)
    ol = next((e for e in els if e.get("label") and "대상체 목록" in e.get("label")), None)
    if ol:
        click(ol["cx"], ol["cy"]); time.sleep(0.45)

    els = dump(pid)
    objs = list_left(els)
    notes.append("objs_after={}".format([(e.get("label"), e.get("cy")) for e in objs]))
    rects = [e for e in objs if "사각" in (e.get("label") or "")]
    if rects:
        click(rects[0]["cx"], rects[0]["cy"]); time.sleep(0.4)
        notes.append("selected_rect")
        fill = next((e for e in els if e.get("label") and "채우기" in e.get("label") and (e.get("cx") or 0) < 2050), None)
        if fill:
            click(fill["cx"], fill["cy"]); time.sleep(0.35)
            notes.append("fill")
        black = next((e for e in els if e.get("label") and "검정" in e.get("label") and (e.get("cx") or 0) < 2050), None)
        if black:
            click(black["cx"], black["cy"]); time.sleep(0.3)
            notes.append("black")
    else:
        notes.append("NO_사각형_in_list")

    # Google via 삽입 menubar dump only
    els = dump(pid)
    ins = next((e for e in els if e.get("role") == "AXMenuBarItem" and e.get("label") == "삽입"), None)
    if ins:
        click(ins["cx"], ins["cy"]); time.sleep(0.45)
        els = dump(pid)
        tb = find_menu_item(els, contains="텍스트")
        if tb:
            notes.append("텍스트_hit={},{}".format(tb.get("cx"), tb.get("cy")))
            click(tb["cx"], tb["cy"]); time.sleep(0.55)
        else:
            notes.append("NO_텍스트_menu_skip_coord")
    chord("cmd", "a"); time.sleep(0.1)
    text("Google"); time.sleep(0.35)
    gx = (c0x + c1x) / 2
    gy = c0y + (c1y - c0y) * 0.3
    click(gx, gy); time.sleep(0.25)
    drag(gx + 10, gy + 8, gx + 200, gy + 40)

    run(["open", "-a", "Keynote"]); time.sleep(0.4)
    run(["screencapture", "-x", str(OUT / "slide_351.png")])
    els = dump(pid)
    notes.append("menus_final={}".format(menus(els)))
    notes.append("wins_final={}".format(windows(els)))
    notes.append("objs_final={}".format([(e.get("label"), e.get("cy")) for e in list_left(els)]))
    notes.append("shot={}".format((OUT / "slide_351.png").stat().st_size if (OUT / "slide_351.png").exists() else 0))
    notes.append("ELAPSED={}".format(int(time.time() - t0)))
    write_notes()
    print("DONE")
    for n in notes:
        print(n)

if __name__ == "__main__":
    main()
