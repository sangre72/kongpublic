"""텔레그램 봇 설정 모듈"""

import os
from dataclasses import dataclass, field


@dataclass
class BotConfig:
    token: str
    allowed_chat_ids: list[int]
    news_check_interval: int = 3600
    conversation_timeout: int = 1800
    max_concurrent_jobs: int = 1


def load_config() -> BotConfig:
    """환경변수에서 봇 설정을 로드합니다.

    필수 환경변수:
        TELEGRAM_BOT_TOKEN: 텔레그램 봇 토큰
        TELEGRAM_ALLOWED_CHAT_IDS: 허용된 채팅 ID 목록 (쉼표 구분, 비어있으면 전체 허용)

    Returns:
        BotConfig: 봇 설정 객체

    Raises:
        ValueError: TELEGRAM_BOT_TOKEN이 설정되지 않은 경우
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN 환경변수가 설정되지 않았습니다."
        )

    raw_ids = os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS", "").strip()
    allowed_chat_ids: list[int] = []
    if raw_ids:
        for part in raw_ids.split(","):
            part = part.strip()
            if part:
                try:
                    allowed_chat_ids.append(int(part))
                except ValueError:
                    pass

    return BotConfig(
        token=token,
        allowed_chat_ids=allowed_chat_ids,
        news_check_interval=int(
            os.environ.get("TELEGRAM_NEWS_CHECK_INTERVAL", "3600")
        ),
        conversation_timeout=int(
            os.environ.get("TELEGRAM_CONVERSATION_TIMEOUT", "1800")
        ),
        max_concurrent_jobs=int(
            os.environ.get("TELEGRAM_MAX_CONCURRENT_JOBS", "1")
        ),
    )
