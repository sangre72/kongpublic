#!/usr/bin/env python3
"""a_346: select 사각형 ONLY (not 텍스트), inspector 너비/높이 or drag SE, Google."""
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
    (OUT / "a346_notes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")

def inspector_fields(els):
    fields = []
    for e in els:
        if e.get("role") != "AXTextField":
            continue
        cx = e.get("cx") or 0
        if cx < 1500:
            continue
        lab = e.get("label") or ""
        fields.append({
            "label": lab, "cx": cx, "cy": e.get("cy"),
            "x": e.get("x"), "y": e.get("y"), "w": e.get("w"), "h": e.get("h"),
            "value": e.get("value"),
        })
    return fields

def find_size_pair(fields):
    """Find 너비/높이 by label or nearby static labels."""
    w_f = h_f = None
    for f in fields:
        lab = (f.get("label") or "")
        if "너비" in lab or lab in ("W", "너비(W)"):
            w_f = f
        if "높이" in lab or lab in ("H", "높이(H)"):
            h_f = f
    return w_f, h_f

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
        run(["screencapture", "-x", str(OUT / "slide_346.png")])
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
    c0x, c0y = wx + 300, wy + 130
    c1x, c1y = wx + ww - 360, wy + wh - 50

    objs = list_left(els)
    notes.append("objs_before={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in objs]))

    # Select 사각형 ONLY — prefer y~154, never 텍스트
    rects = [e for e in objs if "사각" in (e.get("label") or "") or "직사" in (e.get("label") or "")]
    if not rects:
        notes.append("NO_RECT_IN_LIST")
    else:
        # prefer cy near 154, else first 사각형
        rects.sort(key=lambda e: abs((e.get("cy") or 0) - 154))
        rect = rects[0]
        notes.append("selected_target={}".format((rect.get("label"), rect.get("cx"), rect.get("cy"))))
        click(rect["cx"], rect["cy"]); time.sleep(0.55)
        notes.append("clicked_사각형")

    # Open 포맷 > 정렬
    # menubar 포맷 then 정렬 tab in inspector
    click(1937, 93); time.sleep(0.35)  # 포맷 area
    # try labeled 정렬
    els = dump(pid)
    align_btn = next((e for e in els if e.get("label") == "정렬" and (e.get("cx") or 0) > 1500), None)
    if align_btn:
        click(align_btn["cx"], align_btn["cy"]); time.sleep(0.4)
        notes.append("align_tab_labeled={},{}".format(align_btn["cx"], align_btn["cy"]))
    else:
        # job hint 2055,316 or prior 2013,107
        click(2013, 107); time.sleep(0.35)
        click(2055, 316); time.sleep(0.4)
        notes.append("align_tab_coords")

    els = dump(pid)
    fields = inspector_fields(els)
    notes.append("inspector_fields={}".format(fields[:20]))
    # also log any static labels near inspector with 너비/높이
    labs = []
    for e in els:
        lab = e.get("label") or ""
        cx = e.get("cx") or 0
        if cx > 1500 and any(k in lab for k in ("너비", "높이", "W", "H", "pt", "크기")):
            labs.append((lab, e.get("role"), cx, e.get("cy")))
    notes.append("inspector_size_labels={}".format(labs[:30]))

    w_f, h_f = find_size_pair(fields)
    typed = False
    if w_f and h_f:
        notes.append("size_fields_found w={} h={}".format(w_f, h_f))
        # click 너비, type 1920
        click(w_f["cx"], w_f["cy"]); time.sleep(0.3)
        els2 = dump(pid)
        # re-read field focus-ish
        chord("cmd", "a"); time.sleep(0.1)
        text("1920"); time.sleep(0.15)
        run([K, "--yes", "input", "key", "return"]); time.sleep(0.35)
        notes.append("typed_width_1920")
        click(h_f["cx"], h_f["cy"]); time.sleep(0.3)
        chord("cmd", "a"); time.sleep(0.1)
        text("1080"); time.sleep(0.15)
        run([K, "--yes", "input", "key", "return"]); time.sleep(0.35)
        notes.append("typed_height_1080")
        typed = True
        # leak guard: if slide got 0/1920 text, undo
        els = dump(pid)
        left = list_left(els)
        bad = [e for e in left if (e.get("label") or "") in ("0", "1920", "1080", "202124")
               or (e.get("label") or "").startswith("1920")]
        if bad:
            notes.append("leak_suspect={}".format([(e.get("label"), e.get("cy")) for e in bad]))
            chord("cmd", "z"); time.sleep(0.3)
            notes.append("UNDO_leak")
            typed = False
    else:
        notes.append("no_named_size_fields")
        # fallback: reselect 사각형, drag SE
        els = dump(pid)
        rects = [e for e in list_left(els) if "사각" in (e.get("label") or "")]
        if rects:
            rects.sort(key=lambda e: abs((e.get("cy") or 0) - 154))
            r = rects[0]
            click(r["cx"], r["cy"]); time.sleep(0.45)
            notes.append("reselect_rect_for_drag")
        # drag from estimated center SE to canvas BR — careful not to grab text
        # use lower-right of canvas relative drag from mid-lower shape estimate
        se_x = (c0x + c1x) / 2 + 40
        se_y = (c0y + c1y) / 2 + 40
        for i in range(3):
            drag(se_x, se_y, c1x - 10, c1y - 10)
            notes.append("drag_se_{} {},{} -> {},{}".format(i + 1, se_x, se_y, c1x - 10, c1y - 10))
            time.sleep(0.5)
            se_x, se_y = c1x - 40, c1y - 40
            # reselect rect
            els = dump(pid)
            rects = [e for e in list_left(els) if "사각" in (e.get("label") or "")]
            if rects:
                click(rects[0]["cx"], rects[0]["cy"]); time.sleep(0.35)

    # Delete leftover 텍스트 objects that may be tiny black/3-line boxes
    els = dump(pid)
    texts = [e for e in list_left(els) if (e.get("label") or "") == "텍스트"]
    notes.append("texts_before_delete={}".format([(e.get("label"), e.get("cy")) for e in texts]))
    # keep at most none of the junk text; delete all 텍스트 that aren't Google yet
    # job: delete leftover 텍스트 if small black with 3 lines
    for e in texts:
        click(e["cx"], e["cy"]); time.sleep(0.35)
        run([K, "--yes", "input", "key", "delete"]); time.sleep(0.3)
        notes.append("deleted_text cy={}".format(e.get("cy")))

    # Google
    els = dump(pid)
    notes.append("objs_mid={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in list_left(els)]))
    # insert text box via menu coords used before
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
    run(["screencapture", "-x", str(OUT / "slide_346.png")])
    els = dump(pid)
    notes.append("menus_final={}".format(menus(els)))
    notes.append("wins_final={}".format(windows(els)))
    notes.append("objs_final={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in list_left(els)]))
    notes.append("typed_size={}".format(typed))
    notes.append("shot={}".format((OUT / "slide_346.png").stat().st_size if (OUT / "slide_346.png").exists() else 0))
    notes.append("ELAPSED={}".format(int(time.time() - t0)))
    write_notes()
    print("DONE")
    for n in notes:
        print(n)

if __name__ == "__main__":
    main()
