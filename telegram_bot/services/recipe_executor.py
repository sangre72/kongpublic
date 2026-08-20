"""
레시피 실행 엔진

method_config JSON을 읽고 수집 방식별(RSS/API/Playwright/X scrape)로
실행하여 NewsItem 리스트를 반환하는 엔진.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, TYPE_CHECKING

import feedparser

from telegram_bot.models import NewsItem

if TYPE_CHECKING:
    from telegram_bot.services.news_scraper import NewsScraper

logger = logging.getLogger(__name__)

# Reddit 잡담/의견/반복 포스트 필터 패턴 (소문자 매칭)
_REDDIT_SKIP_PATTERNS = [
    # 반복 스레드
    "daily discussion", "daily crypto discussion", "daily general discussion",
    "weekly discussion", "monthly discussion",
    "self-promotion thread", "self promotion thread",
    "who's hiring", "who is hiring", "who wants to be hired",
    "megathread", "mega thread",
    # 토론/의견 태그
    "[d] self-promotion", "[d] monthly who",
    # 질문/의견
    "what do you think about", "what's your opinion",
    "unpopular opinion", "hot take",
    "rant:", "vent:",
    # 규칙/안내
    "welcome to r/", "rules of r/", "subreddit rules",
    "read before posting", "new to this sub",
]


# ──────────────────────────────────────
# 커스텀 예외
# ──────────────────────────────────────


class RecipeExecutionError(Exception):
    """레시피 실행 실패 시 발생하는 예외."""


# ──────────────────────────────────────
# 결과 데이터 클래스
# ──────────────────────────────────────


@dataclass
class ExecutionResult:
    """execute_once()의 반환 타입."""

    success: bool
    items: list[NewsItem]
    items_count: int
    execution_time_ms: int
    error: Optional[str] = None


# ──────────────────────────────────────
# 유틸 헬퍼
# ──────────────────────────────────────


def _now_iso() -> str:
    """현재 시각을 ISO 8601 문자열로 반환 (UTC)."""
    return datetime.now(tz=timezone.utc).isoformat()


def _parse_rss_datetime(published: str) -> str:
    """feedparser에서 반환되는 날짜 문자열을 ISO 8601로 변환.

    news_scraper.py의 동일 함수와 동일한 로직.
    변환 실패 시 원본 문자열을 그대로 반환.
    """
    if not published:
        return ""
    try:
        import email.utils
        parsed = email.utils.parsedate_to_datetime(published)
        return parsed.isoformat()
    except Exception:
        return published


def _domain_from_url(url: str) -> str:
    """URL에서 도메인명을 추출한다. 실패 시 빈 문자열 반환."""
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc
    except Exception:
        return ""


# ──────────────────────────────────────
# 메인 엔진
# ──────────────────────────────────────


class RecipeExecutor:
    """method_config JSON 기반 수집 레시피 실행 엔진.

    지원 수집 방식:
        rss        - feedparser로 RSS/Atom 피드 수집
        api        - httpx로 REST API 호출 + JSON 경로 추출
        playwright - Playwright steps 기반 웹 스크래핑
        x_scrape   - Playwright + 로그인 세션으로 X/Twitter 수집
    """

    def __init__(self, news_scraper: Optional[NewsScraper] = None) -> None:
        """news_scraper는 Playwright 브라우저 공유용 (선택).

        Args:
            news_scraper: NewsScraper 인스턴스. Playwright 브라우저를 공유할 때 전달.
                          None이면 playwright/x_scrape 실행 시 자체 브라우저 시작.
        """
        self._news_scraper = news_scraper

    # ──────────────────────────────────────
    # 공개 인터페이스
    # ──────────────────────────────────────

    async def execute(self, channel: dict) -> list[NewsItem]:
        """채널의 method_config를 해석하여 수집 실행.

        Args:
            channel: research_channels 테이블 row dict.
                     필수 키: method_config, name, id

        Returns:
            수집된 NewsItem 리스트 (중복 제거 전).

        Raises:
            RecipeExecutionError: method_config 파싱 실패 또는 지원하지 않는 method.
        """
        # method_config 파싱
        try:
            raw_config = channel.get("method_config", "{}")
            if isinstance(raw_config, str):
                config = json.loads(raw_config)
            else:
                config = raw_config
        except json.JSONDecodeError as exc:
            raise RecipeExecutionError(
                f"method_config JSON 파싱 실패 (channel={channel.get('name', '?')}): {exc}"
            ) from exc

        method = config.get("method", "")
        logger.info(
            f"레시피 실행 시작: channel={channel.get('name', '?')}, method={method}"
        )

        # 백엔드 함수는 telegram_bot.services.recipe_executors 로 분리
        from telegram_bot.services.recipe_executors import (
            _execute_api,
            _execute_playwright,
            _execute_rss,
            _execute_x_scrape,
        )

        if method == "rss":
            return await _execute_rss(self._news_scraper, config, channel)
        elif method == "api":
            return await _execute_api(self._news_scraper, config, channel)
        elif method == "playwright":
            return await _execute_playwright(self._news_scraper, config, channel)
        elif method == "x_scrape":
            return await _execute_x_scrape(self._news_scraper, config, channel)
        else:
            raise RecipeExecutionError(
                f"지원하지 않는 수집 방식: method={method!r} "
                f"(channel={channel.get('name', '?')}). "
                f"지원 방식: rss, api, playwright, x_scrape"
            )

    async def execute_once(self, channel: dict) -> ExecutionResult:
        """1회 테스트 실행 (타이밍 + 통계 포함).

        Args:
            channel: research_channels 테이블 row dict.

        Returns:
            ExecutionResult(success, items, items_count, execution_time_ms, error)
        """
        start_ms = int(time.monotonic() * 1000)
        try:
            items = await self.execute(channel)
            elapsed = int(time.monotonic() * 1000) - start_ms
            logger.info(
                f"execute_once 완료: channel={channel.get('name', '?')}, "
                f"items={len(items)}, elapsed={elapsed}ms"
            )
            return ExecutionResult(
                success=True,
                items=items,
                items_count=len(items),
                execution_time_ms=elapsed,
                error=None,
            )
        except Exception as exc:
            elapsed = int(time.monotonic() * 1000) - start_ms
            logger.warning(
                f"execute_once 실패: channel={channel.get('name', '?')}, "
                f"error={exc}, elapsed={elapsed}ms"
            )
            return ExecutionResult(
                success=False,
                items=[],
                items_count=0,
                execution_time_ms=elapsed,
                error=str(exc),
            )

    # ──────────────────────────────────────
    # RSS 수집
    # ──────────────────────────────────────

async def _extract_field(element: Any, spec: str) -> str:
    """Playwright element에서 spec 기반으로 값을 추출한다.

    spec 형식:
        ".selector"          - 하위 셀렉터의 innerText
        ".selector@attr"     - 하위 셀렉터의 속성값
        "a@href"             - a 태그의 href 속성
        "time@datetime"      - time 태그의 datetime 속성
        "text"               - element 자체의 innerText (셀렉터 없음)

    Args:
        element: Playwright ElementHandle.
        spec: 추출 명세 문자열.

    Returns:
        추출된 문자열. 실패 시 빈 문자열.
    """
    if not spec:
        return ""

    # "@" 가 포함된 경우 셀렉터@속성명 형식
    if "@" in spec:
        parts = spec.split("@", 1)
        selector_part = parts[0].strip()
        attr_name = parts[1].strip()

        if selector_part:
            target_el = await element.query_selector(selector_part)
        else:
            target_el = element

        if target_el is None:
            return ""

        attr_value = await target_el.get_attribute(attr_name)
        return attr_value or ""

    # "@" 없는 경우: 셀렉터의 innerText
    if spec.strip():
        target_el = await element.query_selector(spec)
        if target_el is None:
            return ""
        text = await target_el.inner_text()
        return text.strip()

    return ""


# ──────────────────────────────────────
# 유틸 헬퍼
# ──────────────────────────────────────


def _parse_compact_number(text: str) -> int:
    """'1.2K', '3M', '500' 형태의 숫자 문자열을 정수로 변환한다.

    Args:
        text: 숫자 문자열.

    Returns:
        정수값. 변환 실패 시 0.
    """
    text = text.strip().replace(",", "")
    if not text:
        return 0
    try:
        if text.endswith("K") or text.endswith("k"):
            return int(float(text[:-1]) * 1_000)
        elif text.endswith("M") or text.endswith("m"):
            return int(float(text[:-1]) * 1_000_000)
        elif text.endswith("B") or text.endswith("b"):
            return int(float(text[:-1]) * 1_000_000_000)
        else:
            return int(float(text))
    except (ValueError, TypeError):
        return 0
