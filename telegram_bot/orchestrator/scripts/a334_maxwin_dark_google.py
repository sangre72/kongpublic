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

def all_windows(els):
    wins = []
    for e in els:
        if e.get("role") == "AXWindow":
            w = e.get("w") or 0
            h = e.get("h") or 0
            wins.append({
                "label": e.get("label"),
                "x": e.get("x"), "y": e.get("y"),
                "w": w, "h": h,
                "area": (w or 0) * (h or 0),
                "cx": e.get("cx"), "cy": e.get("cy"),
            })
    wins.sort(key=lambda z: z["area"], reverse=True)
    return wins

def menus(els):
    return [e.get("label") for e in els if e.get("role") == "AXMenuBarItem" and e.get("label")]

def is_keynote(labs):
    s = set(labs or [])
    return ("삽입" in s or "슬라이드" in s) and ("포맷" in s or "편집" in s) and "이동" not in s

def max_keynote_win(wins):
    # prefer largest with w>=800 h>=500
    for w in wins:
        if (w["w"] or 0) >= 800 and (w["h"] or 0) >= 500:
            return w
    return wins[0] if wins else None

def g_geom_max(mw):
    if not mw:
        return False
    return (mw["w"] or 0) >= 2000 and (mw["h"] or 0) >= 1200

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

def write_notes():
    (OUT / "a334_notes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")

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
        run(["screencapture", "-x", str(OUT / "slide_334.png")])
        write_notes(); return

    # dismiss overlays
    for _ in range(4):
        key("esc"); time.sleep(0.2)

    els = dump(pid)
    wins = all_windows(els)
    notes.append("WINDOWS_ALL={}".format(wins))
    mw = max_keynote_win(wins)
    notes.append("MAX_WIN={}".format(mw))
    used_tiny = bool(mw and ((mw["w"] or 0) < 800 or (mw["h"] or 0) < 500))
    notes.append("used_tiny={}".format(used_tiny))

    # if tiny overlays exist, esc already done; try close red of small win only
    for w in wins:
        if (w["w"] or 0) < 800 and (w["h"] or 0) < 500 and (w["w"] or 0) > 50:
            # red traffic of overlay approx left of window
            rx = (w.get("x") or 0) + 14
            ry = (w.get("y") or 0) + 14
            notes.append("overlay_esc_or_red try {},{}".format(rx, ry))
            key("esc"); time.sleep(0.25)

    els = dump(pid)
    wins = all_windows(els)
    notes.append("WINDOWS_AFTER_ESC={}".format(wins))
    mw = max_keynote_win(wins)
    notes.append("MAX_WIN2={}".format(mw))

    fs = g_geom_max(mw)
    notes.append("FS_max={}".format(fs))

    if not fs:
        # only if max is truly small
        if mw and (mw["w"] or 0) >= 2000:
            notes.append("FS_Y_by_W_only")
            fs = True
        elif mw and (mw["w"] or 0) < (2056 - 80):
            # try 보기 시작
            if is_keynote(menus(els)):
                click(419, 20); time.sleep(0.55)
                els = dump(pid)
                if is_keynote(menus(els)):
                    start = None
                    for e in els:
                        if e.get("label") == "전체 화면 시작":
                            start = e
                            break
                    if start:
                        notes.append("fs_start {},{}".format(start.get("cx"), start.get("cy")))
                        click(start["cx"], start["cy"]); time.sleep(1.5)
                    else:
                        # green on LARGE titlebar: x near max win left + 54, y near win y+20
                        gx = (mw.get("x") or 0) + 54
                        gy = (mw.get("y") or 0) + 20
                        notes.append("green_large {},{}".format(gx, gy))
                        click(gx, gy); time.sleep(1.5)
            els = dump(pid)
            wins = all_windows(els)
            notes.append("WINDOWS_AFTER_FS={}".format(wins))
            mw = max_keynote_win(wins)
            fs = g_geom_max(mw)
            notes.append("MAX_WIN3={} FS={}".format(mw, fs))

    if not fs:
        notes.append("FAIL_FS_max_still_small")
        run(["screencapture", "-x", str(OUT / "slide_334.png")])
        notes.append("shot={}".format((OUT / "slide_334.png").stat().st_size if (OUT / "slide_334.png").exists() else 0))
        notes.append("ELAPSED={}".format(int(time.time() - t0)))
        write_notes()
        print("FAIL_FS")
        for n in notes:
            print(n)
        return

    # proceed dark+google — use FS coords (prod_controls scale for full display)
    notes.append("PROCEED_FS")
    # click center of max window
    cx = (mw.get("x") or 0) + (mw.get("w") or 0) / 2
    cy = (mw.get("y") or 0) + (mw.get("h") or 0) / 2
    click(cx, cy); time.sleep(0.3)
    chord("cmd", "a"); time.sleep(0.2); key("delete"); time.sleep(0.6)

    click(225, 20); time.sleep(0.4)
    click(310, 188); time.sleep(0.4)
    click(492, 188); time.sleep(0.8)
    set_pos_size(0, 0, 1920, 1080)
    fill_hex("202124")
    click(1937, 93); time.sleep(0.3); click(2013, 107); time.sleep(0.3); click(1915, 517); time.sleep(0.35)

    click(225, 20); time.sleep(0.4)
    click(310, 164); time.sleep(0.8)
    chord("cmd", "a"); text("Google"); time.sleep(0.25)
    click(1937, 93); time.sleep(0.3); click(1922, 107); time.sleep(0.3)
    field(2002, 326, 72)
    set_pos_size(710, 338, 500, 92)
    click(1937, 93); time.sleep(0.3); click(2013, 107); time.sleep(0.3); click(1915, 517); time.sleep(0.3)

    run(["screencapture", "-x", str(OUT / "slide_334.png")])
    els = dump(pid)
    notes.append("menus_final={}".format(menus(els)))
    notes.append("shot_keynote={}".format(is_keynote(menus(els))))
    notes.append("shot={}".format((OUT / "slide_334.png").stat().st_size if (OUT / "slide_334.png").exists() else 0))
    notes.append("ELAPSED={}".format(int(time.time() - t0)))
    write_notes()
    print("DONE")
    for n in notes:
        print(n)

if __name__ == "__main__":
    main()
