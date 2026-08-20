"""뉴스 쇼츠 시나리오 생성 서비스 (M9)

대본(script_content) → 씬 단위 시나리오로 분할.
기존 routers/scenario.py 의 build_generate_prompt 패턴을 참조하되
뉴스 앵커 특화 프롬프트로 교체한다.

주요 함수:
    generate_scenario          - 대본 → 시나리오 생성 (공개 API)
    generate_news_scenario     - generate_scenario 의 별칭 (설계서 M9 인터페이스)
    edit_scene                 - 특정 씬의 단일 필드 수정
    regenerate_scenario        - 피드백 반영 재생성
    load_anchor_character_data - 앵커 이름으로 캐릭터 시트 로드
"""

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Optional

from services.director_styles import get_news_default as _get_news_default_style


def _get_news_style_prompt() -> str:
    return _get_news_default_style().get("prompt", "")


def _get_news_style_id() -> str:
    return _get_news_default_style().get("id", "shinkai_makoto")

from services.claude_utils import call_claude_cli, extract_json

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# 내부 상수
# ─────────────────────────────────────────────

SHEET_DIR = Path(__file__).parent.parent.parent / "character_sheets"

# 카메라 앵글 순환 패턴 (씬 번호 기반)
_CAMERA_ANGLES = [
    "front-facing bust shot above desk, dynamic camera movement",
    "slight side angle close-up, slow zoom in, framed above pelvis",
    "close-up portrait from chest up, subtle camera shake",
    "medium close-up showing head shoulders and hand gestures, desk hides lower body",
    "front-facing bust shot with dramatic lighting change",
    "eye-level close-up emphasizing confident expression",
]

# 앵커 표정/제스처 뉴스 톤 매핑 — 과감한 바디 액션 필수
_SCENE_TONE_MAP = {
    "opening": "confident posture, dramatic hand gesture pointing at camera, emphatic body lean forward, expressive eye contact, animated upper body movement",
    "body": "energetic hand gestures explaining with both hands, dynamic body sway, head tilt with emphasis, leaning forward passionately, animated torso movement while speaking",
    "closing": "warm bright smile, enthusiastic wave gesture, slight body bounce, energetic nod, expressive farewell hand motion",
}

# Claude CLI 타임아웃 (초)
_CLAUDE_TIMEOUT = 180


# ─────────────────────────────────────────────
# 캐릭터 시트 로드
# ─────────────────────────────────────────────

def load_anchor_character_data(anchor_name: str) -> Optional[dict]:
    """앵커 이름으로 캐릭터 시트를 로드한다.

    character_sheets/ 디렉토리에서 앵커 이름이 포함된 폴더를 찾아
    metadata.json 의 character 데이터를 반환한다.
    대소문자를 구분하지 않고 검색한다.

    Args:
        anchor_name: 앵커 이름 (예: "emma", "Emma", "sophia")

    Returns:
        캐릭터 데이터 dict (character 키 하위 데이터) 또는 None.

    Example:
        data = load_anchor_character_data("emma")
        # {"name": "Emma", "role": "...", "appearance_prompt": "..."}
    """
    if not SHEET_DIR.exists():
        logger.warning(f"character_sheets 디렉토리 없음: {SHEET_DIR}")
        return None

    anchor_lower = anchor_name.lower()

    # 최신 순으로 정렬 (YYYYMMDD_ 접두사 기준)
    for sheet_dir in sorted(SHEET_DIR.iterdir(), reverse=True):
        if not sheet_dir.is_dir():
            continue
        # tmp_ref 같은 특수 디렉토리 제외
        if not any(c.isdigit() for c in sheet_dir.name[:8]):
            continue
        if anchor_lower not in sheet_dir.name.lower():
            continue

        meta_path = sheet_dir / "metadata.json"
        if not meta_path.exists():
            continue

        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            char = meta.get("character", {})
            if char:
                logger.info(f"캐릭터 시트 로드 성공: {sheet_dir.name}")
                return char
        except Exception as e:
            logger.error(f"캐릭터 시트 읽기 실패 ({sheet_dir.name}): {e}")

    logger.warning(f"앵커 '{anchor_name}' 캐릭터 시트 없음")
    return None


