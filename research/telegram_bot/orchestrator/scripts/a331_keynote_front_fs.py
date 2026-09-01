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

def menubar_labels(els):
    return [e.get("label") for e in els if e.get("role") == "AXMenuBarItem" and e.get("label")]

def is_keynote_menus(labs):
    s = set(labs or [])
    # Keynote has 삽입+슬라이드+포맷; Finder has 이동 often
    return ("삽입" in s or "슬라이드" in s) and ("포맷" in s or "편집" in s) and "이동" not in s

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
    # activate Keynote only
    run(["open", "-a", "Keynote"])
    time.sleep(1.2)
    pid_r = run(["pgrep", "-x", "Keynote"])
    if pid_r.returncode != 0:
        notes.append("NO_KEYNOTE_PID")
        (OUT / "a331_notes.txt").write_text("\n".join(notes) + "\n")
        print("FAIL no keynote")
        return
    pid = pid_r.stdout.strip().split()[0]
    notes.append("PID {}".format(pid))

    for attempt in range(3):
        els = dump(pid)
        labs = menubar_labels(els)
        notes.append("menus{}={}".format(attempt, labs))
        if is_keynote_menus(labs):
            notes.append("menus_ok")
            break
        notes.append("not_keynote_menus_retry_open")
        run(["open", "-a", "Keynote"])
        time.sleep(1.0)
    else:
        notes.append("STOP_FINDER_OR_WRONG_APP")
        run(["screencapture", "-x", str(OUT / "slide_331.png")])
        (OUT / "a331_notes.txt").write_text("\n".join(notes) + "\n")
        print("STOP wrong app")
        for n in notes: print(n)
        return

    # FS
    key("esc"); time.sleep(0.2)
    els = dump(pid)
    w = win(els)
    notes.append("win0={}".format(None if not w else (w.get("w"), w.get("h"), w.get("x"), w.get("y"))))
    g = w and (w.get("w") or 0) >= 2000 and (w.get("h") or 0) >= 1200
    if not g:
        click(419, 20); time.sleep(0.55)
        els = dump(pid)
        if not is_keynote_menus(menubar_labels(els)):
            notes.append("STOP_menu_became_non_keynote_during_view")
            run(["screencapture", "-x", str(OUT / "slide_331.png")])
            (OUT / "a331_notes.txt").write_text("\n".join(notes) + "\n")
            print("STOP mid")
            return
        start = None
        end = False
        for e in els:
            lab = e.get("label") or ""
            if lab == "전체 화면 시작":
                start = e
            if lab == "전체 화면 종료":
                end = True
        if start:
            notes.append("fs_start {},{}".format(start.get("cx"), start.get("cy")))
            click(start["cx"], start["cy"]); time.sleep(1.4)
        elif not end:
            notes.append("green_54_193")
            click(54, 193); time.sleep(1.4)
        else:
            notes.append("has_exit_item")
    els = dump(pid)
    w = win(els)
    fs = bool(w and (w.get("w") or 0) >= 2000 and (w.get("h") or 0) >= 1200)
    notes.append("win1={} FS={}".format(None if not w else (w.get("w"), w.get("h")), fs))

    # objects: google / rect
    goog = [e for e in els if "Google" in (e.get("label") or "")]
    notes.append("google_n={}".format(len(goog)))

    # remake bg+google if needed (always clean for reliability when FS ok or not)
    click(1000, 700); time.sleep(0.25)
    chord("cmd", "a"); time.sleep(0.2); key("delete"); time.sleep(0.5)
    # bg
    click(225, 20); time.sleep(0.4)
    click(310, 188); time.sleep(0.4)
    click(492, 188); time.sleep(0.8)
    set_pos_size(0, 0, 1920, 1080)
    fill_hex("202124")
    click(1937, 93); time.sleep(0.3); click(2013, 107); time.sleep(0.3); click(1915, 517); time.sleep(0.35)
    # google
    click(225, 20); time.sleep(0.4)
    click(310, 164); time.sleep(0.8)
    chord("cmd", "a"); text("Google"); time.sleep(0.25)
    click(1937, 93); time.sleep(0.3); click(1922, 107); time.sleep(0.3)
    field(2002, 326, 72)
    set_pos_size(710, 338, 500, 92)
    click(1937, 93); time.sleep(0.3); click(2013, 107); time.sleep(0.3); click(1915, 517); time.sleep(0.3)

    run(["screencapture", "-x", str(OUT / "slide_331.png")])
    els = dump(pid)
    labs = menubar_labels(els)
    notes.append("menus_final={}".format(labs))
    notes.append("shot_keynote_menus={}".format(is_keynote_menus(labs)))
    notes.append("shot_bytes={}".format((OUT / "slide_331.png").stat().st_size if (OUT / "slide_331.png").exists() else 0))
    notes.append("ELAPSED={}".format(int(time.time() - t0)))
    (OUT / "a331_notes.txt").write_text("\n".join(notes) + "\n")
    print("DONE")
    for n in notes:
        print(n)

if __name__ == "__main__":
    main()
