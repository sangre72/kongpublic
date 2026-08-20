#!/usr/bin/env python3
"""
krita_ring_coord: convert target hue(0-360deg) to Krita color-wheel ring click coordinate.
REG: a_710/714/715/716/717(2026-08-18), formula+36-point radius table pixel-scan-verified.
Center/scale specific to this session's docker position/display — re-verify if docker moves
or display changes(see RECIPE_set_fill_color.txt for re-derivation method).

Usage:
    python3 ring_coord.py <target_hue_degrees>
    -> prints "x y" (logical coords for kongtrol click)

Or import: from ring_coord import ring_coord
"""
import sys, math

CENTER_X, CENTER_Y = 1913, 218  # logical, scale=2.0 confirmed
SCALE = 2.0

# angle(deg, standard math CCW-from-right) -> radius(logical px), pixel-scan-verified a_714/715
RADIUS_TABLE = {
    0:80, 10:80, 20:80, 30:80, 40:80, 50:80, 60:80,
    70:82, 80:82, 90:84, 100:84, 110:86,
    120:100, 130:100, 140:100, 150:100, 160:100, 170:100, 180:100,
    190:100, 200:100, 210:100, 220:100, 230:100, 240:100, 250:100, 260:100, 270:100,
    280:86, 290:86, 300:84, 310:82, 320:82, 330:85, 340:80, 350:80,
}

def _interp_radius(angle):
    angle = angle % 360
    keys = sorted(RADIUS_TABLE.keys())
    for i, k in enumerate(keys):
        if angle <= k:
            if angle == k:
                return RADIUS_TABLE[k]
            prev_k = keys[i-1] if i > 0 else keys[-1] - 360
            prev_r = RADIUS_TABLE[keys[i-1]] if i > 0 else RADIUS_TABLE[keys[-1]]
            span = k - prev_k
            frac = (angle - prev_k) / span
            return prev_r + frac * (RADIUS_TABLE[k] - prev_r)
    return RADIUS_TABLE[keys[0]]

def ring_coord(target_hue_degrees):
    """target_hue_degrees(0-360) -> (x, y) logical click coordinate on the ring."""
    click_angle = (180 - target_hue_degrees) % 360
    radius = _interp_radius(click_angle)
    a = math.radians(click_angle)
    x = CENTER_X + radius * math.cos(a)
    y = CENTER_Y - radius * math.sin(a)
    return round(x), round(y)

if __name__ == "__main__":
    hue = float(sys.argv[1])
    x, y = ring_coord(hue)
    print(f"{x} {y}")
