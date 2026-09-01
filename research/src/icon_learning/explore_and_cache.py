#!/usr/bin/env python3
"""
Prototype: trial-and-observe icon-function learning ("exploration" mode from u_3219).

Strategy 1(missing piece identified by user): click an unknown/unlabeled UI element,
diff the a11y tree before/after, infer the element's FUNCTION from what changed, and
cache (icon-image-hash, app-context) -> inferred-function for future zero-cost reuse.

This complements the two existing strategies already in kong-bot's toolkit:
  2) visual-recognition-by-prior-experience -> CLIP-embedding icon cache (planned, not yet built)
  3) manual/documentation lookup -> kaymaps/RECIPE_*.txt

Usage:
  python3 explore_and_cache.py probe --pid <PID> --x <X> --y <Y> [--label "optional icon label"]
  python3 explore_and_cache.py list

Cache file: research/src/icon_learning/icon_function_cache.json
"""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

KT = "/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol"
CACHE_PATH = Path(__file__).parent / "icon_function_cache.json"


def run_kt(*args):
    result = subprocess.run([KT, *args], capture_output=True, text=True, timeout=10)
    return result.stdout


def get_a11y_snapshot(pid):
    out = run_kt("see", "--a11y", "--pid", str(pid), "--compact")
    return out


def diff_snapshots(before, after):
    before_lines = set(before.strip().splitlines())
    after_lines = set(after.strip().splitlines())
    added = after_lines - before_lines
    removed = before_lines - after_lines
    return sorted(added), sorted(removed)


def load_cache():
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text())
    return {}


def save_cache(cache):
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2))


def infer_function_from_diff(added, removed):
    """Heuristic first-pass inference from a11y diff — refine with real usage."""
    signals = []
    joined_added = " ".join(added).lower()
    joined_removed = " ".join(removed).lower()

    if "table" in joined_added or "grid" in joined_added or "row" in joined_added:
        signals.append("inserts-table")
    if "image" in joined_added or "picture" in joined_added:
        signals.append("inserts-image")
    if "dialog" in joined_added or "sheet" in joined_added or "popover" in joined_added:
        signals.append("opens-dialog")
    if "menu" in joined_added:
        signals.append("opens-menu")
    if "textfield" in joined_added.replace(" ", "") or "editable" in joined_added:
        signals.append("opens-input-form(has-editable-fields)")
    if "checkbox" in joined_added:
        signals.append("opens-form-with-toggle-options")
    if "popupbutton" in joined_added.replace(" ", ""):
        signals.append("opens-form-with-dropdown-selector")
    if removed and not added:
        signals.append("removes-element(possible-delete/close-action)")
    if not signals:
        signals.append(f"unknown(added={len(added)}_removed={len(removed)}_elements)")
    return signals


def probe(pid, x, y, label=None):
    cache = load_cache()
    key = f"pid{pid}_{x}_{y}" if not label else label

    print(f"[1/4] snapshot BEFORE click at ({x},{y})...")
    before = get_a11y_snapshot(pid)

    print(f"[2/4] clicking ({x},{y})...")
    run_kt("input", "click", str(x), str(y), "--yes")
    time.sleep(0.5)

    print("[3/4] snapshot AFTER click...")
    after = get_a11y_snapshot(pid)

    added, removed = diff_snapshots(before, after)
    inferred = infer_function_from_diff(added, removed)

    print(f"[4/4] diff: +{len(added)} elements, -{len(removed)} elements")
    print(f"inferred function(s): {inferred}")

    cache[key] = {
        "coord": [x, y],
        "pid": pid,
        "inferred_function": inferred,
        "diff_added_sample": added[:5],
        "diff_removed_sample": removed[:5],
        "verified": False,
    }
    save_cache(cache)
    print(f"cached under key='{key}' (verified=False, needs human/VLM confirmation before trusted)")
    return inferred


def list_cache():
    cache = load_cache()
    if not cache:
        print("cache empty")
        return
    for key, entry in cache.items():
        v = "VERIFIED" if entry.get("verified") else "unverified"
        print(f"{key}: {entry['inferred_function']} [{v}]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_probe = sub.add_parser("probe")
    p_probe.add_argument("--pid", type=int, required=True)
    p_probe.add_argument("--x", type=int, required=True)
    p_probe.add_argument("--y", type=int, required=True)
    p_probe.add_argument("--label", type=str, default=None)

    sub.add_parser("list")

    args = parser.parse_args()
    if args.cmd == "probe":
        probe(args.pid, args.x, args.y, args.label)
    elif args.cmd == "list":
        list_cache()
