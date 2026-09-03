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


JOB_LIST_BUTTON = "잡목록"
WAKE_WORKER_BUTTON = "워커 깨우기"
# a_3561 + a_3563 PART-A: "컴팩트(/compact)" wake 버튼.
#   ★callback-prefix = `ask|`(och.txt §K7 mandatory; `ans|`=misroute-bug). key="compact".
#   인라인버튼 + 하단고정 ReplyKeyboard 라벨 두 경로 모두 지원.
#   ★각 버튼(라벨)은 독립 발화 가능(a_3563 PART-A): worker-only / orch-only / both 3종 값.
#   ask|compact|orch  | ask|compact|worker | ask|compact|both
COMPACT_ORCH_BUTTON = "컴팩트(orch)"
COMPACT_WORKER_BUTTON = "컴팩트(worker)"
COMPACT_BOTH_BUTTON = "컴팩트(둘다)"
# 하단 고정버튼 라벨 → compact target 매핑(handle_message intercept 용).
COMPACT_LABELS: dict[str, str] = {
    COMPACT_ORCH_BUTTON: "orch",
    COMPACT_WORKER_BUTTON: "worker",
    COMPACT_BOTH_BUTTON: "both",
}

# a_3564: 워커 spawn 모델 수동전환 셀렉터(haiku/sonnet/opus). §K7 ask| prefix.
#   ask|model|{haiku|sonnet|opus} → .env ORCH_WORKER_MODEL upsert → 다음 spawn 이 라이브 반영.
WORKER_MODEL_OPTIONS: tuple[str, ...] = ("haiku", "sonnet", "opus")

# u_3296/3297: ReplyKeyboardMarkup(하단고정)이 iOS에서 입력창 탭만으로 접히는 표준동작을
# is_persistent로도 못 막는 것 확인(리서치+실사용 재현) — 인라인버튼 방식으로 전환.
# 콜백데이터: "menu|report" | "menu|git" | "menu|joblist" | "menu|wake" | "job|{job_id}" | "job|back"
#   + a_3561/3563: "ask|compact|{orch|worker|both}"  + a_3564: "ask|model|{haiku|sonnet|opus}" (§K7 ask| prefix).

def build_main_inline_keyboard() -> list[list[dict[str, Any]]]:
    """메인 인라인메뉴 = [리포트][git][잡목록][워커깨우기] + 컴팩트 3종 + 모델전환 3종."""
    return [
        [{"text": "리포트", "callback_data": "menu|report"}],
        [{"text": "git commit, push", "callback_data": "menu|git"}],
        [{"text": JOB_LIST_BUTTON, "callback_data": "menu|joblist"}],
        [{"text": WAKE_WORKER_BUTTON, "callback_data": "menu|wake"}],
        [
            {"text": COMPACT_WORKER_BUTTON, "callback_data": "ask|compact|worker"},
            {"text": COMPACT_ORCH_BUTTON, "callback_data": "ask|compact|orch"},
            {"text": COMPACT_BOTH_BUTTON, "callback_data": "ask|compact|both"},
        ],
        [
            {"text": f"모델:{m}", "callback_data": f"ask|model|{m}"}
            for m in WORKER_MODEL_OPTIONS
        ],
    ]


def build_control_inline_row() -> list[list[dict[str, Any]]]:
    """a_3566: 컴팩트 3종 + 모델전환 3종만 담은 인라인 행 — 모든 status/report 메시지에 부착.
    build_main_inline_keyboard() 의 컴팩트·모델 행만 재사용(중복정의 금지)."""
    return [
        [
            {"text": COMPACT_WORKER_BUTTON, "callback_data": "ask|compact|worker"},
            {"text": COMPACT_ORCH_BUTTON, "callback_data": "ask|compact|orch"},
            {"text": COMPACT_BOTH_BUTTON, "callback_data": "ask|compact|both"},
        ],
        [
            {"text": f"모델:{m}", "callback_data": f"ask|model|{m}"}
            for m in WORKER_MODEL_OPTIONS
        ],
    ]


def build_persistent_keyboard_rows() -> list[list[str]]:
    """하단 고정 ReplyKeyboard 행 — a_3561/3563: 컴팩트 3종 고정버튼(각 독립 발화).

    라벨 텍스트를 누르면 그 텍스트가 그대로 메시지로 전송됨 → handle_message 가 가로채 액션 실행.
    """
    return [[COMPACT_WORKER_BUTTON, COMPACT_ORCH_BUTTON, COMPACT_BOTH_BUTTON]]


def build_job_submenu_inline_keyboard() -> list[list[dict[str, Any]]]:
    """'잡목록' 클릭시 노출할 인라인 하위메뉴(개별 job 4개 + 뒤로가기)."""
    rows: list[list[dict[str, Any]]] = []
    for job_id, label in JOBS.items():
        if is_running(job_id):
            rows.append([{"text": f"⏳ {label}(진행중)", "callback_data": "job|noop"}])
        else:
            rows.append([{"text": label, "callback_data": f"job|{job_id}"}])
    rows.append([{"text": "◀ 뒤로", "callback_data": "job|back"}])
    return rows
