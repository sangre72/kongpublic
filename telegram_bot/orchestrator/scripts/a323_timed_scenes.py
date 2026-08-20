#!/usr/bin/env python3
"""a_323 one-trial timed scenes: fs_ensure → select Google → text_color gate + shots."""
import json
import os
import subprocess
import time
from pathlib import Path

K = os.environ.get("K", "./kongtrol/target/release/kongtrol")
PID = os.environ.get("PID") or subprocess.check_output(["pgrep", "-x", "Keynote"], text=True).split()[0]
ROOT = Path("/Users/bumsuklee/git/kong-bot")
OUT = ROOT / "kaymaps/keynote"
states = []
t0 = time.time()


def run(args, timeout=60):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


def click(x, y):
    run([K, "--yes", "input", "click", str(int(x)), str(int(y))])


def key(name):
    run([K, "--yes", "input", "key", name])


def dump():
    r = run([K, "--json", "see", "--a11y", "--pid", str(PID)], timeout=60)
    if r.returncode != 0:
        print("dump_fail", (r.stderr or "")[:200], flush=True)
        return []
    j = json.loads(r.stdout)
    data = j.get("data", j)
    if isinstance(data, list):
        return data
    for v in data.values():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            return v
    return []


def shot(name):
    p = OUT / name
    run(["screencapture", "-x", str(p)])
    print("shot", p.name, p.stat().st_size if p.exists() else 0, flush=True)
    return p


def win_info(elems):
    for e in elems:
        if e.get("role") == "AXWindow":
            return e
    return None


def state_line(tag, elems, extra=""):
    w = win_info(elems)
    if w:
        ww, hh = w.get("w") or 0, w.get("h") or 0
        fs = "Y" if ww >= 2000 and hh >= 1200 else "N(%sx%s)" % (ww, hh)
        wxy = "(%s,%s,%sx%s)" % (w.get("x"), w.get("y"), ww, hh)
    else:
        fs, wxy = "?", "?"
    g = None
    for e in elems:
        lab = e.get("label") or ""
        if "Google" in lab:
            g = e
            if (e.get("cx") or 9999) < 500:
                break
    gtxt = "?"
    if g:
        gtxt = "cx=%s cy=%s lab=%s" % (g.get("cx"), g.get("cy"), g.get("label"))
    insp, well = [], []
    for e in elems:
        lab = e.get("label") or ""
        role = e.get("role") or ""
        cx = e.get("cx") or 0
        if lab in ("정렬", "텍스트", "스타일", "포맷") and role in (
            "AXRadioButton",
            "AXButton",
            "AXCheckBox",
            "AXMenuBarItem",
        ):
            insp.append("%s@%s" % (lab, int(cx)))
        if "색상" in lab:
            well.append("%s@%s,%s" % (lab, e.get("cx"), e.get("cy")))
    line = "STATE %s: FS=%s win=%s google=%s insp=%s well=%s %s" % (
        tag,
        fs,
        wxy,
        gtxt,
        insp[:8],
        well[:8],
        extra,
    )
    print(line, flush=True)
    states.append(line)
    return fs


def main():
    print("T0", int(t0), "PID", PID, flush=True)
    key("esc")
    time.sleep(0.25)
    elems = dump()
    w = win_info(elems)
    need = not w or (w.get("w") or 0) < 2000 or (w.get("h") or 0) < 1200
    print("need_fs", need, None if not w else (w.get("w"), w.get("h")), flush=True)
    if need:
        click(419, 20)
        time.sleep(0.55)
        elems2 = dump()
        start = None
        end = False
        for e in elems2:
            lab = e.get("label") or ""
            if lab == "전체 화면 시작":
                start = e
            if lab == "전체 화면 종료":
                end = True
        if start:
            print("FS_START", start.get("cx"), start.get("cy"), flush=True)
            click(start["cx"], start["cy"])
            time.sleep(1.3)
        elif not end:
            print("FS_GREEN_FALLBACK", flush=True)
            click(54, 193)
            time.sleep(1.3)
    else:
        time.sleep(0.3)

    elems = dump()
    state_line("scene1_fs", elems)
    shot("scene_323_1.png")

    elems = dump()
    cands = []
    for e in elems:
        lab = e.get("label") or ""
        if "Google" in lab:
            cands.append(e)
            print("G", e.get("role"), lab, e.get("cx"), e.get("cy"), flush=True)
    best = None
    for e in cands:
        if (e.get("cx") or 9999) < 400:
            best = e
            break
    if not best and cands:
        best = min(cands, key=lambda e: e.get("cx") or 9999)
    if best:
        print("click_Google", best.get("cx"), best.get("cy"), flush=True)
        click(best["cx"], best["cy"])
        time.sleep(0.7)
    else:
        print("NO_Google_fallback_247_129", flush=True)
        click(247, 129)
        time.sleep(0.7)

    elems = dump()
    state_line("scene2_select", elems)
    shot("scene_323_2.png")

    click(1937, 93)
    time.sleep(0.45)
    click(1922, 107)
    time.sleep(0.55)
    elems = dump()
    DW = 2056.0
    text_wells, any_color = [], []
    for e in elems:
        lab = e.get("label") or ""
        cx = e.get("cx") or 0
        x = e.get("x") if e.get("x") is not None else cx
        if "색상" in lab:
            any_color.append((lab, cx, e.get("cy"), x))
        if "텍스트 색상" in lab:
            text_wells.append(e)

    color_note = "STOP: no on-screen 텍스트 색상 well"
    used = None
    for e in text_wells:
        cx = e.get("cx") or 0
        x = e.get("x") if e.get("x") is not None else cx
        if cx < DW and x < DW:
            used = e
            break
    if used:
        print("text_well", used.get("label"), used.get("cx"), used.get("cy"), flush=True)
        click(used["cx"], used["cy"])
        time.sleep(0.6)
        color_note = "well_clicked %s@%s,%s (white not dump-confirmed)" % (
            used.get("label"),
            used.get("cx"),
            used.get("cy"),
        )
    else:
        print("no_text_well other", any_color[:10], flush=True)
        color_note = "STOP: 텍스트 색상 well absent/off-screen; other=%s" % (any_color[:6],)

    elems = dump()
    state_line("scene3_color", elems, extra=color_note)
    shot("scene_323_3.png")
    shot("slide_323.png")
    elapsed = int(time.time() - t0)
    (OUT / "scene_323_states.txt").write_text(
        "\n".join(states + [color_note, "ELAPSED_SEC=%s" % elapsed]) + "\n",
        encoding="utf-8",
    )
    print("COLOR", color_note, flush=True)
    print("ELAPSED_SEC", elapsed, flush=True)
    print("DONE_SCENES", flush=True)


if __name__ == "__main__":
    main()
