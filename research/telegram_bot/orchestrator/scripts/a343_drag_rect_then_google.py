#!/usr/bin/env python3
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
    run([K, "--yes", "input", "drag", str(int(round(x1))), str(int(round(y1))), str(int(round(x2))), str(int(round(y2))), "--scale", "1"])

def key(n):
    run([K, "--yes", "input", "key", n])

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
            wins.append({"label": e.get("label"), "x": e.get("x"), "y": e.get("y"), "w": w, "h": h, "area": w * h})
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
    seen = set()
    uniq = []
    for e in out:
        k = (e.get("label"), round(e.get("cy") or 0, 0))
        if k in seen:
            continue
        seen.add(k)
        uniq.append(e)
    return uniq

def write_notes():
    (OUT / "a343_notes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")

def main():
    run(["open", "-a", "Keynote"]); time.sleep(1.0)
    pr = run(["pgrep", "-x", "Keynote"])
    if pr.returncode != 0:
        notes.append("NO_PID"); write_notes(); return
    pid = pr.stdout.strip().split()[0]
    notes.append("PID {}".format(pid))

    for i in range(3):
        els = dump(pid)
        if is_keynote(menus(els)):
            notes.append("menus_ok")
            break
        run(["open", "-a", "Keynote"]); time.sleep(0.9)
    else:
        notes.append("FAIL_app")
        run(["screencapture", "-x", str(OUT / "slide_343.png")])
        write_notes(); return

    # maximize
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
                notes.append("green")

    els = dump(pid)
    mw = max_doc(windows(els))
    # canvas bounds inside window (approx: menubar/toolbar/list)
    # slide canvas ~ center of max window
    wx, wy = mw.get("x") or 0, mw.get("y") or 0
    ww, wh = mw.get("w") or 1500, mw.get("h") or 1000
    # object list ~ left 280; toolbar ~ top 100 from win
    canvas_x0 = wx + 280
    canvas_y0 = wy + 120
    canvas_x1 = wx + ww - 320  # inspector
    canvas_y1 = wy + wh - 40

    # select 사각형 — do not delete
    rect = next((e for e in list_left(els) if "사각" in (e.get("label") or "") or "직사" in (e.get("label") or "")), None)
    notes.append("objs={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in list_left(els)]))
    if not rect:
        notes.append("no_rect_list — click canvas center once")
        click((canvas_x0 + canvas_x1) / 2, (canvas_y0 + canvas_y1) / 2); time.sleep(0.4)
    else:
        click(rect["cx"], rect["cy"]); time.sleep(0.5)
        notes.append("selected_rect {}".format(rect.get("label")))

    # drag corners: assume current selection is small center square
    # drag bottom-right handle outward then top-left
    cx = (canvas_x0 + canvas_x1) / 2
    cy = (canvas_y0 + canvas_y1) / 2
    # click shape center to ensure selection
    click(cx, cy); time.sleep(0.35)
    # drag SE corner from near center+50 to canvas SE
    drag(cx + 40, cy + 40, canvas_x1 - 10, canvas_y1 - 10)
    time.sleep(0.5)
    notes.append("drag_SE {},{} -> {},{}".format(cx + 40, cy + 40, canvas_x1 - 10, canvas_y1 - 10))
    # drag NW
    drag(cx - 40, cy - 40, canvas_x0 + 10, canvas_y0 + 10)
    time.sleep(0.5)
    notes.append("drag_NW {},{} -> {},{}".format(cx - 40, cy - 40, canvas_x0 + 10, canvas_y0 + 10))
    # second pass SE to fill
    drag(canvas_x0 + 80, canvas_y0 + 80, canvas_x1 - 10, canvas_y1 - 10)
    time.sleep(0.45)
    notes.append("drag_SE2")

    # lock rect
    click(1937, 93); time.sleep(0.3)
    click(2013, 107); time.sleep(0.3)
    click(1915, 517); time.sleep(0.35)

    els = dump(pid)
    left = list_left(els)
    notes.append("after_drag_objs={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in left]))
    notes.append("has_0={}".format(any((e.get("label") or "") == "0" for e in left)))
    notes.append("has_202124={}".format(any("202124" in (e.get("label") or "") for e in left)))

    # Google text only — no number typing for size; place then drag box if needed
    click(225, 20); time.sleep(0.4)
    click(310, 164); time.sleep(0.8)
    chord("cmd", "a"); time.sleep(0.1)
    text("Google"); time.sleep(0.35)
    # drag text box size approximately: click near text then drag corner
    # approximate Google target center on canvas
    gx = canvas_x0 + (canvas_x1 - canvas_x0) * 0.5
    gy = canvas_y0 + (canvas_y1 - canvas_y0) * 0.35
    click(gx, gy); time.sleep(0.3)
    # try drag to expand
    drag(gx + 20, gy + 10, gx + 200, gy + 40)
    time.sleep(0.4)
    notes.append("google_typed_drag_size")
    # lock google
    click(1937, 93); time.sleep(0.3)
    click(2013, 107); time.sleep(0.3)
    click(1915, 517); time.sleep(0.3)

    run(["open", "-a", "Keynote"]); time.sleep(0.4)
    run(["screencapture", "-x", str(OUT / "slide_343.png")])
    els = dump(pid)
    notes.append("menus_final={}".format(menus(els)))
    notes.append("wins_final={}".format(windows(els)))
    notes.append("objs_final={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in list_left(els)]))
    notes.append("shot={}".format((OUT / "slide_343.png").stat().st_size if (OUT / "slide_343.png").exists() else 0))
    notes.append("ELAPSED={}".format(int(time.time() - t0)))
    write_notes()
    print("DONE")
    for n in notes:
        print(n)

if __name__ == "__main__":
    main()
