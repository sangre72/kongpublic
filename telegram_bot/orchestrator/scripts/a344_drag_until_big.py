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
    (OUT / "a344_notes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")

def read_align_wh(pid):
    """Read W/H from 정렬 tab labels *pt if present."""
    click(1937, 93); time.sleep(0.3)
    click(2013, 107); time.sleep(0.4)
    els = dump(pid)
    pts = []
    for e in els:
        lab = e.get("label") or ""
        if e.get("role") == "AXTextField" and lab.endswith("pt") and (e.get("cx") or 0) > 1600:
            try:
                v = float(lab.replace("pt", "").strip())
                pts.append((v, e.get("cx"), e.get("cy"), lab))
            except ValueError:
                pass
    pts.sort(key=lambda t: t[2] or 0)  # by y: W then H typically
    notes.append("align_pt_fields={}".format(pts[:6]))
    w = h = None
    if len(pts) >= 2:
        # first row y~266 W,H
        row1 = [p for p in pts if abs((p[2] or 0) - 266) < 40 or abs((p[2] or 0) - 277) < 40]
        if len(row1) >= 2:
            row1.sort(key=lambda t: t[1] or 0)
            w, h = row1[0][0], row1[1][0]
        else:
            w, h = pts[0][0], pts[1][0]
    return w, h

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
            break
        run(["open", "-a", "Keynote"]); time.sleep(0.9)
    else:
        notes.append("FAIL_app")
        run(["screencapture", "-x", str(OUT / "slide_344.png")])
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
    mw = max_doc(windows(els))
    wx, wy = mw.get("x") or 0, mw.get("y") or 0
    ww, wh = mw.get("w") or 2056, mw.get("h") or 1290
    # slide canvas region (logical)
    c0x, c0y = wx + 300, wy + 130
    c1x, c1y = wx + ww - 360, wy + wh - 50

    rect = next((e for e in list_left(els) if "사각" in (e.get("label") or "") or "직사" in (e.get("label") or "")), None)
    notes.append("objs={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in list_left(els)]))
    if rect:
        click(rect["cx"], rect["cy"]); time.sleep(0.55)
        notes.append("selected_rect")
    else:
        click((c0x + c1x) / 2, (c0y + c1y) / 2); time.sleep(0.4)

    w0, h0 = read_align_wh(pid)
    notes.append("size_before w={} h={}".format(w0, h0))
    # reselect rect after tab clicks
    if rect:
        click(rect["cx"], rect["cy"]); time.sleep(0.45)

    # estimate center of selected shape: use canvas center if tiny
    cx = (c0x + c1x) / 2
    cy = (c0y + c1y) / 2
    # if size known, estimate corners from center - half size * scale
    # slide points ~ canvas; rough scale: 1920 slide ≈ canvas width
    scale = (c1x - c0x) / 1920.0 if (c1x - c0x) > 100 else 0.7
    half_w = ((w0 or 100) / 2.0) * scale
    half_h = ((h0 or 100) / 2.0) * scale
    # SE handle approx
    se_x, se_y = cx + half_w, cy + half_h
    nw_x, nw_y = cx - half_w, cy - half_h
    notes.append("handles SE={},{} NW={},{} scale={}".format(se_x, se_y, nw_x, nw_y, scale))

    last_w, last_h = w0, h0
    for attempt in range(1, 5):
        # reselect
        els = dump(pid)
        rect = next((e for e in list_left(els) if "사각" in (e.get("label") or "") or "직사" in (e.get("label") or "")), None)
        if rect:
            click(rect["cx"], rect["cy"]); time.sleep(0.4)
        # drag SE to far BR
        target_se = (c1x - 5, c1y - 5)
        if attempt <= 2:
            drag(se_x, se_y, target_se[0], target_se[1])
            notes.append("drag{} SE {},{} -> {},{}".format(attempt, se_x, se_y, target_se[0], target_se[1]))
        else:
            # NW then SE
            drag(nw_x, nw_y, c0x + 20, c0y + 20)
            time.sleep(0.4)
            notes.append("drag{} NW -> {},{}".format(attempt, c0x + 20, c0y + 20))
            if rect:
                click(rect["cx"], rect["cy"]); time.sleep(0.35)
            drag(se_x, se_y, target_se[0], target_se[1])
            notes.append("drag{} SE again".format(attempt))
        time.sleep(0.55)
        # update handle estimate outward
        se_x, se_y = target_se[0] - 30, target_se[1] - 30
        nw_x, nw_y = c0x + 40, c0y + 40
        w, h = read_align_wh(pid)
        notes.append("size_after_drag{} w={} h={}".format(attempt, w, h))
        if w is not None and w >= 1500:
            notes.append("REACHED_w>=1500")
            break
        if w is not None and last_w is not None and abs(w - last_w) < 5 and attempt >= 2:
            notes.append("w_unchanged_continue")
        last_w, last_h = w, h

    w_final, h_final = read_align_wh(pid)
    notes.append("size_final w={} h={}".format(w_final, h_final))
    big = (w_final is not None and w_final >= 1500)
    notes.append("dump_w_ge_1500={}".format(big))

    # lock rect
    if rect:
        els = dump(pid)
        rect = next((e for e in list_left(els) if "사각" in (e.get("label") or "")), None)
        if rect:
            click(rect["cx"], rect["cy"]); time.sleep(0.35)
    click(1937, 93); time.sleep(0.3)
    click(2013, 107); time.sleep(0.3)
    click(1915, 517); time.sleep(0.35)

    # Google
    click(225, 20); time.sleep(0.4)
    click(310, 164); time.sleep(0.8)
    chord("cmd", "a"); time.sleep(0.1)
    text("Google"); time.sleep(0.35)
    # drag size only
    gx = (c0x + c1x) / 2
    gy = c0y + (c1y - c0y) * 0.32
    click(gx, gy); time.sleep(0.3)
    drag(gx + 15, gy + 10, gx + 220, gy + 45)
    time.sleep(0.4)
    click(1937, 93); time.sleep(0.25)
    click(2013, 107); time.sleep(0.25)
    click(1915, 517); time.sleep(0.3)

    run(["open", "-a", "Keynote"]); time.sleep(0.4)
    run(["screencapture", "-x", str(OUT / "slide_344.png")])
    els = dump(pid)
    notes.append("menus_final={}".format(menus(els)))
    notes.append("wins_final={}".format(windows(els)))
    notes.append("objs_final={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in list_left(els)]))
    notes.append("shot={}".format((OUT / "slide_344.png").stat().st_size if (OUT / "slide_344.png").exists() else 0))
    notes.append("ELAPSED={}".format(int(time.time() - t0)))
    write_notes()
    print("DONE")
    for n in notes:
        print(n)

if __name__ == "__main__":
    main()
