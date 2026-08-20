"""asyncio.Queue 기반 영상 생성 작업 큐.

동시 1개 작업만 실행하며, worker()를 asyncio.create_task로 실행한다.
완료/실패 작업은 30분 후 메모리에서 자동 정리된다.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """작업 상태."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Job:
    """영상 생성 작업 단위.

    Attributes:
        id: UUID 문자열
        status: 현재 작업 상태
        progress: 사람이 읽을 수 있는 진행 메시지 (예: "TTS 3/6 완료")
        progress_pct: 진행률 (0-100)
        result: 작업 완료 시 반환값
        error: 작업 실패 시 오류 메시지
        chat_id: 텔레그램 채팅 ID
        message_id: 진행률 메시지 ID (편집 대상)
        news_project_id: 연결된 NewsProject ID
        created_at: 작업 생성 시각
    """

    id: str
    status: JobStatus
    progress: str
    progress_pct: int
    result: Optional[Any]
    error: Optional[str]
    chat_id: int
    message_id: int
    news_project_id: str
    created_at: datetime


@dataclass
class _QueueItem:
    """큐 내부 전송 단위."""

    job: Job
    coro_factory: Callable
    kwargs: dict = field(default_factory=dict)


class VideoJobQueue:
    """asyncio.Queue 기반 영상 생성 작업 큐.

    max_concurrent_jobs=1: 동시에 1개 작업만 실행한다.
    worker()는 외부에서 asyncio.create_task(video_queue.worker())로 시작해야 한다.

    Example:
        asyncio.create_task(video_queue.worker())
        job = await video_queue.enqueue(
            my_coro_factory, chat_id=123, message_id=456, news_project_id="abc"
        )
    """

    def __init__(self) -> None:
        self._queue: asyncio.Queue[_QueueItem] = asyncio.Queue()
        self._jobs: dict[str, Job] = {}

    async def enqueue(
        self,
        coro_factory: Callable,
        chat_id: int,
        message_id: int,
        news_project_id: str,
        **kwargs: Any,
    ) -> Job:
        """새 작업을 큐에 추가하고 Job 객체를 반환한다.

        Args:
            coro_factory: 코루틴을 반환하는 팩토리 함수.
                호출 시 job 키워드 인자가 전달된다.
            chat_id: 텔레그램 채팅 ID.
            message_id: 진행률 메시지 ID.
            news_project_id: 연결된 뉴스 프로젝트 ID.
            **kwargs: coro_factory에 추가로 전달할 키워드 인자.

        Returns:
            PENDING 상태의 Job 객체.
        """
        job = Job(
            id=str(uuid.uuid4()),
            status=JobStatus.PENDING,
            progress="대기 중",
            progress_pct=0,
            result=None,
            error=None,
            chat_id=chat_id,
            message_id=message_id,
            news_project_id=news_project_id,
            created_at=datetime.now(),
        )
        self._jobs[job.id] = job

        item = _QueueItem(job=job, coro_factory=coro_factory, kwargs=kwargs)
        await self._queue.put(item)

        logger.info(
            "작업 큐 추가: job_id=%s news_project_id=%s", job.id, news_project_id
        )
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """job_id로 Job 조회.

        Args:
            job_id: 조회할 작업 ID.

        Returns:
            Job 객체 또는 None (존재하지 않거나 이미 정리된 경우).
        """
        return self._jobs.get(job_id)

    def get_active_job(self) -> Optional[Job]:
        """현재 실행 중인 작업(RUNNING) 반환.

        Returns:
            RUNNING 상태의 Job 또는 None.
        """
        for job in self._jobs.values():
            if job.status == JobStatus.RUNNING:
                return job
        return None

    def get_recent_jobs(self, limit: int = 10) -> list[Job]:
        """최근 작업 목록을 생성 시각 역순으로 반환.

        Args:
            limit: 반환할 최대 작업 수. 기본값 10.

        Returns:
            최신 순으로 정렬된 Job 목록.
        """
        sorted_jobs = sorted(
            self._jobs.values(),
            key=lambda j: j.created_at,
            reverse=True,
        )
        return sorted_jobs[:limit]

    def _schedule_cleanup(self, job_id: str) -> None:
        """30분 후 완료된 작업을 메모리에서 제거하도록 예약.

        Args:
            job_id: 정리 대상 작업 ID.
        """
        try:
            loop = asyncio.get_event_loop()
            loop.call_later(
                1800,
                lambda jid=job_id: self._jobs.pop(jid, None),
            )
        except RuntimeError:
            # 이벤트 루프가 없는 환경(테스트 등)에서는 정리 예약 생략
            logger.warning(
                "이벤트 루프 없음 - 작업 정리 예약 생략: job_id=%s", job_id
            )

    async def worker(self) -> None:
        """작업 큐 워커. asyncio.create_task로 실행해야 한다.

        큐에서 작업을 꺼내 순차적으로 실행한다(max_concurrent_jobs=1).
        작업 완료/실패 후 30분 뒤 메모리에서 자동 정리된다.
        """
        logger.info("VideoJobQueue 워커 시작")
        while True:
            item: _QueueItem = await self._queue.get()
            job = item.job
            job.status = JobStatus.RUNNING
            job.progress = "작업 시작"
            logger.info(
                "작업 실행 시작: job_id=%s news_project_id=%s",
                job.id,
                job.news_project_id,
            )

            try:
                result = await item.coro_factory(job=job, **item.kwargs)
                job.result = result
                job.status = JobStatus.DONE
                job.progress_pct = 100
                job.progress = "완료"
                logger.info("작업 완료: job_id=%s", job.id)
            except asyncio.CancelledError:
                job.error = "작업이 취소되었습니다."
                job.status = JobStatus.FAILED
                logger.warning("작업 취소: job_id=%s", job.id)
                raise
            except Exception as exc:
                job.error = str(exc)
                job.status = JobStatus.FAILED
                logger.exception("작업 실패: job_id=%s error=%s", job.id, exc)
            finally:
                self._queue.task_done()
                self._schedule_cleanup(job.id)


# ─────────────────────────────────────────────
# 싱글턴
# ─────────────────────────────────────────────

video_queue = VideoJobQueue()
