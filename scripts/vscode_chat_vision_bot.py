#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VS Code Chat Vision Bot - 게임 봇처럼 화면을 "보면서" 동작하는 자동화 시스템

철학:
- 절대 좌표 없음 (창 크기/폰트 변경에 안전)
- 화면 인식 기반 (OCR + UI 요소 탐지)
- 상태 파악 후 동적 액션
- 실패 시 자동 복구
"""
import pyautogui
import pygetwindow as gw
import pytesseract
from PIL import Image, ImageGrab
import time
import logging
import json
import re
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
import argparse

# 설정
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('outputs/vscode_chat_vision_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class VSCodeWindow:
    """VS Code 창 정보"""
    title: str
    left: int
    top: int
    width: int
    height: int
    
    @property
    def center(self) -> Tuple[int, int]:
        return (self.left + self.width // 2, self.top + self.height // 2)
    
    @property
    def chat_panel_region(self) -> Tuple[int, int, int, int]:
        """오른쪽 하단 영역 (채팅 패널 예상 위치)"""
        # 오른쪽 30%, 하단 40%
        chat_left = self.left + int(self.width * 0.7)
        chat_top = self.top + int(self.height * 0.6)
        return (chat_left, chat_top, self.width - int(self.width * 0.7), int(self.height * 0.4))


class VSCodeVisionBot:
    """화면 인식 기반 VS Code 채팅 자동화 봇"""
    
    def __init__(self, workspace_dir: str = "C:\\workspace\\agi"):
        self.workspace_dir = Path(workspace_dir)
        self.state_file = self.workspace_dir / "outputs" / "chat_bot_state.json"
        self.screenshot_dir = self.workspace_dir / "outputs" / "screenshots"
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        # 상태 초기화
        self.current_state: Dict = {}
        self.vscode_window: Optional[VSCodeWindow] = None
        
        # OCR 설정 (Tesseract 경로 - 필요시 수정)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    def find_vscode_window(self) -> Optional[VSCodeWindow]:
        """VS Code 창 찾기 (제목 패턴 기반)"""
        logger.info("🔍 VS Code 창 검색 중...")
        
        try:
            all_windows = gw.getWindowsWithTitle('')
            vscode_windows = [
                w for w in all_windows 
                if 'Visual Studio Code' in w.title and w.visible
            ]
            
            if not vscode_windows:
                logger.warning("❌ VS Code 창을 찾을 수 없습니다")
                return None
            
            # 가장 큰 창 선택 (메인 창일 가능성 높음)
            main_window = max(vscode_windows, key=lambda w: w.width * w.height)
            
            self.vscode_window = VSCodeWindow(
                title=main_window.title,
                left=main_window.left,
                top=main_window.top,
                width=main_window.width,
                height=main_window.height
            )
            
            logger.info(f"✅ VS Code 창 발견: {main_window.title} ({main_window.width}x{main_window.height})")
            return self.vscode_window
            
        except Exception as e:
            logger.error(f"❌ 창 검색 실패: {e}")
            return None
    
    def capture_region(self, region: Tuple[int, int, int, int], name: str = "capture") -> Optional[Image.Image]:
        """화면 영역 캡처"""
        try:
            screenshot = ImageGrab.grab(bbox=region)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            screenshot.save(self.screenshot_dir / f"{name}_{timestamp}.png")
            return screenshot
        except Exception as e:
            logger.error(f"❌ 캡처 실패: {e}")
            return None
    
    def ocr_region(self, region: Tuple[int, int, int, int]) -> str:
        """영역에서 텍스트 추출 (OCR)"""
        try:
            screenshot = ImageGrab.grab(bbox=region)
            text = pytesseract.image_to_string(screenshot, lang='kor+eng')
            return text.strip()
        except Exception as e:
            logger.error(f"❌ OCR 실패: {e}")
            return ""
    
    def detect_chat_panel_state(self) -> Dict:
        """채팅 패널 상태 감지"""
        if not self.vscode_window:
            return {"visible": False, "has_text": False}
        
        region = self.vscode_window.chat_panel_region
        text = self.ocr_region(region)
        
        # 패턴 매칭으로 상태 파악
        state = {
            "visible": len(text) > 10,  # 텍스트가 있으면 패널 존재
            "has_copilot_text": "copilot" in text.lower() or "github" in text.lower(),
            "has_input_field": "ask" in text.lower() or "send" in text.lower(),
            "detected_text": text[:200]  # 처음 200자만 저장
        }
        
        logger.info(f"📊 채팅 패널 상태: {state['visible']} | Copilot: {state['has_copilot_text']}")
        return state
    
    def find_ui_element(self, image_template: str, region: Optional[Tuple] = None) -> Optional[Tuple[int, int]]:
        """UI 요소 찾기 (템플릿 매칭) - 미구현 (pillow 템플릿 매칭 필요)"""
        # TODO: opencv-python 사용 시 구현 가능
        logger.warning("⚠️  템플릿 매칭 미구현 (opencv 필요)")
        return None
    
    def click_relative(self, x_ratio: float, y_ratio: float, window: Optional[VSCodeWindow] = None) -> bool:
        """창 상대 좌표 클릭 (0.0~1.0 비율)"""
        if not window:
            window = self.vscode_window
        
        if not window:
            logger.error("❌ 창 정보 없음")
            return False
        
        target_x = window.left + int(window.width * x_ratio)
        target_y = window.top + int(window.height * y_ratio)
        
        logger.info(f"🖱️  클릭: ({x_ratio:.2%}, {y_ratio:.2%}) → ({target_x}, {target_y})")
        pyautogui.click(target_x, target_y)
        return True
    
    def open_new_chat(self, method: str = "keyboard") -> bool:
        """새 채팅 열기"""
        logger.info("📝 새 채팅 열기 시도...")
        
        if not self.vscode_window:
            if not self.find_vscode_window():
                return False
        
        # VS Code 창 활성화
        try:
            windows = gw.getWindowsWithTitle(self.vscode_window.title)
            if windows:
                windows[0].activate()
                time.sleep(0.5)
        except Exception as e:
            logger.warning(f"⚠️  창 활성화 실패: {e}")
        
        if method == "keyboard":
            # Ctrl+Shift+I (Copilot 채팅 단축키)
            logger.info("⌨️  Ctrl+Shift+I 전송")
            pyautogui.hotkey('ctrl', 'shift', 'i')
            time.sleep(1.0)
            
            # 상태 확인
            state = self.detect_chat_panel_state()
            return state.get("visible", False)
        
        elif method == "command_palette":
            # Ctrl+Shift+P → "Chat: Focus on Chat View" 검색
            logger.info("⌨️  명령 팔레트 사용")
            pyautogui.hotkey('ctrl', 'shift', 'p')
            time.sleep(0.5)
            pyautogui.write('chat new', interval=0.05)
            time.sleep(0.3)
            pyautogui.press('enter')
            time.sleep(1.0)
            return True
        
        return False
    
    def send_message(self, message: str, use_clipboard: bool = True) -> bool:
        """메시지 전송"""
        logger.info(f"💬 메시지 전송: {message[:50]}...")
        
        if use_clipboard:
            # 클립보드 사용 (한글 안전)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.press('delete')
            time.sleep(0.2)
            
            # 클립보드에 복사
            pyperclip.copy(message)
            time.sleep(0.1)
            
            # 붙여넣기
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.3)
            
            # 전송
            pyautogui.hotkey('ctrl', 'enter')
            logger.info("✅ 메시지 전송 완료")
            return True
        else:
            # 직접 타이핑 (영어만 권장)
            pyautogui.write(message, interval=0.05)
            pyautogui.hotkey('ctrl', 'enter')
            return True
    
    def wait_for_response(self, timeout: int = 30) -> bool:
        """응답 대기 (화면 변화 감지)"""
        logger.info(f"⏳ 응답 대기 중 (최대 {timeout}초)...")
        
        start_time = time.time()
        last_text = ""
        
        while time.time() - start_time < timeout:
            if not self.vscode_window:
                return False
            
            region = self.vscode_window.chat_panel_region
            current_text = self.ocr_region(region)
            
            # 텍스트 변화 감지
            if len(current_text) > len(last_text) + 50:  # 50자 이상 증가
                logger.info("✅ 응답 감지됨")
                return True
            
            last_text = current_text
            time.sleep(1.0)
        
        logger.warning("⏱️  응답 대기 시간 초과")
        return False
    
    def auto_chat_session(self, message: str) -> bool:
        """자동 채팅 세션 (전체 플로우)"""
        logger.info("🚀 자동 채팅 세션 시작")
        
        # 1. VS Code 창 찾기
        if not self.find_vscode_window():
            logger.error("❌ VS Code 창을 찾을 수 없습니다")
            return False
        
        # 2. 현재 상태 캡처
        state = self.detect_chat_panel_state()
        
        # 3. 새 채팅 열기 (필요시)
        if not state.get("visible"):
            if not self.open_new_chat():
                logger.error("❌ 채팅 패널 열기 실패")
                return False
        
        # 4. 입력 영역 클릭 (오른쪽 하단 80%, 90% 위치 추정)
        self.click_relative(0.85, 0.90)
        time.sleep(0.5)
        
        # 5. 메시지 전송
        if not self.send_message(message):
            return False
        
        # 6. 응답 대기
        if not self.wait_for_response():
            logger.warning("⚠️  응답 확인 실패 (하지만 전송은 성공)")
        
        logger.info("✅ 자동 채팅 세션 완료")
        return True


# pyperclip import 추가
try:
    import pyperclip
except ImportError:
    logger.warning("⚠️  pyperclip 미설치 - 한글 입력 제한될 수 있음")
    pyperclip = None


def main():
    parser = argparse.ArgumentParser(description="VS Code Chat Vision Bot")
    parser.add_argument('--message', '-m', help="전송할 메시지")
    parser.add_argument('--test-vision', action='store_true', help="화면 인식 테스트")
    parser.add_argument('--debug', action='store_true', help="디버그 모드")
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    bot = VSCodeVisionBot()
    
    if args.test_vision:
        logger.info("🧪 화면 인식 테스트 모드")
        bot.find_vscode_window()
        state = bot.detect_chat_panel_state()
        logger.info(f"상태: {json.dumps(state, ensure_ascii=False, indent=2)}")
        return
    
    if args.message:
        success = bot.auto_chat_session(args.message)
        exit(0 if success else 1)
    else:
        # 기본 테스트
        logger.info("📝 기본 메시지로 테스트")
        bot.auto_chat_session("테스트 메시지입니다")


if __name__ == "__main__":
    main()
