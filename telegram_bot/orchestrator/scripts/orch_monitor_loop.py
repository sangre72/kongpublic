#!/usr/bin/env python3
"""Drive orch_monitor_tick.sh every 10s. Session-independent heartbeat owner.

Writes logs/.orch_alive via the tick script. launchd KeepAlive restarts this
loop when the Grok/Claude session dies (root cause of 155min death-alert).
ROOT is always this repo (kong-bot). Never follow cwd into sky.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../.."))
TICK = os.path.join(HERE, "orch_monitor_tick.sh")


def main() -> int:
    os.chdir(ROOT)
    env = os.environ.copy()
    env["KONG_ORCH_MON1"] = "1"
    env["KONG_ORCH_ROOT"] = ROOT
    print(f"orch_monitor_loop root={ROOT}", flush=True)
    while True:
        try:
            r = subprocess.run(["bash", TICK], cwd=ROOT, env=env)
            if r.returncode != 0:
                print(f"TICK_ERROR exit={r.returncode} root={ROOT}", flush=True)
        except OSError as exc:
            print(f"TICK_ERROR os={exc}", flush=True)
        time.sleep(10)


if __name__ == "__main__":
    sys.exit(main())
