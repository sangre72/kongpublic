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
    (OUT / "a339_notes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")

def list_left_objs(els):
    out = []
    for e in els:
        lab = (e.get("label") or "").strip()
        cx = e.get("cx") or 0
        cy = e.get("cy") or 0
        if cx > 450 or cy < 100 or cy > 900:
            continue
        if lab in ("텍스트 상자 삽입", "검색") or not lab:
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

def unlock_and_delete(pid, e):
    click(e["cx"], e["cy"]); time.sleep(0.4)
    click(376, 20); time.sleep(0.45)
    els = dump(pid)
    item = next((x for x in els if x.get("role") == "AXMenuItem" and x.get("label") == "잠금 해제"), None)
    if item:
        click(item["cx"], item["cy"]); time.sleep(0.4)
        notes.append("unlock {}".format(e.get("label")))
    else:
        click(452, 306); time.sleep(0.35)
        notes.append("unlock_fallback {}".format(e.get("label")))
    key("delete"); time.sleep(0.35)
    key("esc"); time.sleep(0.15)

def field(x, y, val):
    click(x, y); time.sleep(0.2); chord("cmd", "a"); time.sleep(0.1); text(str(val)); key("enter"); time.sleep(0.35)

def set_pos_size(x, y, w, h):
    click(1937, 93); time.sleep(0.35)
    click(2013, 107); time.sleep(0.35)
    click(2055, 316); time.sleep(0.3)
    field(1903, 266, w); field(1992, 266, h); field(1903, 346, x); field(1992, 346, y)

def fill_hex_shape(hex6):
    """Shape fill via style well then 보기>색상 보기 HEX field — never text box."""
    # style tab + fill well
    click(1937, 93); time.sleep(0.35)
    click(1831, 107); time.sleep(0.4)
    click(2007, 328); time.sleep(0.7)
    # Colors panel
    click(440, 39); time.sleep(0.4)
    click(518, 553); time.sleep(0.8)
    # HEX field in colors panel (prod_controls)
    click(202, 1198); time.sleep(0.25)
    chord("cmd", "a"); time.sleep(0.1)
    text(hex6); key("enter"); time.sleep(0.45)
    key("esc"); time.sleep(0.25)  # close menus if any
    notes.append("fill_hex_shape {}".format(hex6))

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
        run(["screencapture", "-x", str(OUT / "slide_339.png")])
        write_notes(); return

    # max window
    for _ in range(2):
        els = dump(pid)
        wins = windows(els)
        notes.append("WINDOWS={}".format(wins))
        mw = max_doc(wins)
        if mw and (mw["w"] or 0) >= 2000 and (mw["h"] or 0) >= 1200:
            notes.append("FS_ok {}".format(mw))
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
        else:
            run(["open", "-a", "Keynote"]); time.sleep(0.8)

    # delete 202124 and leftovers via list
    for pass_i in range(3):
        els = dump(pid)
        objs = list_left_objs(els)
        notes.append("OBJS_p{}={}".format(pass_i, [(e.get("label"), e.get("cx"), e.get("cy")) for e in objs]))
        # prioritize 202124 glyphs
        targets = [e for e in objs if "202124" in (e.get("label") or "")]
        targets += [e for e in objs if e not in targets]
        if not targets:
            break
        for e in targets:
            unlock_and_delete(pid, e)
        # bulk delete attempt
        click(1000, 700); time.sleep(0.2)
        chord("cmd", "a"); time.sleep(0.2)
        key("delete"); time.sleep(0.5)

    els = dump(pid)
    left = list_left_objs(els)
    notes.append("LEFT_AFTER={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in left]))
    has_202124 = any("202124" in (e.get("label") or "") for e in left)
    notes.append("has_202124_label={}".format(has_202124))

    # insert RECT only
    click(225, 20); time.sleep(0.4)
    click(310, 188); time.sleep(0.45)
    click(492, 188); time.sleep(0.9)
    notes.append("inserted_rect")
    set_pos_size(0, 0, 1920, 1080)
    fill_hex_shape("202124")
    # lock rect
    click(1937, 93); time.sleep(0.3)
    click(2013, 107); time.sleep(0.3)
    click(1915, 517); time.sleep(0.35)

    # check no 202124 text object created
    els = dump(pid)
    bad = [e for e in list_left_objs(els) if "202124" in (e.get("label") or "")]
    notes.append("AFTER_FILL_202124_objs={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in bad]))
    if bad:
        notes.append("UNDO_fill_became_text")
        chord("cmd", "z"); time.sleep(0.4)
        # reselect rect if possible
        for e in list_left_objs(dump(pid)):
            if "사각" in (e.get("label") or "") or "직사" in (e.get("label") or ""):
                click(e["cx"], e["cy"]); time.sleep(0.4)
                break
        fill_hex_shape("202124")

    # Google letters only
    click(225, 20); time.sleep(0.4)
    click(310, 164); time.sleep(0.8)
    chord("cmd", "a"); time.sleep(0.1)
    text("Google"); time.sleep(0.3)  # never 202124
    click(1937, 93); time.sleep(0.3)
    click(1922, 107); time.sleep(0.3)
    field(2002, 326, 72)
    set_pos_size(710, 338, 500, 92)
    click(1937, 93); time.sleep(0.3)
    click(2013, 107); time.sleep(0.3)
    click(1915, 517); time.sleep(0.3)

    run(["open", "-a", "Keynote"]); time.sleep(0.4)
    run(["screencapture", "-x", str(OUT / "slide_339.png")])
    els = dump(pid)
    notes.append("menus_final={}".format(menus(els)))
    notes.append("wins_final={}".format(windows(els)))
    notes.append("objs_final={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in list_left_objs(els)]))
    notes.append("shot={}".format((OUT / "slide_339.png").stat().st_size if (OUT / "slide_339.png").exists() else 0))
    notes.append("ELAPSED={}".format(int(time.time() - t0)))
    write_notes()
    print("DONE")
    for n in notes:
        print(n)

if __name__ == "__main__":
    main()
