"""뉴스 대화 핸들러: 뉴스 선택 → 리서치 → 앵커 선택 → 대본 검토"""

from __future__ import annotations

import logging
from typing import Optional

from telegram import InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from telegram_bot.constants import (
    ANCHOR_CHARACTERS,
    CALLBACK_ANCHOR_PREFIX,
    CALLBACK_CANCEL,
    CALLBACK_NEWS_PREFIX,
    CALLBACK_TOPIC_PREFIX,
    NEWS_TOPICS,
    States,
)
from telegram_bot.handlers.common import check_authorized
from telegram_bot.handlers.news_views import (
    _make_anchor_keyboard,
    _make_news_list_keyboard,
    _make_research_keyboard,
    _make_script_keyboard,
    _make_topic_keyboard,
    _send_anchor_gallery,
    _send_long_message,
)
from telegram_bot.models import NewsItem, ResearchResult, new_news_project

from telegram_bot.services.news_scraper import NewsScraper
from telegram_bot.services.news_script_service import generate_news_script

_scraper = NewsScraper()

logger = logging.getLogger(__name__)

_SCRIPT_PREVIEW_LEN = 300    # 대본 미리보기 최대 길이


# ─────────────────────────────────────────────
# 핸들러
# ─────────────────────────────────────────────


@check_authorized
async def news_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """/news 명령 진입점. 토픽 선택 키보드를 표시한다.

    Returns:
        States.NEWS_FETCH (토픽 선택 대기)
    """
    await update.message.reply_text(
        "뉴스를 수집합니다. 주제를 선택하세요:",
        reply_markup=_make_topic_keyboard(),
    )
    return States.NEWS_FETCH


@check_authorized
async def topic_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """토픽 선택 콜백. 해당 토픽의 뉴스 목록을 조회하여 표시한다.

    callback_data 형식: "topic_{TOPIC_KEY}"

    Returns:
        States.NEWS_SELECT (뉴스 선택 대기)
    """
    query = update.callback_query
    await query.answer()

    topic_key = query.data.removeprefix(CALLBACK_TOPIC_PREFIX)
    topic_label = next(
        (t["label"] for t in NEWS_TOPICS if t["key"] == topic_key),
        topic_key,
    )

    await query.edit_message_text(f"[{topic_label}] 뉴스를 수집하는 중...")

    try:
        news_list: list[NewsItem] = await _scraper.fetch_news(topic=topic_key)
    except Exception as exc:
        logger.exception("뉴스 수집 실패 (topic=%s): %s", topic_key, exc)
        await query.edit_message_text(
            f"뉴스 수집 중 오류가 발생했습니다: {exc}\n/news 명령으로 다시 시작하세요."
        )
        return ConversationHandler.END

    if not news_list:
        await query.edit_message_text(
            "수집된 뉴스가 없습니다. /news 명령으로 다시 시작하세요."
        )
        return ConversationHandler.END

    context.user_data["current_news_list"] = news_list
    context.user_data["current_topic"] = topic_key
    context.user_data["news_page"] = 0

    await query.edit_message_text(
        f"[{topic_label}] 뉴스 {len(news_list)}건을 수집했습니다. 기사를 선택하세요:",
        reply_markup=_make_news_list_keyboard(news_list, page=0),
    )
    return States.NEWS_SELECT


@check_authorized
async def news_page_changed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """뉴스 목록 페이지 이동 콜백.

    callback_data 형식: "news_page_{page_number}"

    Returns:
        States.NEWS_SELECT (뉴스 선택 대기 유지)
    """
    query = update.callback_query
    await query.answer()

    page = int(query.data.removeprefix("news_page_"))
    news_list: list[NewsItem] = context.user_data.get("current_news_list", [])

    if not news_list:
        await query.edit_message_text("뉴스 목록이 만료되었습니다. /news 명령으로 다시 시작하세요.")
        return ConversationHandler.END

    context.user_data["news_page"] = page
    await query.edit_message_text(
        "기사를 선택하세요:",
        reply_markup=_make_news_list_keyboard(news_list, page=page),
    )
    return States.NEWS_SELECT


