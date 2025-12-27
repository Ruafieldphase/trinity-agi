"""
Sequence Detector
이벤트 스트림에서 "하나의 절차 흐름"을 감지하는 계층

이벤트들의 묶음 = 하나의 절차 (Procedure)
"""

import time
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("SequenceDetector")


class SequenceDetector:
    """
    Vision 이벤트 스트림을 받아서 하나의 절차(sequence)로 묶는 감지기
    
    감지 기준:
    - 이벤트 간격이 max_gap 초를 넘으면 새 절차로 간주
    - 앱 전환/컨텍스트 변화가 감지되면 새 절차로 간주
    """
    
    def __init__(self, max_gap: float = 2.0):
        """
        Args:
            max_gap: 이벤트들 사이의 최대 시간 간격 (초)
                     이 시간보다 오래 비면 새로운 절차로 간주
        """
        self.current_events: List[Dict[str, Any]] = []
        self.last_timestamp: Optional[float] = None
        self.max_gap = max_gap
        self._sequence_count = 0
    
    def add_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Vision 이벤트를 추가하고, 하나의 절차(sequence)가 완성되었다고
        판단되면 dict를 반환합니다. 아니면 None을 반환합니다.
        
        Returns:
            완성된 sequence dict or None
        """
        now = event.get("timestamp")
        if now is None:
            now = time.time()
        elif isinstance(now, str):
            # ISO format timestamp to float
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(now.replace("Z", "+00:00"))
                now = dt.timestamp()
            except (ValueError, TypeError):
                now = time.time()
        
        if self._is_boundary(now, event):
            # 이전 sequence를 하나의 절차로 확정
            if self.current_events:
                self._sequence_count += 1
                seq = {
                    "sequence_id": self._sequence_count,
                    "events": self.current_events.copy(),
                    "start": self.current_events[0].get("timestamp", now),
                    "end": self.current_events[-1].get("timestamp", now),
                    "event_count": len(self.current_events),
                }
                logger.debug(f"Sequence #{self._sequence_count} completed with {len(self.current_events)} events")
                
                # 새로운 시퀀스로 초기화
                self.current_events = [event]
                self.last_timestamp = now
                return seq
        
        # 경계가 아니라면 현재 시퀀스에 이어 붙이기
        self.current_events.append(event)
        self.last_timestamp = now
        return None
    
    def _is_boundary(self, now: float, event: Dict[str, Any]) -> bool:
        """
        절차 경계 조건:
        - 이벤트 사이 시간 간격이 max_gap 초를 넘는 경우
        - 앱 전환/큰 컨텍스트 변화가 감지된 경우
        """
        if self.last_timestamp is None:
            return False
        
        # 시간 간격 체크
        if now - self.last_timestamp > self.max_gap:
            logger.debug(f"Boundary detected: time gap {now - self.last_timestamp:.1f}s > {self.max_gap}s")
            return True
        
        # 앱 전환/컨텍스트 전환 감지
        if event.get("context_change"):
            logger.debug("Boundary detected: context_change flag")
            return True
        
        # 앱 변경 감지 (현재 이벤트의 앱과 이전 이벤트들의 앱 비교)
        current_app = event.get("current_app") or event.get("app")
        if current_app and self.current_events:
            prev_event = self.current_events[-1]
            prev_app = prev_event.get("current_app") or prev_event.get("app")
            if prev_app and current_app != prev_app:
                logger.debug(f"Boundary detected: app change {prev_app} -> {current_app}")
                return True
        
        return False
    
    def flush(self) -> Optional[Dict[str, Any]]:
        """강제로 현재 시퀀스를 완료하고 반환"""
        if not self.current_events:
            return None
        
        self._sequence_count += 1
        seq = {
            "sequence_id": self._sequence_count,
            "events": self.current_events.copy(),
            "start": self.current_events[0].get("timestamp"),
            "end": self.current_events[-1].get("timestamp"),
            "event_count": len(self.current_events),
        }
        self.current_events = []
        self.last_timestamp = None
        return seq
    
    def reset(self) -> None:
        """상태 초기화"""
        self.current_events = []
        self.last_timestamp = None
    
    @property
    def pending_events(self) -> int:
        """현재 버퍼에 있는 이벤트 수"""
        return len(self.current_events)
    
    @property
    def sequence_count(self) -> int:
        """완성된 시퀀스 총 수"""
        return self._sequence_count
