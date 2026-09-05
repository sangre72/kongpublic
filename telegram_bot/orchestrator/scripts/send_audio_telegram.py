#!/usr/bin/env python3
"""워커 → 유저 텔레그램 오디오 전송.
사용: python3 telegram_bot/orchestrator/scripts/send_audio_telegram.py <file_path> ["caption"]
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
OCH_DIR = os.path.dirname(HERE)
TG_DIR = os.path.dirname(OCH_DIR)
sys.path.insert(0, TG_DIR)

envp = os.path.join(OCH_DIR, ".env")
if os.path.exists(envp):
    for line in open(envp):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from orchestrator.telegram_io import TelegramIO
token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
_raw = (os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS") or "").split(",")[0].strip()
if not _raw:
    raise SystemExit("TELEGRAM_ALLOWED_CHAT_IDS missing")
chat_id = int(_raw)
if not token:
    raise SystemExit("TELEGRAM_BOT_TOKEN missing")
if len(sys.argv) < 2:
    raise SystemExit("usage: send_audio_telegram.py <file_path> [caption]")

file_path = sys.argv[1]
caption = sys.argv[2] if len(sys.argv) > 2 else None
tg = TelegramIO(token)
r = tg.send_audio_file(chat_id, file_path, caption=caption)
print("sent:", r.get("ok", r))
