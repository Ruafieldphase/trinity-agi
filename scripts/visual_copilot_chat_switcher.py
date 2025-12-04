"""
Visual Copilot Chat Switcher - 화면 인식 기반 새 채팅 전환
게임 봇처럼 화면 상태를 파악하고 요소를 찾아서 클릭
"""
import pyautogui
import time
import sys
from pathlib import Path
import logging
import argparse

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VisualChatSwitcher:
    """화면 인식 기반 채팅 전환기"""
    
    def __init__(self, debug=False):
        self.debug = debug
        # 안전을 위한 failsafe (마우스를 화면 모서리로 이동하면 중단)
        pyautogui.FAILSAFE = True
        # 동작 사이 기본 딜레이
        pyautogui.PAUSE = 0.5
        
        # 이미지 리소스 경로
        self.resources_dir = Path(__file__).parent / "resources" / "copilot_icons"
        self.resources_dir.mkdir(parents=True, exist_ok=True)
        
    def find_element_by_image(self, image_name, confidence=0.8, region=None):
        """
        이미지로 화면 요소 찾기 (게임 봇 방식)
        
        Args:
            image_name: 찾을 이미지 파일명
            confidence: 매칭 신뢰도 (0~1)
            region: 검색 영역 (x, y, width, height) 또는 None (전체 화면)
        
        Returns:
            (x, y) 좌표 또는 None
        """
        image_path = self.resources_dir / image_name
        
        if not image_path.exists():
            logger.warning(f"이미지 파일 없음: {image_path}")
            return None
        
        try:
            location = pyautogui.locateOnScreen(
                str(image_path),
                confidence=confidence,
                region=region
            )
            
            if location:
                # 중심점 반환
                center = pyautogui.center(location)
                logger.info(f"✓ '{image_name}' 발견: {center}")
                return center
            else:
                logger.debug(f"'{image_name}' 찾을 수 없음")
                return None
                
        except Exception as e:
            logger.error(f"이미지 검색 오류: {e}")
            return None
    
    def find_copilot_chat_icon(self):
        """Copilot 채팅 아이콘 찾기"""
        # 여러 변형 시도
        icon_variants = [
            "copilot_chat_icon.png",
            "copilot_sidebar_icon.png",
            "github_copilot_icon.png"
        ]
        
        for icon in icon_variants:
            pos = self.find_element_by_image(icon)
            if pos:
                return pos
        
        logger.warning("Copilot 아이콘을 찾을 수 없습니다")
        return None
    
    def find_new_chat_button(self):
        """새 채팅 버튼 찾기"""
        button_variants = [
            "new_chat_button.png",
            "new_chat_plus_icon.png",
            "chat_new_icon.png"
        ]
        
        for btn in button_variants:
            pos = self.find_element_by_image(btn, confidence=0.75)
            if pos:
                return pos
        
        logger.warning("새 채팅 버튼을 찾을 수 없습니다")
        return None
    
    def find_chat_input_field(self):
        """채팅 입력창 찾기"""
        # 텍스트 필드는 이미지 매칭이 어려우므로 상대 위치 사용
        # 또는 "Ask Copilot" 플레이스홀더 이미지 매칭
        input_variants = [
            "chat_input_placeholder.png",
            "ask_copilot_text.png"
        ]
        
        for img in input_variants:
            pos = self.find_element_by_image(img, confidence=0.7)
            if pos:
                return pos
        
        return None
    
    def wait_for_element(self, image_name, timeout=5, confidence=0.8):
        """요소가 나타날 때까지 대기"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            pos = self.find_element_by_image(image_name, confidence)
            if pos:
                return pos
            time.sleep(0.5)
        
        return None
    
    def safe_click(self, position, clicks=1, interval=0.1):
        """안전한 클릭 (화면 경계 체크)"""
        if not position:
            logger.error("클릭 위치가 None입니다")
            return False
        
        x, y = position
        screen_width, screen_height = pyautogui.size()
        
        # 화면 경계 체크
        if not (0 <= x < screen_width and 0 <= y < screen_height):
            logger.error(f"클릭 위치가 화면 밖: ({x}, {y})")
            return False
        
        try:
            pyautogui.click(x, y, clicks=clicks, interval=interval)
            logger.info(f"✓ 클릭: ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"클릭 실패: {e}")
            return False
    
    def type_text(self, text, interval=0.05):
        """텍스트 입력"""
        try:
            pyautogui.write(text, interval=interval)
            logger.info(f"✓ 텍스트 입력: {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"텍스트 입력 실패: {e}")
            return False
    
    def switch_to_new_chat(self, context_text=None):
        """
        새 채팅으로 전환 (전체 플로우)
        
        Args:
            context_text: 자동으로 입력할 컨텍스트 (선택)
        
        Returns:
            성공 여부
        """
        logger.info("🔄 새 채팅으로 전환 시작...")
        
        # 1단계: Copilot 사이드바 열기
        logger.info("1️⃣ Copilot 사이드바 찾는 중...")
        chat_icon = self.find_copilot_chat_icon()
        
        if not chat_icon:
            # 단축키로 시도
            logger.info("아이콘을 못 찾아서 단축키 사용: Ctrl+Shift+I")
            pyautogui.hotkey('ctrl', 'shift', 'i')
            time.sleep(1)
        else:
            self.safe_click(chat_icon)
            time.sleep(0.5)
        
        # 2단계: 새 채팅 버튼 찾기
        logger.info("2️⃣ 새 채팅 버튼 찾는 중...")
        new_chat_btn = self.wait_for_element("new_chat_button.png", timeout=3)
        
        if not new_chat_btn:
            # 플러스 아이콘이나 다른 변형 시도
            new_chat_btn = self.find_element_by_image("new_chat_plus_icon.png", confidence=0.7)
        
        if not new_chat_btn:
            logger.warning("새 채팅 버튼을 찾을 수 없어서 단축키 사용")
            # Copilot 패널에서 새 채팅 단축키 (일반적으로 Ctrl+L 또는 Ctrl+Shift+L)
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.5)
        else:
            self.safe_click(new_chat_btn)
            time.sleep(0.5)
        
        # 3단계: 입력창 확인 및 컨텍스트 입력
        if context_text:
            logger.info("3️⃣ 컨텍스트 입력 중...")
            
            # 입력창 찾기
            input_field = self.find_chat_input_field()
            if input_field:
                self.safe_click(input_field)
                time.sleep(0.2)
            
            # 클립보드에서 붙여넣기 (더 안정적)
            import pyperclip
            try:
                pyperclip.copy(context_text)
                pyautogui.hotkey('ctrl', 'v')
                logger.info("✓ 컨텍스트 붙여넣기 완료")
            except:
                # pyperclip 없으면 직접 타이핑
                self.type_text(context_text)
        
        logger.info("✅ 새 채팅 전환 완료!")
        return True
    
    def capture_screenshot_for_training(self, element_name):
        """
        화면 요소 캡처 (학습용 이미지 생성)
        
        사용법:
            switcher.capture_screenshot_for_training("new_chat_button")
            → 마우스로 영역을 지정하고 캡처
        """
        logger.info(f"📸 '{element_name}' 캡처 모드")
        logger.info("마우스로 캡처할 영역의 좌상단을 클릭하세요...")
        
        input("준비되면 Enter를 누르고, 캡처할 영역을 클릭하세요 >>> ")
        
        x1, y1 = pyautogui.position()
        logger.info(f"시작점: ({x1}, {y1})")
        
        input("이제 영역의 우하단을 클릭하세요 >>> ")
        x2, y2 = pyautogui.position()
        logger.info(f"끝점: ({x2}, {y2})")
        
        # 영역 캡처
        region = (min(x1, x2), min(y1, y2), abs(x2-x1), abs(y2-y1))
        screenshot = pyautogui.screenshot(region=region)
        
        # 저장
        save_path = self.resources_dir / f"{element_name}.png"
        screenshot.save(save_path)
        logger.info(f"✅ 저장됨: {save_path}")
        
        return save_path


def main():
    parser = argparse.ArgumentParser(description="화면 인식 기반 Copilot 채팅 전환")
    parser.add_argument("--context", type=str, help="자동 입력할 컨텍스트")
    parser.add_argument("--train", type=str, help="학습용 이미지 캡처 모드 (요소 이름)")
    parser.add_argument("--debug", action="store_true", help="디버그 모드")
    
    args = parser.parse_args()
    
    switcher = VisualChatSwitcher(debug=args.debug)
    
    if args.train:
        # 학습 모드: 화면 요소 캡처
        switcher.capture_screenshot_for_training(args.train)
    else:
        # 실행 모드: 새 채팅 전환
        context = args.context
        
        # 컨텍스트가 파일 경로면 읽기
        if context and Path(context).exists():
            context = Path(context).read_text(encoding='utf-8')
        
        switcher.switch_to_new_chat(context)


if __name__ == "__main__":
    main()
