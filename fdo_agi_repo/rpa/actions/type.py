"""
Type Action
Phase 2.5 Week 2 Day 11

키보드 입력 액션
"""

from typing import Dict, Any
from .base import Action
import logging

logger = logging.getLogger(__name__)


class TypeAction(Action):
    """키보드 입력 액션"""
    
    def __init__(self, step: Dict[str, Any]):
        super().__init__(step)
        # target이 입력할 텍스트
        self.text_to_type = self.target
    
    def simulate(self) -> tuple[bool, Dict[str, Any]]:
        """Dry-run: 타이핑 시뮬레이션"""
        logger.info(f"  [SIM] Would type: {self.text_to_type}")
        logger.info(f"  [SIM] Description: {self.description}")
        
        metadata = {
            'text': self.text_to_type,
            'length': len(self.text_to_type),
            'description': self.description,
            'simulated': True
        }
        
        return (True, metadata)
    
    def run(self) -> tuple[bool, Dict[str, Any]]:
        """실제 타이핑 실행"""
        try:
            import pyautogui
            
            logger.info(f"  [LIVE] Typing: {self.text_to_type}")
            pyautogui.write(self.text_to_type, interval=0.1)
            
            metadata = {
                'text': self.text_to_type,
                'length': len(self.text_to_type),
                'description': self.description
            }
            
            return (True, metadata)
        
        except Exception as e:
            logger.error(f"Type failed: {e}")
            return (False, {'error': str(e)})
