"""커뮤니티 시그널 서비스: 커뮤니티 반응 기반 뉴스 랭킹."""

import logging
import re
from datetime import datetime, timezone
from typing import Any

from database import repository as repo

logger = logging.getLogger(__name__)

# 한국어 접미사 제거용 패턴 (is_similar_title에서 재사용)
_KO_SUFFIXES = re.compile(r"(이|가|은|는|을|를|의|에|에서|로|으로|와|과|도|만|부터|까지|한|이다)$")


def _is_similar_title(title1: str, title2: str, threshold: float = 0.6) -> bool:
    """두 제목의 자카드 유사도를 계산하여 threshold 이상이면 True 반환.

    news_scraper.py의 is_similar_title과 동일한 로직.
    커뮤니티 시그널 계산 시 동일 주제 뉴스 집계에 사용.
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


def _recency_factor(created_at: str, hours: int) -> float:
    """최신성 점수 계산 (0.0 ~ 1.0).

    hours 범위 내에서 최신일수록 1.0에 가깝고 오래될수록 0.0에 가까움.

    Args:
        created_at: ISO 8601 형식의 생성일시.
        hours: 기준 시간 범위.

    Returns:
        최신성 점수 (0.0 ~ 1.0).
    """
    if not created_at:
        return 0.0
    try:
        now = datetime.now(timezone.utc)
        if "+" not in created_at and "Z" not in created_at and not created_at.endswith("+00:00"):
            # naive datetime 처리
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(created_at)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age_hours = (now - dt).total_seconds() / 3600.0
        if age_hours < 0:
            age_hours = 0.0
        # 시간 범위 내에서 선형 감소
        factor = max(0.0, 1.0 - (age_hours / hours))
        return round(factor, 4)
    except Exception:
        return 0.0


def _source_authority(source: str) -> float:
    """소스 공신력 점수 계산 (0.0 ~ 1.0).

    알려진 권위 있는 소스에 높은 점수 부여.

    Args:
        source: 뉴스 소스 이름 또는 도메인.

    Returns:
        공신력 점수 (0.0 ~ 1.0).
    """
    if not source:
        return 0.3

    source_lower = source.lower()

    # 최고 권위 소스 (1.0)
    top_tier = [
        "nature", "science", "arxiv", "ieee", "acm",
        "nytimes", "washingtonpost", "reuters", "bloomberg",
        "ft.com", "wsj", "economist",
    ]
    for name in top_tier:
        if name in source_lower:
            return 1.0

    # 높은 권위 소스 (0.8)
    high_tier = [
        "techcrunch", "venturebeat", "wired", "arstechnica",
        "theverge", "mit", "stanford", "openai", "google",
        "microsoft", "deepmind", "anthropic",
        "reddit", "hackernews", "ycombinator",
    ]
    for name in high_tier:
        if name in source_lower:
            return 0.8

    # 중간 권위 소스 (0.6)
    mid_tier = [
        "medium", "substack", "github", "huggingface",
        "towardsdatascience", "kdnuggets",
    ]
    for name in mid_tier:
        if name in source_lower:
            return 0.6

    return 0.3


def count_multi_source_mentions(
    title: str,
    domain_name: str,
    hours: int = 24,
) -> int:
    """같은 주제를 다룬 뉴스가 몇 개 소스에서 수집되었는지 계산.

    is_similar_title()을 사용하여 유사 제목의 뉴스를 찾고,
    고유한 소스(source 필드) 개수를 반환한다.

    Args:
        title: 기준 뉴스 제목.
        domain_name: 검색 도메인 이름 (예: 'ai', 'blockchain').
        hours: 최근 N시간 이내 기사만 검색.

    Returns:
        유사 주제를 다룬 고유 소스 수 (1 이상).
    """
    try:
        # 제목에서 핵심 단어 추출 (3글자 이상)
        words = re.findall(r"[a-zA-Z0-9가-힣]{3,}", title)
        if not words:
            return 1

        # 상위 3개 핵심 단어로 검색
        search_terms = words[:3]
        candidate_news = repo.search_domain_news_by_terms(
            domain_name=domain_name,
            terms=search_terms,
            hours=hours,
            limit=50,
        )

        # 유사 제목 뉴스의 고유 소스 집합
        similar_sources: set[str] = set()
        for news in candidate_news:
            candidate_title = news.get("title", "")
            if _is_similar_title(title, candidate_title):
                source = news.get("source", "unknown")
                if source:
                    similar_sources.add(source)

        # 최소 1 보장
        return max(1, len(similar_sources))

    except Exception as e:
        logger.warning(f"multi_source 카운팅 실패 ({title[:50]}): {e}")
        return 1


def rank_news_by_signals(
    domain_name: str,
    hours: int = 24,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """도메인 내 뉴스를 커뮤니티 시그널 기반으로 랭킹.

    점수 = community_score*0.4 + multi_source_count*0.3
           + recency_factor*0.2 + source_authority*0.1

    community_score: news_items.community_score 필드 (수집 시 설정).
    multi_source_count: 동일 주제를 다룬 소스 수.
    recency_factor: 최신성 (0.0 ~ 1.0).
    source_authority: 소스 공신력 (0.0 ~ 1.0).

    Args:
        domain_name: 도메인 이름 (예: 'ai', 'blockchain').
        hours: 최근 N시간 이내 기사만 대상.
        limit: 반환할 최대 뉴스 수.

    Returns:
        [{"news_item": dict, "rank_score": float,
          "signals": {"community": int, "multi_source": int,
                      "recency": float, "authority": float}}, ...]
        rank_score 내림차순으로 정렬.
    """
    try:
        # 도메인 내 최신 뉴스 수집 (빈 terms = 전체 조회는 미지원이므로 범용 단어로 대체)
        # 도메인 이름 자체를 검색어로 사용
        news_items = repo.search_domain_news_by_terms(
            domain_name=domain_name,
            terms=[domain_name],
            hours=hours,
            limit=limit * 5,  # 충분히 가져온 후 랭킹 후 잘라냄
        )

        if not news_items:
            logger.info(f"랭킹 대상 뉴스 없음 (domain={domain_name}, hours={hours})")
            return []

        ranked: list[dict[str, Any]] = []

        for news in news_items:
            title = news.get("title", "")
            source = news.get("source", "")
            created_at = news.get("created_at", "")

            # 시그널 계산
            community = int(news.get("community_score", 0))
            multi_source = count_multi_source_mentions(title, domain_name, hours)
            recency = _recency_factor(created_at, hours)
            authority = _source_authority(source)

            # 정규화: community_score는 최대 1000 기준으로 0~1 스케일링
            community_norm = min(1.0, community / 1000.0)
            # multi_source는 최대 10 기준
            multi_source_norm = min(1.0, multi_source / 10.0)

            # 가중 합산 점수
            rank_score = (
                community_norm * 0.4
                + multi_source_norm * 0.3
                + recency * 0.2
                + authority * 0.1
            )

            ranked.append({
                "news_item": news,
                "rank_score": round(rank_score, 6),
                "signals": {
                    "community": community,
                    "multi_source": multi_source,
                    "recency": recency,
                    "authority": authority,
                },
            })

        # rank_score 내림차순 정렬
        ranked.sort(key=lambda x: x["rank_score"], reverse=True)

        return ranked[:limit]

    except Exception as e:
        logger.error(f"rank_news_by_signals 실패 (domain={domain_name}): {e}")
        return []
