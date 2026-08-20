#!/usr/bin/env python3
import json, subprocess, time, re
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

def windows(els):
    wins = []
    for e in els:
        if e.get("role") == "AXWindow":
            w, h = e.get("w") or 0, e.get("h") or 0
            wins.append({"label": e.get("label"), "x": e.get("x"), "y": e.get("y"), "w": w, "h": h, "area": w * h})
    wins.sort(key=lambda z: z["area"], reverse=True)
    return wins

def menus(els):
    return [e.get("label") for e in els if e.get("role") == "AXMenuBarItem" and e.get("label")]

def is_keynote(labs):
    s = set(labs or [])
    return ("삽입" in s or "슬라이드" in s) and ("포맷" in s or "편집" in s)

def max_doc(wins):
    for w in wins:
        if (w["w"] or 0) >= 800 and (w["h"] or 0) >= 500:
            return w
    return wins[0] if wins else None

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
    (OUT / "a335_notes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")

def object_candidates(els):
    """Heuristic object list / slide objects with useful labels."""
    ban_roles = {"AXMenuBarItem", "AXMenuItem", "AXMenu", "AXMenuBar", "AXButton", "AXRadioButton", "AXCheckBox", "AXMenuButton", "AXPopUpButton", "AXStaticText", "AXScrollBar", "AXToolbar", "AXImage"}
    # Prefer left object list cells (cx small)
    cands = []
    junk_re = re.compile(r"Google|텍스트|사각형|Feeling|Search|Goo|URL|http|직사|모서리|검색", re.I)
    for e in els:
        lab = (e.get("label") or "").strip()
        role = e.get("role") or ""
        cx = e.get("cx") or 0
        cy = e.get("cy") or 0
        if not lab:
            continue
        if role == "AXWindow":
            continue
        if lab in ("Apple", "Keynote", "파일", "편집", "삽입", "슬라이드", "포맷", "정렬", "보기", "재생", "윈도우", "도움말", "서체", "잠금", "잠금 해제"):
            continue
        # object list often left side
        if cx < 450 and cy > 100 and cy < 1200 and junk_re.search(lab):
            cands.append(e)
        elif cx < 450 and cy > 100 and cy < 1200 and role in ("AXTextField", "AXCell", "AXRow", "AXLayoutItem", "AXGroup"):
            if len(lab) < 40:
                cands.append(e)
    # de-dupe by label+cy
    seen = set()
    out = []
    for e in cands:
        k = ((e.get("label") or ""), round(e.get("cy") or 0, 0))
        if k in seen:
            continue
        seen.add(k)
        out.append(e)
    return out

