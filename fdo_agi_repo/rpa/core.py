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
<<<<<<< HEAD
import json
=======
>>>>>>> origin/main
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import mss
import numpy as np
import pyautogui
from fdo_agi_repo.orchestrator.pipeline_binoche_adapter import enhanced_binoche_decision


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

<<<<<<< HEAD
    # ========================================================================
    # Semantic Actions (Vision-based)
    # ========================================================================
    
    async def click_by_description(self, description: str, timeout: Optional[float] = None) -> bool:
        """비전 분석 결과를 검색하여 설명에 맞는 요소를 클릭"""
        timeout = timeout or self.config.default_timeout
        start_time = time.time()
        
        vision_log_path = Path(__file__).parent.parent.parent / "agi_core" / "memory" / "vision_events.jsonl"
        # 위 경로가 맞는지 확인 (LiveFrameAnalyzer 기준)
        if not vision_log_path.exists():
            # 대안 경로 (상위 디렉토리 구조 차이 대비)
            vision_log_path = Path("agi_core/memory/vision_events.jsonl")
            if not vision_log_path.exists():
                vision_log_path = Path("memory/vision_events.jsonl")

        self.logger.info(f"Searching for UI element by description: '{description}'")
        
        while time.time() - start_time < timeout:
            if not vision_log_path.exists():
                await asyncio.sleep(2.0)
                continue
            
            # 최신 비전 이벤트 읽기 (JSONL + 복구 모드)
            events = self._load_recent_vision_events(vision_log_path, max_events=5)
            if not events:
                await asyncio.sleep(2.0)
                continue

            for data in reversed(events):
                ui_elements = data.get("ui_elements", [])

                if not isinstance(ui_elements, list):
                    continue

                for element in ui_elements:
                    # 이름 또는 설명에 포함되어 있는지 확인
                    name = str(element.get("name", "")).lower()
                    desc = str(element.get("description", "")).lower()
                    match_text = f"{name} {desc}".lower()

                    if description.lower() in match_text:
                        rect = element.get("rect_normalized")
                        if rect and len(rect) == 4:
                            # [ymin, xmin, ymax, xmax]
                            ymin, xmin, ymax, xmax = rect

                            # 화면 크기 가져오기
                            screen_w, screen_h = pyautogui.size()

                            # 중심 좌표 계산
                            target_x = int(((xmin + xmax) / 2) * screen_w)
                            target_y = int(((ymin + ymax) / 2) * screen_h)

                            self.logger.info(f"Target found: '{name}' at ({target_x}, {target_y})")
                            await self.click(target_x, target_y)
                            return True
            
            await asyncio.sleep(2.0)
            
        self.logger.warning(f"Failed to find element by description: '{description}'")
        return False

    async def type_in_element_by_description(
        self,
        description: str,
        text: str,
        timeout: Optional[float] = None
    ) -> bool:
        """설명으로 요소를 찾아 클릭 후 텍스트 입력"""
        success = await self.click_by_description(description, timeout)
        if success:
            await self.type_text(text)
            return True
        return False

    def _load_vision_events_linewise(self, text: str, max_events: int) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                events.append(obj)
        return events[-max_events:]

    def _load_recent_vision_events(self, vision_log_path: Path, max_events: int = 5) -> List[Dict[str, Any]]:
        try:
            text = vision_log_path.read_text(encoding="utf-8", errors="ignore").strip()
            if not text:
                return []
            try:
                data = json.loads(text)
                if isinstance(data, list):
                    return [d for d in data if isinstance(d, dict)][-max_events:]
                if isinstance(data, dict):
                    return [data]
            except Exception:
                pass

            decoder = json.JSONDecoder()
            idx = 0
            length = len(text)
            events: List[Dict[str, Any]] = []
            while idx < length:
                while idx < length and text[idx].isspace():
                    idx += 1
                if idx >= length:
                    break
                try:
                    obj, end = decoder.raw_decode(text, idx)
                except Exception:
                    return self._load_vision_events_linewise(text, max_events)
                if isinstance(obj, dict):
                    events.append(obj)
                idx = end
            if not events:
                return self._load_vision_events_linewise(text, max_events)
            return events[-max_events:]
        except Exception as e:
            self.logger.error(f"Error reading vision log: {e}")
            return []
=======
>>>>>>> origin/main
    async def evaluate_and_decide(
        self,
        task_goal: str,
        rpa_result: Dict[str, Any],
        bqi_coord: Dict[str, Any]
    ) -> Dict[str, Any]:
        """RPA 작업 결과를 평가하고 Binoche 의사결정을 받습니다."""
        self.logger.info("Evaluating RPA task result with Binoche...")

        # 1. 간단한 품질 점수 계산
        quality = 0.85 if rpa_result.get("success") else 0.3
        eval_report = {"quality": quality, "evidence_ok": rpa_result.get("success", False)}

        # 2. Binoche 의사결정 호출
        decision = enhanced_binoche_decision(
            task_goal=task_goal,
            eval_report=eval_report,
            bqi_coord=bqi_coord
        )

        self.logger.info(f"Binoche decision: {decision['action']} (Confidence: {decision['confidence']:.2f})")
        self.logger.info(f"  Reason: {decision['reason']}")

        return decision


# ============================================================================
# CLI Interface
# ============================================================================

async def main():
    """CLI 테스트 및 Binoche 통합 데모"""
    logging.basicConfig(level=logging.INFO)
    
    rpa = RPACore()
    
    print("\n✅ RPA Core initialized for Binoche Integration Demo")
    
    # 1. 테스트 작업 정의
    task_goal = "Take a screenshot and confirm it was saved"
    bqi_coord = {"priority": 1, "emotion": "neutral", "rhythm": "execution"}
    
    print(f"\n🎯 Task: {task_goal}")
    
    # 2. RPA 작업 실행 (시뮬레이션)
    try:
        screenshot_path = await rpa.save_screenshot("test_integration_screenshot.png")
        rpa_result = {"success": True, "output_path": str(screenshot_path)}
        print(f"   RPA task succeeded. Output: {screenshot_path}")
    except Exception as e:
        rpa_result = {"success": False, "error": str(e)}
        print(f"   RPA task failed: {e}")

    # 3. Binoche로 평가 및 의사결정
    if rpa_result["success"]:
        decision = await rpa.evaluate_and_decide(task_goal, rpa_result, bqi_coord)
        print("\n[BQI Phase 6 Integration Complete]")
        print(f"  Action: {decision.get('action')}")
        print(f"  Confidence: {decision.get('confidence')}")
        print(f"  Reason: {decision.get('reason')}")
    else:
        print("\nSkipping Binoche evaluation due to RPA failure.")


if __name__ == "__main__":
    asyncio.run(main())
