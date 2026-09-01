#!/usr/bin/env python3
"""워커 → 유저 텔레그램 단순 알림(버튼 없음, 진행상황 실시간 보고용).
사용: python3 telegram_bot/orchestrator/scripts/notify_telegram.py "메시지"
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
    raise SystemExit("TELEGRAM_ALLOWED_CHAT_IDS 없음 (orchestrator/.env 에 설정)")
chat_id = int(_raw)
if not token:
    raise SystemExit("TELEGRAM_BOT_TOKEN 없음")

text = sys.argv[1]
tg = TelegramIO(token)
r = tg.send_message(chat_id, text)
print("발송 ok:", r.get("ok", r))
