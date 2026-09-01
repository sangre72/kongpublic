"""RecipeExecutor 백엔드 함수들 — recipe_executor.py 에서 분리.

RSS / API / Playwright / X scrape 수집 함수 + 정규화/JSON path 헬퍼.
모두 RecipeExecutor 메서드를 자유 함수로 변환 (self → news_scraper 인자).
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from telegram_bot.models import NewsItem
from telegram_bot.services.news_scraper import NewsScraper

logger = logging.getLogger(__name__)


async def _execute_rss(news_scraper, config: dict, channel: dict) -> list[NewsItem]:
    """feedparser로 RSS 피드를 수집한다.

    config 스키마:
        url              - RSS 피드 URL (필수)
        timeout_seconds  - 타임아웃 (기본 15초)
        time_filter_hours - 이 시간 이내 기사만 수집 (0=무제한, 기본 24시간)
        title_cleanup    - " - 출처명" 패턴 제거 여부 (기본 False)
    """
    url = config.get("url", "")
    if not url:
        raise RecipeExecutionError(
            f"RSS config에 url 필드 없음 (channel={channel.get('name', '?')})"
        )

    timeout_seconds = float(config.get("timeout_seconds", 15))
    time_filter_hours = int(config.get("time_filter_hours", 24))
    title_cleanup = bool(config.get("title_cleanup", False))
    max_items = int(channel.get("max_items_per_fetch", 20))
    channel_name = channel.get("name", "")
    # topic: domain lookup은 호출자 책임; channel에 topic 필드가 있으면 사용
    topic = channel.get("topic", _domain_from_url(url))
    language = channel.get("language", "en")

    # feedparser는 동기 라이브러리 → asyncio.to_thread 래핑 (기존 news_scraper 패턴)
    try:
        feed = await asyncio.wait_for(
            asyncio.to_thread(feedparser.parse, url),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError:
        raise RecipeExecutionError(
            f"RSS 타임아웃 ({timeout_seconds}s): channel={channel_name}, url={url}"
        )
    except Exception as exc:
        raise RecipeExecutionError(
            f"RSS 파싱 실패: channel={channel_name}, url={url}: {exc}"
        ) from exc

    items: list[NewsItem] = []
    now_utc = datetime.now(tz=timezone.utc)

    for entry in feed.entries[:max_items]:
        link = entry.get("link", "")
        if not link:
            continue

        title = entry.get("title", "").strip()
        if not title:
            continue

        # 제목 정리: " - 출처명" 제거 (config 옵션)
        if title_cleanup and " - " in title:
            title = title.rsplit(" - ", 1)[0].strip()

        # 시간 필터 적용
        published_raw = entry.get("published", "")
        published_at = _parse_rss_datetime(published_raw)
        if time_filter_hours > 0 and published_at:
            try:
                pub_dt = datetime.fromisoformat(published_at)
                if pub_dt.tzinfo is None:
                    pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                age = now_utc - pub_dt
                if age > timedelta(hours=time_filter_hours):
                    logger.debug(
                        f"시간 필터 스킵 ({age.total_seconds()/3600:.1f}h): {title[:40]}"
                    )
                    continue
            except Exception:
                pass  # 파싱 실패 시 필터 스킵

        summary = entry.get("summary", "")
        source = (
            entry.get("source", {}).get("title", "")
            or channel_name
        )

        item = _normalize_to_news_item(
            raw={
                "title": title,
                "link": link,
                "source": source,
                "published_at": published_at,
                "summary": summary,
                "community_score": 0,
            },
            channel=channel,
            topic=topic,
            language=language,
        )
        items.append(item)

    logger.info(
        f"_execute_rss 완료: channel={channel_name}, 수집={len(items)}건"
    )
    return items

# ──────────────────────────────────────
# API 수집
# ──────────────────────────────────────

async def _execute_api(news_scraper, config: dict, channel: dict) -> list[NewsItem]:
    """httpx로 REST API를 호출하고 JSON 경로 기반으로 NewsItem을 추출한다.

    config 스키마:
        base_url       - API 엔드포인트 URL (필수)
        headers        - 요청 헤더 dict (선택)
        params         - 쿼리 파라미터 dict (선택)
        auth           - 인증 정보 (선택, {"type": "bearer", "env_key": "ENV_VAR_NAME"})
        response_path  - JSON 응답에서 아이템 배열 경로 (점 구분, 예: "data.children")
        field_map      - 응답 필드 -> NewsItem 필드 매핑 dict
        timeout_seconds - 타임아웃 (기본 30초)
    """
    try:
        import httpx
    except ImportError as exc:
        raise RecipeExecutionError(
            "httpx 패키지가 설치되지 않았습니다. "
            "'uv add httpx' 또는 'pip install httpx' 명령으로 설치하세요."
        ) from exc

    base_url = config.get("base_url", config.get("url", ""))
    if not base_url:
        raise RecipeExecutionError(
            f"API config에 base_url 필드 없음 (channel={channel.get('name', '?')})"
        )

    timeout_seconds = float(config.get("timeout_seconds", 30))
    headers: dict[str, str] = dict(config.get("headers", {}))
    params: dict[str, Any] = dict(config.get("params", {}))
    response_path: str = config.get("response_path", "")
    field_map: dict[str, str] = config.get("field_map", {})
    max_items = int(channel.get("max_items_per_fetch", 20))
    channel_name = channel.get("name", "")
    topic = channel.get("topic", _domain_from_url(base_url))
    language = channel.get("language", "en")

    # 인증 처리
    auth_config = config.get("auth")
    if auth_config and isinstance(auth_config, dict):
        auth_type = auth_config.get("type", "")
        if auth_type == "bearer":
            env_key = auth_config.get("env_key", "")
            token = os.environ.get(env_key, "")
            if not token:
                logger.warning(
                    f"인증 토큰 환경변수 없음: {env_key} (channel={channel_name})"
                )
            else:
                headers["Authorization"] = f"Bearer {token}"

    # HTTP 요청
    try:
        async with httpx.AsyncClient(
            headers=headers,
            timeout=timeout_seconds,
            follow_redirects=True,
        ) as client:
            response = await client.get(base_url, params=params)
            response.raise_for_status()
            resp_data = response.json()
    except httpx.TimeoutException as exc:
        raise RecipeExecutionError(
            f"API 타임아웃 ({timeout_seconds}s): channel={channel_name}, url={base_url}"
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise RecipeExecutionError(
            f"API HTTP 오류 {exc.response.status_code}: "
            f"channel={channel_name}, url={base_url}"
        ) from exc
    except httpx.RequestError as exc:
        raise RecipeExecutionError(
            f"API 요청 실패: channel={channel_name}, url={base_url}: {exc}"
        ) from exc
    except Exception as exc:
        raise RecipeExecutionError(
            f"API 응답 처리 실패: channel={channel_name}: {exc}"
        ) from exc

    # JSON 경로로 아이템 배열 추출
    if response_path:
        raw_items = _extract_json_path(resp_data, response_path)
        if not isinstance(raw_items, list):
            raise RecipeExecutionError(
                f"response_path={response_path!r} 결과가 리스트가 아님: "
                f"type={type(raw_items).__name__} (channel={channel_name})"
            )
    elif isinstance(resp_data, list):
        raw_items = resp_data
    else:
        raise RecipeExecutionError(
            f"API 응답이 리스트가 아니고 response_path도 없음 (channel={channel_name}). "
            f"response_path 필드를 설정하세요."
        )

    items: list[NewsItem] = []
    for raw in raw_items[:max_items]:
        if not isinstance(raw, dict):
            continue

        # field_map으로 NewsItem 필드 매핑
        mapped = _map_fields(raw, field_map) if field_map else {}

        # 필수 필드 확인
        title = str(mapped.get("title", "")).strip()
        link = str(mapped.get("link", "")).strip()
        if not title or not link:
            logger.debug(f"title/link 없음, 스킵: {list(raw.keys())[:5]}")
            continue

        # Reddit 잡담/의견 필터링
        if "reddit.com" in base_url.lower():
            title_lower = title.lower()
            if any(skip in title_lower for skip in _REDDIT_SKIP_PATTERNS):
                logger.debug(f"Reddit 필터: {title[:50]}")
                continue

        # community_score 처리: API 응답의 score/points/likes 등
        community_score = 0
        raw_score = mapped.get("community_score", 0)
        if raw_score is not None:
            try:
                community_score = int(float(str(raw_score)))
            except (ValueError, TypeError):
                community_score = 0

        # published_at: Unix timestamp 처리
        published_at = str(mapped.get("published_at", ""))
        if published_at and published_at.replace(".", "").isdigit():
            try:
                ts = float(published_at)
                published_at = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            except Exception:
                pass

        item = _normalize_to_news_item(
            raw={
                "title": title,
                "link": link,
                "source": str(mapped.get("source", channel_name)),
                "published_at": published_at,
                "summary": str(mapped.get("summary", "")),
                "community_score": community_score,
            },
            channel=channel,
            topic=topic,
            language=language,
        )
        items.append(item)

    logger.info(
        f"_execute_api 완료: channel={channel_name}, 수집={len(items)}건"
    )
    return items


# ──────────────────────────────────────
# 정규화
# ──────────────────────────────────────


def __getattr__(name: str):
    """브라우저 기반 executor(_execute_playwright, _execute_x_scrape) lazy import.

    호환성: 외부에서 from recipe_executors import _execute_playwright 가능.
    별도 모듈로 분리한 결과 모듈 import 순환을 피하기 위해 lazy.
    """
    if name in ("_execute_playwright", "_execute_x_scrape"):
        from telegram_bot.services import recipe_executors_browser as _b
        return getattr(_b, name)
    raise AttributeError(name)

def _normalize_to_news_item(
    raw: dict,
    channel: dict,
    topic: str = "",
    language: str = "en",
) -> NewsItem:
    """수집 결과 dict를 NewsItem으로 정규화한다.

    Args:
        raw: 수집된 원시 데이터. title, link, source, published_at,
             summary, community_score 키를 포함.
        channel: research_channels 테이블 row dict.
        topic: 채널 도메인 이름 (ai, blockchain 등).
        language: 언어 코드.

    Returns:
        NewsItem 인스턴스.
    """
    return NewsItem(
        id=str(uuid.uuid4()),
        title=str(raw.get("title", "")).strip(),
        link=str(raw.get("link", "")).strip(),
        source=str(raw.get("source", channel.get("name", ""))),
        published_at=str(raw.get("published_at", _now_iso())),
        summary=str(raw.get("summary", "")),
        full_text="",
        language=language,
        topic=topic or channel.get("topic", ""),
        is_scraped=False,
        notified_at=None,
        community_score=int(raw.get("community_score", 0)),
        research_channel_id=str(channel.get("id", "")),
    )

# ──────────────────────────────────────
# 유틸 정적 메서드
# ──────────────────────────────────────

def _extract_json_path(data: Any, path: str) -> Any:
    """점(.) 구분 경로로 중첩 JSON 값을 추출한다.

    Args:
        data: JSON 데이터 (dict 또는 list).
        path: 점 구분 경로. 예: "data.children" -> data["data"]["children"]

    Returns:
        추출된 값. 경로를 찾을 수 없으면 None.

    Examples:
        _extract_json_path({"data": {"children": [1, 2]}}, "data.children")
        # -> [1, 2]
    """
    if not path:
        return data

    parts = path.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit():
            idx = int(part)
            current = current[idx] if idx < len(current) else None
        else:
            return None
        if current is None:
            return None
    return current

def _map_fields(raw_item: dict, field_map: dict) -> dict:
    """field_map 기반으로 raw 데이터를 NewsItem 필드로 매핑한다.

    field_map 값 형식:
        - "'literal_value'"  : 작은따옴표로 감싸면 고정 문자열 반환
        - "data.title"       : 점 구분 경로로 raw_item에서 추출

    Args:
        raw_item: API 응답의 단일 아이템 dict.
        field_map: { "newsitem_field": "raw_path_or_literal" } 매핑.

    Returns:
        매핑 결과 dict.

    Examples:
        _map_fields(
            {"data": {"title": "Hello", "url": "http://..."}},
            {"title": "data.title", "link": "data.url",
             "source": "'Reddit'"}
        )
        # -> {"title": "Hello", "link": "http://...", "source": "Reddit"}
    """
    result: dict = {}
    for target_field, spec in field_map.items():
        if not isinstance(spec, str):
            result[target_field] = spec
            continue

        # 리터럴 값: 'value' 형식
        if spec.startswith("'") and spec.endswith("'") and len(spec) >= 2:
            result[target_field] = spec[1:-1]
            continue

        # JSON 경로 추출
        value = _extract_json_path(raw_item, spec)
        result[target_field] = value if value is not None else ""

    return result


# ──────────────────────────────────────
# Playwright 필드 추출 헬퍼
# ──────────────────────────────────────


