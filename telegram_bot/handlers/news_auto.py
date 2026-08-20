"""자동 뉴스 알림 핸들러 — telegram_bot/handlers/news.py 에서 분리.

ConversationHandler 밖에서 동작 (auto_news_*, old_news_*, _auto_process_one, cmd_auto).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest, RetryAfter
from telegram.ext import ContextTypes, ConversationHandler

from telegram_bot.constants import States
from telegram_bot.handlers.common import check_authorized

logger = logging.getLogger(__name__)



# ─────────────────────────────────────────────
# 자동 알림 핸들러 (ConversationHandler 밖에서 동작)
# ─────────────────────────────────────────────


@check_authorized
async def auto_news_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """자동 알림의 [영상화] 버튼 클릭 시 리서치 → 앵커 선택 흐름 시작.

    callback_data 형식: "auto_news_{news_item_id}"
    """
    query = update.callback_query
    await query.answer()

    news_id = query.data.removeprefix("auto_news_")

    # DB에서 뉴스 아이템 조회
    from database.repository import get_news_item
    # 큐에서 현재 뉴스 제거 + 다음 뉴스 전송
    from telegram_bot.bot import _pending_news_queue, _send_next_news
    from telegram_bot.config import load_config
    _pending_news_queue[:] = [n for n in _pending_news_queue if n.id != news_id]
    try:
        config = load_config()
        await _send_next_news(config.allowed_chat_ids)
    except Exception:
        pass

    item_dict = get_news_item(news_id)
    if not item_dict:
        await query.edit_message_text("해당 뉴스를 찾을 수 없습니다.")
        return ConversationHandler.END

    selected = NewsItem(
        id=item_dict["id"],
        title=item_dict["title"],
        link=item_dict["link"],
        source=item_dict.get("source", ""),
        published_at=item_dict.get("published_at", ""),
        summary=item_dict.get("summary", ""),
        full_text=item_dict.get("full_text", ""),
        language=item_dict.get("language", "en"),
        topic=item_dict.get("topic", ""),
        is_scraped=bool(item_dict.get("is_scraped", 0)),
    )

    context.user_data["current_news_list"] = [selected]
    context.user_data["selected_news_id"] = news_id

    await query.edit_message_text(f'🎬 "{selected.title}"\n\n기사 본문 스크래핑 중... (1/2)')

    try:
        full_text = await _scraper.scrape_article(selected.link)
        if not full_text:
            full_text = selected.summary or "(본문 미수집)"
        selected.full_text = full_text
        selected.is_scraped = True
    except Exception as exc:
        logger.warning("기사 스크래핑 실패: %s", exc)
        selected.full_text = selected.summary or ""

    await query.edit_message_text(f'🎬 "{selected.title}"\n\n관련 뉴스 리서치 중... (2/2)')

    try:
        research: ResearchResult = await _scraper.research_news(selected)
    except Exception as exc:
        logger.exception("리서치 실패: %s", exc)
        await query.edit_message_text(f"리서치 실패: {exc}")
        return ConversationHandler.END

    context.user_data["research_data"] = research

    related_lines = "\n".join(
        f"{i + 1}. {art.get('source', '?')}: \"{art.get('title', '')[:50]}...\""
        for i, art in enumerate(research.related_articles[:5])
    )
    keywords_str = ", ".join(research.keywords[:10])

    result_text = (
        "📋 리서치 완료!\n\n"
        f"원본: \"{selected.title}\"\n\n"
        f"관련 뉴스 {len(research.related_articles)}건:\n{related_lines}\n\n"
        f"키워드: {keywords_str}"
    )

    await query.edit_message_text(result_text[:_MSG_MAX_LEN])

    await _send_anchor_gallery(update)
    return States.ANCHOR_SELECT


@check_authorized
async def auto_news_pass(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """자동 알림의 [패스] 버튼 클릭 시 큐에서 제거하고 다음 뉴스를 전송."""
    query = update.callback_query
    try:
        await query.answer("패스했습니다")
    except Exception:
        pass  # 콜백 만료 시 무시
    original_text = query.message.text or ""
    try:
        await query.edit_message_text(f"⏭ {original_text}\n(패스됨)")
    except Exception:
        pass

    # 큐에서 현재 뉴스 제거 + 다음 뉴스 전송
    from telegram_bot.bot import _pending_news_queue, _send_next_news
    from telegram_bot.config import load_config
    news_id = query.data.removeprefix("auto_pass_")
    _pending_news_queue[:] = [n for n in _pending_news_queue if n.id != news_id]
    try:
        config = load_config()
        await _send_next_news(config.allowed_chat_ids)
    except Exception:
        pass


# ─────────────────────────────────────────────
# /oldnews 핸들러
# ─────────────────────────────────────────────

_OLDNEWS_PAGE_SIZE = 5  # /oldnews 한 페이지에 표시할 건수


async def _make_oldnews_keyboard(
    news_list: list[dict],
    page: int = 0,
) -> tuple[str, InlineKeyboardMarkup]:
    """oldnews 목록 텍스트 + 인라인 키보드 생성.

    DB에 저장된 title(번역된 경우 한국어)을 그대로 사용한다.
    별도 번역 호출 없음 — 번역은 뉴스 수집 시 news_processor에서만 수행.
    Returns: (메시지 텍스트, 키보드)
    """
    start = page * _OLDNEWS_PAGE_SIZE
    items = news_list[start : start + _OLDNEWS_PAGE_SIZE]

    # DB에 저장된 title 그대로 사용 (번역된 경우 이미 한국어)
    ko_titles = [item.get("title", "") for item in items]

    lines = []
    rows: list[list[InlineKeyboardButton]] = []
    for idx, (item, ko_title) in enumerate(zip(items, ko_titles), start=start + 1):
        source = item.get("source", "")
        source_text = f" ({source})" if source else ""
        lines.append(f"{idx}. {ko_title}{source_text}")

        item_id = item.get("id", "")
        rows.append([
            InlineKeyboardButton(f"🎬 {idx}번 영상화", callback_data=f"auto_news_{item_id}"),
            InlineKeyboardButton(f"⏭ 패스", callback_data=f"oldnews_pass_{item_id}"),
        ])

    nav_row: list[InlineKeyboardButton] = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅ 이전", callback_data=f"oldnews_page_{page - 1}"))
    if start + _OLDNEWS_PAGE_SIZE < len(news_list):
        nav_row.append(InlineKeyboardButton("다음 ➡", callback_data=f"oldnews_page_{page + 1}"))
    nav_row.append(InlineKeyboardButton("❌ 닫기", callback_data=CALLBACK_CANCEL))
    rows.append(nav_row)

    text = "\n\n".join(lines) if lines else "뉴스 없음"
    return text, InlineKeyboardMarkup(rows)


@check_authorized
async def old_news_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """/oldnews 명령 진입점. 아직 영상화하지 않은 최근 24시간 뉴스 목록을 표시한다.

    각 뉴스에 [영상화] [패스] 버튼을 제공하며 5개씩 페이지네이션한다.
    [영상화] 클릭 시 auto_news_start와 동일한 흐름으로 진입한다.

    Returns:
        States.NEWS_SELECT (목록 표시 후 선택 대기)
    """
    from database.repository import list_unvideoed_news

    await update.message.reply_text("최근 24시간 미영상화 뉴스를 조회하는 중...")

    try:
        news_list = await asyncio.to_thread(list_unvideoed_news, 24, 50)
    except Exception as exc:
        logger.exception("oldnews 목록 조회 실패: %s", exc)
        await update.message.reply_text(
            f"목록 조회 중 오류가 발생했습니다: {exc}\n/oldnews 명령으로 다시 시도하세요."
        )
        return ConversationHandler.END

    if not news_list:
        await update.message.reply_text(
            "최근 24시간 이내 미영상화 뉴스가 없습니다.\n"
            "/news 명령으로 새 뉴스를 수집하세요."
        )
        return ConversationHandler.END

    context.user_data["oldnews_list"] = news_list
    context.user_data["oldnews_page"] = 0

    total = len(news_list)
    page_count = (total + _OLDNEWS_PAGE_SIZE - 1) // _OLDNEWS_PAGE_SIZE

    show_count = min(total, _OLDNEWS_PAGE_SIZE)
    progress_msg = await update.message.reply_text(
        f"뉴스 {show_count}건 번역 중... (전체 {total}건)"
    )
    text, keyboard = await _make_oldnews_keyboard(news_list, page=0)
    await progress_msg.edit_text(
        f"📋 미영상화 뉴스 {total}건 ({page_count}페이지)\n\n{text}",
        reply_markup=keyboard,
    )
    return States.NEWS_SELECT


@check_authorized
async def old_news_page_changed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """oldnews 목록 페이지 이동 콜백.

    callback_data 형식: "oldnews_page_{page_number}"

    Returns:
        States.NEWS_SELECT (목록 유지)
    """
    query = update.callback_query
    await query.answer()

    page = int(query.data.removeprefix("oldnews_page_"))
    news_list: list[dict] = context.user_data.get("oldnews_list", [])

    if not news_list:
        await query.edit_message_text("목록이 만료되었습니다. /oldnews 명령으로 다시 시작하세요.")
        return ConversationHandler.END

    context.user_data["oldnews_page"] = page
    total = len(news_list)
    page_count = (total + _OLDNEWS_PAGE_SIZE - 1) // _OLDNEWS_PAGE_SIZE

    await query.edit_message_text("번역 중...")
    text, keyboard = await _make_oldnews_keyboard(news_list, page=page)
    await query.edit_message_text(
        f"📋 미영상화 뉴스 {total}건 ({page_count}페이지)\n\n{text}",
        reply_markup=keyboard,
    )
    return States.NEWS_SELECT


@check_authorized
async def old_news_pass(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """oldnews 목록의 [패스] 버튼 클릭 시 해당 뉴스를 목록에서 제거하고 갱신."""
    query = update.callback_query
    await query.answer("패스했습니다")

    news_id = query.data.removeprefix("oldnews_pass_")
    news_list: list[dict] = context.user_data.get("oldnews_list", [])
    page: int = context.user_data.get("oldnews_page", 0)

    # 패스한 뉴스 목록에서 제거
    news_list = [n for n in news_list if n.get("id") != news_id]
    context.user_data["oldnews_list"] = news_list

    if not news_list:
        await query.edit_message_text("모든 뉴스를 처리했습니다.")
        return

    # 페이지 범위 보정
    max_page = max(0, (len(news_list) - 1) // _OLDNEWS_PAGE_SIZE)
    page = min(page, max_page)
    context.user_data["oldnews_page"] = page

    total = len(news_list)
    page_count = (total + _OLDNEWS_PAGE_SIZE - 1) // _OLDNEWS_PAGE_SIZE

    await query.edit_message_text("번역 중...")
    text, keyboard = await _make_oldnews_keyboard(news_list, page=page)
    await query.edit_message_text(
        f"📋 미영상화 뉴스 {total}건 ({page_count}페이지)\n\n{text}",
        reply_markup=keyboard,
    )


# ─────────────────────────────────────────────
# /auto 명령 핸들러: 상위 N건 자동 슬라이드쇼 생성
# ─────────────────────────────────────────────

async def _auto_process_one(
    chat_id: int,
    item: NewsItem,
    idx: int,
    total: int,
    anchor_name: str,
    video_mode: str,
    send_message,
) -> None:
    """단일 뉴스 아이템에 대해 스크래핑 → 대본 → 시나리오 → 슬라이드쇼 자동 실행.

    Args:
        chat_id:      텔레그램 채팅 ID
        item:         뉴스 아이템
        idx:          현재 처리 순서 (1부터)
        total:        전체 처리 건수
        anchor_name:  앵커 이름
        video_mode:   영상 모드 ("slideshow" | "shorts")
        send_message: 텔레그램 메시지 전송 코루틴 (text -> message)
    """
    import json as _json
    import unicodedata
    from pathlib import Path
    from datetime import datetime, timezone
    from database import repository as _repo
    from telegram_bot.services.news_script_service import generate_news_script
    from telegram_bot.services import news_scenario_service

    progress_prefix = f"[{idx}/{total}] {item.title[:40]}"

    # 1. 스크래핑
    await send_message(f"{progress_prefix}\n스크래핑 중...")
    try:
        full_text = await _scraper.scrape_article(item.link)
        if not full_text:
            full_text = item.summary or item.title
        item.full_text = full_text
        item.is_scraped = True
    except Exception as exc:
        logger.warning("auto: 스크래핑 실패 (%s): %s", item.id, exc)
        full_text = item.summary or item.title
        item.full_text = full_text

    # 2. 리서치
    try:
        research: ResearchResult = await _scraper.research_news(item)
    except Exception as exc:
        logger.warning("auto: 리서치 실패 (%s): %s", item.id, exc)
        from telegram_bot.models import ResearchResult
        research = ResearchResult(
            original_news=item,
            related_articles=[],
            keywords=[],
            cross_check_summary="",
            background_info="",
            combined_text=full_text,
        )

    # 3. 대본 생성
    await send_message(f"{progress_prefix}\n대본 생성 중...")
    try:
        script_result = await generate_news_script(
            news_text=research.combined_text,
            news_title=item.title,
            news_source=item.source,
            anchor_name=anchor_name,
            target_duration=20,
        )
    except Exception as exc:
        logger.error("auto: 대본 생성 실패 (%s): %s", item.id, exc)
        await send_message(f"{progress_prefix}\n대본 생성 실패: {exc}")
        return

    script_content = script_result.get("content", "")

    # 4. 시나리오 생성
    await send_message(f"{progress_prefix}\n시나리오 생성 중...")
    character_data = news_scenario_service.load_anchor_character_data(anchor_name) or {}
    try:
        scenario_result = await news_scenario_service.generate_light_scenario(
            script_content=script_content,
            anchor_name=anchor_name,
            character_data=character_data,
            target_duration=20,
        )
    except Exception as exc:
        logger.error("auto: 시나리오 생성 실패 (%s): %s", item.id, exc)
        await send_message(f"{progress_prefix}\n시나리오 생성 실패: {exc}")
        return

    # 5. 프로젝트 저장
    import unicodedata as _uc
    raw_title = script_result.get("title", item.title)
    raw_title = _uc.normalize("NFC", raw_title)
    safe_title = re.sub(r'[\\/:*?"<>|!@#$%^&\s]+', '_', raw_title)
    safe_title = re.sub(r'_+', '_', safe_title).strip().strip('._')[:80]
    proj_dir_name = f"{datetime.now().strftime('%Y%m%d')}_{anchor_name}_{safe_title}"
    proj_dir = Path(__file__).parent.parent.parent / "projects" / proj_dir_name
    proj_dir.mkdir(parents=True, exist_ok=True)

    scenes = scenario_result.get("scenes", [])
    proj_json = {
        "id": proj_dir_name,
        "title": proj_dir_name,
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "page": {
            "videoMode": video_mode,
            "scriptForScenario": script_content,
        },
        "scenario": {
            "topic": proj_dir_name,
            "style": "informative",
            "targetDuration": 20,
            "sourceScript": script_content,
            "selectedCharacterNames": [anchor_name],
            "result": scenario_result,
        },
    }
    try:
        with open(proj_dir / "project.json", "w") as f:
            _json.dump(proj_json, f, ensure_ascii=False, indent=2)
        _repo.save_project(
            project_id=proj_dir_name,
            title=proj_dir_name,
            state_json=_json.dumps(proj_json, ensure_ascii=False),
            video_mode=video_mode,
            created_at=proj_json["created_at"],
            updated_at=proj_json["updated_at"],
            scene_count=len(scenes),
            has_tts=False,
            has_video=False,
            media_dir=str(proj_dir),
        )
    except Exception as exc:
        logger.warning("auto: 프로젝트 저장 실패 (무시): %s", exc)

    # 6. 슬라이드쇼 생성 (slideshow 모드 한정)
    if video_mode == "slideshow":
        await send_message(f"{progress_prefix}\n슬라이드쇼 생성 중...")
        try:
            from services.slideshow_service import generate_multi_slideshow

            slideshow_scenes = [
                {
                    "image_path": scene.get("image_url", scene.get("image_path", "")),
                    "narration": scene.get("narration", scene.get("script", "")),
                    "effect": scene.get("effect", "auto"),
                }
                for scene in scenes
            ]
            result = await generate_multi_slideshow(
                scenes=slideshow_scenes,
                aspect_ratio="9:16",
                project_dir=proj_dir / "slideshow",
            )
            video_path = result.get("video_path", "")
            duration = result.get("duration", 0)
            await send_message(
                f"{progress_prefix}\n완료! ({duration:.1f}초)\n{video_path}"
            )
        except Exception as exc:
            logger.error("auto: 슬라이드쇼 생성 실패 (%s): %s", item.id, exc)
            await send_message(f"{progress_prefix}\n슬라이드쇼 생성 실패: {exc}")
    else:
        await send_message(f"{progress_prefix}\n시나리오 저장 완료 (AI 쇼츠는 별도 생성 필요)")


@check_authorized
async def cmd_auto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/auto [N] [topic|mode] 명령: 최신 뉴스 N건을 자동으로 슬라이드쇼 생성한다.

    사용 예:
        /auto            -> 최신 3건 슬라이드쇼
        /auto 5          -> 최신 5건 슬라이드쇼
        /auto 3 ai       -> AI 도메인 최신 3건
        /auto slideshow  -> 최신 3건 슬라이드쇼 (명시)
        /auto 5 ai       -> AI 도메인 5건

    비동기 백그라운드로 실행하여 봇을 블로킹하지 않는다.
    """
    args = context.args or []

    # 인수 파싱: 숫자=건수, 알려진 토픽키=토픽, slideshow/shorts=모드
    count = 3
    topic = "general"
    video_mode = "slideshow"

    known_topics = {t["key"] for t in NEWS_TOPICS}

    for arg in args:
        if arg.isdigit():
            count = max(1, min(int(arg), 10))  # 최대 10건
        elif arg in known_topics:
            topic = arg
        elif arg in ("slideshow", "ai", "shorts"):
            if arg == "ai":
                topic = "ai"
            else:
                video_mode = arg

    anchor_name = "Emma"

    status_msg = await update.message.reply_text(
        f"/auto 시작: {topic} 도메인 {count}건 {video_mode} 모드로 처리합니다..."
    )

    async def _run_auto() -> None:
        """백그라운드 자동 처리 태스크."""
        chat_id = update.effective_chat.id

        async def send_message(text: str):
            try:
                await status_msg.edit_text(text[:_MSG_MAX_LEN])
            except Exception:
                try:
                    await update.effective_chat.send_message(text[:_MSG_MAX_LEN])
                except Exception as exc:
                    logger.warning("auto: 상태 메시지 전송 실패: %s", exc)

        # 뉴스 수집
        try:
            news_list = await _scraper.fetch_news(topic=topic, limit=count)
        except Exception as exc:
            await send_message(f"/auto 오류: 뉴스 수집 실패 - {exc}")
            return

        if not news_list:
            await send_message(f"/auto: [{topic}] 뉴스가 없습니다.")
            return

        actual_count = min(len(news_list), count)
        await send_message(f"/auto: {actual_count}건 처리를 시작합니다...")

        # 순차 처리 (API 부하 방지)
        for idx, item in enumerate(news_list[:actual_count], start=1):
            try:
                await _auto_process_one(
                    chat_id=chat_id,
                    item=item,
                    idx=idx,
                    total=actual_count,
                    anchor_name=anchor_name,
                    video_mode=video_mode,
                    send_message=send_message,
                )
            except Exception as exc:
                logger.exception("auto: 처리 중 예외 (%s): %s", item.id, exc)
                await send_message(f"[{idx}/{actual_count}] 처리 실패: {exc}")

        await update.effective_chat.send_message(
            f"/auto 완료: {actual_count}건 처리 종료."
        )

    asyncio.create_task(_run_auto(), name=f"auto_news_{update.effective_chat.id}")
