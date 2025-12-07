"""
External AI Bridge - 범용 외부 AI 통신 모듈
Trinity가 다양한 외부 AI (ChatGPT, Claude, Comet, Browser)와 대화합니다.
"""
import asyncio
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime

import pyautogui
import pyperclip
import pygetwindow as gw
import numpy as np
from PIL import Image
from services.model_selector import ModelSelector

logger = logging.getLogger("ExternalAIBridge")

# Aura 색상
AURA_COLOR_ACTIVE = "#FF00FF"  # 마젠타 (대화 중)
AURA_COLOR_WAITING = "#00FFFF"  # 시안 (대기 중)


class AITarget(Enum):
    """지원되는 AI 대상"""
    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    COMET = "comet"
    PERPLEXITY = "perplexity"
    BROWSER = "browser"


# 대상별 설정
TARGET_CONFIGS = {
    AITarget.CHATGPT: {
        "window_title": "ChatGPT",
        "app_name": "ChatGPT",
        "is_browser": False,
    },
    AITarget.CLAUDE: {
        "window_title": "Claude",
        "app_name": "Claude",
        "is_browser": False,
    },
    AITarget.COMET: {
        "window_title": "Comet",
        "browser_name": "Comet",
        "is_browser": True,
    },
    AITarget.PERPLEXITY: {
        "window_title": "Perplexity",
        "url": "https://www.perplexity.ai",
        "is_browser": True,
    },
}


