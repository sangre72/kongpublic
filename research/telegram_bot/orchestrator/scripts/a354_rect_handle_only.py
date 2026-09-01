#!/usr/bin/env python3
"""a_354: delete 텍스트, keep 사각형, SE handle drag large, Google."""
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
    (OUT / "a354_notes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")

def find_menu_item(els, exact=None, contains=None):
    cands = []
    for e in els:
        lab = e.get("label") or ""
        if exact and lab == exact:
            cands.append(e)
        elif contains and contains in lab:
            cands.append(e)
    menuish = [e for e in cands if e.get("role") == "AXMenuItem"]
    return menuish[0] if menuish else (cands[0] if cands else None)

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
        run(["screencapture", "-x", str(OUT / "slide_354.png")])
        write_notes(); return

    for _ in range(2):
        els = dump(pid)
        mw = max_doc(windows(els))
        notes.append("MAX={}".format(mw))
        if mw and (mw["w"] or 0) >= 2000 and (mw["h"] or 0) >= 1200:
            notes.append("FS_ok")
            break
        click(419, 20); time.sleep(0.45)
        els = dump(pid)
        start = next((e for e in els if e.get("label") == "전체 화면 시작"), None)
        if start:
            click(start["cx"], start["cy"]); time.sleep(1.4)
            notes.append("fs_start")
        elif mw:
            click((mw.get("x") or 0) + 54, (mw.get("y") or 0) + 20); time.sleep(1.2)

    els = dump(pid)
    mw = max_doc(windows(els)) or {}
    wx, wy = mw.get("x") or 0, mw.get("y") or 0
    ww, wh = mw.get("w") or 2056, mw.get("h") or 1290
    c0x, c0y = wx + 300, wy + 130
    c1x, c1y = wx + ww - 360, wy + wh - 50
    # ensure object list
    click(419, 20); time.sleep(0.35)
    els = dump(pid)
    ol = next((e for e in els if e.get("label") and "대상체 목록" in e.get("label")), None)
    if ol:
        click(ol["cx"], ol["cy"]); time.sleep(0.45)

    els = dump(pid)
    notes.append("objs_before={}".format([(e.get("label"), e.get("cy")) for e in list_left(els)]))

    # Delete all 텍스트, keep 사각형
    for _ in range(12):
        els = dump(pid)
        texts = [e for e in list_left(els) if (e.get("label") or "") == "텍스트"]
        if not texts:
            break
        t = texts[0]
        click(t["cx"], t["cy"]); time.sleep(0.3)
        key("delete"); time.sleep(0.3)
        notes.append("deleted_text cy={}".format(t.get("cy")))

    els = dump(pid)
    objs = list_left(els)
    notes.append("objs_after_delete={}".format([(e.get("label"), e.get("cy")) for e in objs]))
    rects = [e for e in objs if "사각" in (e.get("label") or "")]
    if not rects:
        notes.append("NO_RECT_insert_menu")
        # dump-click insert path from a351
        ins = next((e for e in dump(pid) if e.get("role") == "AXMenuBarItem" and e.get("label") == "삽입"), None)
        if ins:
            click(ins["cx"], ins["cy"]); time.sleep(0.5)
            els = dump(pid)
            shape = find_menu_item(els, exact="도형")
            if shape:
                click(shape["cx"], shape["cy"]); time.sleep(0.55)
                notes.append("도형={},{}".format(shape["cx"], shape["cy"]))
                els = dump(pid)
                rect = find_menu_item(els, exact="직사각형")
                if rect:
                    click(rect["cx"], rect["cy"]); time.sleep(0.7)
                    notes.append("직사각형={},{}".format(rect["cx"], rect["cy"]))
        click((c0x + c1x) / 2, (c0y + c1y) / 2); time.sleep(0.35)
        els = dump(pid)
        rects = [e for e in list_left(els) if "사각" in (e.get("label") or "")]

    if rects:
        click(rects[0]["cx"], rects[0]["cy"]); time.sleep(0.5)
        notes.append("selected_rect cy={}".format(rects[0].get("cy")))
        # SE handle: few px outside BR of tiny black (~center of canvas, ~100pt)
        cx = (c0x + c1x) / 2
        cy = (c0y + c1y) / 2
        target = (1700, 1100)
        for i in range(4):
            se_x = cx + 55 + i * 10
            se_y = cy + 55 + i * 10
            drag(se_x, se_y, target[0], target[1])
            notes.append("drag_SE_{} {},{} -> {},{}".format(i + 1, se_x, se_y, target[0], target[1]))
            time.sleep(0.55)
            els = dump(pid)
            rects = [e for e in list_left(els) if "사각" in (e.get("label") or "")]
            if rects:
                click(rects[0]["cx"], rects[0]["cy"]); time.sleep(0.3)
            # expand estimate outward after each drag
            cx = (cx + target[0]) / 2
            cy = (cy + target[1]) / 2
        notes.append("objs_after_drag={}".format(
            [(e.get("label"), e.get("cy")) for e in list_left(dump(pid))]))
    else:
        notes.append("NO_RECT")

    # Google one clean
    els = dump(pid)
    ins = next((e for e in els if e.get("role") == "AXMenuBarItem" and e.get("label") == "삽입"), None)
    if ins:
        click(ins["cx"], ins["cy"]); time.sleep(0.45)
        els = dump(pid)
        tb = find_menu_item(els, contains="텍스트")
        if tb:
            click(tb["cx"], tb["cy"]); time.sleep(0.55)
            notes.append("text_menu={},{}".format(tb["cx"], tb["cy"]))
    chord("cmd", "a"); time.sleep(0.1)
    text("Google"); time.sleep(0.35)
    gx = (c0x + c1x) / 2
    gy = c0y + (c1y - c0y) * 0.28
    click(gx, gy); time.sleep(0.25)
    drag(gx + 12, gy + 8, gx + 200, gy + 42)
    time.sleep(0.3)

    run(["open", "-a", "Keynote"]); time.sleep(0.35)
    run(["screencapture", "-x", str(OUT / "slide_354.png")])
    els = dump(pid)
    notes.append("menus_final={}".format(menus(els)))
    notes.append("wins_final={}".format(windows(els)))
    notes.append("objs_final={}".format([(e.get("label"), e.get("cy")) for e in list_left(els)]))
    notes.append("shot={}".format((OUT / "slide_354.png").stat().st_size if (OUT / "slide_354.png").exists() else 0))
    notes.append("ELAPSED={}".format(int(time.time() - t0)))
    write_notes()
    print("DONE")
    for n in notes:
        print(n)

if __name__ == "__main__":
    main()
