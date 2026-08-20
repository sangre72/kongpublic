#!/usr/bin/env python3
"""a_365: dismiss 지금 안 함; windowed; fill well dark; slide_365.png."""
import json, subprocess, time
from pathlib import Path

try:
    from PIL import Image
    import numpy as np
except ImportError:
    Image = None
    np = None

K = "/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol"
OUT = Path("/Users/bumsuklee/git/kong-bot/kaymaps/keynote")
PROTO_A = Path("/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/protocol/a")
PROTO_AR = Path("/Users/bumsuklee/git/kong-bot/telegram_bot/orchestrator/protocol/ar")
notes = []
t0 = time.time()


def run(a, t=90):
    return subprocess.run(a, capture_output=True, text=True, timeout=t)


def click(x, y):
    run([K, "--yes", "input", "click", str(int(round(x))), str(int(round(y)))])


def key(n):
    run([K, "--yes", "input", "key", n])


def dump(pid):
    r = run([K, "--json", "see", "--a11y", "--pid", str(pid)], t=60)
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


def wins(els):
    out = []
    for e in els:
        if e.get("role") == "AXWindow":
            w, h = e.get("w") or 0, e.get("h") or 0
            out.append({
                "label": e.get("label"), "w": w, "h": h,
                "x": e.get("x"), "y": e.get("y"), "area": w * h,
            })
    out.sort(key=lambda z: z["area"], reverse=True)
    return out


