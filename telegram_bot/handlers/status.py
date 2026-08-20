"""상태 핸들러: /status, /history 명령.

독립 CommandHandler로 등록되며 ConversationHandler 밖에서 동작합니다.
"""

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from database.repository import list_news_projects
from telegram_bot.handlers.common import check_authorized
from telegram_bot.queue import video_queue

logger = logging.getLogger(__name__)

# 텔레그램 메시지 최대 길이
_MAX_MSG_LEN = 4096

# 뉴스 프로젝트 상태별 이모지
_STATUS_EMOJI: dict[str, str] = {
    "created": "⏳",
    "researching": "🔍",
    "scripting": "📝",
    "scenario": "🎬",
    "generating": "🎨",
    "composing": "🔧",
    "verifying": "🔍",
    "complete": "✅",
    "failed": "❌",
}

_UNKNOWN_EMOJI = "❓"


@check_authorized
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """현재 작업 상태 표시 (/status 명령).

    video_queue에서 RUNNING 상태의 작업을 조회하여 진행 현황을 표시합니다.
    활성 작업이 없으면 /news 안내 메시지를 반환합니다.
    """
    active_job = video_queue.get_active_job()

    if active_job is None:
        await update.message.reply_text(
            "현재 진행 중인 작업이 없습니다.\n"
            "/news로 새 뉴스 영상을 만들어보세요!"
        )
        return

    created_at_str = _format_datetime(active_job.created_at)

    text = (
        "📊 현재 작업 상태\n"
        "\n"
        f"프로젝트: {active_job.news_project_id}\n"
        f"상태: {active_job.status.value}\n"
        f"진행률: {active_job.progress} ({active_job.progress_pct}%)\n"
        f"시작: {created_at_str}"
    )

    await update.message.reply_text(text)


@check_authorized
async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """최근 작업 이력 표시 (/history 명령).

    DB에서 최근 뉴스 프로젝트 10건을 조회하여 목록으로 표시합니다.
    조회된 프로젝트가 없으면 안내 메시지를 반환합니다.
    텔레그램 메시지 4096자 제한을 초과하면 잘라냅니다.
    """
    try:
        projects = list_news_projects(limit=10)
    except Exception as exc:
        logger.error("뉴스 프로젝트 이력 조회 실패: %s", exc)
        await update.message.reply_text(
            "이력 조회 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )
        return

    if not projects:
        await update.message.reply_text(
            "아직 생성 이력이 없습니다.\n"
            "/news로 첫 번째 뉴스 영상을 만들어보세요!"
        )
        return

    lines: list[str] = ["📜 최근 작업 이력\n"]

    for idx, project in enumerate(projects, start=1):
        status = project.get("status", "")
        emoji = _STATUS_EMOJI.get(status, _UNKNOWN_EMOJI)

        title = project.get("title", "") or project.get("id", "")[:8]
        anchor = project.get("anchor_character", "") or "-"
        created_at = _format_date(project.get("created_at", ""))

        if status == "failed":
            line = f"{idx}. {emoji} [{title}] {anchor} / {created_at} (실패)"
        else:
            line = f"{idx}. {emoji} [{title}] {anchor} / {created_at}"

        lines.append(line)

    text = "\n".join(lines)

    # 텔레그램 4096자 제한 처리
    if len(text) > _MAX_MSG_LEN:
        text = text[: _MAX_MSG_LEN - 3] + "..."

    await update.message.reply_text(text)


def _format_datetime(dt: datetime) -> str:
    """datetime 객체를 'YYYY-MM-DD HH:MM' 형식으로 변환."""
    try:
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(dt)


def _format_date(date_str: str) -> str:
    """ISO 날짜 문자열에서 'YYYY-MM-DD' 부분만 추출.

    파싱 실패 시 원본 문자열 그대로 반환합니다.
    """
    if not date_str:
        return "-"
    # ISO 8601: '2026-03-31T12:00:00' 또는 '2026-03-31 12:00:00'
    return date_str[:10]
