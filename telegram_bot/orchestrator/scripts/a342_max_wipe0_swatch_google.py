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
    run([K, "--yes", "input", "click", str(int(x)), str(int(y))])

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

def write_notes():
    (OUT / "a342_notes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")

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

def unlock_del(pid, e):
    click(e["cx"], e["cy"]); time.sleep(0.4)
    click(376, 20); time.sleep(0.45)
    els = dump(pid)
    item = next((x for x in els if x.get("role") == "AXMenuItem" and x.get("label") == "잠금 해제"), None)
    if item:
        click(item["cx"], item["cy"]); time.sleep(0.4)
    else:
        click(452, 306); time.sleep(0.35)
    key("delete"); time.sleep(0.35)
    key("esc"); time.sleep(0.15)
    notes.append("del {}".format(e.get("label")))

def field_if_pt(x, y, val, pid):
    """Type only if click lands on a *pt field label pattern nearby — still risky; use carefully."""
    click(x, y); time.sleep(0.25)
    chord("cmd", "a"); time.sleep(0.1)
    text(str(val)); key("enter"); time.sleep(0.35)
    # check no new "0"/val text object
    bad = [e for e in list_left(dump(pid)) if (e.get("label") or "") in (str(val), "0", "202124")]
    if bad:
        notes.append("size_type_leaked {} undo".format(val))
        chord("cmd", "z"); time.sleep(0.35)
        return False
    return True

def main():
    run(["open", "-a", "Keynote"]); time.sleep(1.0)
    pr = run(["pgrep", "-x", "Keynote"])
    if pr.returncode != 0:
        notes.append("NO_PID"); write_notes(); return
    pid = pr.stdout.strip().split()[0]
    notes.append("PID {}".format(pid))

    for i in range(3):
        els = dump(pid)
        labs = menus(els)
        notes.append("menus{}={}".format(i, labs))
        if is_keynote(labs):
            break
        run(["open", "-a", "Keynote"]); time.sleep(0.9)
    else:
        notes.append("FAIL_not_keynote")
        run(["screencapture", "-x", str(OUT / "slide_342.png")])
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

    # wipe 0 / 202124 / leftovers
    for p in range(3):
        els = dump(pid)
        objs = list_left(els)
        notes.append("OBJS_p{}={}".format(p, [(e.get("label"), e.get("cx"), e.get("cy")) for e in objs]))
        if not objs:
            break
        for e in objs:
            unlock_del(pid, e)
        click(1000, 700); time.sleep(0.15)
        chord("cmd", "a"); time.sleep(0.15)
        key("delete"); time.sleep(0.4)

    els = dump(pid)
    left = list_left(els)
    notes.append("LEFT={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in left]))
    notes.append("has_0={}".format(any((e.get("label") or "") == "0" for e in left)))
    notes.append("has_202124={}".format(any("202124" in (e.get("label") or "") for e in left)))

    # insert rect
    click(225, 20); time.sleep(0.4)
    click(310, 188); time.sleep(0.4)
    click(492, 188); time.sleep(0.9)
    notes.append("rect_inserted")
    # size — try fields with leak guard
    click(1937, 93); time.sleep(0.3)
    click(2013, 107); time.sleep(0.35)
    click(2055, 316); time.sleep(0.3)
    ok_w = field_if_pt(1903, 266, 1920, pid)
    ok_h = field_if_pt(1992, 266, 1080, pid)
    ok_x = field_if_pt(1903, 346, 0, pid)
    ok_y = field_if_pt(1992, 346, 0, pid)
    notes.append("size_ok w={} h={} x={} y={}".format(ok_w, ok_h, ok_x, ok_y))

    # select rect from list
    rect = next((e for e in list_left(dump(pid)) if "사각" in (e.get("label") or "") or "직사" in (e.get("label") or "")), None)
    if rect:
        click(rect["cx"], rect["cy"]); time.sleep(0.4)
        notes.append("selected_rect")

    # fill swatch only — no 색상 보기 HEX type
    click(1937, 93); time.sleep(0.3)
    click(1831, 107); time.sleep(0.35)
    click(2007, 328); time.sleep(0.7)
    # dark chip near fill expand (prod-ish)
    for xy in [(1880, 450), (1920, 480), (1850, 420)]:
        click(xy[0], xy[1]); time.sleep(0.35)
        notes.append("swatch_click {},{}".format(*xy))
        bad = [e for e in list_left(dump(pid)) if (e.get("label") or "") in ("0", "202124") or "202124" in (e.get("label") or "")]
        if bad:
            notes.append("swatch_leaked undo")
            chord("cmd", "z"); time.sleep(0.35)
        else:
            notes.append("swatch_ok_no_text_leak")
            break
    key("esc"); time.sleep(0.2)

    # lock
    click(1937, 93); time.sleep(0.3)
    click(2013, 107); time.sleep(0.3)
    click(1915, 517); time.sleep(0.35)

    # Google letters only
    click(225, 20); time.sleep(0.4)
    click(310, 164); time.sleep(0.8)
    chord("cmd", "a"); time.sleep(0.1)
    text("Google"); time.sleep(0.3)
    # size carefully
    click(1937, 93); time.sleep(0.3)
    click(1922, 107); time.sleep(0.3)
    field_if_pt(2002, 326, 72, pid)
    click(2013, 107); time.sleep(0.3)
    field_if_pt(1903, 266, 500, pid)
    field_if_pt(1992, 266, 92, pid)
    field_if_pt(1903, 346, 710, pid)
    field_if_pt(1992, 346, 338, pid)
    click(1915, 517); time.sleep(0.3)

    run(["open", "-a", "Keynote"]); time.sleep(0.5)
    run(["screencapture", "-x", str(OUT / "slide_342.png")])
    els = dump(pid)
    notes.append("menus_final={}".format(menus(els)))
    notes.append("wins_final={}".format(windows(els)))
    notes.append("objs_final={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in list_left(els)]))
    notes.append("shot={}".format((OUT / "slide_342.png").stat().st_size if (OUT / "slide_342.png").exists() else 0))
    notes.append("ELAPSED={}".format(int(time.time() - t0)))
    write_notes()
    print("DONE")
    for n in notes:
        print(n)

if __name__ == "__main__":
    main()
