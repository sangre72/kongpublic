"""잡리스트 버튼 기능(u_3280/3281) — 자주 쓰는 레시피 작업을 인라인버튼으로 제공.

- 작업목록 = 하드코딩(레시피 기반 반복작업, kaymaps/ 참조), jobs/ 산출물 디렉토리와 무관.
- 실행중인 job은 상태파일(logs/.job_state.json)로 추적해 버튼 비활성화(회색/터치불가 텍스트로 표시).
- 콜백 데이터 포맷: "job|{job_id}" — kong_orchestrator.py의 handle_update가 라우팅.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_STATE_PATH = _REPO_ROOT / "logs" / ".job_state.json"

# job_id: (표시명, 설명 — 실행시 u_ 요청문구로 사용)
JOBS: dict[str, str] = {
    "fortune_gen": "내일 운세 12개 생성",
    "fortune_upload": "생성된 운세 유튜브 업로드",
    "fortune_verify": "운세 12개 검증",
    "fortune_server_toggle": "운세 서버 시작/중지",
}


def _load_state() -> dict[str, Any]:
    if _STATE_PATH.exists():
        try:
            return json.loads(_STATE_PATH.read_text())
        except Exception:  # noqa: BLE001
            return {}
    return {}


def _save_state(state: dict[str, Any]) -> None:
    _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def is_running(job_id: str) -> bool:
    return _load_state().get(job_id, {}).get("status") == "running"


def mark_running(job_id: str) -> None:
    state = _load_state()
    state[job_id] = {"status": "running"}
    _save_state(state)


def mark_idle(job_id: str) -> None:
    state = _load_state()
    state.pop(job_id, None)
    _save_state(state)


def build_keyboard() -> list[list[dict[str, Any]]]:
    """job 목록을 inline_keyboard 형태로 변환. 실행중인 job = 라벨에 ⏳ 표시+콜백 비활성(빈 data 대신 noop)."""
    rows: list[list[dict[str, Any]]] = []
    for job_id, label in JOBS.items():
        if is_running(job_id):
            rows.append([{"text": f"⏳ {label}(진행중)", "callback_data": "job|noop"}])
        else:
            rows.append([{"text": label, "callback_data": f"job|{job_id}"}])
    return rows


JOB_LIST_BUTTON = "잡목록"

def build_persistent_keyboard_rows() -> list[list[str]]:
    """u_3289: 메인 하단버튼 = [리포트][git commit,push][잡목록] 3개만. 개별 job버튼은
    '잡목록' 눌렀을때만 노출(build_job_submenu_rows 참조) — 2단 메뉴 구조."""
    return [["리포트"], ["git commit, push"], [JOB_LIST_BUTTON]]


def build_job_submenu_rows() -> list[list[str]]:
    """'잡목록' 버튼 클릭시 노출할 하위 메뉴(개별 job 4개 + 뒤로가기)."""
    rows: list[list[str]] = []
    for job_id, label in JOBS.items():
        text = f"⏳ {label}(진행중)" if is_running(job_id) else label
        rows.append([text])
    rows.append(["◀ 뒤로"])
    return rows


def match_button_label(text: str) -> str | None:
    """평문 메시지가 잡버튼 라벨과 일치하면 job_id 반환(아니면 None). 진행중 표시(⏳...) 도 매칭."""
    stripped = text.strip()
    for job_id, label in JOBS.items():
        if stripped == label or stripped == f"⏳ {label}(진행중)":
            return job_id
    return None