def main():
    run(["open", "-a", "Keynote"]); time.sleep(1.0)
    pr = run(["pgrep", "-x", "Keynote"])
    if pr.returncode != 0:
        notes.append("NO_PID"); write_notes(); return
    pid = pr.stdout.strip().split()[0]
    notes.append("PID {}".format(pid))

    els = dump(pid)
    notes.append("menus0={}".format(menus(els)))
    if not is_keynote(menus(els)):
        run(["open", "-a", "Keynote"]); time.sleep(1.0)
        els = dump(pid)
        notes.append("menus1={}".format(menus(els)))
        if not is_keynote(menus(els)):
            notes.append("FAIL_not_keynote")
            run(["screencapture", "-x", str(OUT / "slide_335.png")])
            write_notes(); return

    wins = windows(els)
    notes.append("WINDOWS={}".format(wins))
    mw = max_doc(wins)
    notes.append("MAX={}".format(mw))
    fs = bool(mw and (mw["w"] or 0) >= 2000 and (mw["h"] or 0) >= 1200)
    notes.append("FS0={}".format(fs))
    if not fs and mw and (mw["w"] or 0) < 2050:
        click(419, 20); time.sleep(0.55)
        els = dump(pid)
        start = next((e for e in els if e.get("label") == "전체 화면 시작"), None)
        if start:
            notes.append("fs_start")
            click(start["cx"], start["cy"]); time.sleep(1.4)
        els = dump(pid)
        wins = windows(els)
        mw = max_doc(wins)
        fs = bool(mw and (mw["w"] or 0) >= 2000 and (mw["h"] or 0) >= 1200)
        notes.append("FS1={} MAX={}".format(fs, mw))
    else:
        notes.append("skip_FS_clicks already large or ok")

    # close 서체 overlay
    for _ in range(3):
        els = dump(pid)
        font_win = next((w for w in windows(els) if "서체" in (w.get("label") or "")), None)
        if not font_win:
            notes.append("no_font_overlay")
            break
        notes.append("font_overlay={}".format(font_win))
        key("esc"); time.sleep(0.3)
        # cmd+t toggle fonts
        chord("cmd", "t"); time.sleep(0.5)
    els = dump(pid)
    notes.append("WINDOWS_after_font={}".format(windows(els)))

    # object list before
    objs = object_candidates(els)
    notes.append("OBJ_BEFORE={}".format([(e.get("label"), e.get("cx"), e.get("cy"), e.get("role")) for e in objs]))

    # unlock each candidate
    for e in objs[:20]:
        lab = e.get("label") or ""
        cx, cy = e.get("cx"), e.get("cy")
        notes.append("select {}".format(lab))
        click(cx, cy); time.sleep(0.4)
        # try inspector 잠금 해제
        click(1937, 93); time.sleep(0.25)
        click(2013, 107); time.sleep(0.25)
        # 잠금 해제 button prod 2041,517
        click(2041, 517); time.sleep(0.35)
        # also menu 정렬 > 잠금 해제 path via menubar
        # skip if would open 종료
    # bulk unlock via menu: 정렬 menubar item then 잠금 해제 if shown after select all
    click(1000, 700); time.sleep(0.2)
    chord("cmd", "a"); time.sleep(0.25)
    click(376, 20); time.sleep(0.45)  # 정렬 menu
    els = dump(pid)
    unlock = next((e for e in els if e.get("label") == "잠금 해제" and e.get("role") == "AXMenuItem"), None)
    if unlock:
        notes.append("menu_unlock {},{}".format(unlock.get("cx"), unlock.get("cy")))
        click(unlock["cx"], unlock["cy"]); time.sleep(0.5)
    else:
        notes.append("no_menu_unlock_item")
        key("esc"); time.sleep(0.2)

    # delete all
    click(1000, 700); time.sleep(0.2)
    chord("cmd", "a"); time.sleep(0.2)
    key("delete"); time.sleep(0.6)
    chord("cmd", "a"); time.sleep(0.2)
    key("delete"); time.sleep(0.5)

    els = dump(pid)
    objs_after = object_candidates(els)
    notes.append("OBJ_AFTER_DELETE={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in objs_after]))

    # strict empty check: no junk labels left
    junk_left = [e for e in objs_after if re.search(r"Feeling|Search|Goo|URL|http|텍스트|사각형|직사", (e.get("label") or ""), re.I)]
    notes.append("JUNK_LEFT={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in junk_left]))
    if junk_left:
        notes.append("FAIL_leftover_not_empty")
        run(["screencapture", "-x", str(OUT / "slide_335.png")])
        notes.append("shot={}".format((OUT / "slide_335.png").stat().st_size if (OUT / "slide_335.png").exists() else 0))
        notes.append("ELAPSED={}".format(int(time.time() - t0)))
        write_notes()
        print("FAIL_LEFTOVER")
        for n in notes:
            print(n)
        return

    notes.append("EMPTY_OK create")
    # create bg+google
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

    run(["screencapture", "-x", str(OUT / "slide_335.png")])
    els = dump(pid)
    notes.append("menus_final={}".format(menus(els)))
    notes.append("OBJ_FINAL={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in object_candidates(els)]))
    notes.append("shot={}".format((OUT / "slide_335.png").stat().st_size if (OUT / "slide_335.png").exists() else 0))
    notes.append("ELAPSED={}".format(int(time.time() - t0)))
    write_notes()
    print("DONE")
    for n in notes:
        print(n)

if __name__ == "__main__":
    main()
