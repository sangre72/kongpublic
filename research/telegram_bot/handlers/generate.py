"""생성 대화 핸들러: 시나리오 검토 → 영상 생성 → 품질 검증 → 완료

대화 흐름:
    news.script_confirmed()
        → scenario_review()     [States.SCENARIO_REVIEW]
        → scene_edit_start()    [States.SCENE_EDIT]
        → scene_field_edit()    [States.SCENE_EDIT]
        → generate_start()      [States.GENERATE]
        → verify()              [States.VERIFY]
        → verify_complete()     [States.COMPLETE]
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest, RetryAfter
from telegram.ext import ContextTypes, ConversationHandler

from telegram_bot.constants import (
    ANCHOR_CHARACTERS,
    CALLBACK_CANCEL,
    States,
)
from telegram_bot.handlers.common import check_authorized
from telegram_bot.handlers.generate_helpers import (
    _poll_progress,
    _video_generation_factory,
)
from telegram_bot.queue import JobStatus, video_queue
from telegram_bot.services.news_scenario_service import (
    edit_scene,
    generate_scenario,
    generate_light_scenario,
    load_anchor_character_data,
    regenerate_scenario,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# 내부 상수
# ─────────────────────────────────────────────

_POLL_INTERVAL_SEC = 2      # 진행률 폴링 간격 (flood limit 대응)
_MAX_VIDEO_BYTES = 50 * 1024 * 1024   # 50 MB 텔레그램 제한
_NARRATION_PREVIEW_LEN = 20           # 씬 목록에서 나레이션 미리보기 글자 수
_SCENE_EDIT_FIELDS = ("narration", "video_prompt", "duration")

# context.user_data 키
_KEY_SCENARIO = "scenario_data"
_KEY_PROJECT_ID = "news_project_id"
_KEY_ANCHOR = "selected_anchor"
_KEY_SCRIPT = "script_content"
_KEY_SCENE_NO = "editing_scene_number"
_KEY_SCENE_FIELD = "editing_scene_field"
_KEY_JOB_ID = "current_job_id"
_KEY_RESULT_PATH = "result_video_path"


# ─────────────────────────────────────────────
# 키보드 빌더
# ─────────────────────────────────────────────


def _make_scenario_keyboard(scenes: list[dict]) -> InlineKeyboardMarkup:
    """시나리오 검토 화면 인라인 키보드.

    [확인 → 생성] [씬1 편집] [씬2 편집] ... [재생성] [취소]
    """
    rows: list[list[InlineKeyboardButton]] = []

    # 씬 편집 버튼 (2열)
    scene_row: list[InlineKeyboardButton] = []
    for scene in scenes:
        sn = scene.get("scene_number", 0)
        btn = InlineKeyboardButton(
            f"씬{sn} 편집",
            callback_data=f"scene_edit_{sn}",
        )
        scene_row.append(btn)
        if len(scene_row) == 3:
            rows.append(scene_row)
            scene_row = []
    if scene_row:
        rows.append(scene_row)

    rows.append([InlineKeyboardButton("영상 모드 선택 →", callback_data="video_mode_select")])
    rows.append([InlineKeyboardButton("재생성", callback_data="scenario_regenerate")])
    rows.append([InlineKeyboardButton("취소", callback_data=CALLBACK_CANCEL)])
    return InlineKeyboardMarkup(rows)


def _make_scene_edit_keyboard(scene_number: int) -> InlineKeyboardMarkup:
    """씬 편집 화면 인라인 키보드."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("나레이션 수정", callback_data=f"scene_field_narration_{scene_number}")],
        [InlineKeyboardButton("프롬프트 수정", callback_data=f"scene_field_video_prompt_{scene_number}")],
        [InlineKeyboardButton("길이 변경", callback_data=f"scene_field_duration_{scene_number}")],
        [InlineKeyboardButton("돌아가기", callback_data="scene_back")],
        [InlineKeyboardButton("취소", callback_data=CALLBACK_CANCEL)],
    ])


