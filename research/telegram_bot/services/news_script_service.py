"""뉴스 대본 서비스

기존 script_writer 로직을 래핑하여 뉴스 특화 대본을 생성한다.
Claude CLI(동기)를 asyncio.to_thread로 비동기 래핑하여 사용한다.
실패 시 최대 2회 재시도한다.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from services.claude_utils import call_claude_cli, extract_json
from telegram_bot.constants import ANCHOR_CHARACTERS
from telegram_bot.models import ResearchResult

logger = logging.getLogger(__name__)

# 한국어 기준 쇼츠 발화 속도 (글자/초)
_CHARS_PER_SEC_SHORTS = 5.0

# Claude CLI 타임아웃 (초)
_CLAUDE_TIMEOUT = 120

# 최대 재시도 횟수
_MAX_RETRIES = 2


def _get_anchor_tone(anchor_name: str) -> str:
    """앵커 이름으로 캐릭터 톤/성격 설명을 반환한다."""
    char = ANCHOR_CHARACTERS.get(anchor_name)
    if not char:
        # case-insensitive 폴백
        for key, val in ANCHOR_CHARACTERS.items():
            if key.lower() == anchor_name.lower():
                return val["tone"]
    if char:
        return char["tone"]
    return "신뢰감 있고 차분한 뉴스 진행 스타일"


def _calc_target_chars(target_duration: int) -> int:
    """목표 길이(초)를 한국어 글자 수로 변환한다.

    한국어 기준 초당 3.5~4글자. 쇼츠는 약 4글자/초로 산정.
    """
    return int(target_duration * 4)


def _build_script_prompt(
    research: ResearchResult,
    anchor_name: str,
    target_duration: int,
    feedback: Optional[str] = None,
) -> str:
    """뉴스 대본 생성 프롬프트를 구성한다.

    Args:
        research: 리서치 결과 (원본 뉴스 + 관련 뉴스 종합)
        anchor_name: 앵커 캐릭터 이름
        target_duration: 목표 길이 (초)
        feedback: 이전 대본에 대한 사용자 피드백 (재생성 시)

    Returns:
        Claude CLI에 전달할 프롬프트 문자열
    """
    anchor_tone = _get_anchor_tone(anchor_name)
    target_chars = _calc_target_chars(target_duration)

    original = research.original_news
    news_source = original.source or "출처 불명"
    news_title = original.title or ""
    news_text = (original.full_text or original.summary or "")[:3000]

    # 관련 기사 요약 구성
    related_parts: list[str] = []
    for idx, article in enumerate(research.related_articles, 1):
        title = article.get("title", "")
        source = article.get("source", "")
        summary = article.get("summary", "")
        url = article.get("url", "")
        related_parts.append(
            f"[관련 {idx}] {title} ({source})\n{summary}"
            + (f"\n출처: {url}" if url else "")
        )
    related_text = "\n\n".join(related_parts) if related_parts else "(관련 기사 없음)"

    # 키워드 목록
    keywords_str = ", ".join(research.keywords) if research.keywords else ""

    # 배경/맥락 정보
    background = research.background_info or ""
    cross_check = research.cross_check_summary or ""

    parts = [
        "당신은 한국어 뉴스 쇼츠 대본 작가입니다.",
        "",
        f"앵커: {anchor_name}",
        f"앵커 스타일: {anchor_tone}",
        f"목표 길이: {target_duration}초 (YouTube Shorts)",
        f"목표 글자 수: 약 {target_chars}자 (한국어 기준 초당 4글자)",
        "",
        "=== 원본 뉴스 ===",
        f"제목: {news_title}",
        f"출처: {news_source}",
        f"내용:",
        f'"""',
        news_text,
        f'"""',
        "",
        "=== 리서치 결과 ===",
        "관련 기사:",
        related_text,
    ]

    if keywords_str:
        parts += ["", f"핵심 키워드: {keywords_str}"]

    if background:
        parts += ["", "배경 및 맥락:", background[:1000]]

    if cross_check:
        parts += ["", "다양한 시각 종합:", cross_check[:1000]]

    # 논평 시간 계산 (목표의 25%, 최소 4초, 최대 8초)
    commentary_sec = max(4, min(8, target_duration // 4))
    news_sec = target_duration - commentary_sec
    news_chars = int(news_sec * 4)
    commentary_chars = int(commentary_sec * 4)

    parts += [
        "",
        "=== 작성 규칙 ===",
        "1. 단순 번역 금지 — 핵심 팩트만 발췌하여 짧고 임팩트 있게 전달",
        "2. YouTube 수익화 정책 준수: 분석·해설 콘텐츠 (원문 재게시 금지)",
        "",
        f"3. ★★★ 대본 2파트 구조 (총 {target_duration}초) ★★★",
        f"   [파트1: 팩트 요약] {news_sec}초 (약 {news_chars}자)",
        "   - 뉴스의 5W1H 중 가장 중요한 2~3가지만 전달",
        "   - 불필요한 배경 설명 제거, 핵심 사실만 압축",
        "   - 첫 문장은 훅 (질문형 or 충격적 사실)",
        f"   [파트2: 앵커 논평] {commentary_sec}초 (약 {commentary_chars}자)",
        "   - '제 생각에는', '이건 결국', '주목할 점은' 등으로 시작",
        "   - 앵커 개인의 시각/분석/전망을 담은 코멘터리",
        "   - 시청자가 '오' 하고 고개를 끄덕일 인사이트",
        "",
        "   content에 [팩트]와 [논평] 구분자를 넣지 마세요. 자연스럽게 이어지게.",
        "   단, 마지막 1~2문장이 논평이 되도록 구성하세요.",
        "",
        f"4. 앵커 {anchor_name}의 말투와 성격({anchor_tone})을 반영",
        "5. 출처를 자연스럽게 본문에 녹여 넣기 (예: 'BBC 보도에 따르면...')",
        "6. 1인칭 앵커 스타일, 카메라를 보고 말하듯 구어체",
        "7. 군더더기 없이 간결하게. 한 문장에 하나의 정보만.",
    ]

    if feedback:
        parts += [
            "",
            f"=== 이전 대본에 대한 피드백 ===",
            feedback,
            "위 피드백을 반영하여 대본을 다시 작성해주세요.",
        ]

    parts += [
        "",
        "JSON 형식으로 응답 (다른 텍스트 없이):",
        "{",
        '  "title": "영상 제목 (한국어, 30자 이내)",',
        '  "content": "완성된 대본 전문 (나레이션 텍스트만)",',
        '  "word_count": 글자_수_숫자,',
        '  "estimated_duration": 예상_초_숫자,',
        '  "sources": ["출처1", "출처2"],',
        '  "hooks": ["훅 포인트 설명"]',
        "}",
    ]

    return "\n".join(parts)


def _parse_script_result(
    data: dict,
    news_source: str,
    related_articles: list[dict],
) -> dict:
    """Claude 응답 JSON을 대본 결과 dict로 변환한다."""
    content = data.get("content", "")
    word_count = data.get("word_count") or len(content)
    estimated_duration = data.get("estimated_duration") or int(
        word_count / _CHARS_PER_SEC_SHORTS
    )

    # sources: Claude가 반환한 목록 + 원본 출처 보강
    sources: list[str] = data.get("sources", [])
    if news_source and news_source not in sources:
        sources.insert(0, news_source)

    # 관련 기사 출처도 추가 (중복 제거)
    for article in related_articles:
        src = article.get("source", "")
        if src and src not in sources:
            sources.append(src)

    return {
        "success": True,
        "title": data.get("title", ""),
        "content": content,
        "word_count": word_count,
        "estimated_duration": estimated_duration,
        "sources": sources,
        "hooks": data.get("hooks", []),
    }


async def _call_claude_with_retry(prompt: str) -> dict:
    """Claude CLI를 호출하고 실패 시 최대 2회 재시도한다.

    Args:
        prompt: Claude에 전달할 프롬프트

    Returns:
        extract_json으로 파싱된 응답 dict

    Raises:
        Exception: 모든 재시도 실패 시
    """
    last_error: Optional[Exception] = None

    for attempt in range(1, _MAX_RETRIES + 2):  # 최초 1회 + 재시도 2회 = 최대 3회
        try:
            logger.info(f"Claude CLI 호출 시도 {attempt}/{_MAX_RETRIES + 1}")
            raw = await asyncio.to_thread(call_claude_cli, prompt, _CLAUDE_TIMEOUT)
            data = extract_json(raw)
            return data
        except Exception as exc:
            last_error = exc
            logger.warning(f"Claude CLI 호출 실패 (시도 {attempt}): {exc}")
            if attempt <= _MAX_RETRIES:
                # 재시도 전 짧은 대기 (1초)
                await asyncio.sleep(1)

    raise RuntimeError(
        f"Claude CLI 호출이 {_MAX_RETRIES + 1}회 모두 실패했습니다: {last_error}"
    ) from last_error


async def generate_script(
    research: ResearchResult,
    anchor_name: str,
    target_duration: int = 60,
) -> dict:
    """리서치 결과를 기반으로 뉴스 쇼츠 대본을 생성한다.

    Args:
        research: 원본 뉴스 + 관련 뉴스 종합 리서치 결과
        anchor_name: 앵커 캐릭터 이름 (ANCHOR_CHARACTERS 키)
        target_duration: 목표 영상 길이 (초, 기본 60초)

    Returns:
        {
            "success": True,
            "title": "영상 제목",
            "content": "대본 전문",
            "word_count": 350,
            "estimated_duration": 55,
            "sources": ["Reuters", "BBC"],
            "hooks": ["훅 포인트"],
        }

    Raises:
        RuntimeError: Claude CLI 호출이 모든 재시도에서 실패한 경우
    """
    logger.info(
        f"뉴스 대본 생성 시작: anchor={anchor_name}, duration={target_duration}s, "
        f"news='{research.original_news.title[:50]}'"
    )

    prompt = _build_script_prompt(
        research=research,
        anchor_name=anchor_name,
        target_duration=target_duration,
        feedback=None,
    )

    data = await _call_claude_with_retry(prompt)

    result = _parse_script_result(
        data=data,
        news_source=research.original_news.source or "",
        related_articles=research.related_articles,
    )

    logger.info(
        f"뉴스 대본 생성 완료: title='{result['title']}', "
        f"word_count={result['word_count']}, duration={result['estimated_duration']}s"
    )
    return result


async def regenerate_script(
    research: ResearchResult,
    anchor_name: str,
    target_duration: int = 60,
    feedback: str = "",
) -> dict:
    """사용자 피드백을 반영하여 뉴스 대본을 재생성한다.

    Args:
        research: 원본 뉴스 + 관련 뉴스 종합 리서치 결과
        anchor_name: 앵커 캐릭터 이름
        target_duration: 목표 영상 길이 (초)
        feedback: 이전 대본에 대한 사용자 피드백 (빈 문자열이면 피드백 없이 재생성)

    Returns:
        generate_script와 동일한 구조의 dict

    Raises:
        RuntimeError: Claude CLI 호출이 모든 재시도에서 실패한 경우
    """
    log_msg = (
        f"뉴스 대본 재생성 시작: anchor={anchor_name}, duration={target_duration}s"
    )
    if feedback:
        log_msg += f", feedback='{feedback[:50]}'"
    logger.info(log_msg)

    prompt = _build_script_prompt(
        research=research,
        anchor_name=anchor_name,
        target_duration=target_duration,
        feedback=feedback if feedback else None,
    )

    data = await _call_claude_with_retry(prompt)

    result = _parse_script_result(
        data=data,
        news_source=research.original_news.source or "",
        related_articles=research.related_articles,
    )

    logger.info(
        f"뉴스 대본 재생성 완료: title='{result['title']}', "
        f"word_count={result['word_count']}, duration={result['estimated_duration']}s"
    )
    return result


# ---------------------------------------------------------------------------
# 설계서 M8 호환 함수 (generate_news_script)
# news.py 핸들러가 단순 인터페이스를 원할 경우 사용 가능
# ---------------------------------------------------------------------------


async def generate_news_script(
    news_text: str,
    news_title: str,
    news_source: str,
    anchor_name: str,
    target_duration: int = 60,
    language: str = "ko",
) -> dict:
    """뉴스 텍스트를 쇼츠 대본으로 변환한다 (설계서 M8 호환 인터페이스).

    ResearchResult 없이 원본 뉴스 텍스트만으로 대본을 생성할 때 사용한다.

    Args:
        news_text: 원본 뉴스 본문
        news_title: 원본 뉴스 제목
        news_source: 원본 뉴스 출처
        anchor_name: 앵커 캐릭터 이름
        target_duration: 목표 길이 (초)
        language: 출력 언어 ('ko' 또는 'en')

    Returns:
        {
            "success": True,
            "title": "...",
            "content": "...",
            "word_count": 350,
            "estimated_duration": 55,
            "sources": ["Reuters"],
        }
    """
    from telegram_bot.models import NewsItem, ResearchResult

    # 최소 ResearchResult 구성
    dummy_news = NewsItem(
        id="",
        title=news_title,
        link="",
        source=news_source,
        published_at="",
        summary=news_text[:500],
        full_text=news_text,
        language=language,
    )
    dummy_research = ResearchResult(
        original_news=dummy_news,
        related_articles=[],
        keywords=[],
        cross_check_summary="",
        background_info="",
        combined_text=news_text,
    )

    result = await generate_script(
        research=dummy_research,
        anchor_name=anchor_name,
        target_duration=target_duration,
    )

    # 설계서 M8 반환 형식에 source_credit 추가
    result["source_credit"] = news_source
    return result
