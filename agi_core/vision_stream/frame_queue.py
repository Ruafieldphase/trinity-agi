"""
Vision Frame Queue
Thread-safe 프레임 버퍼 (asyncio.Queue 기반)

OBS에서 수신한 프레임을 Vision 분석기로 전달하기 위한 버퍼.
오래된 프레임은 자동으로 드롭하여 실시간성 유지.
"""

import asyncio
import logging
from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger("VisionFrameQueue")


@dataclass
class VisionFrame:
    """프레임 데이터 컨테이너"""
    data: bytes
    timestamp: datetime
    frame_id: int
    
    @classmethod
    def create(cls, data: bytes, frame_id: int) -> "VisionFrame":
        return cls(
            data=data,
            timestamp=datetime.now(timezone.utc),
            frame_id=frame_id
        )


class VisionFrameQueue:
    """
    Thread-safe 비전 프레임 큐
    
    특징:
    - asyncio.Queue 기반
    - 최대 크기 초과 시 가장 오래된 프레임 드롭
    - 프레임 메타데이터 (timestamp, frame_id) 포함
    """
    
    _instance: Optional["VisionFrameQueue"] = None
    _queue: Optional[asyncio.Queue] = None
    _frame_counter: int = 0
    _dropped_frames: int = 0
    
    def __new__(cls, maxsize: int = 10):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._queue = asyncio.Queue(maxsize=maxsize)
            cls._frame_counter = 0
            cls._dropped_frames = 0
            logger.info(f"VisionFrameQueue initialized (maxsize={maxsize})")
        return cls._instance
    
    @classmethod
    def get_instance(cls, maxsize: int = 10) -> "VisionFrameQueue":
        """싱글톤 인스턴스 획득"""
        return cls(maxsize)
    
    async def put(self, frame_bytes: bytes) -> bool:
        """
        프레임을 큐에 추가
        
        Returns:
            True if frame was added, False if dropped
        """
        if self._queue is None:
            return False
            
        self._frame_counter += 1
        frame = VisionFrame.create(frame_bytes, self._frame_counter)
        
        # 큐가 가득 차면 가장 오래된 프레임 드롭
        if self._queue.full():
            try:
                dropped = self._queue.get_nowait()
                self._dropped_frames += 1
                logger.debug(f"Dropped frame #{dropped.frame_id} (queue full)")
            except asyncio.QueueEmpty:
                pass
        
        try:
            self._queue.put_nowait(frame)
            logger.debug(f"Frame #{frame.frame_id} added to queue (size: {self._queue.qsize()})")
            return True
        except asyncio.QueueFull:
            self._dropped_frames += 1
            return False
    
    async def get(self, timeout: Optional[float] = None) -> Optional[VisionFrame]:
        """
        큐에서 프레임 획득
        
        Args:
            timeout: 대기 시간 (초), None이면 무한 대기
            
        Returns:
            VisionFrame or None if timeout
        """
        if self._queue is None:
            return None
            
        try:
            if timeout is not None:
                return await asyncio.wait_for(self._queue.get(), timeout=timeout)
            else:
                return await self._queue.get()
        except asyncio.TimeoutError:
            return None
    
    def get_nowait(self) -> Optional[VisionFrame]:
        """블로킹 없이 프레임 획득"""
        if self._queue is None:
            return None
        try:
            return self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return None
    
    @property
    def size(self) -> int:
        """현재 큐 크기"""
        return self._queue.qsize() if self._queue else 0
    
    @property
    def total_frames(self) -> int:
        """총 수신 프레임 수"""
        return self._frame_counter
    
    @property
    def dropped_frames(self) -> int:
        """드롭된 프레임 수"""
        return self._dropped_frames
    
    def stats(self) -> dict:
        """큐 통계"""
        return {
            "current_size": self.size,
            "total_frames": self.total_frames,
            "dropped_frames": self.dropped_frames,
            "drop_rate": self.dropped_frames / max(self.total_frames, 1)
        }
    
    @classmethod
    def reset(cls) -> None:
        """테스트용 인스턴스 리셋"""
        cls._instance = None
        cls._queue = None
        cls._frame_counter = 0
        cls._dropped_frames = 0


# 편의를 위한 모듈 레벨 함수
_global_queue: Optional[VisionFrameQueue] = None


def get_queue(maxsize: int = 10) -> VisionFrameQueue:
    """전역 큐 인스턴스 획득"""
    global _global_queue
    if _global_queue is None:
        _global_queue = VisionFrameQueue(maxsize)
    return _global_queue
