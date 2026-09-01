"""뉴스 후처리 파이프라인

수집된 뉴스를 정제하여 알림까지 처리한다.

1. 유사 뉴스 클러스터링 → 대표 1건만 선택
2. Claude 1회 호출로 전건 번역 + 중요도 스코어링
3. 중요도 순 정렬 → 상위 N건만 건바이건 알림
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

from telegram_bot.models import NewsItem
from telegram_bot.services.news_scraper import is_similar_title

logger = logging.getLogger(__name__)

# 유사도 임계값 (이 이상이면 같은 뉴스로 판정)
_SIMILARITY_THRESHOLD = 0.45

# 알림 최대 건수
_MAX_NOTIFY = 3

# 중요도 컷오프 (이 이상만 알림)
_IMPORTANCE_CUTOFF = 6

# .env.local 경로 (프로젝트 루트)
_ENV_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env.local")

# 번역 기능 ON/OFF / 백엔드 — 모듈 변수는 API 핸들러가 직접 수정 가능
# spawn 자식 프로세스는 main.py의 load_dotenv를 타지 않으므로 여기서 직접 로드
try:
    from dotenv import load_dotenv as _load_dotenv
    _load_dotenv(os.path.abspath(_ENV_FILE), override=True)
except Exception:
    pass

_TRANSLATION_ENABLED = os.environ.get("NEWS_TRANSLATE", "1") != "0"
_TRANSLATION_BACKEND = os.environ.get("NEWS_TRANSLATE_BACKEND", "gemma4")


def _read_translation_settings() -> tuple[bool, str]:
    """매 번역 호출 시 .env.local을 읽어 최신 설정을 반환한다.

    멀티프로세스(uvicorn --reload) 환경에서 API로 변경한 설정이
    자식 프로세스에 즉시 반영되도록 파일을 직접 읽는다.
    """
    enabled = _TRANSLATION_ENABLED  # 기본값: 모듈 변수
    backend = _TRANSLATION_BACKEND
    try:
        env_path = os.path.abspath(_ENV_FILE)
        if os.path.exists(env_path):
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("NEWS_TRANSLATE="):
                        val = line.split("=", 1)[1].strip()
                        enabled = val != "0"
                    elif line.startswith("NEWS_TRANSLATE_BACKEND="):
                        backend = line.split("=", 1)[1].strip()
    except Exception:
        pass
    return enabled, backend


# ──────────────────────────────────────
# 1. 유사 뉴스 클러스터링
# ──────────────────────────────────────

def cluster_similar_news(items: list[NewsItem]) -> list[NewsItem]:
    """유사 제목의 뉴스를 클러스터링하여 대표 1건만 반환한다.

    O(N²) 비교지만 보통 N < 30이므로 문제없다.
    같은 클러스터 내에서 source가 더 유명한(또는 먼저 수집된) 것을 대표로 선택.
    """
    if len(items) <= 1:
        return items

    clusters: list[list[NewsItem]] = []

    for item in items:
        placed = False
        for cluster in clusters:
            # 클러스터 대표(첫 번째)와 비교
            if is_similar_title(cluster[0].title, item.title, _SIMILARITY_THRESHOLD):
                cluster.append(item)
                placed = True
                break
        if not placed:
            clusters.append([item])

    # 각 클러스터에서 대표 선택 (제목이 가장 긴 것 = 더 상세한 기사)
    representatives: list[NewsItem] = []
    for cluster in clusters:
        # 대표: 제목이 가장 긴 것 (더 상세한 기사)
        rep = max(cluster, key=lambda x: len(x.title))
        representatives.append(rep)
        if len(cluster) > 1:
            others = [f"{it.source}" for it in cluster if it.id != rep.id]
            logger.info(
                f"[클러스터] 대표: [{rep.source}] {rep.title[:40]}... "
                f"(+{len(cluster)-1}건 유사: {', '.join(others[:3])})"
            )

    logger.info(f"클러스터링: {len(items)}건 → {len(representatives)}건 (대표)")
    return representatives


# ──────────────────────────────────────
# 2. 번역 + 중요도 스코어링 (Claude 1회)
# ──────────────────────────────────────

_BATCH_SIZE = 5  # Gemma4 소배치 크기 (JSON 잘림 방지)


def _build_translate_prompt(batch: list[NewsItem], offset: int = 0) -> str:
    """번역+스코어링 프롬프트 생성. offset: 전체 목록에서의 시작 인덱스."""
    news_lines = "\n".join(
        f"{offset + i + 1}. [{item.source}] {item.title}"
        for i, item in enumerate(batch)
    )
    n = len(batch)
    # 예시는 실제 인덱스 범위와 다른 숫자(99)를 써서 혼동 방지
    example = (
        '{"results": ['
        + ", ".join(
            f'{{"index": {offset + i + 1}, "title_ko": "번역된 제목", "importance": 7, "reason": "이유"}}'
            for i in range(n)
        )
        + "]}"
    )
    return "\n".join([
        f"뉴스 제목 {n}건을 분석하세요.",
        "각 항목에 대해 세 가지를 반환하세요:",
        "  index: 아래 번호 그대로",
        "  title_ko: 한국어 자연스러운 번역 (이미 한국어면 그대로)",
        "  importance: 1~10 중요도 정수",
        "  reason: 중요도 이유 10자 이내",
        "",
        "중요도 기준:",
        "  10=전쟁/대형사건/경제위기  8~9=주요정책/국제변화  6~7=주목뉴스  4~5=일반  1~3=가십",
        "",
        "<뉴스목록>",
        news_lines,
        "</뉴스목록>",
        "",
        "위 뉴스목록만 번역하세요. 아래 형식의 JSON만 출력하세요. 다른 텍스트 없이:",
        example,
    ])


async def _translate_batch(
    batch: list[NewsItem],
    offset: int,
    backend: str,
) -> list[dict]:
    """소배치 번역+스코어링. 실패 시 원본 유지."""
    from services.claude_utils import extract_json

    prompt = _build_translate_prompt(batch, offset)

    try:
        if backend == "claude":
            from services.claude_utils import call_claude_cli
            raw = await asyncio.to_thread(call_claude_cli, prompt, 60)
        else:
            from services.gemma4_service import call_gemma4
            raw = await asyncio.to_thread(call_gemma4, prompt, 1024, 0.1)

        data = extract_json(raw)
    except Exception as exc:
        logger.warning(f"배치 번역 실패 (offset={offset}, {len(batch)}건): {exc}")
        return []

    results = data.get("results", [])

    # 예시 반환 감지: title_ko가 "번역된 제목"이면 파싱 실패로 처리
    if any(r.get("title_ko") in ("번역된 제목", "한국어 제목") for r in results):
        logger.warning(f"배치 번역 예시 반환 감지 (offset={offset}), 원본 유지")
        return []

    scored: list[dict] = []
    for entry in results:
        global_idx = entry.get("index", 0) - 1  # 전체 기준 index
        local_idx = global_idx - offset
        if 0 <= local_idx < len(batch):
            item = batch[local_idx]
            try:
                importance = int(entry.get("importance", 5))
            except (ValueError, TypeError):
                importance = 5
            scored.append({
                "id": item.id,
                "original_title": item.title,
                "title_ko": entry.get("title_ko", item.title),
                "importance": importance,
                "reason": entry.get("reason", ""),
                "source": item.source,
                "link": item.link,
                "published_at": item.published_at,
                "topic": item.topic,
            })
    return scored


async def translate_and_score(items: list[NewsItem]) -> list[dict]:
    """번역 + 중요도 스코어링. 소배치(_BATCH_SIZE건씩) 순차 처리.

    NEWS_TRANSLATE=0 설정 시 번역을 건너뛰고 원본 제목 + 중요도 5로 반환.
    설정은 .env.local을 매번 읽어 멀티프로세스 환경에서도 즉시 반영된다.

    Returns:
        [{"id": str, "title_ko": str, "importance": int, "reason": str}, ...]
    """
    if not items:
        return []

    translation_enabled, translation_backend = _read_translation_settings()

    if not translation_enabled:
        logger.info(f"번역 비활성화(NEWS_TRANSLATE=0): {len(items)}건 원본 제목 유지")
        return [
            {"id": item.id, "original_title": item.title, "title_ko": item.title,
             "importance": 5, "reason": "번역OFF", "source": item.source,
             "link": item.link, "published_at": item.published_at, "topic": item.topic}
            for item in items
        ]

    # 소배치로 분할하여 순차 처리
    all_scored: list[dict] = []
    for batch_start in range(0, len(items), _BATCH_SIZE):
        batch = items[batch_start: batch_start + _BATCH_SIZE]
        logger.info(
            f"번역 배치: {batch_start + 1}~{batch_start + len(batch)}건 "
            f"({translation_backend})"
        )
        batch_result = await _translate_batch(batch, batch_start, translation_backend)
        all_scored.extend(batch_result)

    # 누락된 항목 보충 (배치 실패 시 원본 유지)
    scored_ids = {s["id"] for s in all_scored}
    for item in items:
        if item.id not in scored_ids:
            all_scored.append({
                "id": item.id,
                "original_title": item.title,
                "title_ko": item.title,
                "importance": 5,
                "reason": "미분석",
                "source": item.source,
                "link": item.link,
                "published_at": item.published_at,
                "topic": item.topic,
            })

    # 중요도 내림차순 정렬
    all_scored.sort(key=lambda x: x["importance"], reverse=True)

    if all_scored:
        logger.info(
            f"번역+스코어링 완료: {len(all_scored)}건, "
            f"상위: {all_scored[0]['title_ko'][:30]}(중요도{all_scored[0]['importance']})"
        )
    return all_scored


# ──────────────────────────────────────
# 3. DB 업데이트 (번역된 제목 저장)
# ──────────────────────────────────────

async def update_translated_titles(scored_items: list[dict]) -> None:
    """번역된 제목을 DB에 반영한다.

    번역 OFF("번역OFF") 또는 미분석("미분석") 항목은 건너뜀 —
    이미 저장된 번역 제목을 원본으로 덮어쓰지 않기 위함.
    """
    from database.repository import update_news_item

    for item in scored_items:
        # 번역 비활성 또는 실패 항목은 DB 미반영 (기존 제목 보존)
        if item.get("reason") in ("번역OFF", "미분석", "분석실패"):
            continue
        try:
            await asyncio.to_thread(
                update_news_item,
                item["id"],
                title=item["title_ko"],
                # summary는 보존 — 중요도는 title 앞에 태그로 표시하지 않음
            )
        except Exception as exc:
            logger.warning(f"번역 제목 DB 업데이트 실패 ({item['id'][:8]}): {exc}")


# ──────────────────────────────────────
# 4. 건바이건 텔레그램 알림
# ──────────────────────────────────────

async def notify_one_by_one(
    keyword: str,
    scored_items: list[dict],
    max_notify: int = _MAX_NOTIFY,
    importance_cutoff: int = _IMPORTANCE_CUTOFF,
) -> int:
    """중요도 순으로 상위 N건을 건바이건 텔레그램 알림.

    Returns:
        실제 발송 건수
    """
    try:
        import httpx
    except ImportError:
        logger.debug("httpx 미설치, 텔레그램 알림 스킵")
        return 0

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    raw_ids = os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS", "")
    if not token or not raw_ids:
        return 0

    chat_ids = []
    for x in raw_ids.split(","):
        x = x.strip()
        try:
            chat_ids.append(int(x))
        except ValueError:
            logger.warning(f"잘못된 chat_id 무시: {x}")
    if not chat_ids:
        return 0

    # 중요도 컷오프 + 상위 N건
    filtered = [
        item for item in scored_items
        if item["importance"] >= importance_cutoff
    ][:max_notify]

    if not filtered:
        logger.info(f"[{keyword}] 중요도 {importance_cutoff}+ 뉴스 없음, 알림 스킵")
        return 0

    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    sent = 0

    async with httpx.AsyncClient(timeout=10) as client:
        for item in filtered:
            # 중요도 이모지
            imp = item["importance"]
            if imp >= 9:
                emoji = "🔴"
            elif imp >= 7:
                emoji = "🟠"
            else:
                emoji = "🟡"

            message = (
                f"{emoji} [{keyword}] 중요도 {imp}/10\n"
                f"\n"
                f"📰 {item['title_ko']}\n"
                f"📡 {item['source']}\n"
                f"💡 {item.get('reason', '')}\n"
                f"\n"
                f"🔗 {item['link']}"
            )

            for chat_id in chat_ids:
                try:
                    await client.post(api_url, json={
                        "chat_id": chat_id,
                        "text": message,
                        "disable_web_page_preview": True,
                    })
                    sent += 1
                except Exception as e:
                    logger.warning(f"텔레그램 발송 실패 (chat_id={chat_id}): {e}")

            # 건바이건 간격 (0.5초)
            await asyncio.sleep(0.5)

    logger.info(f"[{keyword}] 텔레그램 건바이건 알림: {sent}건 발송")
    return sent


# ──────────────────────────────────────
# 통합 파이프라인
# ──────────────────────────────────────

async def process_news(
    keyword: str,
    items: list[NewsItem],
    max_notify: int = _MAX_NOTIFY,
    importance_cutoff: int = _IMPORTANCE_CUTOFF,
) -> list[dict]:
    """수집된 뉴스를 정제하는 통합 파이프라인.

    1. 유사 뉴스 클러스터링 → 대표 선택
    2. Claude 번역 + 중요도 스코어링
    3. DB 업데이트
    (알림은 bot.py의 _on_new_news에서 [영상화]/[패스] 버튼과 함께 처리)

    Args:
        keyword: 키워드 또는 분야명
        items: 수집된 뉴스 리스트
        max_notify: 최대 알림 건수
        importance_cutoff: 중요도 컷오프

    Returns:
        scored_items (번역 + 중요도 포함, 중요도 내림차순)
    """
    if not items:
        return []

    logger.info(f"[{keyword}] 뉴스 후처리 시작: {len(items)}건")

    # 1. 유사 뉴스 클러스터링
    representatives = cluster_similar_news(items)

    # 2. 번역 + 중요도
    scored = await translate_and_score(representatives)

    # 3. DB 업데이트
    await update_translated_titles(scored)

    logger.info(
        f"[{keyword}] 후처리 완료: "
        f"{len(items)}건 수집 → {len(representatives)}건 대표 → "
        f"중요도 6+: {len([s for s in scored if s['importance'] >= importance_cutoff])}건"
    )
    return scored
