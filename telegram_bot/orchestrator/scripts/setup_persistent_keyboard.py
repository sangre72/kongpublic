#!/usr/bin/env python3
"""오케-유저 텔레그램 채팅 하단에 항상 노출되는 고정 키보드 설치(u_3276/3277).
한번 실행하면 그 뒤로 채팅창 하단에 버튼이 계속 남음(inline_keyboard와 다름).
사용: python3 telegram_bot/orchestrator/scripts/setup_persistent_keyboard.py
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

tg = TelegramIO(token)
KEYBOARD_ROWS = [
    ["리포트"],
    ["git commit, push"],
]
r = tg.send_message_persistent_kb(
    chat_id,
    "고정 버튼 설치했습니다 — 아래 버튼으로 자주 쓰는 명령 바로 입력 가능합니다.",
    KEYBOARD_ROWS,
)
print("설치 ok:", r.get("ok", r))
