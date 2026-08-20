"""
텔레그램 봇 Application 생성, 핸들러 등록, 라이프사이클 관리

FastAPI와 동일 이벤트 루프에서 실행된다.
Application.run_polling() 대신 initialize() + start() + updater.start_polling() 패턴 사용.
"""

import asyncio
import logging
from typing import Optional

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from telegram_bot.config import load_config
from telegram_bot.constants import States
from telegram_bot.queue import video_queue

logger = logging.getLogger(__name__)

# 싱글턴 Application 인스턴스
_app: Optional[Application] = None

# 자동 뉴스 알림 대기 큐 (1건씩 순차 전송)
_pending_news_queue: list = []
# 중복 알림 방지는 DB 기반 (news_notified 테이블, 48시간 보관)


# ─────────────────────────────────────────────
# ConversationHandler 구성
# ─────────────────────────────────────────────

def _build_conversation_handler(conversation_timeout: int) -> ConversationHandler:
    """ConversationHandler를 생성한다.

    각 상태별 핸들러는 handlers/ 모듈의 실제 함수로 등록한다.

    Args:
        conversation_timeout: 대화 비활성 타임아웃 (초)

    Returns:
        ConversationHandler 인스턴스
    """
    from telegram_bot.handlers.news import (
        news_start,
        topic_selected,
        news_selected,
        news_page_changed,
        research_approved,
        research_back,
        anchor_selected,
        script_confirmed,
        script_confirmed_light,
        script_regenerate,
        script_edit_start,
        script_edit_received,
        script_full_view,
        cancel_callback as news_cancel_callback,
        auto_news_start,
        old_news_start,
        old_news_page_changed,
    )
    from telegram_bot.handlers.generate import (
        scenario_review,
        scenario_regenerate,
        scene_edit_start,
        scene_field_select,
        scene_field_edit,
        scene_back,
        video_mode_select,
        video_mode_confirmed,
        generate_start,
        verify,
        verify_preview,
        verify_regenerate_scene,
        verify_complete,
        cancel_callback as generate_cancel_callback,
    )
    from telegram_bot.handlers.common import cancel

    states: dict = {
        # 뉴스 토픽 선택 대기
        States.NEWS_FETCH: [
            CallbackQueryHandler(topic_selected, pattern="^topic_"),
        ],
        # 뉴스 목록 선택 대기
        # news_page_ / oldnews_page_ 먼저 등록하여 news_ / oldnews_ UUID 패턴과 구분
        States.NEWS_SELECT: [
            CallbackQueryHandler(news_page_changed, pattern="^news_page_"),
            CallbackQueryHandler(old_news_page_changed, pattern="^oldnews_page_"),
            CallbackQueryHandler(auto_news_start, pattern="^auto_news_"),
            CallbackQueryHandler(news_selected, pattern="^news_"),
            CallbackQueryHandler(news_cancel_callback, pattern="^cancel$"),
        ],
        # 리서치 결과 승인 대기
        States.RESEARCH: [
            CallbackQueryHandler(research_approved, pattern="^research_approve"),
            CallbackQueryHandler(research_back, pattern="^research_back"),
            CallbackQueryHandler(news_cancel_callback, pattern="^cancel$"),
        ],
        # 앵커 선택 대기
        States.ANCHOR_SELECT: [
            CallbackQueryHandler(anchor_selected, pattern="^anchor_"),
            CallbackQueryHandler(news_cancel_callback, pattern="^cancel$"),
        ],
        # 대본 검토 대기 (인라인 버튼 + 텍스트 직접 수정)
        States.SCRIPT_REVIEW: [
            CallbackQueryHandler(script_confirmed_light, pattern="^confirm_light$"),
            CallbackQueryHandler(script_confirmed, pattern="^confirm$"),
            CallbackQueryHandler(script_regenerate, pattern="^regenerate$"),
            CallbackQueryHandler(script_edit_start, pattern="^script_edit$"),
            CallbackQueryHandler(script_full_view, pattern="^script_full$"),
            CallbackQueryHandler(news_cancel_callback, pattern="^cancel$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, script_edit_received),
        ],
        # 시나리오 검토 대기
        States.SCENARIO_REVIEW: [
            CallbackQueryHandler(video_mode_select, pattern="^video_mode_select$"),
            CallbackQueryHandler(generate_start, pattern="^scenario_confirm$"),
            CallbackQueryHandler(scenario_regenerate, pattern="^scenario_regenerate$"),
            CallbackQueryHandler(scene_edit_start, pattern="^scene_edit_\\d+$"),
            CallbackQueryHandler(generate_cancel_callback, pattern="^cancel$"),
        ],
        # 영상 모드 선택 대기
        States.VIDEO_MODE_SELECT: [
            CallbackQueryHandler(video_mode_confirmed, pattern="^video_mode:"),
            CallbackQueryHandler(generate_cancel_callback, pattern="^cancel$"),
        ],
        # 씬 편집 대기
        States.SCENE_EDIT: [
            CallbackQueryHandler(scene_field_select, pattern="^scene_field_"),
            CallbackQueryHandler(scene_back, pattern="^scene_back$"),
            CallbackQueryHandler(generate_cancel_callback, pattern="^cancel$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, scene_field_edit),
        ],
        # 영상 생성 중 (폴링 대기)
        States.GENERATE: [
            CallbackQueryHandler(generate_cancel_callback, pattern="^cancel$"),
        ],
        # 영상 검증 대기
        States.VERIFY: [
            CallbackQueryHandler(verify_preview, pattern="^verify_preview$"),
            CallbackQueryHandler(verify_regenerate_scene, pattern="^verify_regen_\\d+$"),
            CallbackQueryHandler(verify_complete, pattern="^verify_complete$"),
            CallbackQueryHandler(generate_cancel_callback, pattern="^cancel$"),
        ],
        # 완료
        States.COMPLETE: [
            CallbackQueryHandler(news_start, pattern="^new_news$"),
            CallbackQueryHandler(generate_cancel_callback, pattern="^cancel$"),
        ],
    }

    # 슬래시 없이도 텍스트 명령 인식
    text_news = MessageHandler(filters.Regex(r"^[Nn][Ee][Ww][Ss]$") | filters.Regex(r"^뉴스$"), news_start)
    text_ons = MessageHandler(filters.Regex(r"^[Oo][Nn][Ss]$") | filters.Regex(r"^[Aa][Nn][Ss]$") | filters.Regex(r"^[Oo][Ll][Dd][Nn][Ee][Ww][Ss]$") | filters.Regex(r"^(올드뉴스|이전뉴스)$"), old_news_start)
    text_cancel = MessageHandler(filters.Regex(r"^(cancel|Cancel|취소|그만)$"), cancel)

    return ConversationHandler(
        entry_points=[
            CommandHandler("news", news_start),
            CommandHandler("oldnews", old_news_start),
            CommandHandler("ons", old_news_start),
            CallbackQueryHandler(auto_news_start, pattern="^auto_news_"),
            text_news,
            text_ons,
        ],
        states=states,
        fallbacks=[CommandHandler("cancel", cancel), text_cancel],
        conversation_timeout=conversation_timeout,
        allow_reentry=True,
    )


# ─────────────────────────────────────────────
# 뉴스 모니터링 콜백
# ─────────────────────────────────────────────

async def _on_new_news(new_items, allowed_chat_ids: list[int], scored=None) -> None:
    """새 뉴스 감지 시 중요도 높은 뉴스를 [영상화] [패스] 버튼과 함께 알림 전송.

    Args:
        new_items: 새로 감지된 NewsItem 목록
        allowed_chat_ids: 알림을 전송할 채팅 ID 목록
        scored: process_news에서 반환된 번역+중요도 결과 (없으면 원본 사용)
    """
    global _app

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    if _app is None or not allowed_chat_ids:
        return

    if not new_items:
        return

    # scored 결과로 번역 제목 + 중요도 매핑 구성
    scored_map: dict[str, dict] = {}
    if scored:
        for s in scored:
            scored_map[s["id"]] = s

    # 중요도 6+ 뉴스만 큐에 추가 (DB 기반 48시간 중복 체크)
    global _pending_news_queue

    from database.repository import is_news_notified, save_news_notified

    existing_titles = {n.title for n in _pending_news_queue}

    filtered_items = []
    for item in new_items[:10]:
        # 큐에 이미 있는 제목 스킵
        if item.title in existing_titles:
            continue
        # DB에서 48시간 내 유사 제목 알림 기록 체크
        if is_news_notified(item.title):
            logger.debug(f"이미 알림 보낸 뉴스 스킵: {item.title[:40]}")
            continue
        info = scored_map.get(item.id)
        if info and info.get("importance", 5) < 6:
            continue  # 중요도 낮은 뉴스 스킵
        filtered_items.append(item)

    if not filtered_items:
        logger.info("새 알림 대상 뉴스 없음, 스킵")
        return

    for item in filtered_items[:5]:
        _pending_news_queue.append(item)
        # DB에 알림 기록 저장 (48시간 보관)
        info = scored_map.get(item.id)
        save_news_notified(
            title=item.title,
            source=item.source,
            importance=info.get("importance", 5) if info else 5,
        )

    # scored_map을 모듈 레벨에 캐시 (send_next_news에서 참조)
    global _scored_cache
    _scored_cache.update(scored_map)

    # 현재 대기 중인 알림이 없으면 첫 번째 뉴스 전송
    if len(_pending_news_queue) == len(filtered_items[:5]):
        await _send_next_news(allowed_chat_ids)
    return


# scored 결과 캐시 (번역 재호출 방지)
_scored_cache: dict[str, dict] = {}


async def _send_next_news(allowed_chat_ids: list[int]) -> None:
    """대기 큐에서 다음 뉴스 1건을 텔레그램으로 전송한다."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    global _pending_news_queue, _scored_cache

    if not _pending_news_queue or _app is None:
        return

    item = _pending_news_queue[0]  # 꺼내지 않고 peek (패스/영상화 시 pop)

    # scored 캐시에서 번역 제목 + 중요도 가져오기 (재번역 없음)
    info = _scored_cache.get(item.id)
    if info:
        ko_title = info.get("title_ko", item.title)
        importance = info.get("importance", 5)
        reason = info.get("reason", "")
        # 중요도 이모지
        if importance >= 9:
            imp_emoji = "🔴"
        elif importance >= 7:
            imp_emoji = "🟠"
        else:
            imp_emoji = "🟡"
        imp_text = f"{imp_emoji} 중요도 {importance}/10"
        reason_text = f"\n💡 {reason}" if reason else ""
    else:
        ko_title = item.title
        imp_text = ""
        reason_text = ""

    source = f" ({item.source})" if item.source else ""
    remaining = len(_pending_news_queue) - 1
    remaining_text = f"\n\n📋 대기 뉴스 {remaining}건 더 있음" if remaining > 0 else ""
    text = f"{imp_text}\n📰 {ko_title}{source}{reason_text}{remaining_text}"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎬 영상화", callback_data=f"auto_news_{item.id}"),
            InlineKeyboardButton("⏭ 패스", callback_data=f"auto_pass_{item.id}"),
        ]
    ])

    for chat_id in allowed_chat_ids:
        try:
            await _app.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=keyboard,
            )
        except Exception as exc:
            logger.warning("뉴스 알림 전송 실패 (chat_id=%d, news=%s): %s", chat_id, item.id, exc)


# ─────────────────────────────────────────────
# 봇 라이프사이클
# ─────────────────────────────────────────────

async def start_bot() -> None:
    """텔레그램 봇을 시작한다.

    FastAPI startup 이벤트에서 asyncio.create_task()로 호출해야 한다.
    이벤트 루프를 블로킹하지 않기 위해 Application.run_polling() 대신
    initialize() -> start() -> updater.start_polling() 패턴을 사용한다.

    Raises:
        ValueError: TELEGRAM_BOT_TOKEN 미설정 시
        Exception: 봇 초기화 / 폴링 시작 실패 시
    """
    global _app

    try:
        config = load_config()
    except ValueError as e:
        logger.error("텔레그램 봇 설정 오류: %s", e)
        logger.warning("텔레그램 봇을 시작하지 않습니다.")
        return

    try:
        # Application 생성
        _app = Application.builder().token(config.token).build()

        # ConversationHandler 등록
        conv_handler = _build_conversation_handler(config.conversation_timeout)
        _app.add_handler(conv_handler)

        # 독립 명령어 핸들러 등록 (슬래시 + 텍스트 둘 다)
        from telegram_bot.handlers.common import cmd_start, cmd_help
        from telegram_bot.handlers.status import cmd_status, cmd_history
        from telegram_bot.handlers.news import auto_news_pass, old_news_pass, cmd_auto
        _app.add_handler(CommandHandler("start", cmd_start))
        _app.add_handler(CommandHandler("help", cmd_help))
        _app.add_handler(CommandHandler("status", cmd_status))
        _app.add_handler(CommandHandler("history", cmd_history))
        _app.add_handler(CommandHandler("auto", cmd_auto))
        _app.add_handler(MessageHandler(filters.Regex(r"^(help|Help|도움|도움말)$"), cmd_help))
        _app.add_handler(MessageHandler(filters.Regex(r"^(status|Status|상태)$"), cmd_status))
        _app.add_handler(MessageHandler(filters.Regex(r"^(history|History|이력|히스토리)$"), cmd_history))
        _app.add_handler(CallbackQueryHandler(auto_news_pass, pattern="^auto_pass_"))
        _app.add_handler(CallbackQueryHandler(old_news_pass, pattern="^oldnews_pass_"))

        # 큐 워커 시작 (비동기 백그라운드 태스크)
        asyncio.create_task(video_queue.worker(), name="video_queue_worker")
        logger.info("영상 생성 큐 워커 시작")

        # 봇 초기화 + 폴링 시작 (이벤트 루프 비블로킹)
        await _app.initialize()
        await _app.start()
        await _app.updater.start_polling(drop_pending_updates=True)

        logger.info("텔레그램 봇 시작 완료 (polling 모드)")

        # 뉴스 자동 모니터링 시작
        try:
            from telegram_bot.services.news_scraper import NewsScraper

            scraper = NewsScraper()

            async def on_new_news(new_items, scored=None):
                await _on_new_news(new_items, config.allowed_chat_ids, scored)

            asyncio.create_task(
                scraper.start_monitoring(
                    callback=on_new_news,
                    interval_seconds=config.news_check_interval,
                ),
                name="news_monitoring",
            )
            logger.info(
                "뉴스 모니터링 시작 (간격=%ds)", config.news_check_interval
            )
        except Exception as e:
            logger.warning("뉴스 모니터링 시작 실패 (봇은 정상 동작): %s", e)

    except Exception as e:
        logger.exception("텔레그램 봇 시작 중 오류 발생: %s", e)
        # 부분 초기화된 경우 정리 시도
        if _app is not None:
            try:
                await _app.shutdown()
            except Exception:
                pass
            _app = None
        raise


async def stop_bot() -> None:
    """텔레그램 봇을 안전하게 종료한다.

    FastAPI shutdown 이벤트에서 await으로 호출해야 한다.
    """
    global _app

    if _app is None:
        logger.info("텔레그램 봇이 실행 중이지 않습니다.")
        return

    try:
        logger.info("텔레그램 봇 종료 중...")
        await _app.updater.stop()
        await _app.stop()
        await _app.shutdown()
        logger.info("텔레그램 봇 종료 완료")
    except Exception as e:
        logger.exception("텔레그램 봇 종료 중 오류: %s", e)
    finally:
        _app = None


def get_app() -> Optional[Application]:
    """현재 Application 인스턴스를 반환한다.

    Returns:
        Application 인스턴스 또는 None (봇이 시작되지 않은 경우)
    """
    return _app