def max_doc(ws):
    for w in ws:
        lab = w.get("label") or ""
        if any(k in lab for k in ("서체", "색상", "경고", "업데이트")):
            continue
        if (w["w"] or 0) >= 600:
            return w
    return ws[0] if ws else None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    run(["open", "-a", "Keynote"])
    time.sleep(0.9)
    pr = run(["pgrep", "-x", "Keynote"])
    if pr.returncode != 0:
        notes.append("NO_PID")
        return
    pid = pr.stdout.strip().split()[0]
    notes.append("PID " + pid)

    for i in range(5):
        els = dump(pid)
        labs = [
            (e.get("label"), e.get("cx"), e.get("cy"))
            for e in els
            if e.get("label") and any(
                k in e.get("label") for k in ("지금 안 함", "App Store", "업데이트", "나중에")
            )
        ]
        notes.append("scan{}={}".format(i, labs[:12]))
        btn = next(
            (e for e in els if e.get("label") and "지금 안 함" in e.get("label")),
            None,
        )
        if btn:
            click(btn["cx"], btn["cy"])
            time.sleep(0.65)
            notes.append("dismiss {},{}".format(btn.get("cx"), btn.get("cy")))
            continue
        if i == 0:
            notes.append("no_modal_initial")
        break

    els = dump(pid)
    mw = max_doc(wins(els))
    notes.append("win0={}".format(mw))
    if mw and (mw.get("w") or 0) >= 2000:
        click(419, 20)
        time.sleep(0.35)
        els = dump(pid)
        end = next((e for e in els if e.get("label") == "전체 화면 종료"), None)
        if end:
            click(end["cx"], end["cy"])
            time.sleep(1.2)
            notes.append("fs_exit")

    els = dump(pid)
    mw = max_doc(wins(els))
    notes.append("win1={}".format(mw))

    click(70, 160)
    time.sleep(0.35)
    click(780, 470)
    time.sleep(0.3)
    els = dump(pid)
    fmt = next(
        (
            e
            for e in els
            if e.get("label") == "포맷"
            and e.get("role") in ("AXRadioButton", "AXButton", "AXCheckBox")
            and (e.get("cx") or 0) < 1800
        ),
        None,
    )
    if fmt:
        click(fmt["cx"], fmt["cy"])
        time.sleep(0.4)
        notes.append("fmt")

    els = dump(pid)
    fl = [
        (e.get("role"), e.get("label"), e.get("cx"), e.get("cy"))
        for e in els
        if e.get("label")
        and any(k in e.get("label") for k in ("현재 채우기", "색상 채우기", "그라디언트", "배경", "채우기"))
    ]
    notes.append("fill_labels={}".format(fl[:20]))

    pop = next(
        (
            e
            for e in els
            if e.get("role") == "AXPopUpButton"
            and e.get("label")
            and "채우기" in e.get("label")
        ),
        None,
    )
    if pop and "색상 채우기" not in (pop.get("label") or ""):
        click(pop["cx"], pop["cy"])
        time.sleep(0.4)
        els = dump(pid)
        solid = next(
            (e for e in els if e.get("label") and "색상 채우기" in e.get("label")),
            None,
        )
        if solid:
            click(solid["cx"], solid["cy"])
            time.sleep(0.45)
            notes.append("set_색상_채우기")
        else:
            notes.append("no_solid_menu")
            key("escape")
            time.sleep(0.2)
    elif pop:
        notes.append("already_색상_채우기")

    els = dump(pid)
    well = next(
        (e for e in els if e.get("label") and "현재 채우기" in e.get("label")),
        None,
    )
    chips = [
        e
        for e in els
        if e.get("role") == "AXButton"
        and not (e.get("label") or "")
        and 1500 < (e.get("cx") or 0) < 1850
        and 400 < (e.get("cy") or 0) < 560
    ]
    notes.append("chips={}".format([(e.get("cx"), e.get("cy")) for e in chips[:8]]))
    if chips:
        chips.sort(key=lambda e: abs((e.get("cy") or 0) - 444))
        c = chips[0]
        click(c["cx"], c["cy"])
        time.sleep(0.55)
        notes.append("chip_click {},{}".format(c.get("cx"), c.get("cy")))
        bx, by = c.get("cx") or 1636, c.get("cy") or 444
    elif well:
        click((well.get("cx") or 1545) + 90, well.get("cy") or 444)
        time.sleep(0.55)
        notes.append("well_right")
        bx, by = (well.get("cx") or 1545) + 90, well.get("cy") or 444
    else:
        bx, by = 1636, 444
        notes.append("NO_well")

    els = dump(pid)
    dark = next(
        (
            e
            for e in els
            if e.get("label")
            and any(k in e.get("label") for k in ("검정", "Black", "black", "거의 검정", "차콜"))
        ),
        None,
    )
    if dark:
        click(dark["cx"], dark["cy"])
        time.sleep(0.4)
        notes.append("dark " + (dark.get("label") or ""))
    else:
        for dx, dy in [(0, 100), (40, 140), (-30, 120), (70, 180), (-50, 160), (20, 220)]:
            click(bx + dx, by + dy)
            time.sleep(0.15)
        for x, y in [(1560, 560), (1520, 600), (1600, 640), (1580, 700)]:
            click(x, y)
            time.sleep(0.15)
        notes.append("dark_spots")
    key("escape")
    time.sleep(0.25)

    els = dump(pid)
    btn = next(
        (e for e in els if e.get("label") and "지금 안 함" in e.get("label")),
        None,
    )
    if btn:
        click(btn["cx"], btn["cy"])
        time.sleep(0.5)
        notes.append("redismiss")

    els = dump(pid)
    mw = max_doc(wins(els))
    notes.append("win_final={}".format(mw))
    notes.append(
        "wins_all={}".format(
            [(w.get("label"), w.get("w"), w.get("h")) for w in wins(els)[:6]]
        )
    )
    modal = [
        e.get("label")
        for e in els
        if e.get("label")
        and any(k in e.get("label") for k in ("지금 안 함", "App Store로", "업데이트"))
    ]
    notes.append("modal_left={}".format(modal[:10]))

    shot = OUT / "slide_365.png"
    run(["open", "-a", "Keynote"])
    time.sleep(0.3)
    run(["screencapture", "-x", str(shot)])
    if shot.exists() and Image is not None:
        im = Image.open(shot).convert("RGB")
        a = np.array(im)
        h, w = a.shape[:2]
        patch = a[h // 2 - 100 : h // 2 + 100, w // 2 - 150 : w // 2 + 150]
        mean = tuple(float(x) for x in np.round(patch.mean(axis=(0, 1)), 1))
        notes.append("canvas_mean_rgb={}".format(mean))
        run(["cp", str(shot), str(PROTO_A / "slide_365.png")])
        run(["cp", str(shot), str(PROTO_AR / "slide_365.png")])
        notes.append("shot={}".format(shot.stat().st_size))
    elif shot.exists():
        run(["cp", str(shot), str(PROTO_A / "slide_365.png")])
        run(["cp", str(shot), str(PROTO_AR / "slide_365.png")])
        notes.append("shot={}".format(shot.stat().st_size))
    notes.append("ELAPSED={}".format(int(time.time() - t0)))
    (OUT / "a365_notes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
    print("DONE")
    for n in notes:
        print(n)
