"""
RPA Core Infrastructure
Phase 2.5 Day 5-6: Windows Automation Core

Features:
1. 마우스/키보드 제어 (PyAutoGUI)
2. 화면 캡처 (mss)
3. OCR 텍스트 인식 (EasyOCR)
4. UI 요소 찾기 (템플릿 매칭)
5. 안전 장치 (Fail-safe, 타임아웃)

Design:
- Singleton 패턴 (RPA 세션 관리)
- Retry 메커니즘
- 로깅 및 스크린샷 저장
- Resonance Ledger 통합 준비
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import mss
import numpy as np
import pyautogui


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class RPACoreConfig:
    """RPA Core 설정"""
    output_dir: Path = Path("outputs/rpa_core")
    screenshot_dir: Path = Path("outputs/rpa_core/screenshots")
    
    # PyAutoGUI 설정
    pause: float = 0.5  # 각 동작 후 대기 시간
    failsafe: bool = True  # 마우스를 화면 모서리로 이동 시 예외 발생
    
    # OCR 설정
    enable_ocr: bool = False  # EasyOCR 활성화 (GPU 필요)
    ocr_languages: List[str] = field(default_factory=lambda: ["en", "ko"])
    
    # 템플릿 매칭 설정
    match_threshold: float = 0.8  # 유사도 임계값
    
    # 타임아웃
    default_timeout: float = 30.0  # 기본 타임아웃 (초)
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    log_level: str = "INFO"


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class ScreenRegion:
    """화면 영역"""
    x: int
    y: int
    width: int
    height: int
    
    def to_tuple(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.width, self.height)


@dataclass
class UIElement:
    """UI 요소"""
    name: str
    region: ScreenRegion
    confidence: float
    screenshot: Optional[np.ndarray] = None


class MouseButton(str, Enum):
    """마우스 버튼"""
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


# ============================================================================
# RPA Core
# ============================================================================

class RPACore:
    """RPA Core Infrastructure (Singleton)"""
    
    _instance: Optional['RPACore'] = None
    
    def __new__(cls, config: Optional[RPACoreConfig] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[RPACoreConfig] = None):
        if hasattr(self, '_initialized'):
            return
        
        self.config = config or RPACoreConfig()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.config.log_level)
        
        # PyAutoGUI 설정
        pyautogui.PAUSE = self.config.pause
        pyautogui.FAILSAFE = self.config.failsafe
        
        # Output 디렉토리 생성
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        self.config.screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        # OCR 초기화 (선택적)
        self.ocr_reader = None
        if self.config.enable_ocr:
            try:
                import easyocr
                self.ocr_reader = easyocr.Reader(self.config.ocr_languages, gpu=False)
                self.logger.info("EasyOCR initialized")
            except ImportError:
                self.logger.warning("EasyOCR not available. Install: pip install easyocr")
        
        self._initialized = True
        self.logger.info("RPA Core initialized")
    
    # ========================================================================
    # Mouse Control
    # ========================================================================
    
    async def move_mouse(self, x: int, y: int, duration: float = 0.5):
        """마우스 이동"""
        self.logger.debug(f"Moving mouse to ({x}, {y})")
        await asyncio.to_thread(pyautogui.moveTo, x, y, duration)
    
    async def click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: MouseButton = MouseButton.LEFT,
        clicks: int = 1,
        interval: float = 0.0
    ):
        """마우스 클릭"""
        if x is not None and y is not None:
            await self.move_mouse(x, y)
        
        self.logger.debug(f"Clicking {button} button {clicks} times")
        await asyncio.to_thread(pyautogui.click, button=button.value, clicks=clicks, interval=interval)
    
    async def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 1.0):
        """드래그"""
        self.logger.debug(f"Dragging from ({start_x}, {start_y}) to ({end_x}, {end_y})")
        await self.move_mouse(start_x, start_y)
        await asyncio.to_thread(pyautogui.dragTo, end_x, end_y, duration)
    
    # ========================================================================
    # Keyboard Control
    # ========================================================================
    
    async def type_text(self, text: str, interval: float = 0.1):
        """텍스트 입력"""
        self.logger.debug(f"Typing text: {text[:50]}...")
        await asyncio.to_thread(pyautogui.typewrite, text, interval)
    
    async def press_key(self, key: str, presses: int = 1, interval: float = 0.0):
        """키 입력"""
        self.logger.debug(f"Pressing key: {key} {presses} times")
        await asyncio.to_thread(pyautogui.press, key, presses=presses, interval=interval)
    
    async def hotkey(self, *keys: str):
        """단축키 입력"""
        self.logger.debug(f"Pressing hotkey: {'+'.join(keys)}")
        await asyncio.to_thread(pyautogui.hotkey, *keys)
    
    # ========================================================================
    # Screen Capture
    # ========================================================================
    
    async def capture_screen(self, region: Optional[ScreenRegion] = None) -> np.ndarray:
        """화면 캡처"""
        with mss.mss() as sct:
            if region:
                monitor = {
                    "top": region.y,
                    "left": region.x,
                    "width": region.width,
                    "height": region.height
                }
            else:
                monitor = sct.monitors[1]  # Primary monitor
            
            screenshot = await asyncio.to_thread(sct.grab, monitor)
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            self.logger.debug(f"Captured screen: {img.shape}")
            return img
    
    async def save_screenshot(self, filename: Optional[str] = None) -> Path:
        """스크린샷 저장"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
        
        screenshot = await self.capture_screen()
        filepath = self.config.screenshot_dir / filename
        
        await asyncio.to_thread(cv2.imwrite, str(filepath), screenshot)
        self.logger.info(f"Screenshot saved: {filepath}")
        
        return filepath
    
    # ========================================================================
    # OCR
    # ========================================================================
    
    async def extract_text(self, region: Optional[ScreenRegion] = None) -> str:
        """OCR 텍스트 추출"""
        if not self.ocr_reader:
            raise RuntimeError("OCR not enabled. Set enable_ocr=True in config")
        
        screenshot = await self.capture_screen(region)
        
        # EasyOCR 실행
        results = await asyncio.to_thread(self.ocr_reader.readtext, screenshot)
        
        # 텍스트만 추출
        text = " ".join([result[1] for result in results])
        
        self.logger.debug(f"Extracted text: {text[:100]}...")
        return text
    
    # ========================================================================
    # UI Element Finding
    # ========================================================================
    
    async def find_element(
        self,
        template_path: str,
        threshold: Optional[float] = None,
        region: Optional[ScreenRegion] = None
    ) -> Optional[UIElement]:
        """템플릿 매칭으로 UI 요소 찾기"""
        threshold = threshold or self.config.match_threshold
        
        # 화면 캡처
        screenshot = await self.capture_screen(region)
        
        # 템플릿 로드
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None:
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        # 템플릿 매칭
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= threshold:
            h, w = template.shape[:2]
            element_region = ScreenRegion(
                x=max_loc[0] + (region.x if region else 0),
                y=max_loc[1] + (region.y if region else 0),
                width=w,
                height=h
            )
            
            self.logger.info(f"Found element: {template_path} (confidence: {max_val:.2f})")
            
            return UIElement(
                name=Path(template_path).stem,
                region=element_region,
                confidence=max_val,
                screenshot=screenshot
            )
        
        self.logger.warning(f"Element not found: {template_path} (max confidence: {max_val:.2f})")
        return None
    
    async def wait_for_element(
        self,
        template_path: str,
        timeout: Optional[float] = None,
        check_interval: float = 1.0
    ) -> Optional[UIElement]:
        """UI 요소가 나타날 때까지 대기"""
        timeout = timeout or self.config.default_timeout
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            element = await self.find_element(template_path)
            if element:
                return element
            
            await asyncio.sleep(check_interval)
        
        self.logger.warning(f"Timeout waiting for element: {template_path}")
        return None
    
    # ========================================================================
    # High-level Actions
    # ========================================================================
    
    async def click_element(self, template_path: str, timeout: Optional[float] = None) -> bool:
        """UI 요소 찾아서 클릭"""
        element = await self.wait_for_element(template_path, timeout)
        if not element:
            return False
        
        # 요소 중심 클릭
        center_x = element.region.x + element.region.width // 2
        center_y = element.region.y + element.region.height // 2
        
        await self.click(center_x, center_y)
        return True
    
    async def type_in_element(
        self,
        template_path: str,
        text: str,
        timeout: Optional[float] = None
    ) -> bool:
        """UI 요소 찾아서 텍스트 입력"""
        # 요소 클릭
        success = await self.click_element(template_path, timeout)
        if not success:
            return False
        
        # 텍스트 입력
        await self.type_text(text)
        return True


# ============================================================================
# CLI Interface
# ============================================================================

async def main():
    """CLI 테스트"""
    logging.basicConfig(level=logging.INFO)
    
    rpa = RPACore()
    
    print("\n✅ RPA Core initialized")
    print(f"   Screen size: {pyautogui.size()}")
    print(f"   Mouse position: {pyautogui.position()}")
    print(f"   Failsafe: {pyautogui.FAILSAFE}")
    
    # 스크린샷 테스트
    screenshot_path = await rpa.save_screenshot("test_screenshot.png")
    print(f"\n✅ Screenshot saved: {screenshot_path}")


if __name__ == "__main__":
    asyncio.run(main())
