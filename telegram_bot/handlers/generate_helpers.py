"""Generate handler 큰 헬퍼 — telegram_bot/handlers/generate.py 에서 분리.

- _poll_progress: 영상 생성 진행률 폴링
- _video_generation_factory: 영상 생성 워커 팩토리
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


async def _poll_progress(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    message_id: int,
    job_id: str,
) -> None:
    """영상 생성 진행률을 2초마다 폴링하여 메시지를 업데이트한다.

    작업 완료 또는 실패 시 verify 단계로 전환한다.
    """
    job = video_queue.get_job(job_id)
    if job is None:
        logger.error("진행률 폴링 대상 job 없음: job_id=%s", job_id)
        return

    while job.status in (JobStatus.PENDING, JobStatus.RUNNING):
        await asyncio.sleep(_POLL_INTERVAL_SEC)
        job = video_queue.get_job(job_id)
        if job is None:
            break

        status_icon = "생성 중" if job.status == JobStatus.RUNNING else "대기 중"
        text = (
            f"영상 {status_icon}...\n"
            f"{job.progress}\n"
            f"진행률: {job.progress_pct}%"
        )
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
            )
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
        except BadRequest as e:
            if "message is not modified" not in str(e).lower():
                logger.warning("폴링 메시지 편집 실패: %s", e)
        except Exception as e:
            logger.warning("폴링 중 예외: %s", e)

    # 폴링 종료 후 결과 메시지 업데이트
    if job is None:
        await context.bot.send_message(
            chat_id=chat_id,
            text="작업 정보를 찾을 수 없습니다. /news 명령으로 다시 시작하세요.",
        )
        return

    if job.status == JobStatus.DONE:
        result = job.result or {}
        file_path: str = result.get("output_path", "")
        context.user_data[_KEY_RESULT_PATH] = file_path

        # 파일 크기 계산
        try:
            size_bytes = os.path.getsize(file_path) if file_path and os.path.exists(file_path) else 0
            size_mb = round(size_bytes / (1024 * 1024), 1)
        except OSError:
            size_mb = 0.0

        scenario: dict = context.user_data.get(_KEY_SCENARIO, {})
        total_duration = scenario.get("total_duration", 0)
        scenes = scenario.get("scenes", [])

        verify_text = (
            f"생성 완료!\n"
            f"총 길이: {total_duration}초 / 크기: {size_mb}MB\n\n"
            "결과를 확인하세요:"
        )
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=verify_text,
                reply_markup=_make_verify_keyboard(scenes),
            )
        except Exception as e:
            logger.warning("완료 메시지 편집 실패: %s", e)
            await context.bot.send_message(
                chat_id=chat_id,
                text=verify_text,
                reply_markup=_make_verify_keyboard(scenes),
            )

    else:  # FAILED
        error_msg = job.error or "알 수 없는 오류"
        fail_text = (
            f"영상 생성에 실패했습니다.\n"
            f"오류: {error_msg}\n\n"
            "/news 명령으로 다시 시작하거나 잠시 후 다시 시도하세요."
        )
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=fail_text,
            )
        except Exception as e:
            logger.warning("실패 메시지 편집 실패: %s", e)
            await context.bot.send_message(chat_id=chat_id, text=fail_text)


# ─────────────────────────────────────────────
# 영상 생성 코루틴 팩토리
# ─────────────────────────────────────────────


async def _video_generation_factory(job, scenario: dict, anchor_name: str,
                                      script_content: str = "", news_project_id: str = "",
                                      character_data: dict = None, video_mode: str = "shorts",
                                      **kwargs) -> dict:
    """영상 생성 작업 코루틴. video_mode에 따라 pipeline 또는 slideshow 서비스를 호출한다.

    Args:
        job:              VideoJobQueue.worker 가 전달하는 Job 객체
        scenario:         씬 목록이 포함된 시나리오 dict
        anchor_name:      앵커 캐릭터 이름
        script_content:   대본 텍스트
        news_project_id:  뉴스 프로젝트 ID
        character_data:   캐릭터 시트 데이터
        video_mode:       영상 모드 ("shorts" | "slideshow")

    Returns:
        {"output_path": str, "thumbnail_path": str, "title": str, "tags": list[str]}
    """
    from telegram_bot.services.news_scenario_service import load_anchor_character_data

    if character_data is None:
        character_data = load_anchor_character_data(anchor_name) or {}

    if video_mode == "slideshow":
        from services.slideshow_service import generate_multi_slideshow
        from pathlib import Path

        scenes = scenario.get("scenes", [])
        slideshow_scenes = [
            {
                "image_path": scene.get("image_url", scene.get("image_path", "")),
                "narration": scene.get("narration", scene.get("script", "")),
                "effect": scene.get("effect", "auto"),
            }
            for scene in scenes
        ]
        projects_dir = Path(__file__).parent.parent.parent / "projects"
        project_dir = projects_dir / (news_project_id or "slideshow") / "slideshow"

        result = await generate_multi_slideshow(
            scenes=slideshow_scenes,
            aspect_ratio=scenario.get("aspect_ratio", "9:16"),
            project_dir=project_dir,
        )
        return {
            "output_path": result.get("video_path", ""),
            "thumbnail_path": "",
            "title": scenario.get("title", ""),
            "tags": scenario.get("tags", []),
        }

    from telegram_bot.services.pipeline import run_pipeline

    result = await run_pipeline(
        job=job,
        news_project_id=news_project_id,
        script_content=script_content,
        scenario_data=scenario,
        anchor_name=anchor_name,
        character_data=character_data,
    )

    return result


# ─────────────────────────────────────────────
