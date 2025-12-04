"""
Base Action Class
Phase 2.5 Week 2 Day 11

모든 RPA 액션의 베이스 클래스
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class ActionResult:
    """액션 실행 결과"""
    success: bool
    action_type: str
    duration: float = 0.0  # 기본값 (execution_time과 동기화됨)
    action_name: str = ""  # 액션 이름 (식별용)
    execution_time: float = 0.0  # 별칭 (duration과 동일)
    dry_run: bool = False
    error: Optional[str] = None
    error_message: Optional[str] = None  # 별칭 (error와 동일)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """초기화 후 별칭 동기화"""
        # execution_time과 duration 중 하나라도 설정되면 둘 다 동기화
        if self.execution_time > 0.0 and self.duration == 0.0:
            self.duration = self.execution_time
        elif self.duration > 0.0 and self.execution_time == 0.0:
            self.execution_time = self.duration
        
        # error_message가 설정되지 않았으면 error 사용
        if self.error_message is None and self.error is not None:
            self.error_message = self.error
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'success': self.success,
            'action_type': self.action_type,
            'action_name': self.action_name,
            'duration': self.duration,
            'execution_time': self.execution_time,
            'dry_run': self.dry_run,
            'error': self.error,
            'error_message': self.error_message,
            'metadata': self.metadata
        }


class Action(ABC):
    """실행 가능한 액션 베이스 클래스"""
    
    def __init__(self, step: Dict[str, Any]):
        """
        Args:
            step: Step Extractor/Refiner에서 생성된 단계
                  예: {'action': 'INSTALL', 'target': 'docker', ...}
        """
        self.step = step
        self.action_type = step.get('action', 'UNKNOWN').upper()
        self.target = step.get('target', '')
        self.description = step.get('description', '')
        self.confidence = step.get('confidence', 0.0)
        self.timestamp = step.get('timestamp', 0.0)
    
    def execute(self, dry_run: bool = True) -> ActionResult:
        """
        액션 실행 (dry_run 또는 실제 실행)
        
        Args:
            dry_run: True면 시뮬레이션만, False면 실제 실행
        
        Returns:
            ActionResult
        """
        start_time = time.time()
        
        try:
            if dry_run:
                logger.info(f"[DRY-RUN] Simulating {self.action_type}: {self.target}")
                success, metadata = self.simulate()
            else:
                logger.info(f"[LIVE] Executing {self.action_type}: {self.target}")
                success, metadata = self.run()
            
            duration = time.time() - start_time
            
            return ActionResult(
                success=success,
                action_type=self.action_type,
                duration=duration,
                dry_run=dry_run,
                metadata=metadata
            )
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Error executing {self.action_type}: {e}")
            
            return ActionResult(
                success=False,
                action_type=self.action_type,
                duration=duration,
                dry_run=dry_run,
                error=str(e)
            )
    
    @abstractmethod
    def simulate(self) -> tuple[bool, Dict[str, Any]]:
        """
        Dry-run 시뮬레이션
        
        Returns:
            (success, metadata)
        """
        pass
    
    @abstractmethod
    def run(self) -> tuple[bool, Dict[str, Any]]:
        """
        실제 실행
        
        Returns:
            (success, metadata)
        """
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(action={self.action_type}, target={self.target})"
