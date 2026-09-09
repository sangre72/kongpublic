#!/usr/bin/env python3
"""
kong-blender-wrap CLI (kbwrap) — drive headless Blender from kong-bot.

Runs on system python. Builds a JSON job-spec from high-level commands, then
invokes Blender headless: `blender --background --python scripts/runner.py -- <spec>`.
The bpy-side interpreter is scripts/runner.py.

Two modes:
  1. Single-shot flags (quick smoke test / simple renders):
       kbwrap.py smoke --out output/cube.png
       kbwrap.py render-spec examples/scene.json
  2. Spec file: a JSON {output, ops:[...]} authored by the caller (kong-bot worker).

Spec format (see examples/):
  {
    "output": "/abs/path/out.png",
    "ops": [
      {"op":"add","kind":"cube","location":[0,0,0],"size":2,"color":[0.8,0.2,0.2]},
      {"op":"camera","location":[7,-7,5],"look_at":[0,0,0]},
      {"op":"light","location":[4,-4,8],"energy":1000,"light_type":"SUN"},
      {"op":"render","width":640,"height":480}
    ]
  }
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
RUNNER = os.path.join(HERE, "scripts", "runner.py")
BLENDER = os.environ.get("KBW_BLENDER", "/Applications/Blender.app/Contents/MacOS/Blender")


def find_blender():
    if os.path.exists(BLENDER):
        return BLENDER
    # PATH fallback
    from shutil import which
    b = which("blender")
    if b:
        return b
    sys.exit(f"KBW_ERROR: Blender not found at {BLENDER} or on PATH. Set KBW_BLENDER env.")


def _mux_frames_to_mp4(frames_dir, fps, out_path):
    """ffmpeg: frame_%04d.png sequence -> h264 mp4 (yuv420p, even dims)."""
    from shutil import which
    ff = which("ffmpeg") or "ffmpeg"
    cmd = [ff, "-y", "-framerate", str(fps),
           "-i", os.path.join(frames_dir, "frame_%04d.png"),
           "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", out_path]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write(p.stderr + "\n")
    return p.returncode == 0


def run_spec(spec, out_path):
    spec = dict(spec)
    out_path = os.path.abspath(out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    blender = find_blender()

    if spec.get("animation"):
        # animation: render frame-seq to temp dir, then ffmpeg-mux to mp4
        frames_dir = tempfile.mkdtemp(prefix="kbw_frames_")
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(spec, f); spec_path = f.name
        cmd = [blender, "--background", "--python", RUNNER, "--", spec_path, frames_dir]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        os.unlink(spec_path)
        if "KBW_OK:" not in proc.stdout:
            sys.stderr.write(proc.stdout + "\n" + proc.stderr + "\n")
            return False, out_path, proc.stdout
        fps = spec["animation"].get("fps", 24)
        muxed = _mux_frames_to_mp4(frames_dir, fps, out_path)
        import shutil as _sh
        _sh.rmtree(frames_dir, ignore_errors=True)
        return muxed, out_path, proc.stdout

    # single still
    spec["output"] = out_path
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(spec, f); spec_path = f.name
    cmd = [blender, "--background", "--python", RUNNER, "--", spec_path]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    os.unlink(spec_path)
    ok = "KBW_OK:" in proc.stdout
    if not ok:
        sys.stderr.write(proc.stdout + "\n" + proc.stderr + "\n")
    return ok, out_path, proc.stdout


SMOKE_SPEC = {
    "ops": [
        {"op": "add", "kind": "cube", "location": [0, 0, 0], "size": 2, "color": [0.85, 0.35, 0.2]},
        {"op": "add", "kind": "plane", "location": [0, 0, -1], "size": 20, "color": [0.4, 0.6, 0.4]},
        {"op": "camera", "location": [6, -6, 4.5], "look_at": [0, 0, 0]},
        {"op": "light", "location": [4, -4, 8], "energy": 3.0, "light_type": "SUN"},
        {"op": "render", "width": 640, "height": 480},
    ]
}


def main():
    ap = argparse.ArgumentParser(prog="kbwrap", description="headless Blender wrapper for kong-bot")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_smoke = sub.add_parser("smoke", help="render a default cube-on-plane (smoke test)")
    p_smoke.add_argument("--out", default=os.path.join(HERE, "output", "smoke.png"))

    p_spec = sub.add_parser("render-spec", help="render from a JSON job spec")
    p_spec.add_argument("spec", help="path to spec JSON")
    p_spec.add_argument("--out", default=None, help="override output path")

    p_ver = sub.add_parser("version", help="print Blender version")

    args = ap.parse_args()

    if args.cmd == "version":
        subprocess.run([find_blender(), "--version"])
        return

    if args.cmd == "smoke":
        ok, out, log = run_spec(SMOKE_SPEC, args.out)
    elif args.cmd == "render-spec":
        spec = json.load(open(args.spec))
        out = args.out or spec.get("output") or os.path.join(HERE, "output", "render.png")
        ok, out, log = run_spec(spec, out)

    if ok:
        print(f"OK {out}")
    else:
        sys.exit("KBW_ERROR: render failed (see stderr)")


if __name__ == "__main__":
    main()