# ─────────────────────────────────────────────
# 프롬프트 빌더
# ─────────────────────────────────────────────

def _build_news_scenario_prompt(
    script_content: str,
    anchor_name: str,
    character_data: dict,
    target_duration: int,
    news_source: str = "",
    feedback: str = "",
) -> str:
    """뉴스 앵커 특화 시나리오 생성 프롬프트 구성.

    Args:
        script_content:  대본 텍스트 (한국어 나레이션)
        anchor_name:     앵커 캐릭터 이름
        character_data:  캐릭터 시트 데이터 (appearance_prompt 포함)
        target_duration: 목표 영상 길이 (초)
        news_source:     뉴스 출처 (선택)
        feedback:        피드백 텍스트 (재생성 시 사용)

    Returns:
        Claude CLI 에 전달할 프롬프트 문자열.
    """
    raw_appearance = character_data.get(
        "appearance_prompt",
        f"A professional news anchor named {anchor_name}, upper body portrait, studio lighting"
    )
    # Grok API 거부 방지: 선정적 표현 제거
    _FILTER_WORDS = [
        "voluptuous", "E-cup", "bust", "cleavage", "busty", "sexy",
        "seductive", "revealing", "naked", "nude", "breast", "top-heavy",
        "jiggle", "bounce", "nsfw",
    ]
    # 전신 묘사 제거 (뉴스 앵커는 골반 위만 표시)
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
    # 중복 공백/쉼표/마침표 정리 (반복 적용)
    for _ in range(3):
        appearance_prompt = re.sub(r",\s*,+", ",", appearance_prompt)
        appearance_prompt = re.sub(r",\s*\.", ".", appearance_prompt)
        appearance_prompt = re.sub(r"\.\s*\.", ".", appearance_prompt)
        appearance_prompt = re.sub(r",\s*with\s*,", ",", appearance_prompt)
    appearance_prompt = re.sub(r"\s+", " ", appearance_prompt).strip()
    appearance_prompt = appearance_prompt.strip(",. ")
    anchor_tone = character_data.get("tone", "신뢰감 있고 차분한 뉴스 진행 스타일")
    anchor_display = character_data.get("display_name", anchor_name)

    # 대본은 최대 3000자
    script_truncated = script_content.strip()[:3000]

    # 최소 씬 수 계산 (씬당 14초 기준)
    min_scenes = max(3, target_duration // 14)

    parts = [
        "당신은 10명의 영상 제작 전문가가 합쳐진 올인원 시나리오 생성기입니다.",
        "뉴스 쇼츠(YouTube Shorts)를 영화 트레일러 수준의 비주얼로 제작합니다.",
        "",
        "제작진: 감독(비전/장르/톤) | PD(씬구성/페이싱) | 시나리오작가(스토리/나레이션) |",
        "연출가(연기/표정/제스처) | 촬영감독(카메라/렌즈/조명) | 미술감독(세트/소품/배경) |",
        "음향감독(BGM/효과음/음성톤) | 편집감독(컷타이밍/전환/리듬) | 컬러리스트(색감/그레이딩) |",
        "VFX(자막애니메이션/모션그래픽/파티클)",
        "",
        f"앵커: {anchor_display} ({anchor_name})",
        f"앵커 스타일: {anchor_tone}",
        f"목표 영상 길이: {target_duration}초",
        f"포맷: 9:16 세로 쇼츠 (모바일 풀스크린)",
    ]

    if news_source:
        parts.append(f"뉴스 출처: {news_source}")

    parts.extend([
        "",
        "뉴스 대본:",
        f'"""\n{script_truncated}\n"""',
    ])

    # 캐릭터 시트 주입
    parts.extend([
        "",
        "★★★ 앵커 캐릭터 시트 (절대 변경 금지, video_prompt 에 이 묘사를 그대로 사용) ★★★",
        f"캐릭터 이름: {anchor_name}",
        "외모 묘사 (영어, video_prompt 에 반드시 이 텍스트를 복사하여 사용):",
        f'"{appearance_prompt}"',
        "",
        "규칙: 모든 씬의 video_prompt 에 위 외모 묘사를 반드시 포함하세요.",
        "외모 묘사를 임의로 수정하거나 요약하지 마세요. 그대로 복사하세요.",
    ])

    if feedback:
        parts.extend([
            "",
            f"★ 재생성 피드백 (반드시 반영) ★",
            feedback,
        ])

    # 논평 시간 계산 (목표의 25%, 최소 4초, 최대 8초)
    commentary_sec = max(4, min(8, target_duration // 4))
    news_sec = target_duration - commentary_sec

    parts.extend([
        "",
        "★★★ 씬 구성 규칙 (2파트 구조) ★★★",
        "",
        f"[파트1: 팩트 씬] 총 {news_sec}초",
        "- 씬1: 훅 — 시청자를 사로잡는 강렬한 첫 마디 (질문형 or 충격적 사실)",
        "- 나머지 씬: 핵심 사실만 간결하게 전달 (불필요한 배경 제거)",
        "",
        f"[파트2: 논평 씬] 마지막 1개 씬, {commentary_sec}초",
        "- 앵커의 개인적 시각/분석/전망",
        "- '제 생각에는', '결국 이건', '주목할 점은' 등으로 자연스럽게 전환",
        "- 시청자에게 인사이트를 주는 코멘터리",
        "- 배경: 앵커 클로즈업 + 핵심 키워드/인포그래픽 배경",
        "",
        f"총 씬 수: {min_scenes}~{min_scenes + 1}개 (마지막 씬은 반드시 논평)",
        "★ duration 계산: 나레이션 글자 수 ÷ 7 (한국어 TTS 초당 7글자). 최소 3초, 최대 14초",
        "나레이션은 duration에 딱 맞는 길이로 (너무 짧거나 길지 않게)",
        "",
    ])

    # 공통 프롬프트 규칙 (prompt_rules에서 가져오기)
    from services.prompt_rules import get_news_prompt_rules
    parts.extend(get_news_prompt_rules())

    parts.extend([
        "",
        f"총 길이가 {target_duration}초에 최대한 근접하도록 씬들의 duration 합산을 맞추세요.",
        "",
        "JSON 형식으로 응답 (다른 텍스트 없이):",
        "{",
        '  "scenes": [',
        "    {",
        '      "scene_number": 1,',
        '      "duration": 10,',
        '      "narration": "앵커가 시청자에게 뉴스를 전달하는 말투 (한국어, 장면 묘사 금지, 글자 수 = (duration - 1) × 7)",',
        '      "subtitle": "",',
        '      "video_prompt": "영어 시네마틱 프롬프트 (appearance + background + camera + action + expression + lighting + quality tags 모두 통합)",',
        '      "camera": "slow dolly in from medium to close-up, shallow DOF f/1.8",',
        '      "action": "leans forward confidently, gestures with right hand, slight shoulder turn",',
        '      "expression": "intense serious look softening into knowing nod",',
        '      "transition": "smooth dissolve"',
        "    }",
        "  ],",
        '  "total_duration": 60',
        "}",
    ])

    return "\n".join(parts)


# ─────────────────────────────────────────────
# 내부 헬퍼
# ─────────────────────────────────────────────


def _normalize_scenes(scenes: list[dict]) -> list[dict]:
    """씬 목록을 정규화한다.

    - scene_number 순서 부여 (누락 시 인덱스로 대체)
    - 나레이션 글자 수 기반 duration 재계산 (한국어 TTS 초당 7글자)
    - 나레이션 없는 씬은 Claude 제공 duration 유지
    - 기타 필수 필드 기본값 보정

    Args:
        scenes: Claude가 반환한 씬 dict 목록

    Returns:
        정규화된 씬 dict 목록
    """
    normalized: list[dict] = []
    for i, scene in enumerate(scenes, 1):
        narration = scene.get("narration", "")
        # 나레이션 글자 수 기반 duration (한국어 TTS 초당 7글자)
        calculated_duration = max(3, min(14, round(len(narration) / 7)))
        raw_duration = int(scene.get("duration", calculated_duration))
        # Claude가 준 duration과 계산값 중 합리적인 것 사용
        if narration:
            duration = calculated_duration
        else:
            duration = raw_duration

        normalized.append({
            "scene_number": scene.get("scene_number", i),
            "duration": duration,
            "narration": narration,
            "subtitle": scene.get("subtitle", ""),
            "video_prompt": scene.get("video_prompt", ""),
            "camera": scene.get("camera", "slow dolly in, shallow DOF"),
            "action": scene.get("action", "natural gestures while speaking"),
            "expression": scene.get("expression", "serious and focused"),
            "transition": scene.get("transition", "smooth dissolve"),
        })
    return normalized


# ─────────────────────────────────────────────
# 공개 API
# ─────────────────────────────────────────────

async def generate_scenario(
    script_content: str,
    anchor_name: str,
    character_data: dict,
    target_duration: int = 60,
    news_source: str = "",
) -> dict:
    """대본을 씬 단위 시나리오로 변환한다.

    Claude CLI 를 asyncio.to_thread 로 래핑하여 비동기 호출한다.

    Args:
        script_content:  뉴스 대본 텍스트 (한국어)
        anchor_name:     앵커 캐릭터 이름 (예: "emma")
        character_data:  캐릭터 시트 데이터 (appearance_prompt, tone 등 포함)
                         없으면 빈 dict {} 전달 가능 (폴백 묘사 사용)
        target_duration: 목표 영상 길이 (초, 기본 60)
        news_source:     뉴스 출처 문자열 (선택)

    Returns:
        {
            "success": True,
            "scenes": [
                {
                    "scene_number": int,
                    "duration": int,
                    "narration": str,     # 한국어 나레이션
                    "subtitle": str,      # 한국어 자막
                    "video_prompt": str,  # 영어, Grok 영상 생성용
                    "camera": str,        # 카메라 앵글
                    "action": str,        # 표정/제스처
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
    if not script_content or not script_content.strip():
        return {
            "success": False,
            "error": "대본 내용이 비어 있습니다.",
            "scenes": [],
            "total_duration": 0,
        }

    # 제작 회의를 별도 호출하지 않고, 프롬프트에 전문가 관점을 통합 (1회 호출)
    prompt = _build_news_scenario_prompt(
        script_content=script_content,
        anchor_name=anchor_name,
        character_data=character_data,
        target_duration=target_duration,
        news_source=news_source,
    )

    try:
        raw = await asyncio.to_thread(call_claude_cli, prompt, _CLAUDE_TIMEOUT)
    except Exception as e:
        logger.error(f"Claude CLI 호출 실패 (generate_scenario): {e}")
        return {
            "success": False,
            "error": f"AI 시나리오 생성 실패: {e}",
            "scenes": [],
            "total_duration": 0,
        }

    try:
        data = extract_json(raw)
    except ValueError as e:
        logger.error(f"JSON 파싱 실패 (generate_scenario): {e}\n원본: {raw[:300]}")
        return {
            "success": False,
            "error": "시나리오 응답 파싱 실패. 다시 시도해 주세요.",
            "scenes": [],
            "total_duration": 0,
        }

    scenes = data.get("scenes", [])
    if not scenes:
        return {
            "success": False,
            "error": "시나리오에 씬이 없습니다. 다시 시도해 주세요.",
            "scenes": [],
            "total_duration": 0,
        }

    # 필수 필드 보정 + duration을 나레이션 길이 기반으로 계산
    normalized_scenes = _normalize_scenes(scenes)

    total_duration = data.get("total_duration") or sum(
        s["duration"] for s in normalized_scenes
    )

    return {
        "success": True,
        "scenes": normalized_scenes,
        "total_duration": int(total_duration),
    }


async def generate_news_scenario(
    script_content: str,
    anchor_name: str,
    anchor_character_data: dict,
    target_duration: int = 60,
    news_source: str = "",
) -> dict:
    """generate_scenario 의 설계서 M9 인터페이스 별칭.

    Args:
        script_content:       뉴스 대본 텍스트
        anchor_name:          앵커 이름
        anchor_character_data: 캐릭터 시트 데이터
        target_duration:      목표 길이 (초)
        news_source:          뉴스 출처 (선택)

    Returns:
        generate_scenario 와 동일한 구조.
    """
    return await generate_scenario(
        script_content=script_content,
        anchor_name=anchor_name,
        character_data=anchor_character_data,
        target_duration=target_duration,
        news_source=news_source,
    )


def edit_scene(scenario: dict, scene_number: int, field: str, new_value: str) -> dict:
    """특정 씬의 단일 필드를 수정한다.

    원본 scenario dict 를 직접 변경하지 않고 새로운 dict 를 반환한다.

    Args:
        scenario:     generate_scenario 반환값 (scenes 키 포함)
        scene_number: 수정할 씬 번호 (1부터 시작)
        field:        수정할 필드명.
                      허용값: "narration" | "subtitle" | "video_prompt" |
                               "duration" | "camera" | "action"
        new_value:    새 값 (str). duration 은 int 로 자동 변환됨.

    Returns:
        수정된 시나리오 dict.
        {
            "success": True,
            "scenes": [...],
            "total_duration": int,
        }

        씬을 찾지 못한 경우:
        {
            "success": False,
            "error": str,
            ...원본 scenario 내용 유지...
        }

    Raises:
        없음 (모든 오류는 success=False 로 반환).
    """
    allowed_fields = {"narration", "subtitle", "video_prompt", "duration", "camera", "action", "expression", "transition"}

    if field not in allowed_fields:
        return {
            **scenario,
            "success": False,
            "error": f"허용되지 않은 필드: '{field}'. 허용: {sorted(allowed_fields)}",
        }

    scenes = [dict(s) for s in scenario.get("scenes", [])]
    target = next((s for s in scenes if s.get("scene_number") == scene_number), None)

    if target is None:
        return {
            **scenario,
            "success": False,
            "error": f"씬 {scene_number} 을 찾을 수 없습니다.",
        }

    # duration 은 정수로 변환
    if field == "duration":
        try:
            target[field] = int(new_value)
        except (ValueError, TypeError):
            return {
                **scenario,
                "success": False,
                "error": f"duration 은 정수여야 합니다: '{new_value}'",
            }
    else:
        target[field] = new_value

    total_duration = sum(s.get("duration", 0) for s in scenes)

    return {
        "success": True,
        "scenes": scenes,
        "total_duration": total_duration,
    }


# ─────────────────────────────────────────────
# 라이트 시나리오 (대본 보존)
# ─────────────────────────────────────────────


def _split_script_to_scenes(script: str, target_duration: int) -> list[dict]:
    """대본을 문장 단위로 잘라서 씬 배분한다.

    Claude 없이 Python만으로 실행된다.

    - 문장 분리: '.', '!', '?' 기준 (단, 문장 끝이 아닌 위치의 마침표는 제외)
    - 각 문장의 TTS 예상 시간: 글자 수 / 7 (초당 7글자)
    - 씬 하나가 5~10초가 되도록 문장을 묶는다
    - 마지막 씬은 남은 문장 중 마지막 1~2개 문장을 논평으로 배정

    Args:
        script:          대본 전체 텍스트
        target_duration: 목표 영상 길이 (초) — 현재 참고용 (씬 수 결정에만 사용)

    Returns:
        [{"scene_number": 1, "narration": "...", "duration": 7}, ...]
    """
    # 1. 문장 분리 — 마침표/느낌표/물음표 뒤 공백 기준
    raw_sentences = re.split(r"(?<=[.!?])\s+", script.strip())
    sentences: list[str] = [s.strip() for s in raw_sentences if s.strip()]

    # 2. 각 문장의 예상 TTS 시간 계산
    def _duration_of(text: str) -> int:
        return max(2, round(len(text) / 7))

    # 3. 문장을 씬으로 묶기 (씬당 5~10초 목표)
    TARGET_MIN = 5
    TARGET_MAX = 10
    scenes_raw: list[list[str]] = []
    current_group: list[str] = []
    current_secs = 0

    for sentence in sentences:
        secs = _duration_of(sentence)
        if current_secs + secs > TARGET_MAX and current_group:
            # 현재 그룹이 이미 최소치를 넘으면 새 씬 시작
            if current_secs >= TARGET_MIN:
                scenes_raw.append(current_group)
                current_group = [sentence]
                current_secs = secs
            else:
                # 아직 최소치 미만이면 억지로 합침
                current_group.append(sentence)
                current_secs += secs
                scenes_raw.append(current_group)
                current_group = []
                current_secs = 0
        else:
            current_group.append(sentence)
            current_secs += secs

    if current_group:
        scenes_raw.append(current_group)

    # 씬이 1개 이하면 그냥 전체를 씬 1개로
    if len(scenes_raw) <= 1:
        return [
            {
                "scene_number": 1,
                "narration": script.strip(),
                "duration": max(3, min(14, _duration_of(script.strip()))),
            }
        ]

    # 4. 마지막 씬을 논평 처리 (마지막 씬이 너무 짧으면 앞 씬과 병합 후 분리)
    last_group = scenes_raw[-1]
    if len(last_group) >= 2:
        # 마지막 2개 문장을 논평 씬으로 분리
        commentary_sentences = last_group[-2:]
        main_sentences = last_group[:-2]
        if main_sentences:
            scenes_raw[-1] = main_sentences
            scenes_raw.append(commentary_sentences)
        else:
            # 분리할 문장이 없으면 그대로 유지
            pass
    # else: 마지막 씬이 1문장이면 그대로 논평으로 사용

    # 5. dict 변환
    result: list[dict] = []
    for i, group in enumerate(scenes_raw, 1):
        narration = " ".join(group)
        duration = max(3, min(14, _duration_of(narration)))
        result.append({
            "scene_number": i,
            "narration": narration,
            "duration": duration,
        })

    return result



async def regenerate_scenario(
    script_content: str,
    anchor_name: str,
    character_data: dict,
    target_duration: int = 60,
    feedback: str = "",
    news_source: str = "",
) -> dict:
    """피드백을 반영하여 시나리오를 재생성한다.

    Args:
        script_content:  뉴스 대본 텍스트
        anchor_name:     앵커 이름
        character_data:  캐릭터 시트 데이터
        target_duration: 목표 길이 (초)
        feedback:        사용자 피드백 (예: "씬이 너무 길어요", "오프닝을 더 임팩트 있게")
        news_source:     뉴스 출처 (선택)

    Returns:
        generate_scenario 와 동일한 구조.
    """
    if not script_content or not script_content.strip():
        return {
            "success": False,
            "error": "대본 내용이 비어 있습니다.",
            "scenes": [],
            "total_duration": 0,
        }

    prompt = _build_news_scenario_prompt(
        script_content=script_content,
        anchor_name=anchor_name,
        character_data=character_data,
        target_duration=target_duration,
        news_source=news_source,
        feedback=feedback,
    )

    try:
        raw = await asyncio.to_thread(call_claude_cli, prompt, _CLAUDE_TIMEOUT)
    except Exception as e:
        logger.error(f"Claude CLI 호출 실패 (regenerate_scenario): {e}")
        return {
            "success": False,
            "error": f"AI 시나리오 재생성 실패: {e}",
            "scenes": [],
            "total_duration": 0,
        }

    try:
        data = extract_json(raw)
    except ValueError as e:
        logger.error(f"JSON 파싱 실패 (regenerate_scenario): {e}\n원본: {raw[:300]}")
        return {
            "success": False,
            "error": "시나리오 응답 파싱 실패. 다시 시도해 주세요.",
            "scenes": [],
            "total_duration": 0,
        }

    scenes = data.get("scenes", [])
    if not scenes:
        return {
            "success": False,
            "error": "재생성된 시나리오에 씬이 없습니다. 다시 시도해 주세요.",
            "scenes": [],
            "total_duration": 0,
        }

    normalized_scenes = _normalize_scenes(scenes)

    total_duration = data.get("total_duration") or sum(
        s["duration"] for s in normalized_scenes
    )

    return {
        "success": True,
        "scenes": normalized_scenes,
        "total_duration": int(total_duration),
    }


# Light scenario 는 news_scenario_light.py 로 분리 — 호환 re-export
from telegram_bot.services.news_scenario_light import (  # noqa: E402
    _build_light_visual_prompt,
    generate_light_scenario,
)
