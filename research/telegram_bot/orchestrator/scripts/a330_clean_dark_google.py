#!/usr/bin/env python3
import json, subprocess, time
from pathlib import Path

K = "/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol"
OUT = Path("/Users/bumsuklee/git/kong-bot/kaymaps/keynote")
PID = subprocess.check_output(["pgrep", "-x", "Keynote"], text=True).split()[0]
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

def dump():
    r = run([K, "--json", "see", "--a11y", "--pid", PID], timeout=60)
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

def field(x, y, val):
    click(x, y)
    time.sleep(0.2)
    chord("cmd", "a")
    time.sleep(0.1)
    text(str(val))
    key("enter")
    time.sleep(0.35)

def set_pos_size(x, y, w, h):
    click(1937, 93)
    time.sleep(0.35)
    click(2013, 107)
    time.sleep(0.35)
    click(2055, 316)
    time.sleep(0.3)
    field(1903, 266, w)
    field(1992, 266, h)
    field(1903, 346, x)
    field(1992, 346, y)

def fill_hex(hex6):
    click(1937, 93)
    time.sleep(0.3)
    click(1831, 107)
    time.sleep(0.3)
    click(2007, 328)
    time.sleep(0.7)
    click(440, 39)
    time.sleep(0.35)
    click(518, 553)
    time.sleep(0.7)
    click(202, 1198)
    time.sleep(0.2)
    chord("cmd", "a")
    text(hex6)
    key("enter")
    time.sleep(0.35)

def close_panels():
    # esc repeatedly to close colors/font panels
    for _ in range(3):
        key("esc")
        time.sleep(0.2)

def ensure_fs():
    close_panels()
    els = dump()
    w = win(els)
    notes.append("win0={}".format(None if not w else (w.get("w"), w.get("h"), w.get("x"), w.get("y"))))
    if w and (w.get("w") or 0) >= 2000 and (w.get("h") or 0) >= 1200:
        notes.append("already_fs")
        return True
    # 보기
    click(419, 20)
    time.sleep(0.55)
    els = dump()
    start = None
    end = False
    for e in els:
        lab = e.get("label") or ""
        if lab == "전체 화면 시작":
            start = e
        if lab == "전체 화면 종료":
            end = True
    if start:
        notes.append("click_fs_start {},{}".format(start.get("cx"), start.get("cy")))
        click(start["cx"], start["cy"])
        time.sleep(1.4)
    elif not end:
        # traffic green only when windowed
        notes.append("green_fallback_54_193")
        click(54, 193)
        time.sleep(1.4)
    else:
        notes.append("has_fs_exit_but_geom_fail")
    els = dump()
    w = win(els)
    ok = bool(w and (w.get("w") or 0) >= 2000 and (w.get("h") or 0) >= 1200)
    notes.append("win1={} G={}".format(None if not w else (w.get("w"), w.get("h")), ok))
    return ok

def main():
    notes.append("PID {}".format(PID))
    fs = ensure_fs()
    close_panels()
    # delete all unlockable junk — select all on canvas then delete
    # click canvas center
    click(1000, 700)
    time.sleep(0.3)
    chord("cmd", "a")
    time.sleep(0.25)
    key("delete")
    time.sleep(0.6)
    # if locked objects remain, leave them; else remake bg
    # insert rect bg
    click(225, 20)
    time.sleep(0.4)
    click(310, 188)
    time.sleep(0.4)
    click(492, 188)
    time.sleep(0.8)
    set_pos_size(0, 0, 1920, 1080)
    fill_hex("202124")
    # lock
    click(1937, 93)
    time.sleep(0.3)
    click(2013, 107)
    time.sleep(0.3)
    click(1915, 517)
    time.sleep(0.4)
    # Google text box
    click(225, 20)
    time.sleep(0.4)
    click(310, 164)
    time.sleep(0.8)
    chord("cmd", "a")
    time.sleep(0.1)
    text("Google")
    time.sleep(0.3)
    # font 72
    click(1937, 93)
    time.sleep(0.3)
    click(1922, 107)
    time.sleep(0.3)
    field(2002, 326, 72)
    set_pos_size(710, 338, 500, 92)
    # lock google
    click(1937, 93)
    time.sleep(0.3)
    click(2013, 107)
    time.sleep(0.3)
    click(1915, 517)
    time.sleep(0.3)
    run(["screencapture", "-x", str(OUT / "slide_330.png")])
    els = dump()
    w = win(els)
    g = [e for e in els if "Google" in (e.get("label") or "")]
    notes.append("final_win={}".format(None if not w else (w.get("w"), w.get("h"))))
    notes.append("google_labels={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in g[:6]]))
    notes.append("fs_ok={}".format(fs))
    notes.append("shot={}".format((OUT / "slide_330.png").stat().st_size if (OUT / "slide_330.png").exists() else 0))
    notes.append("ELAPSED={}".format(int(time.time() - t0)))
    (OUT / "a330_notes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")
    print("DONE")
    for n in notes:
        print(n)

if __name__ == "__main__":
    main()