def _make_verify_keyboard(scenes: list[dict]) -> InlineKeyboardMarkup:
    """품질 검증 화면 인라인 키보드."""
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton("미리보기 전송", callback_data="verify_preview")],
    ]

    # 씬 재생성 버튼 (2열)
    regen_row: list[InlineKeyboardButton] = []
    for scene in scenes:
        sn = scene.get("scene_number", 0)
        btn = InlineKeyboardButton(
            f"씬{sn} 재생성",
            callback_data=f"verify_regen_{sn}",
        )
        regen_row.append(btn)
        if len(regen_row) == 3:
            rows.append(regen_row)
            regen_row = []
    if regen_row:
        rows.append(regen_row)

    rows.append([InlineKeyboardButton("최종 확인", callback_data="verify_complete")])
    rows.append([InlineKeyboardButton("취소", callback_data=CALLBACK_CANCEL)])
    return InlineKeyboardMarkup(rows)


def _make_complete_keyboard() -> InlineKeyboardMarkup:
    """완료 화면 인라인 키보드."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("새 뉴스", callback_data="new_news")],
        [InlineKeyboardButton("취소", callback_data=CALLBACK_CANCEL)],
    ])


# ─────────────────────────────────────────────
# 유틸 함수
# ─────────────────────────────────────────────


def _build_scenario_text(scenario: dict) -> str:
    """시나리오 목록 메시지 텍스트 구성."""
    scenes: list[dict] = scenario.get("scenes", [])
    total_duration: int = scenario.get("total_duration", 0)

    lines = [f"시나리오 ({len(scenes)}개 씬, 총 {total_duration}초)\n"]
    for scene in scenes:
        sn = scene.get("scene_number", "?")
        narration = scene.get("narration", "")
        preview = narration[:_NARRATION_PREVIEW_LEN]
        if len(narration) > _NARRATION_PREVIEW_LEN:
            preview += "..."
        duration = scene.get("duration", 0)
        lines.append(f"씬{sn}: {preview} / {duration}초")

    return "\n".join(lines)


def _build_scene_text(scene: dict) -> str:
    """씬 편집 화면 메시지 텍스트 구성."""
    sn = scene.get("scene_number", "?")
    narration = scene.get("narration", "")
    video_prompt = scene.get("video_prompt", "")
    duration = scene.get("duration", 0)

    return (
        f"씬 {sn} 편집\n\n"
        f"나레이션: \"{narration}\"\n"
        f"영상 프롬프트: \"{video_prompt}\"\n"
        f"길이: {duration}초"
    )


async def _safe_edit_message(
    bot,
    chat_id: int,
    message_id: int,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
) -> None:
    """메시지 편집 시 BadRequest(동일 텍스트) 예외를 무시한다."""
    try:
        kwargs = {"chat_id": chat_id, "message_id": message_id, "text": text}
        if reply_markup is not None:
            kwargs["reply_markup"] = reply_markup
        await bot.edit_message_text(**kwargs)
    except BadRequest as e:
        if "message is not modified" not in str(e).lower():
            logger.warning("edit_message_text 실패 (chat=%s, msg=%s): %s", chat_id, message_id, e)


# ─────────────────────────────────────────────
# 진행률 폴링 태스크
# ─────────────────────────────────────────────


@check_authorized
async def scenario_review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """대본 확인 후 시나리오를 생성하고 씬 목록을 표시한다.

    news.py의 script_confirmed에서 States.SCENARIO_REVIEW로 전환된 후 진입.

    Returns:
        States.SCENARIO_REVIEW (시나리오 검토 대기)
    """
    query = update.callback_query
    if query:
        await query.answer()

    script_content: str = context.user_data.get(_KEY_SCRIPT, "")
    anchor_name: str = context.user_data.get(_KEY_ANCHOR, "")

    if not script_content or not anchor_name:
        msg = "세션 데이터가 손실되었습니다. /news 명령으로 다시 시작하세요."
        if query:
            await query.edit_message_text(msg)
        else:
            await update.effective_message.reply_text(msg)
        return ConversationHandler.END

    # 진행 메시지 전송
    progress_msg = await update.effective_chat.send_message("시나리오를 생성하는 중...")

    # 캐릭터 시트 로드 (없으면 빈 dict)
    character_data: dict = load_anchor_character_data(anchor_name) or {}

    scenario_mode = context.user_data.get("scenario_mode", "light")

    try:
        if scenario_mode == "light":
            result = await generate_light_scenario(
                script_content=script_content,
                anchor_name=anchor_name,
                character_data=character_data,
                target_duration=20,
            )
        else:
            result = await generate_scenario(
                script_content=script_content,
                anchor_name=anchor_name,
                character_data=character_data,
                target_duration=60,
            )
    except Exception as exc:
        logger.exception("시나리오 생성 예외 (anchor=%s, mode=%s): %s", anchor_name, scenario_mode, exc)
        await progress_msg.edit_text(
            f"시나리오 생성 중 오류가 발생했습니다: {exc}\n/news 명령으로 다시 시작하세요."
        )
        return ConversationHandler.END

    if not result.get("success"):
        error = result.get("error", "알 수 없는 오류")
        await progress_msg.edit_text(
            f"시나리오 생성 실패: {error}\n/news 명령으로 다시 시작하세요."
        )
        return ConversationHandler.END

    context.user_data[_KEY_SCENARIO] = result

    # project.json에 시나리오 결과 저장
    try:
        import json as _json
        from pathlib import Path
        proj_dir = context.user_data.get("project_dir", "")
        if proj_dir:
            proj_file = Path(proj_dir) / "project.json"
            if proj_file.exists():
                with open(proj_file) as f:
                    proj = _json.load(f)
                sc = proj.get("scenario", {})
                sc["result"] = result
                proj["scenario"] = sc
                with open(proj_file, "w") as f:
                    _json.dump(proj, f, ensure_ascii=False, indent=2)
                logger.info("시나리오 결과 project.json 저장 완료")
    except Exception as exc:
        logger.warning("시나리오 project.json 저장 실패 (무시): %s", exc)

    scenario_text = _build_scenario_text(result)
    scenes = result.get("scenes", [])

    await progress_msg.edit_text(
        scenario_text,
        reply_markup=_make_scenario_keyboard(scenes),
    )
    return States.SCENARIO_REVIEW


@check_authorized
async def scenario_regenerate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """시나리오 재생성 콜백.

    callback_data: "scenario_regenerate"

    Returns:
        States.SCENARIO_REVIEW
    """
    query = update.callback_query
    await query.answer()

    script_content: str = context.user_data.get(_KEY_SCRIPT, "")
    anchor_name: str = context.user_data.get(_KEY_ANCHOR, "")

    if not script_content or not anchor_name:
        await query.edit_message_text("세션 데이터가 손실되었습니다. /news 명령으로 다시 시작하세요.")
        return ConversationHandler.END

    await query.edit_message_text("시나리오를 재생성하는 중...")

    character_data: dict = load_anchor_character_data(anchor_name) or {}

    try:
        result = await regenerate_scenario(
            script_content=script_content,
            anchor_name=anchor_name,
            character_data=character_data,
        )
    except Exception as exc:
        logger.exception("시나리오 재생성 예외 (anchor=%s): %s", anchor_name, exc)
        await query.edit_message_text(
            f"시나리오 재생성 중 오류가 발생했습니다: {exc}\n/news 명령으로 다시 시작하세요."
        )
        return ConversationHandler.END

    if not result.get("success"):
        error = result.get("error", "알 수 없는 오류")
        await query.edit_message_text(
            f"시나리오 재생성 실패: {error}\n/news 명령으로 다시 시작하세요."
        )
        return ConversationHandler.END

    context.user_data[_KEY_SCENARIO] = result

    scenario_text = _build_scenario_text(result)
    scenes = result.get("scenes", [])

    await query.edit_message_text(
        scenario_text,
        reply_markup=_make_scenario_keyboard(scenes),
    )
    return States.SCENARIO_REVIEW


@check_authorized
async def scene_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """특정 씬 편집 화면으로 전환한다.

    callback_data 형식: "scene_edit_{scene_number}"

    Returns:
        States.SCENE_EDIT
    """
    query = update.callback_query
    await query.answer()

    raw = query.data.removeprefix("scene_edit_")
    try:
        scene_number = int(raw)
    except ValueError:
        await query.answer("잘못된 씬 번호입니다.", show_alert=True)
        return States.SCENARIO_REVIEW

    scenario: dict = context.user_data.get(_KEY_SCENARIO, {})
    scenes = scenario.get("scenes", [])
    scene = next((s for s in scenes if s.get("scene_number") == scene_number), None)

    if scene is None:
        await query.answer(f"씬 {scene_number}을 찾을 수 없습니다.", show_alert=True)
        return States.SCENARIO_REVIEW

    context.user_data[_KEY_SCENE_NO] = scene_number

    await query.edit_message_text(
        _build_scene_text(scene),
        reply_markup=_make_scene_edit_keyboard(scene_number),
    )
    return States.SCENE_EDIT


@check_authorized
async def scene_field_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """씬 편집 필드 선택 콜백. 사용자 텍스트 입력 대기 상태로 전환한다.

    callback_data 형식: "scene_field_{field}_{scene_number}"
    예: "scene_field_narration_2", "scene_field_duration_3"

    Returns:
        States.SCENE_EDIT (텍스트 입력 대기)
    """
    query = update.callback_query
    await query.answer()

    raw = query.data.removeprefix("scene_field_")
    # field_name에 언더스코어가 포함될 수 있으므로 마지막 언더스코어 기준으로 분리
    parts = raw.rsplit("_", 1)
    if len(parts) != 2:
        await query.answer("잘못된 요청입니다.", show_alert=True)
        return States.SCENE_EDIT

    field, scene_num_str = parts
    try:
        scene_number = int(scene_num_str)
    except ValueError:
        await query.answer("잘못된 씬 번호입니다.", show_alert=True)
        return States.SCENE_EDIT

    context.user_data[_KEY_SCENE_NO] = scene_number
    context.user_data[_KEY_SCENE_FIELD] = field

    field_labels = {
        "narration": "나레이션",
        "video_prompt": "영상 프롬프트 (영어)",
        "duration": "길이 (초 단위 숫자)",
    }
    label = field_labels.get(field, field)

    await query.edit_message_text(
        f"씬 {scene_number}의 {label}을 입력하세요.\n\n취소하려면 /cancel 을 입력하세요."
    )
    return States.SCENE_EDIT


@check_authorized
async def scene_field_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """사용자가 입력한 값으로 씬 필드를 수정한다.

    scene_field_select() 후 사용자가 텍스트 메시지를 전송하면 호출된다.

    Returns:
        States.SCENE_EDIT (씬 편집 화면으로 복귀)
    """
    scene_number: Optional[int] = context.user_data.get(_KEY_SCENE_NO)
    field: Optional[str] = context.user_data.get(_KEY_SCENE_FIELD)

    if scene_number is None or field is None:
        await update.effective_message.reply_text(
            "편집할 씬이 선택되지 않았습니다. /news 명령으로 다시 시작하세요."
        )
        return ConversationHandler.END

    new_value = update.message.text.strip()
    if not new_value:
        await update.message.reply_text(
            "빈 값은 저장되지 않습니다. 다시 입력하거나 /cancel 로 취소하세요."
        )
        return States.SCENE_EDIT

    scenario: dict = context.user_data.get(_KEY_SCENARIO, {})
    updated = edit_scene(scenario, scene_number, field, new_value)

    if not updated.get("success"):
        error = updated.get("error", "알 수 없는 오류")
        await update.message.reply_text(
            f"씬 수정 실패: {error}\n다시 입력하거나 /cancel 로 취소하세요."
        )
        return States.SCENE_EDIT

    context.user_data[_KEY_SCENARIO] = updated
    context.user_data.pop(_KEY_SCENE_FIELD, None)

    scenes = updated.get("scenes", [])
    scene = next((s for s in scenes if s.get("scene_number") == scene_number), None)

    reply_text = f"씬 {scene_number} 수정 완료!"
    if scene:
        reply_text += f"\n\n{_build_scene_text(scene)}"

    await update.message.reply_text(
        reply_text,
        reply_markup=_make_scene_edit_keyboard(scene_number),
    )
    return States.SCENE_EDIT


@check_authorized
async def scene_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """씬 편집에서 시나리오 검토 화면으로 돌아간다.

    callback_data: "scene_back"

    Returns:
        States.SCENARIO_REVIEW
    """
    query = update.callback_query
    await query.answer()

    context.user_data.pop(_KEY_SCENE_NO, None)
    context.user_data.pop(_KEY_SCENE_FIELD, None)

    scenario: dict = context.user_data.get(_KEY_SCENARIO, {})
    scenes = scenario.get("scenes", [])

    if not scenes:
        await query.edit_message_text("시나리오 데이터가 없습니다. /news 명령으로 다시 시작하세요.")
        return ConversationHandler.END

    await query.edit_message_text(
        _build_scenario_text(scenario),
        reply_markup=_make_scenario_keyboard(scenes),
    )
    return States.SCENARIO_REVIEW


@check_authorized
async def video_mode_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """시나리오 검토 후 영상 모드 선택 화면을 표시한다.

    callback_data: "video_mode_select"

    Returns:
        States.VIDEO_MODE_SELECT (영상 모드 선택 대기)
    """
    query = update.callback_query
    await query.answer()

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("AI 쇼츠 ($0.87)", callback_data="video_mode:shorts"),
            InlineKeyboardButton("슬라이드쇼 ($0.09)", callback_data="video_mode:slideshow"),
        ],
        [InlineKeyboardButton("취소", callback_data=CALLBACK_CANCEL)],
    ])

    await query.edit_message_text(
        "영상 생성 모드를 선택하세요:\n\n"
        "AI 쇼츠: AI가 캐릭터 영상을 직접 생성합니다 (고품질, 비용 높음)\n"
        "슬라이드쇼: 이미지 슬라이드쇼로 빠르게 제작합니다 (저비용)",
        reply_markup=keyboard,
    )
    return States.VIDEO_MODE_SELECT


@check_authorized
async def video_mode_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """영상 모드 선택 완료. 선택된 모드를 저장하고 영상 생성을 시작한다.

    callback_data: "video_mode:shorts" | "video_mode:slideshow"

    Returns:
        States.GENERATE
    """
    query = update.callback_query
    await query.answer()

    mode = query.data.removeprefix("video_mode:")
    if mode not in ("shorts", "slideshow"):
        await query.edit_message_text("알 수 없는 모드입니다. /news 명령으로 다시 시작하세요.")
        return ConversationHandler.END

    context.user_data["video_mode"] = mode
    return await generate_start(update, context)


@check_authorized
async def generate_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """시나리오 확정 후 영상 생성 작업을 큐에 등록한다.

    callback_data: "scenario_confirm" (하위 호환) 또는 video_mode_confirmed 경유

    진행률 폴링 태스크(poll_progress)를 asyncio.create_task로 백그라운드 실행한다.

    Returns:
        States.GENERATE
    """
    query = update.callback_query
    await query.answer()

    scenario: dict = context.user_data.get(_KEY_SCENARIO, {})
    anchor_name: str = context.user_data.get(_KEY_ANCHOR, "")
    project_id: str = context.user_data.get(_KEY_PROJECT_ID, "")
    video_mode: str = context.user_data.get("video_mode", "shorts")

    # 시나리오에 title이 없으면 script_result에서 가져오기
    if not scenario.get("title"):
        script_result = context.user_data.get("script_result", {})
        scenario["title"] = script_result.get("title", "뉴스")

    if not scenario.get("scenes"):
        await query.edit_message_text("시나리오가 없습니다. /news 명령으로 다시 시작하세요.")
        return ConversationHandler.END

    mode_label = "슬라이드쇼" if video_mode == "slideshow" else "AI 쇼츠"
    # 진행률 메시지 먼저 전송
    progress_msg = await update.effective_chat.send_message(
        f"{mode_label} 영상 생성을 시작합니다. 잠시 기다려주세요..."
    )

    chat_id = update.effective_chat.id
    message_id = progress_msg.message_id

    script_content: str = context.user_data.get(_KEY_SCRIPT, "")

    try:
        job = await video_queue.enqueue(
            _video_generation_factory,
            chat_id=chat_id,
            message_id=message_id,
            news_project_id=project_id,
            scenario=scenario,
            anchor_name=anchor_name,
            script_content=script_content,
            video_mode=video_mode,
        )
    except Exception as exc:
        logger.exception("작업 큐 등록 실패: %s", exc)
        await progress_msg.edit_text(
            f"영상 생성 작업 등록에 실패했습니다: {exc}\n/news 명령으로 다시 시작하세요."
        )
        return ConversationHandler.END

    context.user_data[_KEY_JOB_ID] = job.id

    # 원본 시나리오 확인 메시지 편집 (중복 메시지 방지)
    try:
        await query.edit_message_text("시나리오가 확정되었습니다. 영상 생성 대기열에 등록했습니다.")
    except BadRequest:
        pass

    # 진행률 폴링 백그라운드 태스크 시작
    asyncio.create_task(
        _poll_progress(
            context=context,
            chat_id=chat_id,
            message_id=message_id,
            job_id=job.id,
        )
    )

    return States.GENERATE


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


# verify 단계는 generate_verify.py 로 분리 — 호환 re-export
from telegram_bot.handlers.generate_verify import (  # noqa: E402
    verify,
    verify_complete,
    verify_preview,
    verify_regenerate_scene,
)
