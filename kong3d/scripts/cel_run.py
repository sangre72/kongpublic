#!/usr/bin/env python3
"""Robust cel painter: reads cel_plan.json (canvas coords), maps to screen coords
via a freshly-calibrated linear transform, drives kongtrol directly (no shell pipe).
Fills first (flat zones), then long contour outlines on top.

Calibrated 2026-09-09 for Chrome window bounds {0,39,1500,954}:
  sx = 144.7 + cx*1.117 ; sy = 126.1 + cy*1.119
Toolbar: 색상입력(72,172) 색상적용(72,204) brushBtn(72,~366) sizeSlider y~310
"""
import json, subprocess, time, sys

KT = "/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol"
PLAN = "/Users/bumsuklee/git/kong-bot/kong3d/cel_plan.json"

# toolbar coords at current window (re-measured from a11y)
HEX_FIELD = (72, 172)
SET_COLOR = (72, 204)
BRUSH_BTN = (72, 365)
CLEAR_BTN = (72, 483)
SLIDER_Y = 309
SLIDER_X0 = 46          # slider left edge (min=2)
SLIDER_XSPAN = 52       # slider width in px

# canvas->screen linear map
def SX(cx): return int(round(144.7 + cx * 1.117))
def SY(cy): return int(round(126.1 + cy * 1.119))

def kt(*args):
    subprocess.run([KT, *[str(a) for a in args]],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def click(x, y): kt("input", "click", x, y, "--yes"); time.sleep(0.08)
def drag(x0, y0, x1, y1): kt("input", "drag", x0, y0, x1, y1, "--yes"); time.sleep(0.03)

def set_color(hexv):
    click(*HEX_FIELD); time.sleep(0.05)
    kt("input", "chord", "cmd", "a", "--yes"); time.sleep(0.06)
    kt("input", "text", "--yes", hexv); time.sleep(0.06)
    click(*SET_COLOR); time.sleep(0.08)

def set_size(px):
    # calibrated 2026-09-09: value = 8 + (x-30)*0.79  ->  x = 30 + (px-8)*1.266
    px = max(2, min(80, px))
    sx = int(round(30 + (px - 8) * 1.266))
    sx = max(24, min(120, sx))
    drag(72, SLIDER_Y, sx, SLIDER_Y); time.sleep(0.1)

def brush():
    click(*BRUSH_BTN); time.sleep(0.1)

def main():
    p = json.load(open(PLAN))
    brush()
    set_size(40)  # flat-fill brush
    # --- fills: flat color zones as horizontal runs ---
    for zi, z in enumerate(p["fills"]):
        set_color(z["c"])
        n = 0
        for cy, x0, x1 in z["runs"]:
            drag(SX(x0), SY(cy), SX(x1), SY(cy)); n += 1
        print(f"[fill {zi+1}/{len(p['fills'])}] {z['c']} {n} runs", flush=True)
    print("ZONES_DONE", flush=True)
    # --- outlines: thin dark continuous contours on top ---
    set_size(5)
    brush()
    set_color("#161616")
    for ci, c in enumerate(p["contours"]):
        for i in range(len(c) - 1):
            a, b = c[i], c[i+1]
            drag(SX(a[0]), SY(a[1]), SX(b[0]), SY(b[1]))
        print(f"[contour {ci+1}/{len(p['contours'])}] {len(c)} pts", flush=True)
    print("CEL_DONE", flush=True)

if __name__ == "__main__":
    main()
