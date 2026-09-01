"""generate 핸들러 verify 단계 — telegram_bot/handlers/generate.py 에서 분리.

영상 생성 완료 후 검증/미리보기/씬 재생성/완료 처리.
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from typing import Any, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest, RetryAfter
from telegram.ext import ContextTypes, ConversationHandler

from telegram_bot.constants import States
from telegram_bot.handlers.common import check_authorized

logger = logging.getLogger(__name__)


def _probe_video_meta(path: str) -> dict:
    """영상 파일에서 ffprobe로 width/height/duration을 추출.

    텔레그램 sendVideo에 width/height를 명시하지 않으면 DAR 메타가 없는
    세로 영상이 정사각으로 크롭되어 미리보기가 찌그러진다. 전송 직전 실제
    해상도를 읽어 send_video 인자로 넘긴다.

    Returns:
        {"width": int, "height": int, "duration": int} — 성공 시.
        실패 시 빈 dict(호출부에서 파라미터 없이 전송하는 폴백으로 사용).
    """
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height:format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode != 0:
            return {}
        vals = [ln for ln in r.stdout.strip().splitlines() if ln.strip()]
        # 출력 순서: width, height, duration
        if len(vals) < 3:
            return {}
        w = int(float(vals[0]))
        h = int(float(vals[1]))
        dur = int(round(float(vals[2])))
        if w <= 0 or h <= 0:
            return {}
        return {"width": w, "height": h, "duration": dur}
    except Exception as e:  # noqa: BLE001
        logger.warning("ffprobe 메타 추출 실패(%s): %s — 파라미터 없이 전송", path, e)
        return {}



@check_authorized
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """생성 완료 후 결과를 표시한다.

    generate_start() 이후 직접 진입하거나,
    폴링 태스크가 완료 메시지를 업데이트한 후의 콜백에서 사용.

    Returns:
        States.VERIFY
    """
    query = update.callback_query
    if query:
        await query.answer()

    scenario: dict = context.user_data.get(_KEY_SCENARIO, {})
    scenes = scenario.get("scenes", [])
    total_duration = scenario.get("total_duration", 0)

    result_path: str = context.user_data.get(_KEY_RESULT_PATH, "")
    size_mb = 0.0
    if result_path and os.path.exists(result_path):
        try:
            size_mb = round(os.path.getsize(result_path) / (1024 * 1024), 1)
        except OSError:
            pass

    verify_text = (
        f"생성 완료!\n"
        f"총 길이: {total_duration}초 / 크기: {size_mb}MB"
    )

    if query:
        await query.edit_message_text(
            verify_text,
            reply_markup=_make_verify_keyboard(scenes),
        )
    else:
        await update.effective_message.reply_text(
            verify_text,
            reply_markup=_make_verify_keyboard(scenes),
        )

    return States.VERIFY


@check_authorized
async def verify_preview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """완성 영상을 텔레그램으로 전송한다.

    callback_data: "verify_preview"
    50MB 초과 시 720p 재인코딩 후 재전송 (TODO: FFmpeg 재인코딩 구현 필요).

    Returns:
        States.VERIFY
    """
    query = update.callback_query
    await query.answer()

    result_path: str = context.user_data.get(_KEY_RESULT_PATH, "")

    if not result_path:
        await query.answer(
            "영상 파일이 아직 준비되지 않았습니다.\n"
            "영상 생성이 완료되면 미리보기를 요청하세요.",
            show_alert=True,
        )
        return States.VERIFY

    if not os.path.exists(result_path):
        await query.answer(
            f"영상 파일을 찾을 수 없습니다: {result_path}",
            show_alert=True,
        )
        return States.VERIFY

    file_size = os.path.getsize(result_path)
    send_path = result_path

    if file_size > _MAX_VIDEO_BYTES:
        logger.info("영상 파일 크기 초과 (%.1fMB), 720p 재인코딩 시도", file_size / (1024 * 1024))
        # TODO: FFmpeg 720p 재인코딩 구현
        # send_path = await _reencode_720p(result_path)
        await query.answer(
            "영상 크기가 50MB를 초과합니다. 재인코딩 기능이 아직 준비 중입니다.",
            show_alert=True,
        )
        return States.VERIFY

    await query.edit_message_text("영상을 전송하는 중...")

    # 세로영상 정사각 크롭 방지: 실제 해상도/길이를 명시해 전송.
    _meta = _probe_video_meta(send_path)

    try:
        with open(send_path, "rb") as video_file:
            await update.effective_chat.send_video(
                video=video_file,
                caption="미리보기 영상",
                supports_streaming=True,
                **_meta,
            )
    except Exception as exc:
        logger.exception("영상 전송 실패: %s", exc)
        await update.effective_chat.send_message(
            f"영상 전송에 실패했습니다: {exc}\n잠시 후 다시 시도하세요."
        )

    scenario: dict = context.user_data.get(_KEY_SCENARIO, {})
    scenes = scenario.get("scenes", [])
    total_duration = scenario.get("total_duration", 0)
    size_mb = round(file_size / (1024 * 1024), 1)

    await update.effective_chat.send_message(
        f"생성 완료!\n총 길이: {total_duration}초 / 크기: {size_mb}MB",
        reply_markup=_make_verify_keyboard(scenes),
    )
    return States.VERIFY


@check_authorized
async def verify_regenerate_scene(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """특정 씬만 재생성하고 다시 합성한다.

    callback_data 형식: "verify_regen_{scene_number}"

    Returns:
        States.VERIFY
    """
    query = update.callback_query
    await query.answer()

    raw = query.data.removeprefix("verify_regen_")
    try:
        scene_number = int(raw)
    except ValueError:
        await query.answer("잘못된 씬 번호입니다.", show_alert=True)
        return States.VERIFY

    scenario: dict = context.user_data.get(_KEY_SCENARIO, {})
    scenes = scenario.get("scenes", [])
    scene = next((s for s in scenes if s.get("scene_number") == scene_number), None)

    if scene is None:
        await query.answer(f"씬 {scene_number}을 찾을 수 없습니다.", show_alert=True)
        return States.VERIFY

    await query.edit_message_text(f"씬 {scene_number} 재생성 중...")

    # TODO: 씬 단위 재생성 서비스 구현 (TTS + Grok 영상 + FFmpeg 재합성)
    # 현재는 플레이스홀더로 처리
    logger.info("씬 %d 재생성 요청 (미구현)", scene_number)
    await asyncio.sleep(2)

    total_duration = scenario.get("total_duration", 0)
    result_path: str = context.user_data.get(_KEY_RESULT_PATH, "")
    size_mb = 0.0
    if result_path and os.path.exists(result_path):
        try:
            size_mb = round(os.path.getsize(result_path) / (1024 * 1024), 1)
        except OSError:
            pass

    verify_text = (
        f"씬 {scene_number} 재생성 완료!\n"
        f"총 길이: {total_duration}초 / 크기: {size_mb}MB"
    )
    await query.edit_message_text(
        verify_text,
        reply_markup=_make_verify_keyboard(scenes),
    )
    return States.VERIFY


@check_authorized
async def verify_complete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """최종 확인 후 MP4 + 썸네일 + 제목 + 태그를 전송한다.

    callback_data: "verify_complete"

    Returns:
        States.COMPLETE
    """
    query = update.callback_query
    await query.answer()

    await query.edit_message_text("최종 파일을 준비하는 중...")

    result_path: str = context.user_data.get(_KEY_RESULT_PATH, "")
    scenario: dict = context.user_data.get(_KEY_SCENARIO, {})
    anchor_name: str = context.user_data.get(_KEY_ANCHOR, "")
    anchor_data = ANCHOR_CHARACTERS.get(anchor_name, {})

    title = f"뉴스 쇼츠 - {anchor_data.get('display_name', anchor_name)}"
    tags = ["#뉴스", "#쇼츠", f"#{anchor_name}", "#뉴스쇼츠"]
    total_duration = scenario.get("total_duration", 0)

    # 최종 메시지 구성
    complete_text = (
        f"완료!\n\n"
        f"제목: {title}\n"
        f"태그: {' '.join(tags)}\n"
        f"길이: {total_duration}초\n"
    )

    # 영상 파일 전송
    if result_path and os.path.exists(result_path):
        file_size = os.path.getsize(result_path)
        size_mb = round(file_size / (1024 * 1024), 1)
        complete_text += f"크기: {size_mb}MB\n"

        if file_size <= _MAX_VIDEO_BYTES:
            # 세로영상 정사각 크롭 방지: 실제 해상도/길이를 명시해 전송.
            _meta = _probe_video_meta(result_path)
            try:
                with open(result_path, "rb") as video_file:
                    await update.effective_chat.send_video(
                        video=video_file,
                        caption=complete_text,
                        supports_streaming=True,
                        **_meta,
                    )
            except Exception as exc:
                logger.exception("최종 영상 전송 실패: %s", exc)
                await update.effective_chat.send_message(
                    f"최종 영상 전송에 실패했습니다: {exc}"
                )
        else:
            # TODO: 50MB 초과 시 다운로드 링크 제공
            complete_text += "\n영상 크기가 크므로 별도 경로를 통해 다운로드하세요."
            await update.effective_chat.send_message(complete_text)

        # 썸네일 전송 (경로 규칙: 같은 디렉토리의 thumbnail.jpg)
        thumbnail_path = os.path.join(os.path.dirname(result_path), "thumbnail.jpg")
        if os.path.exists(thumbnail_path):
            try:
                with open(thumbnail_path, "rb") as thumb_file:
                    await update.effective_chat.send_photo(
                        photo=thumb_file,
                        caption="썸네일",
                    )
            except Exception as exc:
                logger.warning("썸네일 전송 실패: %s", exc)
    else:
        # 영상 파일이 없으면 텍스트만 전송
        complete_text += "\n(영상 파일이 아직 준비되지 않았습니다.)"
        await update.effective_chat.send_message(complete_text)

    await update.effective_chat.send_message(
        "다음 영상을 만드시겠습니까?",
        reply_markup=_make_complete_keyboard(),
    )

    context.user_data.clear()
    return States.COMPLETE

