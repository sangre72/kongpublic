"""리서치 도메인 서비스: 도메인 등록/관리 + claude -p 채널 발견."""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from database import repository as repo
from telegram_bot.services.channel_discovery_svc import ChannelDiscoveryService

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ResearchDomainService:
    """리서치 도메인 비즈니스 로직."""

    def __init__(self) -> None:
        self._discovery_svc = ChannelDiscoveryService()

    # ─── 도메인 CRUD ───

    def create_domain(
        self,
        name: str,
        display_name: str,
        description: str = "",
        core_keywords: Optional[list[str]] = None,
    ) -> dict:
        """도메인 생성. 중복 이름 체크 포함.

        Args:
            name: 도메인 키 (예: 'ai', 'blockchain').
            display_name: 표시 이름 (예: 'AI/인공지능').
            description: 도메인 설명.
            core_keywords: 핵심 키워드 목록.

        Returns:
            {"success": bool, "domain": dict | None, "error": str | None}
        """
        name = name.strip().lower()
        if not name:
            return {"success": False, "domain": None, "error": "도메인 이름을 입력해주세요."}

        # 중복 체크
        existing = repo.get_research_domain_by_name(name)
        if existing:
            return {"success": False, "domain": None, "error": f"이미 등록된 도메인입니다: {name}"}

        domain_id = str(uuid.uuid4())
        now = _now_iso()
        keywords_list = core_keywords or []
        keywords_json = json.dumps(keywords_list, ensure_ascii=False)

        try:
            repo.save_research_domain(
                domain_id=domain_id,
                name=name,
                display_name=display_name,
                description=description,
                core_keywords=keywords_json,
                created_at=now,
                updated_at=now,
            )
        except Exception as e:
            logger.error(f"도메인 생성 실패: {e}")
            return {"success": False, "domain": None, "error": f"도메인 생성 실패: {e}"}

        row = repo.get_research_domain(domain_id)
        if not row:
            return {"success": False, "domain": None, "error": "도메인 생성 후 조회 실패"}

        logger.info(f"도메인 생성 완료: {name} ({domain_id})")
        return {"success": True, "domain": row, "error": None}

    def get_domain(self, domain_id: str) -> Optional[dict]:
        """도메인 단건 조회.

        Args:
            domain_id: UUID 문자열.

        Returns:
            도메인 dict 또는 None.
        """
        try:
            return repo.get_research_domain(domain_id)
        except Exception as e:
            logger.error(f"도메인 조회 실패 ({domain_id}): {e}")
            return None

    def list_domains(self, active_only: bool = False) -> list[dict]:
        """도메인 목록 조회.

        Args:
            active_only: True이면 활성 도메인만 반환.

        Returns:
            도메인 dict 목록.
        """
        try:
            return repo.list_research_domains(active_only=active_only)
        except Exception as e:
            logger.error(f"도메인 목록 조회 실패: {e}")
            return []

    def update_domain(self, domain_id: str, **kwargs) -> dict:
        """도메인 수정.

        Args:
            domain_id: UUID 문자열.
            **kwargs: 수정할 필드 (display_name, description, core_keywords, is_active).

        Returns:
            {"success": bool, "domain": dict | None, "error": str | None}
        """
        existing = repo.get_research_domain(domain_id)
        if not existing:
            return {"success": False, "domain": None, "error": "도메인을 찾을 수 없습니다."}

        updates: dict = {"updated_at": _now_iso()}

        if "display_name" in kwargs and kwargs["display_name"] is not None:
            updates["display_name"] = kwargs["display_name"]
        if "description" in kwargs and kwargs["description"] is not None:
            updates["description"] = kwargs["description"]
        if "core_keywords" in kwargs and kwargs["core_keywords"] is not None:
            kw = kwargs["core_keywords"]
            updates["core_keywords"] = json.dumps(kw, ensure_ascii=False) if isinstance(kw, list) else kw
        if "is_active" in kwargs and kwargs["is_active"] is not None:
            updates["is_active"] = 1 if kwargs["is_active"] else 0

        try:
            repo.update_research_domain(domain_id, **updates)
        except Exception as e:
            logger.error(f"도메인 수정 실패 ({domain_id}): {e}")
            return {"success": False, "domain": None, "error": f"도메인 수정 실패: {e}"}

        row = repo.get_research_domain(domain_id)
        return {"success": True, "domain": row, "error": None}

    def delete_domain(self, domain_id: str) -> bool:
        """도메인 삭제 (연결된 채널도 CASCADE 삭제).

        Args:
            domain_id: UUID 문자열.

        Returns:
            삭제 성공 여부.
        """
        try:
            return repo.delete_research_domain(domain_id)
        except Exception as e:
            logger.error(f"도메인 삭제 실패 ({domain_id}): {e}")
            return False

    # ─── 채널 발견 ───

    async def discover_channels(self, domain_id: str) -> list[dict]:
        """claude -p로 도메인에 적합한 채널 발견.

        발견된 채널을 research_channels에 pending 상태로 등록.

        Args:
            domain_id: 도메인 UUID.

        Returns:
            등록된 채널 dict 목록.
        """
        domain = repo.get_research_domain(domain_id)
        if not domain:
            logger.warning(f"도메인 없음: {domain_id}")
            return []

        # 기존 채널 URL 수집 (중복 방지)
        existing_channels = repo.list_research_channels(domain_id=domain_id)
        existing_urls = [ch.get("source_url", "") for ch in existing_channels if ch.get("source_url")]

        # 핵심 키워드 파싱
        core_keywords_raw = domain.get("core_keywords", "[]")
        if isinstance(core_keywords_raw, str):
            try:
                core_keywords = json.loads(core_keywords_raw)
            except (json.JSONDecodeError, TypeError):
                core_keywords = []
        else:
            core_keywords = core_keywords_raw or []

        # claude -p로 채널 탐색
        discovered = self._discovery_svc.discover_for_domain(
            domain_name=domain["name"],
            display_name=domain["display_name"],
            core_keywords=core_keywords,
            existing_channels=existing_urls,
        )

        if not discovered:
            logger.info(f"채널 발견 결과 없음: {domain['name']}")
            return []

        # DB 저장 (pending 상태)
        registered: list[dict] = []
        now = _now_iso()
        for ch in discovered:
            channel_id = str(uuid.uuid4())
            method_config_json = json.dumps(ch.get("method_config", {}), ensure_ascii=False)
            try:
                repo.save_research_channel(
                    channel_id=channel_id,
                    domain_id=domain_id,
                    name=ch["name"],
                    channel_type=ch["channel_type"],
                    method_config=method_config_json,
                    interval_seconds=ch.get("interval_seconds", 900),
                    priority=ch.get("priority", 5),
                    max_items_per_fetch=20,
                    source_url=ch.get("source_url", ""),
                    discovery_source="claude",
                    created_at=now,
                    updated_at=now,
                )
                row = repo.get_research_channel(channel_id)
                if row:
                    registered.append(row)
                    logger.info(f"채널 등록: {ch['name']} ({channel_id})")
            except Exception as e:
                logger.error(f"채널 저장 실패 ({ch.get('name', '')}): {e}")

        # 도메인 channel_count 갱신
        self._refresh_channel_count(domain_id)

        return registered

    # ─── 도메인 통계 ───

    def get_domain_stats(self, domain_id: str) -> dict:
        """도메인 통계: 활성 채널 수, 총 수집 건수, 최근 수집 시각.

        Args:
            domain_id: 도메인 UUID.

        Returns:
            통계 dict.
        """
        try:
            domain = repo.get_research_domain(domain_id)
            if not domain:
                return {"success": False, "error": "도메인을 찾을 수 없습니다."}

            channels = repo.list_research_channels(domain_id=domain_id)

            active_count = sum(1 for ch in channels if ch.get("status") == "active")
            total_fetched = sum(ch.get("total_items_fetched", 0) for ch in channels)

            # 가장 최근 수집 시각
            last_fetched_times = [
                ch["last_fetched_at"]
                for ch in channels
                if ch.get("last_fetched_at")
            ]
            last_fetched_at = max(last_fetched_times) if last_fetched_times else None

            return {
                "success": True,
                "domain_id": domain_id,
                "domain_name": domain["name"],
                "total_channels": len(channels),
                "active_channels": active_count,
                "pending_channels": sum(1 for ch in channels if ch.get("status") == "pending"),
                "failed_channels": sum(1 for ch in channels if ch.get("status") in ("failed", "retired")),
                "total_items_fetched": total_fetched,
                "last_fetched_at": last_fetched_at,
            }
        except Exception as e:
            logger.error(f"도메인 통계 조회 실패 ({domain_id}): {e}")
            return {"success": False, "error": f"통계 조회 실패: {e}"}

    # ─── 내부 유틸 ───

    def _refresh_channel_count(self, domain_id: str) -> None:
        """도메인의 channel_count를 실제 채널 수로 갱신."""
        try:
            channels = repo.list_research_channels(domain_id=domain_id)
            count = len(channels)
            repo.update_research_domain(domain_id, channel_count=count, updated_at=_now_iso())
        except Exception as e:
            logger.warning(f"channel_count 갱신 실패 ({domain_id}): {e}")