@check_authorized
async def news_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """뉴스 선택 콜백. 기사 본문을 스크래핑하고 관련 뉴스를 리서치한다.

    callback_data 형식: "news_{news_item_id}"

    Returns:
        States.RESEARCH (리서치 결과 승인 대기)
    """
    query = update.callback_query
    await query.answer()

    news_id = query.data.removeprefix(CALLBACK_NEWS_PREFIX)
    news_list: list[NewsItem] = context.user_data.get("current_news_list", [])

    selected: Optional[NewsItem] = next((n for n in news_list if n.id == news_id), None)
    if selected is None:
        await query.edit_message_text("선택한 뉴스를 찾을 수 없습니다. /news 명령으로 다시 시작하세요.")
        return ConversationHandler.END

    context.user_data["selected_news_id"] = news_id

    await query.edit_message_text(f'"{selected.title}"\n\n관련 뉴스를 리서치하는 중... (1/2)')

    try:
        full_text = await _scraper.scrape_article(selected.link)
        if not full_text:
            full_text = selected.summary or "(본문 미수집)"
        selected.full_text = full_text
        selected.is_scraped = True
    except Exception as exc:
        logger.warning("기사 본문 스크래핑 실패 (url=%s): %s", selected.link, exc)
        full_text = selected.summary or ""
        selected.full_text = full_text

    await query.edit_message_text(f'"{selected.title}"\n\n관련 뉴스를 리서치하는 중... (2/2)')

    try:
        research: ResearchResult = await _scraper.research_news(selected)
    except Exception as exc:
        logger.exception("리서치 실패 (news_id=%s): %s", news_id, exc)
        await query.edit_message_text(
            f"리서치 중 오류가 발생했습니다: {exc}\n/news 명령으로 다시 시작하세요."
        )
        return ConversationHandler.END

    context.user_data["research_data"] = research

    related_lines = "\n".join(
        f"{i + 1}. {art.get('source', '?')}: \"{art.get('title', '')[:50]}...\""
        for i, art in enumerate(research.related_articles[:5])
    )
    keywords_str = ", ".join(research.keywords[:10])

    result_text = (
        "리서치 완료!\n\n"
        f'원본: "{selected.title}"\n'
        f"관련 뉴스 {len(research.related_articles)}건 수집:\n"
        f"{related_lines}\n\n"
        f"종합 키워드: {keywords_str}"
    )

    await _send_long_message(
        update,
        result_text,
        reply_markup=_make_research_keyboard(),
    )

    # edit_message_text는 이미 위에서 수행했으므로 별도 메시지로 표시
    try:
        await query.edit_message_text(result_text)
    except Exception:
        pass  # 텍스트가 같거나 이미 수정된 경우 무시

    return States.RESEARCH


