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

def win(els):
    for e in els:
        if e.get("role") == "AXWindow":
            return e
    return None

def menus(els):
    return [e.get("label") for e in els if e.get("role") == "AXMenuBarItem" and e.get("label")]

def is_keynote(labs):
    s = set(labs or [])
    return ("삽입" in s or "슬라이드" in s) and ("포맷" in s or "편집" in s) and "이동" not in s

def g_geom(w):
    return bool(w and (w.get("w") or 0) >= 2000 and (w.get("h") or 0) >= 1200)

def field(x, y, val):
    click(x, y); time.sleep(0.2); chord("cmd", "a"); time.sleep(0.1); text(str(val)); key("enter"); time.sleep(0.35)

def set_pos_size(x, y, w, h):
    click(1937, 93); time.sleep(0.35)
    click(2013, 107); time.sleep(0.35)
    click(2055, 316); time.sleep(0.3)
    field(1903, 266, w); field(1992, 266, h); field(1903, 346, x); field(1992, 346, y)

def fill_hex(hex6):
    click(1937, 93); time.sleep(0.3)
    click(1831, 107); time.sleep(0.3)
    click(2007, 328); time.sleep(0.7)
    click(440, 39); time.sleep(0.35)
    click(518, 553); time.sleep(0.7)
    click(202, 1198); time.sleep(0.2)
    chord("cmd", "a"); text(hex6); key("enter"); time.sleep(0.35)

def main():
    run(["open", "-a", "Keynote"]); time.sleep(1.2)
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
        run(["open", "-a", "Keynote"]); time.sleep(1.0)
    else:
        notes.append("FAIL_not_keynote")
        run(["screencapture", "-x", str(OUT / "slide_333.png")])
        write_notes(); print("FAIL app"); return

    # FS only
    key("esc"); time.sleep(0.2)
    els = dump(pid)
    w = win(els)
    notes.append("win0={}".format(None if not w else (w.get("w"), w.get("h"), w.get("x"), w.get("y"))))
    if not g_geom(w):
        if not is_keynote(menus(els)):
            notes.append("FAIL_menus_before_fs")
            run(["screencapture", "-x", str(OUT / "slide_333.png")]); write_notes(); return
        click(419, 20); time.sleep(0.55)
        els = dump(pid)
        if not is_keynote(menus(els)):
            notes.append("FAIL_menus_during_view")
            run(["screencapture", "-x", str(OUT / "slide_333.png")]); write_notes(); return
        start = end = None
        for e in els:
            lab = e.get("label") or ""
            if lab == "전체 화면 시작":
                start = e
            if lab == "전체 화면 종료":
                end = e
        if start:
            notes.append("fs_start {},{}".format(start.get("cx"), start.get("cy")))
            click(start["cx"], start["cy"]); time.sleep(1.5)
        elif not end:
            notes.append("green_54_193")
            click(54, 193); time.sleep(1.5)
        else:
            notes.append("already_exit_item")
    els = dump(pid)
    w = win(els)
    notes.append("win1={}".format(None if not w else (w.get("w"), w.get("h"))))
    if not g_geom(w):
        notes.append("FAIL_G_GEOM STOP_no_windowed_clicks")
        run(["screencapture", "-x", str(OUT / "slide_333.png")])
        notes.append("shot={}".format((OUT / "slide_333.png").stat().st_size))
        notes.append("ELAPSED={}".format(int(time.time() - t0)))
        write_notes()
        print("FAIL_FS")
        for n in notes:
            print(n)
        return

    notes.append("G_GEOM_Y")
    # clean
    click(1000, 700); time.sleep(0.25)
    chord("cmd", "a"); time.sleep(0.2); key("delete"); time.sleep(0.6)
    # bg
    click(225, 20); time.sleep(0.4)
    click(310, 188); time.sleep(0.4)
    click(492, 188); time.sleep(0.8)
    set_pos_size(0, 0, 1920, 1080)
    fill_hex("202124")
    click(1937, 93); time.sleep(0.3); click(2013, 107); time.sleep(0.3); click(1915, 517); time.sleep(0.35)
    # google text box via 삽입>텍스트 상자 (xy) not toolbar 텍스트
    click(225, 20); time.sleep(0.4)
    click(310, 164); time.sleep(0.8)
    chord("cmd", "a"); text("Google"); time.sleep(0.25)
    click(1937, 93); time.sleep(0.3); click(1922, 107); time.sleep(0.3)
    field(2002, 326, 72)
    set_pos_size(710, 338, 500, 92)
    click(1937, 93); time.sleep(0.3); click(2013, 107); time.sleep(0.3); click(1915, 517); time.sleep(0.3)

    run(["screencapture", "-x", str(OUT / "slide_333.png")])
    els = dump(pid)
    notes.append("menus_final={}".format(menus(els)))
    notes.append("shot_keynote={}".format(is_keynote(menus(els))))
    notes.append("shot={}".format((OUT / "slide_333.png").stat().st_size if (OUT / "slide_333.png").exists() else 0))
    notes.append("ELAPSED={}".format(int(time.time() - t0)))
    write_notes()
    print("DONE")
    for n in notes:
        print(n)

def write_notes():
    (OUT / "a333_notes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
