"""
뉴스 스크래퍼 서비스

Google News RSS 수집 + Playwright 기사 본문 스크래핑 + 관련 뉴스 심층 리서치.
"""

from __future__ import annotations

import asyncio
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Callable, Awaitable, Optional

if TYPE_CHECKING:
    from telegram_bot.services.recipe_executor import RecipeExecutor

import feedparser
from playwright.async_api import async_playwright, Browser, Playwright

from database.repository import (
    delete_old_news,
    get_channels_due_for_fetch,
    is_news_duplicate,
    record_channel_fetch_result,
    save_news_item,
)
from telegram_bot.constants import (
    CATEGORY_RSS_FEEDS,
    CATEGORY_TO_GOOGLE_TOPIC,
    DEFAULT_NEWS_COUNTRY,
    DEFAULT_NEWS_LANGUAGE,
    DEFAULT_NEWS_LIMIT,
    RSS_URL_PATTERNS,
)
from telegram_bot.models import NewsItem, ResearchResult

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    """현재 시각을 ISO 8601 문자열로 반환 (UTC)."""
    return datetime.now(tz=timezone.utc).isoformat()


def _parse_rss_datetime(published: str) -> str:
    """feedparser에서 반환되는 날짜 문자열을 ISO 8601로 변환.

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


_KO_SUFFIXES = re.compile(r"(은|는|이|가|을|를|에|의|로|와|과|도|만|에서|으로|부터|까지|라고|라는|에서는|으로는)$")

# 유대인 관련 필터 키워드 (Grok API 거부 방지) — 루프 외부 모듈 상수로 정의
_JEWISH_FILTER = ["jewish", "jew ", "synagogue", "antisemit", "holocaust", "hebrew", "zionist"]


def is_similar_title(title1: str, title2: str, threshold: float = 0.7) -> bool:
    """두 제목의 자카드 유사도를 계산하여 threshold 이상이면 True 반환.

    자카드 유사도: |교집합| / |합집합| (단어 단위 집합 비교)
    24시간 내 동일 뉴스 재알림 방지에 사용.
    """
    def _tokenize(text: str) -> set[str]:
        tokens = set(re.findall(r"[a-zA-Z0-9가-힣]+", text.lower()))
        return {_KO_SUFFIXES.sub("", t) for t in tokens if len(t) >= 2}

    words1 = _tokenize(title1)
    words2 = _tokenize(title2)

    if not words1 or not words2:
        return False

    intersection = words1 & words2
    union = words1 | words2
    similarity = len(intersection) / len(union)
    return similarity >= threshold


def _extract_keywords(title: str, full_text: str, max_keywords: int = 8) -> list[str]:
    """제목 + 본문에서 핵심 키워드 추출.

    고유명사(대문자 시작), 한글 단어, 고빈도 명사를 우선으로 추출.
    """
    combined = f"{title} {full_text}"

    # 영문 고유명사 (대문자 시작 2자 이상)
    proper_nouns = re.findall(r"\b[A-Z][a-zA-Z]{1,}\b", combined)

    # 한글 단어 (2자 이상)
    korean_words = re.findall(r"[가-힣]{2,}", combined)

    # 숫자 포함 복합어 (연도, 수치 포함 표현)
    numbers = re.findall(r"\b\d{4}\b", combined)  # 연도

    # 빈도 카운트 (영문 소문자 일반화)
    word_freq: dict[str, int] = {}
    for word in re.findall(r"[a-zA-Z0-9가-힣]{3,}", combined):
        key = word.lower()
        word_freq[key] = word_freq.get(key, 0) + 1

    # 고유명사 우선 정렬
    candidates = list(dict.fromkeys(proper_nouns + korean_words + numbers))

    # 빈도 기반 추가 (상위 단어)
    freq_sorted = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    for word, _ in freq_sorted:
        if word not in [c.lower() for c in candidates]:
            candidates.append(word)
        if len(candidates) >= max_keywords * 2:
            break

    # 불용어 제거 (영문 불용어)
    stopwords = {
        "the", "and", "for", "that", "this", "with", "from", "are",
        "was", "has", "have", "had", "will", "been", "not", "but",
        "its", "also", "said", "says", "more", "new", "after",
    }
    filtered = [
        w for w in candidates
        if w.lower() not in stopwords and len(w) >= 2
    ]

    return filtered[:max_keywords]


class NewsScraper:
    """Google News RSS 수집 + Playwright 기사 본문 스크래핑.

    브라우저는 싱글턴으로 유지하며, context는 스크래핑마다 새로 생성한다.
    """

    def __init__(self) -> None:
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._browser_lock = asyncio.Lock()
        self._monitoring_task: Optional[asyncio.Task] = None
        self._stop_monitoring_event = asyncio.Event()
        self._recipe_executor: Optional["RecipeExecutor"] = None

    def _get_recipe_executor(self) -> "RecipeExecutor":
        """RecipeExecutor 싱글턴 반환 (지연 초기화)."""
        if self._recipe_executor is None:
            from telegram_bot.services.recipe_executor import RecipeExecutor
            self._recipe_executor = RecipeExecutor(news_scraper=self)
        return self._recipe_executor

    # ──────────────────────────────────────
    # 브라우저 생명주기
    # ──────────────────────────────────────

    async def startup(self) -> None:
        """Playwright headless chromium 브라우저 시작."""
        async with self._browser_lock:
            if self._browser is not None:
                return
            try:
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                    ],
                )
                logger.info("Playwright 브라우저 시작 완료")
            except Exception as exc:
                logger.error(f"Playwright 브라우저 시작 실패: {exc}")
                self._playwright = None
                self._browser = None
                raise

    async def shutdown(self) -> None:
        """Playwright 브라우저 종료."""
        async with self._browser_lock:
            if self._browser is not None:
                try:
                    await self._browser.close()
                except Exception as exc:
                    logger.warning(f"브라우저 close 오류: {exc}")
                finally:
                    self._browser = None

            if self._playwright is not None:
                try:
                    await self._playwright.stop()
                except Exception as exc:
                    logger.warning(f"Playwright stop 오류: {exc}")
                finally:
                    self._playwright = None

        logger.info("Playwright 브라우저 종료 완료")

    async def get_browser(self) -> Browser:
        """브라우저 싱글턴 반환. 아직 시작되지 않았으면 startup() 호출."""
        if self._browser is None:
            await self.startup()
        return self._browser  # type: ignore[return-value]

    # ──────────────────────────────────────
    # RSS 뉴스 수집
    # ──────────────────────────────────────

    async def fetch_news(
        self,
        topic: str = "TOP",
        language: str = DEFAULT_NEWS_LANGUAGE,
        country: str = DEFAULT_NEWS_COUNTRY,
        limit: int = DEFAULT_NEWS_LIMIT,
        search_query: str = "",
    ) -> list[NewsItem]:
        """뉴스를 수집하고 DB에 저장한다.

        분야 키(tech, economy 등)가 주어지면 해당 분야의 직접 RSS 피드를
        모두 병렬 수집한 뒤 Google News를 보조로 추가한다.
        기존 Google News 키(TOP, TECHNOLOGY 등)도 하위 호환 유지.

        Args:
            topic: 분야 키 또는 Google News 토픽 키
            language: 언어 코드 (en, ko 등)
            country: 국가 코드 (US, KR 등)
            limit: 최대 수집 건수
            search_query: 검색 쿼리 (지정 시 topic 무시, SEARCH 패턴 사용)

        Returns:
            중복 제외 후 저장된 NewsItem 리스트.
        """
        # 키워드 검색 모드
        if search_query:
            url_pattern = RSS_URL_PATTERNS["SEARCH"]
            url = url_pattern.format(query=search_query, lang=language, country=country)
            return await self._fetch_single_feed(
                url=url,
                topic=f"SEARCH:{search_query[:30]}",
                source_name="Google News",
                language=language,
                limit=limit,
            )

        topic_lower = topic.lower()

        # 분야 키(tech, economy 등) → 다중 RSS 병렬 수집
        if topic_lower in CATEGORY_RSS_FEEDS:
            return await self._fetch_category_news(
                category=topic_lower,
                language=language,
                country=country,
                limit=limit,
            )

        # 기존 Google News 키(TOP, TECHNOLOGY 등) → 하위 호환
        url_pattern = RSS_URL_PATTERNS.get(topic.upper(), RSS_URL_PATTERNS["TOP"])
        url = url_pattern.format(lang=language, country=country)
        return await self._fetch_single_feed(
            url=url,
            topic=topic,
            source_name="Google News",
            language=language,
            limit=limit,
        )

    async def _fetch_category_news(
        self,
        category: str,
        language: str,
        country: str,
        limit: int,
    ) -> list[NewsItem]:
        """분야별 직접 RSS + Google News 보조를 병렬 수집한다."""
        feeds = CATEGORY_RSS_FEEDS.get(category, [])
        google_topic = CATEGORY_TO_GOOGLE_TOPIC.get(category)

        # 병렬 수집 태스크 구성
        tasks: list[asyncio.Task] = []
        per_feed_limit = max(limit // max(len(feeds) + 1, 1), 5)

        for feed_info in feeds:
            tasks.append(
                asyncio.create_task(
                    self._fetch_single_feed(
                        url=feed_info["url"],
                        topic=category,
                        source_name=feed_info["name"],
                        language=language,
                        limit=per_feed_limit,
                    )
                )
            )

        # Google News 보조 추가
        if google_topic and google_topic in RSS_URL_PATTERNS:
            google_url = RSS_URL_PATTERNS[google_topic].format(
                lang=language, country=country,
            )
            tasks.append(
                asyncio.create_task(
                    self._fetch_single_feed(
                        url=google_url,
                        topic=category,
                        source_name="Google News",
                        language=language,
                        limit=per_feed_limit,
                    )
                )
            )

        if not tasks:
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 병합 (중복 링크 제거, limit 적용)
        seen_links: set[str] = set()
        merged: list[NewsItem] = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"RSS 수집 실패: {result}")
                continue
            for item in result:
                if item.link not in seen_links:
                    seen_links.add(item.link)
                    merged.append(item)

        logger.info(
            f"fetch_category_news 완료: category={category}, "
            f"소스={len(feeds)}+Google, 수집={len(merged)}건"
        )
        return merged[:limit]

    async def _fetch_single_feed(
        self,
        url: str,
        topic: str,
        source_name: str,
        language: str,
        limit: int,
    ) -> list[NewsItem]:
        """단일 RSS 피드에서 뉴스를 수집하고 DB에 저장한다."""
        try:
            feed = await asyncio.wait_for(
                asyncio.to_thread(feedparser.parse, url),
                timeout=15.0,
            )
        except asyncio.TimeoutError:
            logger.warning(f"RSS 타임아웃 (source={source_name}, url={url})")
            return []
        except Exception as exc:
            logger.error(f"RSS 파싱 실패 (source={source_name}, url={url}): {exc}")
            return []

        items: list[NewsItem] = []
        for entry in feed.entries[:limit]:
            link = entry.get("link", "")
            if not link:
                continue

            title = entry.get("title", "")
            # Google News RSS 제목에 포함된 " - 언론사명" 패턴 제거
            if " - " in title:
                title_parts = title.rsplit(" - ", 1)
                source_from_title = title_parts[-1].strip()
                title = title_parts[0].strip()
            else:
                source_from_title = ""

            # 시간 필터: 6시간 이내 뉴스만 수집
            published_raw = entry.get("published", "")
            published_at = _parse_rss_datetime(published_raw)
            if published_at:
                try:
                    pub_dt = datetime.fromisoformat(published_at)
                    if pub_dt.tzinfo is None:
                        pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                    age = datetime.now(tz=timezone.utc) - pub_dt
                    if age > timedelta(hours=6):
                        logger.debug(f"오래된 뉴스 스킵 ({age.total_seconds()/3600:.1f}h): {title[:40]}")
                        continue
                except Exception:
                    pass  # 파싱 실패 시 필터 스킵

            # 중복 체크 (링크 + 제목 유사도)
            if is_news_duplicate(link, title):
                logger.debug(f"중복 뉴스 스킵: {title[:40]}")
                continue

            source = (
                entry.get("source", {}).get("title", "")
                or source_from_title
                or source_name
            )
            summary = entry.get("summary", "")

            # 유대인 관련 뉴스 필터링 (Grok API 거부 방지)
            title_lower = title.lower()
            if any(w in title_lower for w in _JEWISH_FILTER):
                logger.info(f"뉴스 필터링 (유대인 관련): {title[:50]}")
                continue

            news_id = str(uuid.uuid4())
            now = _now_iso()

            item = NewsItem(
                id=news_id,
                title=title,
                link=link,
                source=source,
                published_at=published_at,
                summary=summary,
                full_text="",
                language=language,
                topic=topic,
                is_scraped=False,
                notified_at=None,
            )

            try:
                save_news_item({
                    "id": news_id,
                    "title": title,
                    "link": link,
                    "source": source,
                    "published_at": published_at,
                    "summary": summary,
                    "full_text": "",
                    "language": language,
                    "topic": topic,
                    "rss_feed_url": url,
                    "is_scraped": False,
                    "notified_at": None,
                    "created_at": now,
                })
            except Exception as exc:
                logger.warning(f"뉴스 DB 저장 실패 ({news_id}): {exc}")

            items.append(item)

        logger.info(f"_fetch_single_feed 완료: source={source_name}, 수집={len(items)}건")
        return items

    # ──────────────────────────────────────
    # 기사 본문 스크래핑
    # ──────────────────────────────────────

    async def scrape_article(self, url: str) -> str:
        """기사 URL에서 본문을 추출한다.

        Playwright headless chromium으로 JS 렌더링 후 기사 본문 셀렉터를 순서대로 시도.
        실패 시 빈 문자열 반환 (에러 로깅).

        Args:
            url: 기사 URL (Google News 리다이렉트 URL 포함)

        Returns:
            추출된 본문 텍스트. 실패 시 빈 문자열.
        """
        browser = await self.get_browser()
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=10000)

            # 기사 본문 셀렉터 우선순위 (일반적인 뉴스 사이트 패턴)
            selectors = [
                "article",
                "[itemprop='articleBody']",
                ".article-body",
                ".story-body",
                ".post-content",
                ".article-content",
                ".news-content",
                ".entry-content",
                "#article-body",
                "#article_content",
                "main article",
                "main",
            ]

            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        texts = []
                        for el in elements:
                            try:
                                text = await el.inner_text()
                                if text.strip():
                                    texts.append(text.strip())
                            except Exception:
                                continue
                        full_text = "\n".join(texts)
                        if len(full_text) > 100:
                            return full_text[:5000]  # 최대 5000자 제한
                except Exception:
                    continue

            # 폴백: p 태그 수집
            try:
                p_elements = await page.query_selector_all("p")
                if p_elements:
                    texts = []
                    for el in p_elements:
                        try:
                            text = await el.inner_text()
                            if text.strip() and len(text.strip()) > 20:
                                texts.append(text.strip())
                        except Exception:
                            continue
                    p_text = "\n".join(texts)
                    if len(p_text) > 100:
                        return p_text[:5000]
            except Exception:
                pass

            # 최종 폴백: body 전체 텍스트
            try:
                body_text = await page.inner_text("body")
                return body_text[:3000] if body_text else ""
            except Exception:
                return ""

        except Exception as exc:
            logger.warning(f"scrape_article 실패 (url={url}): {exc}")
            return ""
        finally:
            try:
                await context.close()
            except Exception:
                pass

    # ──────────────────────────────────────
    # 관련 뉴스 심층 리서치 (services/news_research.py 위임)
    # ──────────────────────────────────────

    async def research_news(self, news_item):
        from telegram_bot.services.news_research import research_news as _impl
        return await _impl(self, news_item)

    async def start_monitoring(
        self,
        callback: Callable[[list[NewsItem]], Awaitable[None]],
        topic: str = "TOP",
        language: str = DEFAULT_NEWS_LANGUAGE,
        country: str = DEFAULT_NEWS_COUNTRY,
        interval_seconds: int = 3600,
    ) -> None:
        """주기적으로 RSS를 체크하여 새 뉴스 감지 시 callback을 호출한다.

        Args:
            callback: 새 뉴스 리스트를 인자로 받는 async 콜백 함수.
            topic: 모니터링할 RSS 토픽.
            language: 언어 코드.
            country: 국가 코드.
            interval_seconds: 체크 간격 (기본 1시간).
        """
        if self._monitoring_task is not None and not self._monitoring_task.done():
            logger.warning("모니터링이 이미 실행 중입니다.")
            return

        self._stop_monitoring_event.clear()

        async def _monitor_loop() -> None:
            logger.info(
                f"뉴스 모니터링 시작: topic={topic}, interval={interval_seconds}s"
            )
            while not self._stop_monitoring_event.is_set():
                # 1) 다국어 TOP 토픽 병렬 수집 (en/ko/zh)
                _LANG_FEEDS = [
                    (language, country),          # 기본 (en/US)
                    ("ko", "KR"),                 # 한국어
                    ("zh-CN", "CN"),              # 중국어
                ]
                try:
                    all_new_items: list[NewsItem] = []
                    for lang, ctry in _LANG_FEEDS:
                        try:
                            items = await self.fetch_news(
                                topic=topic,
                                language=lang,
                                country=ctry,
                                limit=DEFAULT_NEWS_LIMIT,
                            )
                            if items:
                                all_new_items.extend(items)
                        except Exception as lang_exc:
                            logger.warning(f"뉴스 수집 실패 ({lang}/{ctry}): {lang_exc}")

                    if all_new_items:
                        logger.info(f"새 뉴스 {len(all_new_items)}건 감지 → 후처리 파이프라인")
                        from telegram_bot.services.news_processor import process_news
                        scored = await process_news(topic, all_new_items)
                        await callback(all_new_items, scored)
                except Exception as exc:
                    logger.error(f"모니터링 중 오류 발생: {exc}")

                # 2) 키워드별 RSS 수집
                await self._fetch_keyword_news(callback, language, country)

                # 3) 리서치 채널 수집
                await self._fetch_research_channels(callback)

                # 오래된 뉴스 정리 (12시간 초과)
                try:
                    await asyncio.to_thread(delete_old_news, 12)
                except Exception as exc:
                    logger.warning(f"오래된 뉴스 삭제 중 오류 (무시): {exc}")

                # interval_seconds 대기 (중단 이벤트 응답성 확보)
                try:
                    await asyncio.wait_for(
                        self._stop_monitoring_event.wait(),
                        timeout=float(interval_seconds),
                    )
                except asyncio.TimeoutError:
                    pass  # 정상: 타임아웃 후 다음 순환

            logger.info("뉴스 모니터링 종료")

        self._monitoring_task = asyncio.create_task(_monitor_loop())

    async def _fetch_keyword_news(
        self,
        callback: Callable[[list[NewsItem]], Awaitable[None]],
        language: str = DEFAULT_NEWS_LANGUAGE,
        country: str = DEFAULT_NEWS_COUNTRY,
    ) -> None:
        """managed_keywords 테이블의 활성 키워드별로 RSS 수집 + 텔레그램 알림."""
        try:
            from database.repository import (
                list_managed_keywords,
                save_news_verification,
                find_verification_by_title,
            )
            import json as _json

            keywords = await asyncio.to_thread(list_managed_keywords, True)  # active_only=True
            if not keywords:
                return

            for kw in keywords:
                try:
                    text = kw["text"]
                    synonyms_raw = kw.get("synonyms", "[]")
                    if isinstance(synonyms_raw, str):
                        synonyms = _json.loads(synonyms_raw)
                    else:
                        synonyms = synonyms_raw

                    # OR 쿼리 생성
                    all_terms = [text] + (synonyms or [])
                    query = "+OR+".join(t.replace(" ", "+") for t in all_terms if t)

                    new_items = await self.fetch_news(
                        search_query=query,
                        language="ko",
                        country="KR",
                        limit=10,
                    )

                    if new_items:
                        logger.info(f"[키워드:{text}] 새 뉴스 {len(new_items)}건 수집")

                        # Claude 관련성 검증 + DB 저장
                        relevant_items = []
                        for item in new_items:
                            cached = await asyncio.to_thread(
                                find_verification_by_title, kw["id"], item.title
                            )
                            if cached is not None:
                                if cached:
                                    relevant_items.append(item)
                            else:
                                # 새 뉴스 → 일단 관련으로 간주 (Claude 검증은 모달에서)
                                await asyncio.to_thread(
                                    save_news_verification, kw["id"], item.id, item.title, True
                                )
                                relevant_items.append(item)

                        # 후처리: 클러스터링 → 번역 → 중요도
                        scored = []
                        if relevant_items:
                            from telegram_bot.services.news_processor import process_news
                            scored = await process_news(text, relevant_items)
                            await callback(relevant_items, scored)

                except Exception as exc:
                    logger.warning(f"[키워드:{kw.get('text', '?')}] 수집 실패: {exc}")

        except Exception as exc:
            logger.warning(f"키워드별 뉴스 수집 실패: {exc}")

    async def _fetch_research_channels(
        self,
        callback: Callable[[list[NewsItem], list], Awaitable[None]],
    ) -> None:
        """research_channels 테이블의 수집 주기가 도래한 활성 채널에서 뉴스 수집.

        채널 목록을 priority 그룹별로 asyncio.gather 병렬 실행한다.
        """
        try:
            channels = await asyncio.to_thread(get_channels_due_for_fetch)
            if not channels:
                return

            executor = self._get_recipe_executor()

            tasks = [
                asyncio.create_task(
                    self._execute_channel(executor, channel, callback)
                )
                for channel in channels
            ]

            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as exc:
            logger.warning(f"리서치 채널 수집 실패: {exc}")

    async def _execute_channel(
        self,
        executor: "RecipeExecutor",
        channel: dict,
        callback: Callable[[list[NewsItem], list], Awaitable[None]],
    ) -> None:
        """단일 리서치 채널 실행 + 결과 처리."""
        channel_name = channel.get("name", channel.get("id", "?"))
        try:
            items = await executor.execute(channel)

            if items:
                # 중복 제거 + DB 저장
                new_items: list[NewsItem] = []
                for item in items:
                    if not is_news_duplicate(item.link, item.title):
                        try:
                            save_news_item({
                                "id": item.id,
                                "title": item.title,
                                "link": item.link,
                                "source": item.source,
                                "published_at": item.published_at,
                                "summary": item.summary,
                                "full_text": item.full_text,
                                "language": item.language,
                                "topic": item.topic,
                                "rss_feed_url": "",
                                "is_scraped": item.is_scraped,
                                "notified_at": item.notified_at,
                                "created_at": item.published_at or "",
                                "community_score": getattr(item, "community_score", 0),
                                "research_channel_id": getattr(item, "research_channel_id", ""),
                            })
                            new_items.append(item)
                        except Exception as save_exc:
                            logger.warning(f"[채널:{channel_name}] 뉴스 DB 저장 실패: {save_exc}")

                await asyncio.to_thread(
                    record_channel_fetch_result,
                    channel["id"], True, len(items)
                )

                if new_items:
                    logger.info(f"[채널:{channel_name}] {len(new_items)}건 수집 (중복제거 전 {len(items)}건)")
                    from telegram_bot.services.news_processor import process_news
                    scored = await process_news(channel.get("name", ""), new_items)
                    await callback(new_items, scored)
            else:
                await asyncio.to_thread(
                    record_channel_fetch_result,
                    channel["id"], True, 0
                )

        except Exception as exc:
            logger.warning(f"[채널:{channel_name}] 수집 실패: {exc}")
            try:
                await asyncio.to_thread(
                    record_channel_fetch_result,
                    channel["id"], False, 0, str(exc)
                )
            except Exception as record_exc:
                logger.warning(f"[채널:{channel_name}] 수집 결과 기록 실패: {record_exc}")

    async def stop_monitoring(self) -> None:
        """모니터링 루프를 중단한다."""
        self._stop_monitoring_event.set()
        if self._monitoring_task is not None:
            try:
                await asyncio.wait_for(self._monitoring_task, timeout=5.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                self._monitoring_task.cancel()
            finally:
                self._monitoring_task = None
        logger.info("뉴스 모니터링 중단 완료")


# ──────────────────────────────────────
# 내부 헬퍼
# ──────────────────────────────────────



# 싱글턴
news_scraper = NewsScraper()

# _analyze_articles 는 news_research.py 로 분리 — 호환 re-export
from telegram_bot.services.news_research import _analyze_articles  # noqa: E402, F401
