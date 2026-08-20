"""뉴스 light scenario 생성 — news_scenario_service.py 에서 분리.

비주얼만 요청하는 가벼운 시나리오 (narration+duration 확정 후).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _build_light_visual_prompt(
    scenes: list[dict],
    anchor_name: str,
    appearance_prompt: str,
) -> str:
    """씬 목록(narration+duration 확정)을 주고 비주얼만 요청하는 프롬프트.

    Args:
        scenes:           _split_script_to_scenes 반환값
        anchor_name:      앵커 이름
        appearance_prompt: 필터링된 외모 묘사 문자열 (영어)

    Returns:
        Claude CLI 에 전달할 프롬프트 문자열.
    """
    from services.prompt_rules import get_news_prompt_rules

    scenes_json = json.dumps(
        [{"scene_number": s["scene_number"], "narration": s["narration"], "duration": s["duration"]}
         for s in scenes],
        ensure_ascii=False,
        indent=2,
    )

    parts = [
        "당신은 뉴스 영상 촬영 감독입니다.",
        "아래 씬별 나레이션이 이미 확정되었습니다. 나레이션을 절대 수정하지 마세요.",
        "각 씬에 대해 camera, action, expression, video_prompt, transition 만 작성하세요.",
        "",
        "★★★ VISUAL STYLE (MANDATORY — apply to ALL scenes) ★★★",
        f"- {_get_news_style_prompt()}",
        f"- Every video_prompt MUST include this style direction at the beginning",
        f"- scene_style for all scenes: {_get_news_style_id()}",
        "",
        f"앵커 캐릭터 이름: {anchor_name}",
        "외모 묘사 (video_prompt 에 반드시 이 텍스트를 그대로 포함):",
        f'"{appearance_prompt}"',
        "",
        "확정된 씬 목록:",
        scenes_json,
        "",
    ]

    # 공통 비주얼 규칙
    parts.extend(get_news_prompt_rules())

    parts.extend([
        "",
        "★ 나레이션(narration)과 duration 값은 변경하지 마세요. 그대로 반환하세요. ★",
        "",
        "JSON 응답 (다른 텍스트 없이):",
        "{",
        '  "scenes": [',
        "    {",
        '      "scene_number": 1,',
        '      "camera": "slow dolly in from medium to close-up, shallow DOF",',
        '      "action": "leans forward confidently, gestures with right hand",',
        '      "expression": "serious gaze with knowing nod",',
        '      "video_prompt": "영어 시네마틱 프롬프트 (appearance + background + camera + action + lighting + quality tags)",',
        '      "transition": "smooth dissolve"',
        "    }",
        "  ]",
        "}",
    ])

    return "\n".join(parts)


async def generate_light_scenario(
    script_content: str,
    anchor_name: str,
    character_data: dict,
    target_duration: int = 20,
) -> dict:
    """대본을 그대로 유지하면서 씬 분할 + 비주얼만 생성한다.

    기존 generate_scenario 와 다른 점:
    - 나레이션: Claude 가 새로 쓰지 않음. 대본을 초당 7글자로 잘라서 씬 배분 (Python)
    - Claude 는 camera/action/expression/video_prompt/transition 만 생성
    - 대본 길이 = 영상 길이 (정확한 시간 제어)

    Args:
        script_content:  뉴스 대본 텍스트 (한국어)
        anchor_name:     앵커 캐릭터 이름 (예: "Chihiro")
        character_data:  캐릭터 시트 데이터 (appearance_prompt, tone 등 포함)
                         없으면 빈 dict {} 전달 가능 (폴백 묘사 사용)
        target_duration: 목표 영상 길이 (초, 기본 20)
                         씬 분할 시 참고하며, 실제 길이는 대본 길이에 따라 결정됨

    Returns:
        {
            "success": True,
            "scenes": [
                {
                    "scene_number": int,
                    "duration": int,
                    "narration": str,     # 원본 대본에서 잘라낸 한국어 나레이션
                    "subtitle": str,      # 항상 ""
                    "video_prompt": str,  # 영어, Grok 영상 생성용
                    "camera": str,
                    "action": str,
                    "expression": str,
                    "transition": str,
                }
            ],
            "total_duration": int,
        }

        실패 시:
        {
            "success": False,
            "error": str,
            "scenes": [],
            "total_duration": 0,
        }
    """
    # 순환 회피 lazy import
    from services.claude_utils import call_claude_cli, extract_json
    from telegram_bot.services.news_scenario_service import (
        _CLAUDE_TIMEOUT,
        _normalize_scenes,
        _split_script_to_scenes,
    )

    if not script_content or not script_content.strip():
        return {
            "success": False,
            "error": "대본 내용이 비어 있습니다.",
            "scenes": [],
            "total_duration": 0,
        }

    # Step 1: 대본을 씬으로 분할 (Python, Claude 없이)
    split_scenes = _split_script_to_scenes(script_content.strip(), target_duration)

    # Step 2: appearance_prompt 필터링 (기존 _build_news_scenario_prompt 의 로직 재사용)
    raw_appearance = character_data.get(
        "appearance_prompt",
        f"A professional news anchor named {anchor_name}, upper body portrait, studio lighting",
    )
    _FILTER_WORDS = [
        "voluptuous", "E-cup", "bust", "cleavage", "busty", "sexy",
        "seductive", "revealing", "naked", "nude", "breast", "top-heavy",
        "jiggle", "bounce", "nsfw",
    ]
    _BODY_FILTER_PHRASES = [
        "long elegant legs", "elegant legs", "long legs", "slim legs",
        "slim elegant body", "elegant figure", "full body",
        "graceful posture", "white skirt", "short skirt", "mini skirt",
        "thigh", "knee", "feet", "shoes", "heels",
    ]
    appearance_prompt = raw_appearance
    for word in _FILTER_WORDS:
        appearance_prompt = appearance_prompt.replace(word, "")
    for phrase in _BODY_FILTER_PHRASES:
        appearance_prompt = re.sub(
            re.escape(phrase), "", appearance_prompt, flags=re.IGNORECASE
        )
    for _ in range(3):
        appearance_prompt = re.sub(r",\s*,+", ",", appearance_prompt)
        appearance_prompt = re.sub(r",\s*\.", ".", appearance_prompt)
        appearance_prompt = re.sub(r"\.\s*\.", ".", appearance_prompt)
        appearance_prompt = re.sub(r",\s*with\s*,", ",", appearance_prompt)
    appearance_prompt = re.sub(r"\s+", " ", appearance_prompt).strip()
    appearance_prompt = appearance_prompt.strip(",. ")

    # Step 3: Claude 로 비주얼만 생성
    prompt = _build_light_visual_prompt(
        scenes=split_scenes,
        anchor_name=anchor_name,
        appearance_prompt=appearance_prompt,
    )

    try:
        raw = await asyncio.to_thread(call_claude_cli, prompt, _CLAUDE_TIMEOUT)
    except Exception as e:
        logger.error(f"Claude CLI 호출 실패 (generate_light_scenario): {e}")
        return {
            "success": False,
            "error": f"AI 비주얼 생성 실패: {e}",
            "scenes": [],
            "total_duration": 0,
        }

    try:
        data = extract_json(raw)
    except ValueError as e:
        logger.error(
            f"JSON 파싱 실패 (generate_light_scenario): {e}\n원본: {raw[:300]}"
        )
        return {
            "success": False,
            "error": "비주얼 응답 파싱 실패. 다시 시도해 주세요.",
            "scenes": [],
            "total_duration": 0,
        }

    visual_scenes = data.get("scenes", [])
    if not visual_scenes:
        return {
            "success": False,
            "error": "비주얼 씬 목록이 비어 있습니다. 다시 시도해 주세요.",
            "scenes": [],
            "total_duration": 0,
        }

    # Step 4: Step 1 의 나레이션/duration + Step 3 의 비주얼 병합
    # scene_number 기준으로 매핑
    visual_map: dict[int, dict] = {
        v.get("scene_number", i + 1): v for i, v in enumerate(visual_scenes)
    }

    merged: list[dict] = []
    for base in split_scenes:
        sn = base["scene_number"]
        vis = visual_map.get(sn, {})
        merged.append({
            "scene_number": sn,
            "duration": base["duration"],       # 원본 대본 기반 — 변경 불가
            "narration": base["narration"],     # 원본 대본 — 변경 불가
            "subtitle": "",
            "video_prompt": vis.get("video_prompt", ""),
            "camera": vis.get("camera", "slow dolly in, shallow DOF"),
            "action": vis.get("action", "natural gestures while speaking"),
            "expression": vis.get("expression", "serious and focused"),
            "transition": vis.get("transition", "smooth dissolve"),
        })

    total_duration = sum(s["duration"] for s in merged)

    return {
        "success": True,
        "scenes": merged,
        "total_duration": total_duration,
    }