class ExternalAIBridge:
    """
    범용 외부 AI 통신 브리지
    여러 AI 대상을 통합된 인터페이스로 관리합니다.
    """
    
    def __init__(self):
        self.screenshot_dir = Path("outputs/external_ai_screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.3
        self.model_selector = ModelSelector(logger=logger)
        
        # 세션 추적
        self.active_sessions: Dict[AITarget, Any] = {}  # 열린 창들
        self.last_used_target: Optional[AITarget] = None
        

        # Aura 프로세스
        self.aura_process = None
        
        # Resonance Ledger
        self.resonance_ledger_path = Path("C:/workspace/agi/memory/resonance_ledger.jsonl")
        
    def _log_resonance(self, event_type: str, content: str, target: AITarget):
        """공명 장부에 이벤트 기록"""
        try:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "type": "dialogue_event",
                "layer": "external_bridge",
                "event": event_type,
                "target": target.value,
                "content_summary": content[:100] + "..." if len(content) > 100 else content,
                "length": len(content)
            }
            
            self.resonance_ledger_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.resonance_ledger_path, 'a', encoding='utf-8') as f:
                import json
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                
        except Exception as e:
            logger.warning(f"Failed to log resonance: {e}")

    def _find_window(self, target: AITarget) -> Optional[Any]:
        """대상 AI의 창 찾기"""
        config = TARGET_CONFIGS.get(target)
        if not config:
            return None
            
        try:
            title = config.get("window_title", "")
            windows = gw.getWindowsWithTitle(title)
            
            for win in windows:
                if title.lower() in win.title.lower():
                    logger.info(f"Found existing window: {win.title}")
                    return win
            return None
        except Exception as e:
            logger.warning(f"Window detection failed for {target}: {e}")
            return None
    
    def _activate_window(self, window) -> bool:
        """창 활성화"""
        try:
            if window.isMinimized:
                window.restore()
            window.activate()
            logger.info(f"Activated: {window.title}")
            return True
        except Exception as e:
            logger.warning(f"Activation failed: {e}")
            return False
    
    async def _open_app(self, target: AITarget) -> bool:
        """앱 실행 (Win+S 검색)"""
        config = TARGET_CONFIGS.get(target)
        if not config:
            return False
        
        app_name = config.get("app_name", config.get("window_title", ""))
        
        # Win+S → 검색
        pyautogui.hotkey('win', 's')
        await asyncio.sleep(0.5)
        
        # 앱 이름 입력
        pyperclip.copy(app_name)
        pyautogui.hotkey('ctrl', 'v')
        await asyncio.sleep(1)
        
        # Enter → 실행
        pyautogui.press('enter')
        logger.info(f"Launched app: {app_name}")
        await asyncio.sleep(2)
        
        return True
    
    async def _open_browser_url(self, target: AITarget) -> bool:
        """브라우저에서 URL 열기"""
        config = TARGET_CONFIGS.get(target)
        if not config:
            return False
            
        # Comet 브라우저의 경우
        if target == AITarget.COMET:
            browser_name = config.get("browser_name", "Comet")
            return await self._open_app(target)
        
        # URL이 있는 경우 기본 브라우저로 열기
        url = config.get("url")
        if url:
            import webbrowser
            webbrowser.open(url)
            logger.info(f"Opened URL: {url}")
            await asyncio.sleep(3)
            return True
            
        return False
    
    async def find_or_open(self, target: AITarget) -> bool:
        """
        대상 AI 창을 찾거나 열기
        맥락 인식: 이미 열려있으면 활성화, 아니면 새로 열기
        """
        # 1. 이미 열린 창 찾기
        window = self._find_window(target)
        
        if window:
            # 창이 있으면 활성화
            logger.info(f"Reusing existing {target.value} window")
            self.active_sessions[target] = window
            return self._activate_window(window)
        
        # 2. 창이 없으면 새로 열기
        logger.info(f"Opening new {target.value}...")
        config = TARGET_CONFIGS.get(target)
        
        if config.get("is_browser"):
            success = await self._open_browser_url(target)
        else:
            success = await self._open_app(target)
        
        if success:
            # 열린 후 창 다시 찾기
            await asyncio.sleep(2)
            window = self._find_window(target)
            if window:
                self.active_sessions[target] = window
                
        return success
    
    async def _type_message(self, message: str):
        """메시지 입력 (클립보드 사용)"""
        await asyncio.sleep(0.5)
        pyperclip.copy(message)
        pyautogui.hotkey('ctrl', 'v')
        logger.info(f"Typed message ({len(message)} chars)")
    
    def _compare_screenshots(self, img1: Image.Image, img2: Image.Image, threshold: float = 0.98) -> bool:
        """스크린샷 비교 (응답 완료 감지용)"""
        try:
            arr1 = np.array(img1.convert('L'))
            arr2 = np.array(img2.convert('L'))
            
            if arr1.shape != arr2.shape:
                return False
            
            diff = np.abs(arr1.astype(float) - arr2.astype(float))
            similarity = 1 - (np.sum(diff) / (arr1.size * 255))
            
            return similarity >= threshold
        except:
            return False
    
    async def _wait_for_response(self, timeout_sec: int = 60) -> None:
        """응답 완료 대기 (스크린샷 비교)"""
        logger.info("Waiting for response...")
        await asyncio.sleep(5)  # 초기 대기
        
        start_time = time.time()
        prev_screenshot = pyautogui.screenshot()
        stable_count = 0
        
        while time.time() - start_time < timeout_sec:
            await asyncio.sleep(2.5)
            curr_screenshot = pyautogui.screenshot()
            
            if self._compare_screenshots(prev_screenshot, curr_screenshot):
                stable_count += 1
                if stable_count >= 2:
                    logger.info("Response complete")
                    return
            else:
                stable_count = 0
            
            prev_screenshot = curr_screenshot
        
        logger.warning(f"Timeout after {timeout_sec}s")
    
    async def _capture_and_extract_response(self) -> Optional[str]:
        """화면 캡처 후 Vision으로 응답 추출"""
        selector = getattr(self, "model_selector", None)
        if not selector or not selector.available:
            logger.warning("Vision model not available")
            return None
        
        screenshot = pyautogui.screenshot()
        timestamp = int(time.time())
        path = self.screenshot_dir / f"response_{timestamp}.png"
        screenshot.save(str(path))
        logger.info(f"Screenshot saved: {path}")
        
        try:
            img = Image.open(path)
            prompt = """이 화면에서 AI의 응답을 추출해줘. 
            가장 최근 응답 내용만 텍스트로 반환해줘."""
            
            response, model_used = selector.try_generate_content(
                [prompt, img],
                vision=True,
                generation_config={"temperature": 0.1},
            )
            if not response:
                return None
            extracted = response.text.strip()
            logger.info(f"Extracted response via {model_used or 'unknown'}: {extracted[:100]}...")
            return extracted
        except Exception as e:
            logger.error(f"Response extraction failed: {e}")
            return None
    
    def _start_aura(self, color: str = AURA_COLOR_ACTIVE):
        """오라 효과 시작"""
        try:
            self._stop_aura()
            script_path = Path(__file__).parent / "agi_aura.py"
            if script_path.exists():
                self.aura_process = subprocess.Popen(
                    [sys.executable, str(script_path), "--color", color],
                    stdout=subprocess.DEVNULL
                )
                logger.info(f"Aura started: {color}")
        except Exception as e:
            logger.warning(f"Aura start failed: {e}")
    
    def _stop_aura(self):
        """오라 효과 중지"""
        if self.aura_process:
            try:
                self.aura_process.terminate()
                self.aura_process = None
                logger.info("Aura stopped")
            except:
                pass
    
    async def send_message(
        self,
        target: AITarget,
        message: str,
        context: Optional[str] = None,
        identity: Optional[str] = None,
        timeout_sec: int = 60
    ) -> Optional[str]:
        """
        외부 AI에게 메시지 보내고 응답 받기
        
        Args:
            target: AI 대상 (ChatGPT, Claude, etc.)
            message: 보낼 메시지
            context: 추가 컨텍스트
            identity: 신분 소개 (선택)
            timeout_sec: 응답 대기 시간
        """
        logger.info(f"Sending message to {target.value}...")
        self._start_aura(AURA_COLOR_ACTIVE)
        
        try:
            # 1. 창 찾거나 열기
            if not await self.find_or_open(target):
                logger.error(f"Failed to open {target.value}")
                return None
            
            await asyncio.sleep(1)
            
            # 2. 메시지 구성
            full_message = ""
            if identity:
                full_message += identity + "\n\n"
            full_message += message
            if context:
                full_message += f"\n\n[Context]\n{context}"
            
            # 3. 메시지 입력
            await self._type_message(full_message)
            
            # 4. Enter 전송
            pyautogui.press('enter')
            logger.info("Message sent")
            
            self._log_resonance("message_sent", message, target)
            
            # 5. 응답 대기
            await self._wait_for_response(timeout_sec)
            
            # 6. 응답 추출
            response = await self._capture_and_extract_response()
            
            if response:
                self._log_resonance("response_received", response, target)
            
            self.last_used_target = target
            return response
            
        finally:
            self._stop_aura()
    
    def get_active_sessions(self) -> List[AITarget]:
        """현재 열린 AI 세션 목록"""
        active = []
        for target in AITarget:
            if self._find_window(target):
                active.append(target)
        return active


# 편의 함수
async def ask_external_ai(
    target: str,
    message: str,
    **kwargs
) -> Optional[str]:
    """외부 AI에게 질문하는 편의 함수"""
    bridge = ExternalAIBridge()
    
    # 문자열 → Enum 변환
    target_enum = AITarget(target.lower())
    
    return await bridge.send_message(target_enum, message, **kwargs)
