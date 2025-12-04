"""
Screenshot Capture Utility
Phase 2.5 Week 2 Day 12

화면 캡처 및 영역 지정 캡처
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
import logging

import pyautogui
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class ScreenRegion:
    """화면 영역 정의"""
    left: int
    top: int
    width: int
    height: int
    
    @property
    def right(self) -> int:
        return self.left + self.width
    
    @property
    def bottom(self) -> int:
        return self.top + self.height
    
    def to_tuple(self) -> Tuple[int, int, int, int]:
        """PIL.Image.crop()에 사용할 튜플 반환 (left, top, right, bottom)"""
        return (self.left, self.top, self.right, self.bottom)
    
    def to_pyautogui_tuple(self) -> Tuple[int, int, int, int]:
        """pyautogui.screenshot()에 사용할 튜플 반환 (left, top, width, height)"""
        return (self.left, self.top, self.width, self.height)


class ScreenshotCapture:
    """
    스크린샷 캡처 유틸리티
    
    Features:
    - 전체 화면 캡처
    - 영역 지정 캡처
    - 자동 파일 저장
    - 메모리 효율적 처리
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Args:
            output_dir: 스크린샷 저장 디렉토리 (None이면 저장 안함)
        """
        self.output_dir = output_dir
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # 화면 크기
        self.screen_width, self.screen_height = pyautogui.size()
        logger.info(f"Screen size: {self.screen_width}x{self.screen_height}")
    
    def capture_full_screen(
        self,
        filename: Optional[str] = None,
        save: bool = True
    ) -> Image.Image:
        """
        전체 화면 캡처
        
        Args:
            filename: 저장할 파일명 (None이면 자동 생성)
            save: 파일로 저장할지 여부
        
        Returns:
            PIL Image 객체
        """
        logger.debug("Capturing full screen...")
        
        # pyautogui로 캡처
        screenshot = pyautogui.screenshot()
        
        # 저장
        if save and self.output_dir:
            if filename is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            
            filepath = self.output_dir / filename
            # On Windows, PIL may raise OSError: Invalid argument when saving
            # directly by path in rare cases. Use explicit binary file handle.
            with open(filepath, "wb") as fp:
                screenshot.save(fp, format="PNG")
            logger.info(f"Screenshot saved: {filepath}")
        
        return screenshot
    
    def capture_region(
        self,
        region: ScreenRegion,
        filename: Optional[str] = None,
        save: bool = True
    ) -> Image.Image:
        """
        특정 영역 캡처
        
        Args:
            region: 캡처할 영역
            filename: 저장할 파일명
            save: 파일로 저장할지 여부
        
        Returns:
            PIL Image 객체
        """
        logger.debug(f"Capturing region: {region}")
        
        # 영역 검증
        if region.left < 0 or region.top < 0:
            raise ValueError(f"Region coordinates cannot be negative: {region}")
        
        if region.right > self.screen_width or region.bottom > self.screen_height:
            logger.warning(
                f"Region {region} exceeds screen bounds "
                f"({self.screen_width}x{self.screen_height}), clipping..."
            )
        
        # pyautogui로 영역 캡처
        screenshot = pyautogui.screenshot(region=region.to_pyautogui_tuple())
        
        # 저장
        if save and self.output_dir:
            if filename is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"region_{timestamp}.png"
            
            filepath = self.output_dir / filename
            with open(filepath, "wb") as fp:
                screenshot.save(fp, format="PNG")
            logger.info(f"Region screenshot saved: {filepath}")
        
        return screenshot
    
    def capture_window(
        self,
        window_title: str,
        filename: Optional[str] = None,
        save: bool = True
    ) -> Optional[Image.Image]:
        """
        특정 윈도우 캡처
        
        Args:
            window_title: 윈도우 제목 (부분 일치)
            filename: 저장할 파일명
            save: 파일로 저장할지 여부
        
        Returns:
            PIL Image 객체 (윈도우를 찾지 못하면 None)
        """
        try:
            import pygetwindow as gw
        except ImportError:
            logger.error("pygetwindow not installed. Install with: pip install pygetwindow")
            return None
        
        logger.debug(f"Searching for window: {window_title}")
        
        # 윈도우 찾기
        windows = gw.getWindowsWithTitle(window_title)
        if not windows:
            logger.warning(f"Window not found: {window_title}")
            return None
        
        window = windows[0]
        logger.info(f"Found window: {window.title} at ({window.left}, {window.top})")
        
        # 윈도우 영역으로 캡처
        region = ScreenRegion(
            left=window.left,
            top=window.top,
            width=window.width,
            height=window.height
        )
        
        return self.capture_region(region, filename, save)
    
    def capture_sequence(
        self,
        count: int,
        interval: float = 1.0,
        prefix: str = "seq"
    ) -> list[Image.Image]:
        """
        연속 캡처 (타임랩스)
        
        Args:
            count: 캡처 횟수
            interval: 캡처 간격 (초)
            prefix: 파일명 접두사
        
        Returns:
            PIL Image 객체 리스트
        """
        logger.info(f"Starting sequence capture: {count} shots, {interval}s interval")
        
        screenshots = []
        for i in range(count):
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}_{i:03d}_{timestamp}.png"
            
            screenshot = self.capture_full_screen(filename=filename, save=True)
            screenshots.append(screenshot)
            
            if i < count - 1:  # 마지막이 아니면 대기
                time.sleep(interval)
        
        logger.info(f"Sequence capture complete: {count} screenshots")
        return screenshots
    
    @staticmethod
    def get_screen_size() -> Tuple[int, int]:
        """
        화면 크기 반환
        
        Returns:
            (width, height)
        """
        return pyautogui.size()
    
    @staticmethod
    def get_mouse_position() -> Tuple[int, int]:
        """
        현재 마우스 위치 반환
        
        Returns:
            (x, y)
        """
        return pyautogui.position()


# ============================================================================
# Convenience Functions
# ============================================================================

def capture_screen(output_path: Optional[Path] = None) -> Image.Image:
    """
    간편한 전체 화면 캡처
    
    Args:
        output_path: 저장 경로 (None이면 저장 안함)
    
    Returns:
        PIL Image 객체
    """
    if output_path:
        output_dir = output_path.parent
        filename = output_path.name
    else:
        output_dir = None
        filename = None
    
    capturer = ScreenshotCapture(output_dir=output_dir)
    return capturer.capture_full_screen(filename=filename, save=(output_path is not None))


def capture_region_coords(
    left: int,
    top: int,
    width: int,
    height: int,
    output_path: Optional[Path] = None
) -> Image.Image:
    """
    간편한 영역 캡처 (좌표 직접 지정)
    
    Args:
        left, top, width, height: 영역 좌표
        output_path: 저장 경로
    
    Returns:
        PIL Image 객체
    """
    region = ScreenRegion(left=left, top=top, width=width, height=height)
    
    if output_path:
        output_dir = output_path.parent
        filename = output_path.name
    else:
        output_dir = None
        filename = None
    
    capturer = ScreenshotCapture(output_dir=output_dir)
    return capturer.capture_region(region, filename=filename, save=(output_path is not None))


# ============================================================================
# CLI
# ============================================================================

if __name__ == '__main__':
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # 간단한 테스트
    output_dir = Path("outputs/screenshots")
    capturer = ScreenshotCapture(output_dir=output_dir)
    
    print("\n" + "="*60)
    print("  Screenshot Capture Utility Test")
    print("="*60)
    
    # 1. 전체 화면
    print("\n[Test 1] Full screen capture")
    img = capturer.capture_full_screen(filename="test_full.png")
    print(f"✅ Captured: {img.size}")
    
    # 2. 영역 캡처
    print("\n[Test 2] Region capture (100x100 at 0,0)")
    region = ScreenRegion(left=0, top=0, width=100, height=100)
    img = capturer.capture_region(region, filename="test_region.png")
    print(f"✅ Captured: {img.size}")
    
    # 3. 마우스 위치
    print("\n[Test 3] Mouse position")
    x, y = capturer.get_mouse_position()
    print(f"✅ Mouse at: ({x}, {y})")
    
    print("\n" + "="*60)
    print(f"  Screenshots saved to: {output_dir}")
    print("="*60 + "\n")
