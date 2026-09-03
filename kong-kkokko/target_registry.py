"""프로젝트 이름 → orch 세션 tty 파일 매핑 레지스트리.

현재는 kong-bot 단일 프로젝트만 존재하지만, 나중에 여러 프로젝트를 지원할 수 있게
이름→tty-file 매핑을 데이터로 둔다(하드코딩 분산 금지, code-structure.md §2 취지).

tty 파일 규약: <repo>/logs/.orch_tty_orch (session_register_tty.sh 가 등록).
"""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]  # kong-kkokko/ 의 부모 = repo 루트

# 프로젝트명(발화 토큰 후보들) → 그 프로젝트 orch 세션의 tty 파일 경로.
#   키는 소문자·공백제거로 정규화해 매칭. alias 여러 개 허용(리스트).
# ★확장 지점: 새 프로젝트 생기면 여기에 한 줄 추가(멀티프로젝트 과설계 금지 — 지금은 kong-bot 만).
_PROJECTS: dict[str, Path] = {
    "kong-bot": _REPO_ROOT / "logs" / ".orch_tty_orch",
    "kongbot": _REPO_ROOT / "logs" / ".orch_tty_orch",
    "콩봇": _REPO_ROOT / "logs" / ".orch_tty_orch",
    "콩": _REPO_ROOT / "logs" / ".orch_tty_orch",  # 프로젝트명 생략 시 기본 = kong-bot
}

DEFAULT_PROJECT = "kong-bot"


def _norm(token: str) -> str:
    return token.strip().lower().replace(" ", "").replace("_", "-")


def resolve_tty(project_token: str | None) -> tuple[str | None, str]:
    """프로젝트 토큰 → (tty-path 문자열, 매칭된 프로젝트명). tty 미등록/미존재면 (None, name)."""
    name = _norm(project_token) if project_token else _norm(DEFAULT_PROJECT)
    tty_file = _PROJECTS.get(name)
    if tty_file is None:
        # 미등록 프로젝트 → 기본(kong-bot)으로 폴백하되 어떤 이름이었는지 알린다.
        tty_file = _PROJECTS[_norm(DEFAULT_PROJECT)]
        name = DEFAULT_PROJECT
    if not tty_file.exists():
        return (None, name)
    tty = tty_file.read_text(encoding="utf-8").strip()
    return (tty or None, name)


def parse_project_token(text: str) -> str | None:
    """STT 결과 앞머리에서 프로젝트명 토큰을 뽑는다(예: "콩봇한테 ~", "kong-bot ~").

    등록된 프로젝트 alias 중 텍스트에 등장하는 것을 찾아 반환. 없으면 None(→기본 프로젝트).
    """
    low = text.lower()
    for alias in _PROJECTS:
        if alias in low or alias in text:
            return alias
    return None
