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
WORKER_MODEL_OPTIONS: tuple[str, ...] = ("haiku", "fable", "sonnet", "opus")

# u_3296/3297: ReplyKeyboardMarkup(하단고정)이 iOS에서 입력창 탭만으로 접히는 표준동작을
# is_persistent로도 못 막는 것 확인(리서치+실사용 재현) — 인라인버튼 방식으로 전환.
# 콜백데이터: "menu|report" | "menu|git" | "menu|joblist" | "menu|wake" | "job|{job_id}" | "job|back"
#   + a_3561/3563: "ask|compact|{orch|worker|both}"  + a_3564: "ask|model|{haiku|sonnet|opus}" (§K7 ask| prefix).

# u_5004: 오케에게 '그대로 계속 진행' 을 시키는 버튼.
#   WHY: 리포트를 보고 '진행해'를 매번 타이핑하는 게 반복이라 버튼으로 뺀다.
#   report/git 과 같은 경로 — u_ 로 기록되면 오케가 평소처럼 읽고 이어서 한다.
CONTINUE_BUTTON = "▶ 계속하기"
STATUS_BUTTON = "상태"
STOP_BUTTON = "■ 중지"

# u_5012: 검증→보강 2단계 버튼.
#   오너 의도(정정): 자주 쓰는 업무를 나열하는 게 아니라,
#   "지금 하던 작업이 목적대로 제대로 구현됐는지" 를 싸고 빠른 모델로 먼저 검증시키고,
#   그 결과를 파일로 남긴 뒤, 강한 모델로 바꿔 그 파일대로 보강하게 하는 흐름이다.
#   (u_5010 에서 내가 '주행학습/운세생성/전체점검/정리' 로 잘못 만들었던 것을 대체)
# ★logs/ 는 .gitignore 에 걸려 있어 커밋이 안 된다(u_5015 실측).
#   검증 결과는 남아야 하는 산출물이므로 추적되는 경로에 쓴다.
AUDIT_FILE = "docs/audit_findings.md"

AUDIT_BUTTON = "🔍 검증(fable)"
APPLY_BUTTON = "🔧 보강 실행(opus)"

AUDIT_PROMPT = (
    "지금 진행 중이던 작업이 '목적에 비례해 제대로 구현됐는지' 검증해라.\n"
    "1) 최근 작업이 뭐였는지 먼저 확인(git log, 최근 u_/ar_).\n"
    "2) 코드를 읽고 실제로 돌려봐서 확인한다 — 추측 금지, 실측만.\n"
    "3) 목적 대비 빠진 것 / 잘못된 것 / 보강할 것을 찾는다.\n"
    f"4) 결과를 {AUDIT_FILE} 에 쓴다. 형식:\n"
    "   ## 검증일시 / ## 대상 / ## 확인된 것(실측값 포함) / ## 문제점 / ## 보강할 점(우선순위순)\n"
    "5) 고치지는 마라. 이 단계는 '찾아서 적기'까지다.\n"
    "끝나면 몇 개 찾았는지 한 줄로 보고."
)

APPLY_PROMPT = (
    f"{AUDIT_FILE} 를 읽고 거기 적힌 '보강할 점'을 우선순위대로 실제로 구현해라.\n"
    "· 하나 고칠 때마다 실측으로 검증하고 수치를 남긴다.\n"
    "· 못 고치는 게 있으면 왜 못 고치는지 적는다.\n"
    "· 끝나면 무엇을 고쳤고 무엇이 남았는지 보고."
)


def _model_label(current: str, m: str) -> str:
    """현재 선택된 모델에 표시를 붙인다(u_5010).

    문제였던 것: 세 버튼이 똑같이 보여서 지금 무슨 모델인지 알 수 없었다.
    """
    return ("✅ " if m == current else "") + m


def current_worker_model() -> str:
    """.env 의 ORCH_WORKER_MODEL — 버튼 라벨에 현재값을 비추기 위해 읽는다."""
    import os
    from pathlib import Path
    p = Path(__file__).resolve().parent / ".env"
    try:
        for ln in p.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln.startswith("ORCH_WORKER_MODEL="):
                return ln.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return os.environ.get("ORCH_WORKER_MODEL", "haiku")


def build_main_inline_keyboard() -> list[list[dict[str, Any]]]:
    """메인 인라인메뉴 = [계속진행][리포트/상태][git][잡목록][워커깨우기] + 컴팩트 3종 + 모델전환 3종."""
    return [
        [{"text": CONTINUE_BUTTON, "callback_data": "menu|continue"}],
        [
            {"text": "리포트", "callback_data": "menu|report"},
            {"text": STATUS_BUTTON, "callback_data": "menu|status"},
            {"text": STOP_BUTTON, "callback_data": "menu|stop"},
        ],
        [{"text": "git commit, push", "callback_data": "menu|git"}],
        [{"text": JOB_LIST_BUTTON, "callback_data": "menu|joblist"}],
        [{"text": WAKE_WORKER_BUTTON, "callback_data": "menu|wake"}],
        [
            {"text": COMPACT_WORKER_BUTTON, "callback_data": "ask|compact|worker"},
            {"text": COMPACT_ORCH_BUTTON, "callback_data": "ask|compact|orch"},
            {"text": COMPACT_BOTH_BUTTON, "callback_data": "ask|compact|both"},
        ],
        [
            {"text": f"모델:{_model_label(current_worker_model(), m)}",
             "callback_data": f"ask|model|{m}"}
            for m in WORKER_MODEL_OPTIONS
        ],
        [
            {"text": AUDIT_BUTTON, "callback_data": "audit|check"},
            {"text": APPLY_BUTTON, "callback_data": "audit|apply"},
        ],
    ]


def build_control_inline_row() -> list[list[dict[str, Any]]]:
    """a_3566: 컴팩트 3종 + 모델전환 3종만 담은 인라인 행 — 모든 status/report 메시지에 부착.
    build_main_inline_keyboard() 의 컴팩트·모델 행만 재사용(중복정의 금지).
    u_5004: 리포트 바로 아래에서 이어서 시킬 수 있게 [계속 진행] 을 맨 위에 붙인다."""
    return [
        [
            {"text": CONTINUE_BUTTON, "callback_data": "menu|continue"},
            {"text": STOP_BUTTON, "callback_data": "menu|stop"},
        ],
        [
            {"text": COMPACT_WORKER_BUTTON, "callback_data": "ask|compact|worker"},
            {"text": COMPACT_ORCH_BUTTON, "callback_data": "ask|compact|orch"},
            {"text": COMPACT_BOTH_BUTTON, "callback_data": "ask|compact|both"},
        ],
        [
            {"text": f"모델:{_model_label(current_worker_model(), m)}",
             "callback_data": f"ask|model|{m}"}
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
