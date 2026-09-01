"""뉴스 핸들러용 키보드/메시지 빌더.

handlers/news.py 에서 분리한 InlineKeyboard 빌더와 메시지 분할 유틸.
"""
from __future__ import annotations

import logging
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

from telegram_bot.constants import (
    ANCHOR_CHARACTERS,
    CALLBACK_ANCHOR_PREFIX,
    CALLBACK_CANCEL,
    CALLBACK_CONFIRM,
    CALLBACK_NEWS_PREFIX,
    CALLBACK_REGENERATE,
    CALLBACK_TOPIC_PREFIX,
    NEWS_TOPICS,
)
from telegram_bot.models import NewsItem

logger = logging.getLogger(__name__)

_NEWS_PAGE_SIZE = 5          # 한 페이지에 표시할 뉴스 수
_MSG_MAX_LEN = 4096          # 텔레그램 메시지 최대 길이


def _split_message(text: str, max_len: int = _MSG_MAX_LEN) -> list[str]:
    """텔레그램 메시지 길이 제한 초과 시 분할한다."""
    if len(text) <= max_len:
        return [text]
    parts: list[str] = []
    while text:
        parts.append(text[:max_len])
        text = text[max_len:]
    return parts


async def _send_long_message(
    update: Update,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
) -> None:
    """4096자를 초과하는 메시지를 분할 전송한다.

    마지막 파트에만 reply_markup을 붙인다.
    """
    parts = _split_message(text)
    for i, part in enumerate(parts):
        markup = reply_markup if i == len(parts) - 1 else None
        await update.effective_message.reply_text(part, reply_markup=markup)


def _make_topic_keyboard() -> InlineKeyboardMarkup:
    """토픽 선택 인라인 키보드를 생성한다."""
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for i, topic in enumerate(NEWS_TOPICS):
        btn = InlineKeyboardButton(
            topic["label"],
            callback_data=f"{CALLBACK_TOPIC_PREFIX}{topic['key']}",
        )
        row.append(btn)
        if len(row) == 3 or i == len(NEWS_TOPICS) - 1:
            rows.append(row)
            row = []
    return InlineKeyboardMarkup(rows)


def _make_news_list_keyboard(
    news_list: list[NewsItem],
    page: int = 0,
) -> InlineKeyboardMarkup:
    """뉴스 목록 인라인 키보드를 생성한다.

    한 페이지에 _NEWS_PAGE_SIZE 건을 표시하고 [이전] [다음] [취소] 네비게이션을 붙인다.
    """
    start = page * _NEWS_PAGE_SIZE
    items = news_list[start : start + _NEWS_PAGE_SIZE]

    rows: list[list[InlineKeyboardButton]] = []
    for i, item in enumerate(items):
        label = item.title[:40] + "..." if len(item.title) > 40 else item.title
        rows.append(
            [InlineKeyboardButton(
                f"{start + i + 1}. {label}",
                callback_data=f"{CALLBACK_NEWS_PREFIX}{item.id}",
            )]
        )

    nav_row: list[InlineKeyboardButton] = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("이전", callback_data=f"news_page_{page - 1}"))
    if start + _NEWS_PAGE_SIZE < len(news_list):
        nav_row.append(InlineKeyboardButton("다음", callback_data=f"news_page_{page + 1}"))
    nav_row.append(InlineKeyboardButton("취소", callback_data=CALLBACK_CANCEL))
    rows.append(nav_row)

    return InlineKeyboardMarkup(rows)


