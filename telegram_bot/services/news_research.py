"""뉴스 심층 리서치 — news_scraper.py 에서 분리.

원본 뉴스 + 관련 기사 → 교차 검증된 ResearchResult.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from telegram_bot.models import NewsItem, ResearchResult

logger = logging.getLogger(__name__)


async def research_news(scraper, news_item: NewsItem) -> ResearchResult:
    """원본 뉴스 기사를 기반으로 관련 뉴스를 추가 수집하고 교차 분석한다.

    1. 원본 기사 본문이 없으면 스크래핑
    2. 제목 + 본문에서 핵심 키워드 추출
    3. 키워드로 Google News 검색 RSS 수집 (3~5건)
    4. 관련 기사 본문 스크래핑
    5. 공통 팩트 및 상충 정보 분석
    6. ResearchResult 반환

    Args:
        news_item: 원본 뉴스 아이템

    Returns:
        ResearchResult (combined_text = 대본 생성 입력용)
    """
    # 1. 원본 기사 본문 확보
    full_text = news_item.full_text
    if not full_text:
        logger.info(f"원본 기사 스크래핑 시작: {news_item.link}")
        full_text = await scraper.scrape_article(news_item.link)

    # 2. 키워드 추출
    keywords = _extract_keywords(news_item.title, full_text, max_keywords=5)
    logger.info(f"추출된 키워드: {keywords}")

    if not keywords:
        # 키워드가 없으면 제목에서 단어 2개 사용
        title_words = re.findall(r"[a-zA-Z가-힣]{3,}", news_item.title)
        keywords = title_words[:3]

    # 3. 키워드로 관련 뉴스 검색 (상위 2~3개 키워드 조합)
    search_query = " ".join(keywords[:3])
    related_articles: list[dict] = []

    search_url_pattern = RSS_URL_PATTERNS["SEARCH"]
    search_url = search_url_pattern.format(
        query=search_query,
        lang=news_item.language or DEFAULT_NEWS_LANGUAGE,
        country=DEFAULT_NEWS_COUNTRY,
    )

    try:
        feed = await asyncio.wait_for(
            asyncio.to_thread(feedparser.parse, search_url),
            timeout=15.0,
        )
        entries = feed.entries[:6]  # 최대 6건 후보 (중복/원본 제외 후 3~5건 확보)
    except asyncio.TimeoutError:
        logger.warning(f"관련 뉴스 검색 RSS 타임아웃 (query={search_query})")
        entries = []
    except Exception as exc:
        logger.warning(f"관련 뉴스 검색 실패 (query={search_query}): {exc}")
        entries = []

    # 원본 뉴스 링크 기록 (제외용)
    seen_links = {news_item.link}

    for entry in entries:
        if len(related_articles) >= 5:
            break

        link = entry.get("link", "")
        if not link or link in seen_links:
            continue

        # 원본과 제목 유사도가 너무 높으면 스킵 (동일 뉴스 변형)
        entry_title = entry.get("title", "")
        if is_similar_title(news_item.title, entry_title, threshold=0.85):
            logger.debug(f"유사 제목 스킵: {entry_title}")
            seen_links.add(link)
            continue

        seen_links.add(link)

        # 관련 기사 본문 스크래핑
        logger.info(f"관련 기사 스크래핑: {link}")
        article_text = await scraper.scrape_article(link)

        source = entry.get("source", {}).get("title", "")
        if not source and " - " in entry_title:
            source = entry_title.rsplit(" - ", 1)[-1].strip()
            entry_title = entry_title.rsplit(" - ", 1)[0].strip()

        related_articles.append({
            "title": entry_title,
            "source": source,
            "summary": entry.get("summary", "")[:500],
            "url": link,
            "full_text": article_text[:3000],
        })

    logger.info(f"관련 기사 수집 완료: {len(related_articles)}건")

    # 4. 교차 분석: 공통 팩트 vs 상충 정보
    cross_check_summary, background_info = _analyze_articles(
        original_title=news_item.title,
        original_text=full_text,
        related=related_articles,
    )

    # 5. combined_text 구성 (대본 생성 LLM 입력용)
    combined_parts = [
        f"[원본 뉴스]\n제목: {news_item.title}\n출처: {news_item.source}\n\n{full_text[:2000]}",
    ]
    for i, art in enumerate(related_articles, start=1):
        combined_parts.append(
            f"\n[관련 뉴스 {i}]\n제목: {art['title']}\n출처: {art['source']}\n\n{art['full_text'][:1000]}"
        )
    if cross_check_summary:
        combined_parts.append(f"\n[교차 분석]\n{cross_check_summary}")
    if background_info:
        combined_parts.append(f"\n[배경 정보]\n{background_info}")

    combined_text = "\n".join(combined_parts)

    return ResearchResult(
        original_news=news_item,
        related_articles=related_articles,
        keywords=keywords,
        cross_check_summary=cross_check_summary,
        background_info=background_info,
        combined_text=combined_text,
    )

# ──────────────────────────────────────
# 자동 모니터링
# ──────────────────────────────────────



def _analyze_articles(
    original_title: str,
    original_text: str,
    related: list[dict],
) -> tuple[str, str]:
    """관련 기사들과 교차 분석하여 공통 팩트 및 상충 정보를 요약한다.

    단순 텍스트 분석 (LLM 미사용):
    - 공통 키워드 빈도 기반으로 핵심 팩트 추정
    - 수치/날짜 표현에서 불일치 패턴 탐지

    Args:
        original_title: 원본 뉴스 제목.
        original_text: 원본 뉴스 본문.
        related: 관련 기사 딕셔너리 리스트.

    Returns:
        (cross_check_summary, background_info) 튜플.
    """
    if not related:
        return "", ""

    # 숫자/수치 패턴 추출 (불일치 탐지용)
    number_pattern = re.compile(r"\b\d+(?:[,\.]\d+)*(?:\s*(?:%|억|조|만|천|백|달러|원|명|건|개))?")

    original_numbers = set(number_pattern.findall(original_text))
    conflicting_numbers: list[str] = []

    sources_covered: list[str] = []
    for art in related:
        if art.get("source"):
            sources_covered.append(art["source"])
        art_numbers = set(number_pattern.findall(art.get("full_text", "")))
        # 원본에 없는 수치가 관련 기사에 등장하면 상충 후보
        new_numbers = art_numbers - original_numbers
        if new_numbers:
            conflicting_numbers.extend(list(new_numbers)[:3])

    # 공통 사실 요약
    cross_check_parts: list[str] = []
    cross_check_parts.append(
        f"총 {len(related)}개 언론사에서 관련 기사를 확인했습니다. "
        f"({', '.join(sources_covered[:5])})"
    )
    if conflicting_numbers:
        unique_conflicts = list(dict.fromkeys(conflicting_numbers))[:5]
        cross_check_parts.append(
            f"추가 수치 정보: {', '.join(unique_conflicts)}"
        )

    cross_check_summary = " ".join(cross_check_parts)

    # 배경 정보: 관련 기사들의 요약 취합
    background_parts: list[str] = []
    for art in related[:3]:
        if art.get("summary"):
            background_parts.append(f"- {art['source']}: {art['summary'][:200]}")

    background_info = "\n".join(background_parts)

    return cross_check_summary, background_info


# ──────────────────────────────────────
# 싱글턴
