#!/usr/bin/env python3
import json, subprocess, time
from pathlib import Path

K = "/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol"
OUT = Path("/Users/bumsuklee/git/kong-bot/kaymaps/keynote")
notes = []
t0 = time.time()

TARGET_LABELS = {
    "텍스트",
    "사각형",
    "I'm Feeling Lucky",
    "Search Google or type a URL",
}

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
    return ("삽입" in s or "슬라이드" in s) and ("포맷" in s or "편집" in s) and "이동" not in s

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
    (OUT / "a336_notes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")

def ensure_keynote(pid_holder):
    for i in range(4):
        run(["open", "-a", "Keynote"]); time.sleep(0.9)
        pr = run(["pgrep", "-x", "Keynote"])
        if pr.returncode != 0:
            continue
        pid = pr.stdout.strip().split()[0]
        pid_holder[0] = pid
        els = dump(pid)
        labs = menus(els)
        notes.append("menus_try{}={}".format(i, labs))
        if is_keynote(labs):
            return els
    return []

def list_targets(els):
    out = []
    for e in els:
        lab = (e.get("label") or "").strip()
        if lab not in TARGET_LABELS:
            continue
        if e.get("role") not in ("AXTextField", "AXStaticText", "AXCell", "AXRow"):
            # still allow if exact label match on left list
            if (e.get("cx") or 9999) > 400:
                continue
        if (e.get("cx") or 9999) > 450:
            continue
        out.append(e)
    # de-dupe
    seen = set()
    uniq = []
    for e in out:
        k = (e.get("label"), round(e.get("cy") or 0, 0))
        if k in seen:
            continue
        seen.add(k)
        uniq.append(e)
    return uniq

def unlock_one(pid, e):
    lab = e.get("label")
    cx, cy = e.get("cx"), e.get("cy")
    notes.append("unlock_select {} @{},{}".format(lab, cx, cy))
    click(cx, cy); time.sleep(0.45)
    # 정렬 menu
    click(376, 20); time.sleep(0.5)
    els = dump(pid)
    item = next((x for x in els if x.get("role") == "AXMenuItem" and (x.get("label") or "") == "잠금 해제"), None)
    if item:
        notes.append("click 잠금 해제 {},{}".format(item.get("cx"), item.get("cy")))
        click(item["cx"], item["cy"]); time.sleep(0.45)
        return True
    # map fallback 452,306 if menu open
    notes.append("no_unlock_label try 452,306")
    click(452, 306); time.sleep(0.4)
    key("esc"); time.sleep(0.2)
    # padlock right of name ~ +80x
    click((cx or 200) + 80, cy); time.sleep(0.35)
    return False

def main():
    pid_h = [None]
    els = ensure_keynote(pid_h)
    if not els or not pid_h[0]:
        notes.append("FAIL_no_keynote")
        run(["screencapture", "-x", str(OUT / "slide_336.png")])
        write_notes(); print("FAIL app"); return
    pid = pid_h[0]
    notes.append("PID {}".format(pid))

    # maximize if needed — NO cmd-t
    for _ in range(2):
        els = dump(pid)
        wins = windows(els)
        notes.append("WINDOWS={}".format(wins))
        mw = max_doc(wins)
        notes.append("MAX={}".format(mw))
        if mw and (mw["w"] or 0) >= 2000 and (mw["h"] or 0) >= 1200:
            notes.append("FS_ok")
            break
        if not is_keynote(menus(els)):
            els = ensure_keynote(pid_h)
            pid = pid_h[0]
            continue
        click(419, 20); time.sleep(0.55)
        els = dump(pid)
        start = next((e for e in els if e.get("label") == "전체 화면 시작"), None)
        if start:
            notes.append("fs_start")
            click(start["cx"], start["cy"]); time.sleep(1.4)
        elif mw:
            gx = (mw.get("x") or 0) + 54
            gy = (mw.get("y") or 0) + 20
            notes.append("green_title {},{}".format(gx, gy))
            click(gx, gy); time.sleep(1.4)
        key("esc"); time.sleep(0.2)

    els = dump(pid)
    if not is_keynote(menus(els)):
        notes.append("refront_before_unlock")
        els = ensure_keynote(pid_h)
        pid = pid_h[0]

    # unlock passes
    for pass_i in range(2):
        els = dump(pid)
        targets = list_targets(els)
        notes.append("TARGETS_p{}={}".format(pass_i, [(e.get("label"), e.get("cx"), e.get("cy")) for e in targets]))
        for e in targets:
            unlock_one(pid, e)
            key("esc"); time.sleep(0.15)

    # delete passes
    for del_i in range(2):
        click(1000, 700); time.sleep(0.2)
        chord("cmd", "a"); time.sleep(0.25)
        key("delete"); time.sleep(0.55)
        els = dump(pid)
        left = list_targets(els)
        notes.append("LEFT_p{}={}".format(del_i, [(e.get("label"), e.get("cx"), e.get("cy")) for e in left]))
        if not left:
            break
        # recover unlock again
        for e in left:
            unlock_one(pid, e)

    els = dump(pid)
    left = list_targets(els)
    notes.append("LEFT_FINAL={}".format([(e.get("label"), e.get("cx"), e.get("cy")) for e in left]))
    empty = len(left) == 0
    notes.append("leftover_empty={}".format(empty))

    # create even if partial empty? HARD says if leftover recover then CONTINUE - create after best effort
    # but a_335 said don't create on junk. a_336 says recover once more then CONTINUE - so create after 2nd pass even if partial? 
    # "If leftover: recover unlock+delete once more then CONTINUE" implies continue to create.
    # Prefer create after best effort.

    if not is_keynote(menus(dump(pid))):
        ensure_keynote(pid_h)
        pid = pid_h[0]

    notes.append("CREATE start empty={}".format(empty))
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

    # ensure keynote front for shot
    if not is_keynote(menus(dump(pid))):
        ensure_keynote(pid_h)
        time.sleep(0.5)
    run(["screencapture", "-x", str(OUT / "slide_336.png")])
    els = dump(pid)
    notes.append("menus_final={}".format(menus(els)))
    notes.append("shot_keynote={}".format(is_keynote(menus(els))))
    notes.append("WINDOWS_final={}".format(windows(els)))
    notes.append("shot={}".format((OUT / "slide_336.png").stat().st_size if (OUT / "slide_336.png").exists() else 0))
    notes.append("ELAPSED={}".format(int(time.time() - t0)))
    write_notes()
    print("DONE")
    for n in notes:
        print(n)

if __name__ == "__main__":
    main()
