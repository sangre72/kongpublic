"""Playwright + X/Twitter 스크래핑 executor.

recipe_executors.py 에서 분리한 브라우저 기반 수집 함수들.
_normalize_to_news_item 등 공용 헬퍼는 원본 모듈에서 lazy import.
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

from telegram_bot.models import NewsItem
from telegram_bot.services.recipe_executor import RecipeExecutionError, _extract_field
from telegram_bot.services.recipe_executors import _normalize_to_news_item

logger = logging.getLogger(__name__)


# ──────────────────────────────────────
# Playwright 수집
# ──────────────────────────────────────

async def _execute_playwright(news_scraper, config: dict, channel: dict) -> list[NewsItem]:
    """Playwright steps 배열을 순서대로 실행하여 NewsItem 목록을 추출한다.

    config 스키마:
        steps          - 실행할 액션 배열 (필수)
            goto       - {"action": "goto", "url": "..."}
            wait       - {"action": "wait", "selector": "...", "timeout": 5000}
            scroll     - {"action": "scroll", "count": 2, "delay": 1000}
            click      - {"action": "click", "selector": "..."}
            extract_list - {"action": "extract_list", "selector": "...",
                            "fields": {"title": "h2", "link": "a@href", ...}}
        timeout_seconds - 전체 타임아웃 (기본 30초)
    """
    steps: list[dict] = config.get("steps", [])
    if not steps:
        raise RecipeExecutionError(
            f"Playwright config에 steps 배열 없음 (channel={channel.get('name', '?')})"
        )

    timeout_seconds = float(config.get("timeout_seconds", 30))
    max_items = int(channel.get("max_items_per_fetch", 20))
    channel_name = channel.get("name", "")
    topic = channel.get("topic", "")
    language = channel.get("language", "en")

    # 브라우저: news_scraper에서 공유하거나 자체 시작
    if news_scraper is not None:
        browser = await news_scraper.get_browser()
    else:
        from playwright.async_api import async_playwright
        _pw_instance = await async_playwright().start()
        browser = await _pw_instance.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )

    context = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    )
    page = await context.new_page()
    raw_items: list[dict] = []

    try:
        async def _run_steps() -> None:
            for step in steps:
                action = step.get("action", "")

                if action == "goto":
                    goto_url = step.get("url", "")
                    if goto_url:
                        await page.goto(goto_url, wait_until="domcontentloaded")

                elif action == "wait":
                    selector = step.get("selector", "")
                    step_timeout = step.get("timeout", 5000)
                    if selector:
                        await page.wait_for_selector(
                            selector, timeout=step_timeout
                        )

                elif action == "scroll":
                    count = int(step.get("count", 1))
                    delay_ms = int(step.get("delay", 1000))
                    for _ in range(count):
                        await page.evaluate(
                            "window.scrollBy(0, window.innerHeight)"
                        )
                        await asyncio.sleep(delay_ms / 1000)

                elif action == "click":
                    selector = step.get("selector", "")
                    if selector:
                        try:
                            await page.click(selector, timeout=5000)
                        except Exception as exc:
                            logger.debug(
                                f"click 실패 (무시): selector={selector}, {exc}"
                            )

                elif action == "extract_list":
                    selector = step.get("selector", "")
                    fields: dict[str, str] = step.get("fields", {})
                    if not selector or not fields:
                        logger.warning(
                            f"extract_list: selector 또는 fields 없음 (channel={channel_name})"
                        )
                        continue

                    elements = await page.query_selector_all(selector)
                    for el in elements[:max_items]:
                        extracted: dict[str, str] = {}
                        for field_name, field_spec in fields.items():
                            try:
                                value = await _extract_field(el, field_spec)
                                extracted[field_name] = value
                            except Exception as exc:
                                logger.debug(
                                    f"필드 추출 실패: field={field_name}, "
                                    f"spec={field_spec!r}: {exc}"
                                )
                                extracted[field_name] = ""
                        raw_items.append(extracted)

                else:
                    logger.warning(
                        f"알 수 없는 Playwright action: {action!r} "
                        f"(channel={channel_name})"
                    )

        await asyncio.wait_for(_run_steps(), timeout=timeout_seconds)

    except asyncio.TimeoutError:
        raise RecipeExecutionError(
            f"Playwright 실행 타임아웃 ({timeout_seconds}s): channel={channel_name}"
        )
    except Exception as exc:
        raise RecipeExecutionError(
            f"Playwright 실행 실패: channel={channel_name}: {exc}"
        ) from exc
    finally:
        try:
            await context.close()
        except Exception:
            pass

    # raw 결과 → NewsItem 정규화
    items: list[NewsItem] = []
    for raw in raw_items:
        title = raw.get("title", "").strip()
        link = raw.get("link", "").strip()
        if not title or not link:
            continue

        # 상대 경로 링크 처리 (goto URL 기반)
        if link.startswith("/") and steps:
            for step in steps:
                if step.get("action") == "goto":
                    base = step.get("url", "")
                    if base:
                        from urllib.parse import urljoin
                        link = urljoin(base, link)
                    break

        item = _normalize_to_news_item(
            raw={
                "title": title,
                "link": link,
                "source": channel_name,
                "published_at": raw.get("date", raw.get("published_at", "")),
                "summary": raw.get("summary", raw.get("excerpt", "")),
                "community_score": 0,
            },
            channel=channel,
            topic=topic,
            language=language,
        )
        items.append(item)

    logger.info(
        f"_execute_playwright 완료: channel={channel_name}, 수집={len(items)}건"
    )
    return items

# ──────────────────────────────────────
# X/Twitter 스크래핑
# ──────────────────────────────────────

async def _execute_x_scrape(news_scraper, config: dict, channel: dict) -> list[NewsItem]:
    """Playwright + 세션 쿠키로 X/Twitter 프로필 페이지를 스크래핑한다.

    config 스키마:
        account_handle        - "@OpenAI" 형태의 X 계정 핸들 (필수)
        session_cookie_env    - .env에서 로드할 세션 쿠키 환경변수명 (필수)
        max_tweets            - 최대 수집 트윗 수 (기본 20)
        include_replies       - 리플라이 포함 여부 (기본 False)
        min_likes             - 최소 좋아요 수 필터 (기본 0)
        timeout_seconds       - 전체 타임아웃 (기본 30초)
    """
    account_handle = config.get("account_handle", "")
    if not account_handle:
        raise RecipeExecutionError(
            f"x_scrape config에 account_handle 없음 (channel={channel.get('name', '?')})"
        )

    session_cookie_env = config.get("session_cookie_env", "")
    if not session_cookie_env:
        raise RecipeExecutionError(
            f"x_scrape config에 session_cookie_env 없음 (channel={channel.get('name', '?')})"
        )

    session_cookie = os.environ.get(session_cookie_env, "")
    if not session_cookie:
        raise RecipeExecutionError(
            f"세션 쿠키 환경변수 없음: {session_cookie_env}. "
            f".env 파일에 {session_cookie_env}=<cookie_value>를 추가하세요."
        )

    max_tweets = int(config.get("max_tweets", 20))
    include_replies = bool(config.get("include_replies", False))
    min_likes = int(config.get("min_likes", 0))
    timeout_seconds = float(config.get("timeout_seconds", 30))
    channel_name = channel.get("name", "")
    topic = channel.get("topic", "")
    language = channel.get("language", "en")

    # 핸들 정규화: "@OpenAI" -> "OpenAI"
    handle = account_handle.lstrip("@")
    profile_url = f"https://x.com/{handle}"

    # 브라우저: news_scraper에서 공유하거나 자체 시작
    if news_scraper is not None:
        browser = await news_scraper.get_browser()
    else:
        from playwright.async_api import async_playwright
        _pw_instance = await async_playwright().start()
        browser = await _pw_instance.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )

    # 세션 쿠키 주입 (auth_token 형식으로 처리)
    context = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    )

    # 쿠키 값이 JSON 배열 형식인지 확인 후 주입
    try:
        cookies_data = json.loads(session_cookie)
        if isinstance(cookies_data, list):
            await context.add_cookies(cookies_data)
        else:
            # 단일 auth_token 값으로 처리
            await context.add_cookies([{
                "name": "auth_token",
                "value": session_cookie,
                "domain": ".x.com",
                "path": "/",
            }])
    except (json.JSONDecodeError, Exception):
        # JSON 파싱 실패 시 단순 쿠키 값으로 처리
        await context.add_cookies([{
            "name": "auth_token",
            "value": session_cookie,
            "domain": ".x.com",
            "path": "/",
        }])

    page = await context.new_page()
    items: list[NewsItem] = []

    try:
        async def _scrape_tweets() -> list[NewsItem]:
            await page.goto(
                profile_url,
                wait_until="domcontentloaded",
                timeout=int(timeout_seconds * 1000),
            )

            # 트윗 로딩 대기
            try:
                await page.wait_for_selector(
                    "[data-testid='tweet']", timeout=10000
                )
            except Exception:
                raise RecipeExecutionError(
                    f"X/Twitter 트윗 셀렉터 응답 없음 (url={profile_url}). "
                    f"세션 쿠키가 만료되었을 수 있습니다. "
                    f"{session_cookie_env} 환경변수를 최신 쿠키 값으로 갱신하세요."
                )

            tweet_elements = await page.query_selector_all(
                "[data-testid='tweet']"
            )
            result: list[NewsItem] = []

            for el in tweet_elements[:max_tweets * 2]:  # 필터 여유분
                if len(result) >= max_tweets:
                    break
                try:
                    # 리플라이 필터
                    if not include_replies:
                        reply_indicator = await el.query_selector(
                            "[data-testid='reply']"
                        )
                        # 리플라이 여부는 @mention으로 시작하는 텍스트로 판별
                        tweet_text_el = await el.query_selector(
                            "[data-testid='tweetText']"
                        )
                        if tweet_text_el:
                            tweet_text = await tweet_text_el.inner_text()
                            if tweet_text.strip().startswith("@"):
                                continue

                    # 트윗 텍스트 추출
                    text_el = await el.query_selector(
                        "[data-testid='tweetText']"
                    )
                    if not text_el:
                        continue
                    tweet_text = (await text_el.inner_text()).strip()
                    if not tweet_text:
                        continue

                    # 좋아요 수 추출
                    likes = 0
                    like_el = await el.query_selector(
                        "[data-testid='like'] span"
                    )
                    if like_el:
                        like_text = (await like_el.inner_text()).strip()
                        try:
                            # "1.2K" → 1200, "2M" → 2000000 형태 처리
                            likes = _parse_compact_number(like_text)
                        except Exception:
                            likes = 0

                    # min_likes 필터
                    if likes < min_likes:
                        continue

                    # 트윗 링크 추출
                    tweet_link = profile_url  # 폴백
                    link_el = await el.query_selector(
                        "a[href*='/status/']"
                    )
                    if link_el:
                        href = await link_el.get_attribute("href")
                        if href:
                            tweet_link = (
                                f"https://x.com{href}"
                                if href.startswith("/")
                                else href
                            )

                    # 날짜 추출
                    published_at = _now_iso()
                    time_el = await el.query_selector("time")
                    if time_el:
                        datetime_attr = await time_el.get_attribute("datetime")
                        if datetime_attr:
                            published_at = datetime_attr

                    item = _normalize_to_news_item(
                        raw={
                            "title": tweet_text[:200],  # 트윗 텍스트를 제목으로
                            "link": tweet_link,
                            "source": f"@{handle}",
                            "published_at": published_at,
                            "summary": tweet_text,
                            "community_score": likes,
                        },
                        channel=channel,
                        topic=topic,
                        language=language,
                    )
                    result.append(item)

                except Exception as exc:
                    logger.debug(f"트윗 파싱 실패 (무시): {exc}")
                    continue

            return result

        result_items = await asyncio.wait_for(
            _scrape_tweets(), timeout=timeout_seconds
        )
        items = result_items

    except asyncio.TimeoutError:
        raise RecipeExecutionError(
            f"X/Twitter 스크래핑 타임아웃 ({timeout_seconds}s): "
            f"channel={channel_name}, url={profile_url}"
        )
    except RecipeExecutionError:
        raise
    except Exception as exc:
        raise RecipeExecutionError(
            f"X/Twitter 스크래핑 실패: channel={channel_name}: {exc}"
        ) from exc
    finally:
        try:
            await context.close()
        except Exception:
            pass

    logger.info(
        f"_execute_x_scrape 완료: channel={channel_name}, "
        f"handle=@{handle}, 수집={len(items)}건"
    )
    return items
