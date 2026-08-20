#!/usr/bin/env python3
"""Drive worker1_monitor_tick.sh every 10s. Matching logic stays in the tick script.

ROOT is always this repo (kong-bot). Never follow cwd into sky or another project.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
# Always this file's repo root (…/kong-bot). Never inherit a foreign cwd (sky).
ROOT = os.path.abspath(os.path.join(HERE, "../../.."))
TICK = os.path.join(HERE, "worker1_monitor_tick.sh")


def main() -> int:
    os.chdir(ROOT)
    env = os.environ.copy()
    env["KONG_WORKER_MON1"] = "1"
    env["KONG_WORKER_ROOT"] = ROOT
    print(f"worker1_monitor_loop root={ROOT}", flush=True)
    while True:
        try:
            r = subprocess.run(["bash", TICK], cwd=ROOT, env=env)
            if r.returncode != 0:
                print(f"TICK_ERROR exit={r.returncode} root={ROOT}", flush=True)
        except OSError as exc:
            print(f"TICK_ERROR os={exc}", flush=True)
        time.sleep(5)


if __name__ == "__main__":
    sys.exit(main())
