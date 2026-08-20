#!/usr/bin/env python3
"""a_359: keep selected 사각형; SE handle drag×4 to ~1800,1100; insert Google text. NO delete."""
import json, subprocess, time
from pathlib import Path

K = "/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol"
OUT = Path("/Users/bumsuklee/git/kong-bot/kaymaps/keynote")
PROTO_A = Path("/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/protocol/a")
PROTO_AR = Path("/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/protocol/ar")
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


def key(n):
    run([K, "--yes", "input", "key", n])


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


def menu_items(els):
    items = []
    for e in els:
        lab = (e.get("label") or "").strip()
        role = e.get("role") or ""
        if not lab:
            continue
        if role in ("AXMenuItem", "AXMenuBarItem", "AXButton", "AXStaticText", "AXImage"):
            items.append((lab, e.get("cx"), e.get("cy"), role))
    return items


def write_notes():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "a359_notes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")


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
        run(["screencapture", "-x", str(OUT / "slide_359.png")])
        write_notes(); return

    for _ in range(2):
        els = dump(pid)
        mw = max_doc(windows(els))
        notes.append("MAX={}".format(mw))
        if mw and (mw["w"] or 0) >= 2000 and (mw["h"] or 0) >= 1200:
            notes.append("FS_ok")
            break
        click(419, 20); time.sleep(0.4)
        els = dump(pid)
        start = next((e for e in els if e.get("label") == "전체 화면 시작"), None)
        if start:
            click(start["cx"], start["cy"]); time.sleep(1.4)
            notes.append("fs_start")
        elif mw:
            click((mw.get("x") or 0) + 54, (mw.get("y") or 0) + 20); time.sleep(1.2)

    els = dump(pid)
    mw = max_doc(windows(els)) or {}
    wx, wy = mw.get("x") or 0, mw.get("y") or 0
    ww, wh = mw.get("w") or 2056, mw.get("h") or 1290
    # canvas center estimate for postage-stamp black box
    box_cx = wx + ww * 0.48
    box_cy = wy + wh * 0.48

    # ensure object list visible
    click(419, 20); time.sleep(0.35)
    els = dump(pid)
    ol = next((e for e in els if e.get("label") and "대상체 목록" in e.get("label")), None)
    if ol:
        click(ol["cx"], ol["cy"]); time.sleep(0.45)
        notes.append("list_toggle")

    els = dump(pid)
    objs = list_left(els)
    notes.append("objs_before={}".format([(e.get("label"), e.get("cy")) for e in objs]))
    rects = [e for e in objs if "사각" in (e.get("label") or "")]
    # HARD: do NOT delete anything
    if not rects:
        notes.append("NO_RECT_list")
        # try click canvas center to keep/select shape
        click(box_cx, box_cy); time.sleep(0.4)
    else:
        click(rects[0]["cx"], rects[0]["cy"]); time.sleep(0.5)
        notes.append("selected_rect cy={}".format(rects[0].get("cy")))

    # Drag SE handle knob (bottom-right of 8 dots) → ~1800,1100 ×4
    half = 48
    for i in range(4):
        se_x = box_cx + half
        se_y = box_cy + half
        notes.append("drag_SE_{} from {},{} -> 1800,1100".format(i + 1, int(se_x), int(se_y)))
        drag(se_x, se_y, 1800, 1100)
        time.sleep(0.55)
        # reselect 사각형 only (never delete)
        els = dump(pid)
        rects = [e for e in list_left(els) if "사각" in (e.get("label") or "")]
        if rects:
            click(rects[0]["cx"], rects[0]["cy"]); time.sleep(0.3)
            notes.append("reselect_rect after drag {}".format(i + 1))
        # grow estimate: SE moved toward 1800,1100
        box_cx = min(box_cx + 120, 1500)
        box_cy = min(box_cy + 90, 900)
        half = 60 + i * 40

    notes.append("objs_after_drag={}".format(
        [(e.get("label"), e.get("cy")) for e in list_left(dump(pid))]))

    # Insert text box via 삽입 dump → 텍스트 상자, type Google only
    els = dump(pid)
    ins = next((e for e in els if e.get("role") == "AXMenuBarItem" and e.get("label") == "삽입"), None)
    if ins:
        click(ins["cx"], ins["cy"]); time.sleep(0.45)
        els = dump(pid)
        items = menu_items(els)
        notes.append("after_삽입={}".format(items[:40]))
        tb = next((e for e in els if e.get("label") and "텍스트 상자" in e.get("label")), None)
        if not tb:
            # partial match
            tb = next((e for e in els if (e.get("label") or "") in ("텍스트", "텍스트 상자", "텍스트 상자 삽입")), None)
        if tb:
            click(tb["cx"], tb["cy"]); time.sleep(0.5)
            notes.append("click_textbox {},{}".format(tb.get("cx"), tb.get("cy")))
            # place on canvas
            click(900, 400); time.sleep(0.4)
            text("Google"); time.sleep(0.4)
            notes.append("typed_Google")
        else:
            notes.append("NO_TEXTBOX_MENU")
            # toolbar fallback: 텍스트 button
            tb2 = next((e for e in els if e.get("role") == "AXButton" and e.get("label") == "텍스트"), None)
            if tb2:
                click(tb2["cx"], tb2["cy"]); time.sleep(0.45)
                click(900, 400); time.sleep(0.35)
                text("Google"); time.sleep(0.35)
                notes.append("typed_Google_toolbar")
            else:
                # escape menu then toolbar from fresh dump
                key("escape"); time.sleep(0.2)
                els = dump(pid)
                tb2 = next((e for e in els if e.get("role") == "AXButton" and e.get("label") == "텍스트"), None)
                if tb2:
                    click(tb2["cx"], tb2["cy"]); time.sleep(0.45)
                    click(900, 400); time.sleep(0.35)
                    text("Google"); time.sleep(0.35)
                    notes.append("typed_Google_toolbar2")
                else:
                    notes.append("FAIL_google_insert")
    else:
        notes.append("NO_MENUBAR_삽입")

    # deselect typing with esc once
    key("escape"); time.sleep(0.2)

    els = dump(pid)
    notes.append("objs_final={}".format([(e.get("label"), e.get("cy")) for e in list_left(els)]))
    notes.append("menus_final={}".format(menus(els)))
    notes.append("wins_final={}".format(windows(els)))

    shot_path = OUT / "slide_359.png"
    run(["open", "-a", "Keynote"]); time.sleep(0.3)
    run(["screencapture", "-x", str(shot_path)])
    # also copy to protocol/a
    if shot_path.exists():
        for dest in (PROTO_A / "slide_359.png", PROTO_AR / "slide_359.png"):
            run(["cp", str(shot_path), str(dest)])
        notes.append("shot={}".format(shot_path.stat().st_size))
    else:
        notes.append("shot=0")
    notes.append("ELAPSED={}".format(int(time.time() - t0)))
    write_notes()
    print("DONE")
    for n in notes:
        print(n)


if __name__ == "__main__":
    main()