@check_authorized
async def research_approved(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """리서치 승인 콜백. 앵커 사진을 보여주고 선택 화면으로 전환한다.

    callback_data: "research_approve"

    Returns:
        States.ANCHOR_SELECT (앵커 선택 대기)
    """
    import os
    from pathlib import Path
    from telegram import InputMediaPhoto

    query = update.callback_query
    await query.answer()

    await query.edit_message_text("앵커 캐릭터를 불러오는 중...")

    await _send_anchor_gallery(update)
    return States.ANCHOR_SELECT


@check_authorized
async def research_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """다른 뉴스 선택 콜백. 뉴스 목록으로 돌아간다.

    callback_data: "research_back"

    Returns:
        States.NEWS_SELECT (뉴스 선택 대기)
    """
    query = update.callback_query
    await query.answer()

    news_list: list[NewsItem] = context.user_data.get("current_news_list", [])
    page: int = context.user_data.get("news_page", 0)

    if not news_list:
        await query.edit_message_text("뉴스 목록이 만료되었습니다. /news 명령으로 다시 시작하세요.")
        return ConversationHandler.END

    await query.edit_message_text(
        "기사를 선택하세요:",
        reply_markup=_make_news_list_keyboard(news_list, page=page),
    )
    return States.NEWS_SELECT


@check_authorized
async def anchor_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """앵커 선택 콜백. 대본을 생성하고 검토 화면을 표시한다.

    callback_data 형식: "anchor_{anchor_name}" 또는 "anchor_random"

    Returns:
        States.SCRIPT_REVIEW (대본 검토 대기)
    """
    import random as _random

    query = update.callback_query
    await query.answer()

    anchor_name = query.data.removeprefix(CALLBACK_ANCHOR_PREFIX)

    if anchor_name == "random":
        anchor_name = _random.choice(list(ANCHOR_CHARACTERS.keys()))

    anchor_data = ANCHOR_CHARACTERS.get(anchor_name)
    if anchor_data is None:
        await query.edit_message_text(
            f"알 수 없는 앵커입니다: {anchor_name}\n/news 명령으로 다시 시작하세요."
        )
        return ConversationHandler.END

    context.user_data["selected_anchor"] = anchor_name

    # "앵커를 선택하세요:" 텍스트 메시지를 업데이트
    await query.edit_message_text(
        f"✅ 앵커 [{anchor_data['display_name']}] 선택 완료!\n대본을 생성하는 중..."
    )

    research: Optional[ResearchResult] = context.user_data.get("research_data")
    news_id = context.user_data.get("selected_news_id")
    news_list: list[NewsItem] = context.user_data.get("current_news_list", [])
    selected: Optional[NewsItem] = next((n for n in news_list if n.id == news_id), None)

    if research is None or selected is None:
        await query.edit_message_text("세션 데이터가 손실되었습니다. /news 명령으로 다시 시작하세요.")
        return ConversationHandler.END

    try:
        script_result = await generate_news_script(
            news_text=research.combined_text,
            news_title=selected.title,
            news_source=selected.source,
            anchor_name=anchor_name,
            target_duration=20,
        )
    except Exception as exc:
        logger.exception("대본 생성 실패 (anchor=%s): %s", anchor_name, exc)
        await query.edit_message_text(
            f"대본 생성 중 오류가 발생했습니다: {exc}\n/news 명령으로 다시 시작하세요."
        )
        return ConversationHandler.END

    context.user_data["script_content"] = script_result.get("content", "")
    context.user_data["script_result"] = script_result

    project = new_news_project(
        news_item_id=news_id,
        telegram_chat_id=update.effective_chat.id,
        anchor_character=anchor_name,
        status="scripting",
        script_content=script_result.get("content", ""),
        title=script_result.get("title", ""),
    )

    from telegram_bot.handlers.news_views import _create_news_project_artifacts
    proj_dir, proj_dir_name = _create_news_project_artifacts(
        project=project,
        script_result=script_result,
        news_id=news_id,
        chat_id=update.effective_chat.id,
        anchor_name=anchor_name,
    )
    if proj_dir:
        context.user_data["project_dir"] = proj_dir
        context.user_data["project_dir_name"] = proj_dir_name

    context.user_data["news_project_id"] = project.id
    context.user_data["news_project"] = project

    preview = script_result.get("content", "")[:_SCRIPT_PREVIEW_LEN]
    duration = script_result.get("estimated_duration", 0)

    script_text = (
        "대본 생성 완료!\n\n"
        f"제목: {script_result.get('title', selected.title)}\n"
        f"앵커: {anchor_data['display_name']}\n"
        f"예상 길이: {duration}초\n\n"
        f"{preview}"
        + ("..." if len(script_result.get("content", "")) > _SCRIPT_PREVIEW_LEN else "")
    )

    await query.edit_message_text(
        script_text,
        reply_markup=_make_script_keyboard(),
    )
    return States.SCRIPT_REVIEW


@check_authorized
async def script_full_view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """대본 전체 보기 콜백. 전체 대본을 별도 메시지로 전송한다.

    callback_data: "script_full"

    Returns:
        States.SCRIPT_REVIEW (대본 검토 대기 유지)
    """
    query = update.callback_query
    await query.answer()

    content: str = context.user_data.get("script_content", "")
    if not content:
        await query.answer("대본이 없습니다.", show_alert=True)
        return States.SCRIPT_REVIEW

    for part in _split_message(f"[전체 대본]\n\n{content}"):
        await update.effective_chat.send_message(part)

    return States.SCRIPT_REVIEW


@check_authorized
async def script_confirmed_light(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """라이트 시나리오 선택. 대본 유지, 카메라/액션만 생성.

    callback_data: "confirm_light"
    """
    query = update.callback_query
    await query.answer()
    context.user_data["scenario_mode"] = "light"
    await query.edit_message_text("대본이 확인되었습니다. 라이트 시나리오를 생성합니다...")
    from telegram_bot.handlers.generate import scenario_review
    return await scenario_review(update, context)


@check_authorized
async def script_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """일반 시나리오 선택. Claude가 전체 시나리오 생성.

    callback_data: "confirm"

    Returns:
        States.SCENARIO_REVIEW (시나리오 검토 대기)
    """
    query = update.callback_query
    await query.answer()
    context.user_data["scenario_mode"] = "normal"
    await query.edit_message_text("대본이 확인되었습니다. 일반 시나리오를 생성합니다...")

    # generate.py의 scenario_review를 직접 호출하여 시나리오 생성
    from telegram_bot.handlers.generate import scenario_review
    return await scenario_review(update, context)


@check_authorized
async def script_regenerate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """대본 재생성 콜백. 현재 앵커로 대본을 다시 생성한다.

    callback_data: "regenerate"

    Returns:
        States.SCRIPT_REVIEW (대본 검토 대기)
    """
    query = update.callback_query
    await query.answer()

    await query.edit_message_text("대본을 재생성하는 중...")

    anchor_name: str = context.user_data.get("selected_anchor", "")
    anchor_data = ANCHOR_CHARACTERS.get(anchor_name)
    news_id: str = context.user_data.get("selected_news_id", "")
    news_list: list[NewsItem] = context.user_data.get("current_news_list", [])
    research: Optional[ResearchResult] = context.user_data.get("research_data")
    selected: Optional[NewsItem] = next((n for n in news_list if n.id == news_id), None)

    if not anchor_name or anchor_data is None or research is None or selected is None:
        await query.edit_message_text("세션 데이터가 손실되었습니다. /news 명령으로 다시 시작하세요.")
        return ConversationHandler.END

    try:
        script_result = await generate_news_script(
            news_text=research.combined_text,
            news_title=selected.title,
            news_source=selected.source,
            anchor_name=anchor_name,
            target_duration=20,
        )
    except Exception as exc:
        logger.exception("대본 재생성 실패 (anchor=%s): %s", anchor_name, exc)
        await query.edit_message_text(
            f"대본 재생성 중 오류가 발생했습니다: {exc}\n/news 명령으로 다시 시작하세요."
        )
        return ConversationHandler.END

    context.user_data["script_content"] = script_result.get("content", "")
    context.user_data["script_result"] = script_result

    preview = script_result.get("content", "")[:_SCRIPT_PREVIEW_LEN]
    duration = script_result.get("estimated_duration", 0)

    script_text = (
        "대본 재생성 완료!\n\n"
        f"제목: {script_result.get('title', selected.title)}\n"
        f"앵커: {anchor_data['display_name']}\n"
        f"예상 길이: {duration}초\n\n"
        f"{preview}"
        + ("..." if len(script_result.get("content", "")) > _SCRIPT_PREVIEW_LEN else "")
    )

    await query.edit_message_text(
        script_text,
        reply_markup=_make_script_keyboard(),
    )
    return States.SCRIPT_REVIEW


@check_authorized
async def script_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """직접 수정 콜백. 사용자 텍스트 입력 대기 상태로 전환한다.

    callback_data: "script_edit"

    Returns:
        States.SCRIPT_REVIEW (텍스트 입력 대기; MessageHandler로 수신)
    """
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "수정할 대본 전체를 입력하세요.\n"
        "입력한 텍스트가 현재 대본을 완전히 대체합니다.\n\n"
        "취소하려면 /cancel 을 입력하세요."
    )
    context.user_data["script_edit_mode"] = True
    return States.SCRIPT_REVIEW


@check_authorized
async def script_edit_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """사용자가 입력한 텍스트로 대본을 교체한다.

    script_edit_mode가 True일 때만 처리한다.

    Returns:
        States.SCRIPT_REVIEW (대본 검토 대기)
    """
    if not context.user_data.get("script_edit_mode"):
        return States.SCRIPT_REVIEW

    context.user_data["script_edit_mode"] = False

    new_content = update.message.text.strip()
    if not new_content:
        await update.message.reply_text("빈 텍스트는 저장되지 않습니다. 다시 입력하거나 /cancel 로 취소하세요.")
        context.user_data["script_edit_mode"] = True
        return States.SCRIPT_REVIEW

    context.user_data["script_content"] = new_content

    script_result: dict = context.user_data.get("script_result", {})
    script_result["content"] = new_content
    context.user_data["script_result"] = script_result

    preview = new_content[:_SCRIPT_PREVIEW_LEN]
    script_text = (
        "대본이 저장되었습니다.\n\n"
        f"{preview}"
        + ("..." if len(new_content) > _SCRIPT_PREVIEW_LEN else "")
    )

    await _send_long_message(
        update,
        script_text,
        reply_markup=_make_script_keyboard(),
    )
    return States.SCRIPT_REVIEW


# ─────────────────────────────────────────────
# 취소 콜백 (인라인 버튼)
# ─────────────────────────────────────────────


@check_authorized
async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """인라인 키보드의 [취소] 버튼 콜백.

    callback_data: "cancel"

    Returns:
        ConversationHandler.END
    """
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("작업이 취소되었습니다.")
    context.user_data.clear()
    return ConversationHandler.END



# 자동 알림 핸들러는 news_auto.py 로 분리 — 호환 re-export
from telegram_bot.handlers.news_auto import (  # noqa: E402
    _auto_process_one,
    _make_oldnews_keyboard,
    auto_news_pass,
    auto_news_start,
    cmd_auto,
    old_news_page_changed,
    old_news_pass,
    old_news_start,
)
