"""텔레그램 봇 뉴스 파이프라인 데이터 모델"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    """현재 시각을 ISO 8601 문자열로 반환 (UTC)."""
    return datetime.now(tz=timezone.utc).isoformat()


@dataclass
class NewsItem:
    """뉴스 기사 단위 데이터 모델.

    RSS 파싱 결과 또는 스크래핑된 기사 본문을 담는다.
    """

    id: str
    title: str
    link: str
    source: str
    published_at: str
    summary: str
    full_text: str = ""
    language: str = "en"
    topic: str = ""
    is_scraped: bool = False
    notified_at: Optional[str] = None
    community_score: int = 0
    research_channel_id: str = ""


@dataclass
class NewsProject:
    """뉴스 기반 쇼츠 프로젝트 데이터 모델.

    뉴스 선택 ~ 최종 영상 전송까지 전체 파이프라인 상태를 추적한다.

    status 값:
        created      - 프로젝트 최초 생성
        researching  - 관련 뉴스 심층 리서치 진행 중
        scripting    - 대본 생성 중
        scenario     - 시나리오 생성 중
        generating   - TTS / Grok 영상 생성 중
        composing    - FFmpeg 합성 중
        verifying    - 품질 검증 단계
        complete     - 완료 (영상 전송까지)
        failed       - 오류로 중단
    """

    id: str
    news_item_id: str
    telegram_chat_id: int
    created_at: str
    updated_at: str
    project_id: Optional[str] = None
    anchor_character: str = ""
    status: str = "created"
    script_content: str = ""
    scenario_json: str = ""
    research_data: str = ""
    related_news_ids: str = ""
    final_video_path: str = ""
    thumbnail_path: str = ""
    title: str = ""
    description: str = ""
    tags: str = ""
    error_message: str = ""


@dataclass
class ResearchResult:
    """관련 뉴스 심층 리서치 결과 데이터 모델.

    원본 뉴스 + 관련 뉴스 3~5건의 종합 분석 결과를 담는다.
    combined_text 는 대본 생성 시 LLM 입력 소스로 사용된다.

    related_articles 각 항목 구조:
        {
            "title": str,
            "source": str,
            "summary": str,
            "url": str,
        }
    """

    original_news: NewsItem
    related_articles: list[dict]
    keywords: list[str]
    cross_check_summary: str
    background_info: str
    combined_text: str


# ---------------------------------------------------------------------------
# 유틸 함수
# ---------------------------------------------------------------------------


def new_news_item(**kwargs) -> NewsItem:
    """NewsItem 을 생성한다. id 는 UUID4 로 자동 생성된다.

    Args:
        **kwargs: NewsItem 필드 값. id 를 제외한 모든 필수 필드를 포함해야 한다.

    Returns:
        id 가 채워진 NewsItem 인스턴스.

    Example:
        item = new_news_item(
            title="Breaking News",
            link="https://example.com/news/1",
            source="Reuters",
            published_at="2026-03-29T00:00:00+00:00",
            summary="Summary text here.",
        )
    """
    kwargs.setdefault("id", str(uuid.uuid4()))
    return NewsItem(**kwargs)


def new_news_project(**kwargs) -> NewsProject:
    """NewsProject 를 생성한다.

    id, created_at, updated_at 은 자동으로 설정된다.
    이미 값이 제공된 경우 해당 값을 우선한다.

    Args:
        **kwargs: NewsProject 필드 값. id / created_at / updated_at 을 제외한
                  모든 필수 필드(news_item_id, telegram_chat_id)를 포함해야 한다.

    Returns:
        id / created_at / updated_at 이 채워진 NewsProject 인스턴스.

    Example:
        project = new_news_project(
            news_item_id="some-uuid",
            telegram_chat_id=123456789,
        )
    """
    now = _now_iso()
    kwargs.setdefault("id", str(uuid.uuid4()))
    kwargs.setdefault("created_at", now)
    kwargs.setdefault("updated_at", now)
    return NewsProject(**kwargs)
