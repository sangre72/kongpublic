"""공통 핸들러: /start, /help, /cancel 및 인증 데코레이터"""

import logging
from functools import wraps
from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from telegram_bot.config import load_config

logger = logging.getLogger(__name__)

_START_MESSAGE = (
    "🎬 뉴스 쇼츠 생성 봇입니다!\n"
    "\n"
    "명령어:\n"
    "/news - 새 뉴스 확인 및 영상 생성\n"
    "/status - 진행 중인 작업 상태\n"
    "/history - 최근 생성 이력\n"
    "/help - 도움말\n"
    "/cancel - 현재 작업 취소"
)

_HELP_MESSAGE = (
    "도움말\n"
    "\n"
    "이 봇은 최신 뉴스를 가져와 쇼츠 영상을 자동으로 생성합니다.\n"
    "\n"
    "사용 순서:\n"
    "1. /news 명령으로 최신 뉴스를 확인합니다.\n"
    "2. 원하는 뉴스를 선택합니다.\n"
    "3. 앵커 스타일을 고릅니다.\n"
    "4. 대본과 시나리오를 검토·수정합니다.\n"
    "5. 생성을 시작하면 영상이 완성되면 전송됩니다.\n"
    "\n"
    "명령어:\n"
    "/news - 새 뉴스 확인 및 영상 생성\n"
    "/status - 진행 중인 작업 상태\n"
    "/history - 최근 생성 이력\n"
    "/cancel - 현재 작업 취소"
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """봇 시작 메시지 + 사용 가능한 명령어 안내"""
    await update.message.reply_text(_START_MESSAGE)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """도움말 메시지"""
    await update.message.reply_text(_HELP_MESSAGE)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """현재 대화를 취소하고 ConversationHandler.END를 반환합니다."""
    await update.message.reply_text("작업이 취소되었습니다.")
    return ConversationHandler.END


def check_authorized(func: Callable) -> Callable:
    """인증 데코레이터: config의 allowed_chat_ids에 있는 사용자만 허용합니다.

    allowed_chat_ids가 비어있으면 모든 사용자를 허용합니다.
    목록에 없는 사용자는 '권한이 없습니다.' 메시지 후 ConversationHandler.END를 반환합니다.
    """

    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            config = load_config()
        except ValueError as exc:
            logger.error("설정 로드 실패: %s", exc)
            await update.effective_message.reply_text("봇 설정에 오류가 있습니다. 관리자에게 문의하세요.")
            return ConversationHandler.END

        chat_id = update.effective_chat.id

        if not config.allowed_chat_ids:
            logger.warning("allowed_chat_ids 미설정 — 모든 접근 차단 (chat_id: %d)", chat_id)
            await update.effective_message.reply_text("봇 허용 목록이 설정되지 않았습니다. 관리자에게 문의하세요.")
            return ConversationHandler.END

        if chat_id not in config.allowed_chat_ids:
            logger.warning("미허용 chat_id 접근 시도: %d", chat_id)
            await update.effective_message.reply_text("권한이 없습니다.")
            return ConversationHandler.END

        return await func(update, context)

    return wrapper
