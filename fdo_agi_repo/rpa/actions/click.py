"""
Click Action
Phase 2.5 Week 2 Day 11

화면 클릭 액션
"""

from typing import Dict, Any
from .base import Action
import logging

logger = logging.getLogger(__name__)


class ClickAction(Action):
    """화면 클릭 액션"""
    
    def __init__(self, step: Dict[str, Any]):
        super().__init__(step)
        # target에서 클릭 위치 추출 (OCR 결과 또는 좌표)
        self.click_target = self.target
    
    def simulate(self) -> tuple[bool, Dict[str, Any]]:
        """Dry-run: 클릭 시뮬레이션"""
        logger.info(f"  [SIM] Would click on: {self.click_target}")
        logger.info(f"  [SIM] Description: {self.description}")
        
        metadata = {
            'click_target': self.click_target,
            'description': self.description,
            'simulated': True
        }
        
        return (True, metadata)
    
    def run(self) -> tuple[bool, Dict[str, Any]]:
        """실제 클릭 실행"""
        try:
            import pyautogui
            
            # TODO: OCR로 target 텍스트 찾기 또는 좌표 사용
            # 지금은 화면 중앙 클릭 (데모)
            screen_width, screen_height = pyautogui.size()
            x, y = screen_width // 2, screen_height // 2
            
            logger.info(f"  [LIVE] Clicking at ({x}, {y})")
            pyautogui.click(x, y)
            
            metadata = {
                'click_target': self.click_target,
                'position': (x, y),
                'description': self.description
            }
            
            return (True, metadata)
        
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return (False, {'error': str(e)})
