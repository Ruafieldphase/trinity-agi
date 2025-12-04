"""
Install Action
Phase 2.5 Week 2 Day 11

설치 액션 (파일 다운로드, 실행 등)
"""

from typing import Dict, Any
from .base import Action
import logging

logger = logging.getLogger(__name__)


class InstallAction(Action):
    """설치 액션"""
    
    def __init__(self, step: Dict[str, Any]):
        super().__init__(step)
        # target이 설치할 프로그램
        self.program = self.target
    
    def simulate(self) -> tuple[bool, Dict[str, Any]]:
        """Dry-run: 설치 시뮬레이션"""
        logger.info(f"  [SIM] Would install: {self.program}")
        logger.info(f"  [SIM] Description: {self.description}")
        
        # 설치 단계 시뮬레이션
        steps = [
            f"Download {self.program} installer",
            f"Run installer",
            f"Follow installation wizard",
            f"Verify installation"
        ]
        
        for i, step in enumerate(steps, 1):
            logger.info(f"  [SIM]   Step {i}: {step}")
        
        metadata = {
            'program': self.program,
            'description': self.description,
            'install_steps': steps,
            'simulated': True
        }
        
        return (True, metadata)
    
    def run(self) -> tuple[bool, Dict[str, Any]]:
        """실제 설치 실행"""
        # TODO: 실제 설치는 매우 복잡하므로 Phase 3에서 구현
        # 지금은 dry-run만 지원
        logger.warning(f"  [LIVE] Install action not yet implemented: {self.program}")
        logger.warning(f"  [LIVE] Use dry-run mode for now")
        
        metadata = {
            'program': self.program,
            'description': self.description,
            'note': 'Installation requires manual intervention'
        }
        
        return (False, metadata)