def _make_research_keyboard() -> InlineKeyboardMarkup:
    """리서치 결과 확인 후 다음 단계 선택 키보드를 생성한다."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("앵커 선택 →", callback_data="research_approve")],
        [InlineKeyboardButton("추가 검색", callback_data="research_more")],
        [InlineKeyboardButton("다른 뉴스 선택", callback_data="research_back")],
        [InlineKeyboardButton("취소", callback_data=CALLBACK_CANCEL)],
    ])


async def _send_anchor_gallery(update: Update) -> None:
    """앵커 사진을 미디어 그룹으로 보내고, 하단에 선택 버튼을 전송한다."""
    from pathlib import Path
    from telegram import InputMediaPhoto

    sheet_dir = Path(__file__).resolve().parent.parent.parent / "character_sheets"
    anchors = list(ANCHOR_CHARACTERS.values())

    media_group = []
    for anchor in anchors:
        name = anchor["name"]
        display = anchor["display_name"]
        matching = sorted(sheet_dir.glob(f"*_{name}"), reverse=True)
        if matching:
            face_path = matching[0] / "face_front.png"
            if face_path.exists():
                media_group.append(
                    InputMediaPhoto(media=open(str(face_path), "rb"), caption=display)
                )

    if media_group:
        try:
            await update.effective_chat.send_media_group(media=media_group)
        except Exception as exc:
            logger.warning("앵커 사진 그룹 전송 실패: %s", exc)

    await update.effective_chat.send_message(
        "앵커를 선택하세요:",
        reply_markup=_make_anchor_keyboard(),
    )


def _make_anchor_keyboard() -> InlineKeyboardMarkup:
    """앵커 선택 인라인 키보드를 생성한다."""
    anchors = list(ANCHOR_CHARACTERS.values())
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for i, anchor in enumerate(anchors):
        btn = InlineKeyboardButton(
            anchor["display_name"],
            callback_data=f"{CALLBACK_ANCHOR_PREFIX}{anchor['name']}",
        )
        row.append(btn)
        if len(row) == 2 or i == len(anchors) - 1:
            rows.append(row)
            row = []
    rows.append([
        InlineKeyboardButton("랜덤", callback_data=f"{CALLBACK_ANCHOR_PREFIX}random"),
        InlineKeyboardButton("취소", callback_data=CALLBACK_CANCEL),
    ])
    return InlineKeyboardMarkup(rows)


def _create_news_project_artifacts(
    *,
    project,
    script_result: dict,
    news_id: str,
    chat_id: int,
    anchor_name: str,
) -> tuple[Optional[str], Optional[str]]:
    """뉴스 프로젝트 DB 저장 + UI 프로젝트 폴더(project.json) 생성.

    Returns: (proj_dir_path, proj_dir_name) — 실패하면 (None, None).
    """
    import json as _json
    import re as _re
    import unicodedata
    from datetime import datetime, timezone
    from pathlib import Path

    from database.repository import save_news_project
    from database import repository as _repo

    try:
        save_news_project({
            "id": project.id,
            "news_item_id": project.news_item_id,
            "project_id": "",
            "telegram_chat_id": chat_id,
            "anchor_character": anchor_name,
            "status": project.status,
            "script_content": project.script_content,
            "title": script_result.get("title", ""),
            "scenario_json": "",
            "research_data": "",
            "related_news_ids": "",
            "final_video_path": "",
            "thumbnail_path": "",
            "description": "",
            "tags": "",
            "error_message": "",
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        })
        logger.info("뉴스 프로젝트 DB 저장 완료: %s", project.id)
    except Exception as exc:
        logger.error("뉴스 프로젝트 DB 저장 실패: %s", exc)

    try:
        raw_title = script_result.get("title", "news")
        raw_title = unicodedata.normalize("NFC", raw_title)
        safe_title = _re.sub(r'[\\/:*?"<>|!@#$%^&\s]+', "_", raw_title)
        safe_title = _re.sub(r"_+", "_", safe_title).strip().strip("._")[:80]
        proj_dir_name = f"{datetime.now().strftime('%Y%m%d')}_{anchor_name}_{safe_title}"
        proj_dir = Path(__file__).parent.parent.parent / "projects" / proj_dir_name
        proj_dir.mkdir(parents=True, exist_ok=True)

        proj_json = {
            "id": proj_dir_name,
            "title": proj_dir_name,
            "version": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "page": {
                "videoMode": "shorts",
                "scriptForScenario": script_result.get("content", ""),
            },
            "scenario": {
                "topic": proj_dir_name,
                "style": "informative",
                "targetDuration": 20,
                "sourceScript": script_result.get("content", ""),
                "selectedCharacterNames": [anchor_name],
                "result": None,
            },
        }
        with open(proj_dir / "project.json", "w") as f:
            _json.dump(proj_json, f, ensure_ascii=False, indent=2)

        _repo.save_project(
            project_id=proj_dir_name,
            title=proj_dir_name,
            state_json=_json.dumps(proj_json, ensure_ascii=False),
            video_mode="shorts",
            created_at=proj_json["created_at"],
            updated_at=proj_json["updated_at"],
            scene_count=0,
            has_tts=False,
            has_video=False,
            media_dir=str(proj_dir),
        )
        logger.info("UI 프로젝트 중간 저장 + DB 등록 완료: %s", proj_dir)
        return str(proj_dir), proj_dir_name
    except Exception as exc:
        logger.warning("UI 프로젝트 중간 저장 실패 (무시): %s", exc)
        return None, None


def _make_script_keyboard() -> InlineKeyboardMarkup:
    """대본 검토 후 다음 단계 선택 키보드를 생성한다."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("전체 보기", callback_data="script_full")],
        [
            InlineKeyboardButton("라이트 시나리오", callback_data="confirm_light"),
            InlineKeyboardButton("일반 시나리오", callback_data=CALLBACK_CONFIRM),
        ],
        [InlineKeyboardButton("재생성", callback_data=CALLBACK_REGENERATE)],
        [InlineKeyboardButton("직접 수정", callback_data="script_edit")],
        [InlineKeyboardButton("취소", callback_data=CALLBACK_CANCEL)],
    ])
