#!/usr/bin/env python3
"""
HybridSummarizer - 실시간(규칙) + 백그라운드(LLM) 요약 시스템

설계:
- 실시간 대화 중: 규칙 기반 요약 (<1ms, 빠른 응답)
- 세션 종료 후: LLM 기반 고품질 요약 (~3초, 백그라운드)

사용 예시:
```python
from persona_system.utils.hybrid_summarizer import get_hybrid_summarizer

summarizer = get_hybrid_summarizer()

# 실시간 요약
summary = summarizer.get_realtime_summary(messages, running_summary)

# 세션 종료 시 백그라운드 요약
summarizer.queue_session_summary(session_id, messages)
```
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, TYPE_CHECKING
from datetime import datetime

from .summary_utils import update_running_summary
from .summary_llm import summarize_with_llm
from .session_summary_storage import get_session_storage

if TYPE_CHECKING:
    from .session_summary_storage import SessionSummary

logger = logging.getLogger(__name__)


@dataclass
class SummaryTask:
    """백그라운드 요약 작업"""

    session_id: str
    user_id: str
    messages: List[Dict[str, str]]
    max_bullets: int = 8
    max_chars: int = 800
    temperature: float = 0.3
    created_at: datetime = None
    priority: int = 0  # 낮을수록 우선순위 높음

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class HybridSummarizer:
    """하이브리드 요약기: 실시간(규칙) + 백그라운드(LLM)"""

    def __init__(self):
        """초기화"""
        self.task_queue: asyncio.Queue = None
        self.worker_task: Optional[asyncio.Task] = None
        self.session_summaries: Dict[str, str] = {}  # session_id -> summary (메모리 캐시)
        self.storage = get_session_storage()  # 영구 저장소
        self.stats = {
            "realtime_summaries": 0,
            "session_summaries_queued": 0,
            "session_summaries_completed": 0,
            "session_summaries_failed": 0,
        }
        self._initialized = False
        logger.info("HybridSummarizer created with persistent storage (not started)")

    def initialize(self):
        """비동기 큐 초기화 및 워커 시작"""
        if self._initialized:
            logger.warning("HybridSummarizer already initialized")
            return

        try:
            # 이벤트 루프 가져오기 또는 생성
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # 이벤트 루프가 없으면 새로 생성
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # 큐 생성
            self.task_queue = asyncio.Queue(maxsize=100)

            # 백그라운드 워커 시작
            self.worker_task = asyncio.create_task(self._background_worker())

            self._initialized = True
            logger.info("HybridSummarizer initialized with background worker")

        except Exception as e:
            logger.error(f"Failed to initialize HybridSummarizer: {e}")
            self._initialized = False

    async def _background_worker(self):
        """백그라운드 작업 워커"""
        logger.info("Background summary worker started")

        while True:
            try:
                # 작업 대기 (타임아웃 1초)
                try:
                    task: SummaryTask = await asyncio.wait_for(
                        self.task_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    # 타임아웃 시 계속 대기
                    continue

                # LLM 요약 생성
                logger.info(
                    f"Processing session summary: session_id={task.session_id}, "
                    f"messages={len(task.messages)}"
                )

                start = time.time()
                try:
                    summary = await asyncio.to_thread(
                        summarize_with_llm,
                        messages=task.messages,
                        max_bullets=task.max_bullets,
                        max_chars=task.max_chars,
                        temperature=task.temperature,
                    )

                    elapsed = (time.time() - start) * 1000

                    # 결과 저장 (메모리 캐시)
                    self.session_summaries[task.session_id] = summary

                    # 영구 저장소에 저장
                    self.storage.save(
                        session_id=task.session_id,
                        user_id=task.user_id,
                        summary=summary,
                        summary_type="llm",
                        message_count=len(task.messages),
                        metadata={
                            "max_bullets": task.max_bullets,
                            "max_chars": task.max_chars,
                            "temperature": task.temperature,
                            "elapsed_ms": int(elapsed),
                        },
                    )

                    self.stats["session_summaries_completed"] += 1

                    logger.info(
                        f"[OK] Session summary completed and saved: session_id={task.session_id}, "
                        f"time={elapsed:.0f}ms, length={len(summary)}"
                    )

                except Exception as e:
                    elapsed = (time.time() - start) * 1000
                    logger.error(
                        f"[FAIL] Session summary failed: session_id={task.session_id}, "
                        f"time={elapsed:.0f}ms, error={e}"
                    )
                    self.stats["session_summaries_failed"] += 1

                # 작업 완료 표시
                self.task_queue.task_done()

            except asyncio.CancelledError:
                logger.info("Background worker cancelled")
                break
            except Exception as e:
                logger.error(f"Background worker error: {e}", exc_info=True)
                await asyncio.sleep(1)  # 에러 발생 시 1초 대기

    def get_realtime_summary(
        self,
        messages: List[Dict[str, str]],
        running_summary: Optional[str] = None,
        max_bullets: int = 6,
        max_chars: int = 600,
        per_line_max: int = 120,
    ) -> str:
        """
        실시간 요약 (규칙 기반)

        Args:
            messages: 메시지 목록
            running_summary: 기존 러닝 요약
            max_bullets: 최대 불릿 수
            max_chars: 최대 글자 수
            per_line_max: 줄당 최대 길이

        Returns:
            요약 문자열
        """
        start = time.time()

        summary = update_running_summary(
            running_summary=running_summary,
            new_messages=messages,
            max_bullets=max_bullets,
            max_chars=max_chars,
            per_line_max=per_line_max,
        )

        elapsed = (time.time() - start) * 1000
        self.stats["realtime_summaries"] += 1

        logger.debug(
            f"Realtime summary: time={elapsed:.2f}ms, "
            f"messages={len(messages)}, length={len(summary)}"
        )

        return summary

    def queue_session_summary(
        self,
        session_id: str,
        user_id: str,
        messages: List[Dict[str, str]],
        max_bullets: int = 8,
        max_chars: int = 800,
        temperature: float = 0.3,
        priority: int = 0,
    ) -> bool:
        """
        세션 요약 큐에 추가 (백그라운드 LLM 요약)

        Args:
            session_id: 세션 ID
            user_id: 사용자 ID
            messages: 메시지 목록
            max_bullets: 최대 불릿 수
            max_chars: 최대 글자 수
            temperature: LLM temperature
            priority: 우선순위 (낮을수록 먼저 처리)

        Returns:
            성공 여부
        """
        if not self._initialized:
            logger.warning("HybridSummarizer not initialized. Call initialize() first.")
            return False

        try:
            task = SummaryTask(
                session_id=session_id,
                user_id=user_id,
                messages=messages,
                max_bullets=max_bullets,
                max_chars=max_chars,
                temperature=temperature,
                priority=priority,
            )

            # 큐에 추가 (논블로킹)
            try:
                self.task_queue.put_nowait(task)
                self.stats["session_summaries_queued"] += 1
                logger.info(f"Session summary queued: session_id={session_id}")
                return True

            except asyncio.QueueFull:
                logger.warning(
                    f"Session summary queue full: session_id={session_id}, "
                    f"size={self.task_queue.qsize()}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to queue session summary: {e}")
            return False

    def get_session_summary(self, session_id: str) -> Optional[str]:
        """
        완료된 세션 요약 조회

        Args:
            session_id: 세션 ID

        Returns:
            요약 문자열 (없으면 None)
        """
        # 메모리 캐시 확인
        if session_id in self.session_summaries:
            return self.session_summaries[session_id]

        # 영구 저장소에서 로드
        session_summary = self.storage.load(session_id)
        if session_summary:
            # 메모리 캐시에 저장
            self.session_summaries[session_id] = session_summary.summary
            return session_summary.summary

        return None

    def search_session_memory(self, **filters) -> List["SessionSummary"]:
        """
        세션 저장소 검색 헬퍼 (필터/임베딩 검색 포함)

        Args:
            **filters: storage.search 에 전달할 인자

        Returns:
            SessionSummary 리스트
        """
        return self.storage.search(**filters)

    def list_recent_session_memory(
        self, limit: int = 10, include_embeddings: bool = False
    ) -> List["SessionSummary"]:
        """최근 요약 목록"""
        return self.storage.list_recent(
            limit=limit, include_embeddings=include_embeddings
        )

    def get_stats(self) -> Dict[str, any]:
        """통계 반환"""
        queue_size = self.task_queue.qsize() if self.task_queue else 0

        # 저장소 통계
        storage_stats = self.storage.get_stats()

        return {
            "initialized": self._initialized,
            "realtime_summaries": self.stats["realtime_summaries"],
            "session_summaries_queued": self.stats["session_summaries_queued"],
            "session_summaries_completed": self.stats["session_summaries_completed"],
            "session_summaries_failed": self.stats["session_summaries_failed"],
            "queue_size": queue_size,
            "success_rate": (
                f"{self.stats['session_summaries_completed'] / self.stats['session_summaries_queued'] * 100:.1f}%"
                if self.stats["session_summaries_queued"] > 0
                else "N/A"
            ),
            "storage": storage_stats,
        }

    async def shutdown(self):
        """워커 종료"""
        if self.worker_task:
            logger.info("Shutting down background worker...")
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
            logger.info("Background worker shut down")

        self._initialized = False


# 싱글톤 인스턴스
_hybrid_summarizer: Optional[HybridSummarizer] = None


def get_hybrid_summarizer(auto_initialize: bool = True) -> HybridSummarizer:
    """
    HybridSummarizer 싱글톤 반환

    Args:
        auto_initialize: True일 경우 자동으로 initialize() 호출

    Returns:
        HybridSummarizer 인스턴스
    """
    global _hybrid_summarizer

    if _hybrid_summarizer is None:
        _hybrid_summarizer = HybridSummarizer()

    if auto_initialize and not _hybrid_summarizer._initialized:
        _hybrid_summarizer.initialize()

    return _hybrid_summarizer


def reset_hybrid_summarizer():
    """HybridSummarizer 리셋 (테스트용)"""
    global _hybrid_summarizer

    if _hybrid_summarizer and _hybrid_summarizer._initialized:
        asyncio.create_task(_hybrid_summarizer.shutdown())

    _hybrid_summarizer = None
    logger.info("HybridSummarizer reset")
