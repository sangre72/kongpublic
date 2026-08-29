#!/usr/bin/env python3
"""tier-1 menu lookup runtime, per kong-models/docs/RUNTIME.md 4-step flow.
usage: python3 lookup_runtime.py <AppName> <menu_type> <item_label>
prints resolved coord(x,y) on success, or a FAIL:<reason> line otherwise.
"""
import json
import os
import re
import subprocess
import sys
import time

KT = "/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol"
KONG_MODELS = "/Users/bumsuklee/git/kong-bot/kong-models"
CACHE_FILE = "/private/tmp/kong_lookup_frame_cache.json"


def run_kt(*args):
    return subprocess.run([KT, *args], capture_output=True, text=True, timeout=15).stdout


def get_pid(app_name):
    r = subprocess.run(["pgrep", "-x", app_name], capture_output=True, text=True)
    if not r.stdout.strip():
        r = subprocess.run(["pgrep", "-f", app_name], capture_output=True, text=True)
    lines = r.stdout.strip().splitlines()
    return lines[0] if lines else None


def a11y_compact(pid):
    return run_kt("see", "--a11y", "--pid", pid, "--compact")


def a11y_frame(pid):
    """cheap window-frame read(center+size) for smart-cache comparison, near-instant vs full visual-confirm."""
    out = run_kt("see", "--a11y", "--pid", pid)
    m = re.search(r"AXWindow\s+@\((\d+),(\d+)\)\s+\[(\d+)x(\d+)\]", out)
    return tuple(int(g) for g in m.groups()) if m else None


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)


def fast_vl_confirm(app_name):
    """fast VLM binary-check. history of fixes(a_2557/2558/2559, keep for future reference):
    a_2557: coordinate-embedded questions("화면 x=0~300,y=0~100 영역에...") cause a
    SYSTEMATIC(0/3) wrong-answer. dropped coordinate-language entirely.
    a_2558 hypothesized generic-menu-text(e.g."파일") would be more reliable than
    app-brand-name(e.g."Finder") — REVERSED by a_2559's 10x10 statistical test:
    text-presence("파일")=0/10 correct(100% wrong, confirmed not quote-mark-related,
    re-tested unquoted=still 0/5) vs brand-identity("Finder")=7/10 correct(70%), on
    IDENTICAL unchanged ground-truth verified before+after. generic Korean words seem to
    get a reflexive "no" from this VLM; a distinctive brand-name is a stronger visual anchor.
    ★use app-name(brand), NOT the generic menu-label-text. majority-vote(2-of-3) kept as
    safeguard since even 70% single-query accuracy needs it."""
    votes = []
    for _ in range(3):
        q = f"이 화면 맨 위에 {app_name}라는 글자가 보이나? 예/아니오로만 답해"
        out = run_kt("see", "--vl", q).strip()
        votes.append(out.startswith("예") or out.lower().startswith("yes"))
    return sum(votes) >= 2


def step0_foreground_check(app_name, menu_label):
    """menu_label kept as param for compatibility but no longer used for visual-confirm
    (a_2559 found brand-name questions more reliable, see fast_vl_confirm docstring)."""
    pid = get_pid(app_name)
    if pid is None:
        subprocess.run(["open", "-a", app_name])
        time.sleep(2)
        pid = get_pid(app_name)
        if pid is None:
            return None, "app-not-launchable"
    out = a11y_compact(pid)
    if len(out.splitlines()) < 5:
        subprocess.run(["open", "-a", app_name])
        time.sleep(2)
        out = a11y_compact(pid)
        if len(out.splitlines()) < 5:
            return None, "still-backgrounded-after-activate"

    # ★smart-cache(a_2555): compare current window-frame vs last-confirmed frame.
    # identical frame → skip expensive visual-confirm, reuse cached-clean status.
    # changed/missing → run fast-VLM visual-confirm.
    frame = a11y_frame(pid)
    cache = load_cache()
    cached = cache.get(app_name)
    if frame is not None and cached == list(frame):
        return pid, None  # cache-hit, skip visual-confirm entirely

    if frame is not None:
        if not fast_vl_confirm(app_name):
            return None, "visual-confirm-failed,app-occluded-or-not-truly-frontmost"
        cache[app_name] = list(frame)
        save_cache(cache)
    return pid, None


def load_stored(menu_type, app_name):
    fname = app_name.replace(" ", "")
    path = os.path.join(KONG_MODELS, menu_type, f"{fname}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def step1_drift_check(pid, stored, menu_label):
    live = a11y_compact(pid)
    live_labels = set(re.findall(r"AXMenuItem\s+(.+?)\t", live))
    if not live_labels:
        click_menu_bar_item(pid, menu_label)
        time.sleep(0.4)
        live = a11y_compact(pid)
        live_labels = set(re.findall(r"AXMenuItem\s+(.+?)\t", live))
    stored_labels = {it["label"] for it in stored["items"]}
    overlap = live_labels & stored_labels
    drift = len(overlap) < max(1, len(stored_labels) * 0.5)
    return drift, live


def click_menu_bar_item(pid, menu_label):
    out = a11y_compact(pid)
    for line in out.splitlines():
        if "AXMenuBarItem" in line and menu_label in line:
            m = re.search(r"(\d+)\s+(\d+)\s*$", line)
            if m:
                x, y = m.group(1), m.group(2)
                run_kt("input", "click", x, y, "--yes")
                return True
    return False


def step2_lookup_item_coord(live_a11y_text, item_label):
    for line in live_a11y_text.splitlines():
        if "AXMenuItem" in line and item_label in line:
            m = re.search(r"(\d+)\s+(\d+)\s*$", line)
            if m:
                return int(m.group(1)), int(m.group(2))
    return None


def step3_safety_gate(stored, item_label):
    for it in stored["items"]:
        if it["label"] == item_label:
            return it.get("safe_to_click", False), it
    return False, None


def main():
    if len(sys.argv) != 4:
        print("FAIL:usage: lookup_runtime.py <AppName> <menu_type> <item_label>")
        sys.exit(1)
    app_name, menu_type, item_label = sys.argv[1], sys.argv[2], sys.argv[3]

    t0 = time.time()

    stored = load_stored(menu_type, app_name)
    if stored is None:
        print(f"FAIL:no-stored-data-for:{app_name}:{menu_type}")
        sys.exit(1)
    menu_label = stored["menu_label"]  # loaded FIRST now, needed by step0's text-presence VLM-check

    pid, err = step0_foreground_check(app_name, menu_label)
    if err:
        print(f"FAIL:step0:{err}")
        sys.exit(1)

    safe, item = step3_safety_gate(stored, item_label)
    if not safe:
        print(f"FAIL:step3:not-safe-to-click-or-unknown-item:{item_label}")
        sys.exit(1)

    drift, live_text = step1_drift_check(pid, stored, menu_label)
    if drift:
        print("FAIL:step1:drift-detected,stale-data,relearn-needed")
        sys.exit(1)

    coord = step2_lookup_item_coord(live_text, item_label)
    if coord is None:
        print(f"FAIL:step2:item-not-found-live:{item_label}")
        sys.exit(1)

    elapsed = time.time() - t0
    print(f"OK:{coord[0]},{coord[1]}:elapsed={elapsed:.3f}s")


if __name__ == "__main__":
    main()
