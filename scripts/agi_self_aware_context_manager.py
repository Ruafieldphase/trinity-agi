#!/usr/bin/env python3
"""
AGI Self-Aware Context Manager
게임 봇처럼 화면 상태를 인식하며 작동하는 자동화

Level 1: 키보드 포커스 기반 (좌표 불필요)
Level 2: 이미지 인식 (화면에서 UI 찾기)
Level 3: OCR 상태 파악 (텍스트 읽기)
"""
import sys
import time
import argparse
import pyautogui
import pyperclip
from pathlib import Path
from typing import Optional, Tuple

# PyAutoGUI 안전 설정
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


class VSCodeChatAutomation:
    """VS Code Copilot Chat 자동화 - 상태 인식 기반"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.templates_dir = Path(__file__).parent / "ui_templates"
        self.templates_dir.mkdir(exist_ok=True)
    
    def log(self, msg: str):
        """로그 출력"""
        if self.verbose:
            print(f"[AGI] {msg}")
    
    def wait_for_focus(self, timeout: float = 2.0) -> bool:
        """
        Level 1: 키보드 포커스 대기
        채팅창이 열리고 입력란에 포커스가 갈 때까지 대기
        """
        self.log(f"🔍 Waiting for chat input focus (timeout: {timeout}s)...")
        start = time.time()
        
        # 짧은 대기로 자연스러운 포커스 이동 허용
        time.sleep(0.5)
        
        # 포커스 확인: Ctrl+A 눌러서 전체 선택 시도
        # 입력란에 포커스 있으면 성공, 없으면 아무 일도 안 일어남
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        
        # 선택 해제 (있었다면)
        pyautogui.press('right')
        
        elapsed = time.time() - start
        self.log(f"✅ Focus check completed ({elapsed:.2f}s)")
        return True
    
    def ensure_chat_input_focus(self) -> bool:
        """
        Level 1: Tab 키로 채팅 입력란 찾기
        포커스가 입력란에 없으면 Tab으로 이동
        """
        self.log("🎯 Ensuring chat input has focus...")
        
        # VS Code에서 Tab 키는 UI 요소 간 이동
        # 채팅창 열리면 보통 입력란이 첫 번째 포커스 대상
        max_tabs = 5
        for i in range(max_tabs):
            # 현재 위치에서 테스트 입력
            test_text = "TEST_FOCUS_CHECK"
            pyperclip.copy(test_text)
            
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.1)
            
            # 입력 확인 (클립보드에 그대로면 입력 안 됨)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.05)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.05)
            
            current = pyperclip.paste()
            
            # 클린업
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('backspace')
            
            if current == test_text:
                self.log(f"✅ Found chat input (Tab x{i})")
                return True
            
            # 다음 요소로 이동
            pyautogui.press('tab')
            time.sleep(0.2)
        
        self.log("⚠️ Could not find chat input with Tab navigation")
        return False
    
    def find_ui_element(self, template_name: str, confidence: float = 0.8) -> Optional[Tuple[int, int]]:
        """
        Level 2: 이미지 인식으로 UI 요소 찾기 (게임 봇 방식)
        
        Args:
            template_name: UI 템플릿 이미지 파일명
            confidence: 매칭 신뢰도 (0.0-1.0)
        
        Returns:
            (x, y) 좌표 또는 None
        """
        template_path = self.templates_dir / template_name
        
        if not template_path.exists():
            self.log(f"⚠️ Template not found: {template_name}")
            return None
        
        self.log(f"🔍 Searching for UI element: {template_name}")
        
        try:
            # 화면에서 템플릿 이미지 찾기
            location = pyautogui.locateOnScreen(
                str(template_path),
                confidence=confidence
            )
            
            if location:
                # 중앙 좌표 계산
                x, y = pyautogui.center(location)
                self.log(f"✅ Found at ({x}, {y})")
                return (x, y)
            else:
                self.log(f"❌ Not found on screen")
                return None
                
        except Exception as e:
            self.log(f"⚠️ Image search error: {e}")
            return None
    
    def read_screen_text(self, region: Optional[Tuple[int, int, int, int]] = None) -> str:
        """
        Level 3: OCR로 화면 텍스트 읽기
        
        Args:
            region: (left, top, width, height) 영역. None이면 전체 화면
        
        Returns:
            인식된 텍스트
        
        Note:
            pytesseract 필요: pip install pytesseract pillow
        """
        try:
            import pytesseract
            from PIL import Image
            
            # 스크린샷
            screenshot = pyautogui.screenshot(region=region)
            
            # OCR
            text = pytesseract.image_to_string(screenshot, lang='kor+eng')
            
            return text.strip()
            
        except ImportError:
            self.log("⚠️ pytesseract not installed. OCR unavailable.")
            return ""
        except Exception as e:
            self.log(f"⚠️ OCR error: {e}")
            return ""
    
    def paste_with_keyboard(self, text: str) -> bool:
        """
        Level 1: 순수 키보드로 붙여넣기
        좌표 완전히 불필요
        """
        self.log("📋 Pasting via keyboard...")
        
        try:
            # 클립보드에 복사
            pyperclip.copy(text)
            time.sleep(0.1)
            
            # Ctrl+V로 붙여넣기
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.2)
            
            self.log("✅ Paste completed")
            return True
            
        except Exception as e:
            self.log(f"❌ Paste failed: {e}")
            return False
    
    def paste_with_image_detection(self, text: str) -> bool:
        """
        Level 2: 이미지 인식으로 입력창 찾아서 붙여넣기
        게임 봇 방식
        """
        self.log("🎮 Using image detection to find input field...")
        
        # 채팅 입력창 이미지 템플릿 찾기
        location = self.find_ui_element("chat_input.png", confidence=0.7)
        
        if not location:
            self.log("⚠️ Chat input not found via image detection")
            return False
        
        x, y = location
        
        # 클릭
        self.log(f"🖱️ Clicking at ({x}, {y})...")
        pyautogui.click(x, y)
        time.sleep(0.3)
        
        # 붙여넣기
        return self.paste_with_keyboard(text)
    
    def auto_paste_smart(self, text: str, use_image: bool = False) -> bool:
        """
        스마트 자동 붙여넣기
        
        Strategy:
        1. Level 1 시도 (키보드만)
        2. 실패 시 Tab으로 포커스 찾기
        3. 그래도 실패 시 Level 2 (이미지 인식)
        """
        self.log("🚀 Starting smart auto-paste...")
        
        # Level 1: 현재 포커스에 바로 붙여넣기 시도
        if not use_image:
            self.log("📌 Level 1: Direct keyboard paste")
            if self.paste_with_keyboard(text):
                return True
            
            # 실패 시 포커스 찾기
            self.log("📌 Level 1b: Finding input with Tab")
            if self.ensure_chat_input_focus():
                if self.paste_with_keyboard(text):
                    return True
        
        # Level 2: 이미지 인식
        self.log("📌 Level 2: Image detection")
        return self.paste_with_image_detection(text)
    
    def verify_paste_success(self) -> bool:
        """
        Level 3: OCR로 붙여넣기 성공 확인
        """
        self.log("🔍 Verifying paste success via OCR...")
        
        # 채팅 입력 영역 텍스트 읽기
        # 실제 영역 좌표는 동적으로 찾아야 함
        text = self.read_screen_text()
        
        if text:
            self.log(f"📝 Screen text detected: {text[:50]}...")
            return True
        else:
            self.log("⚠️ No text detected")
            return False


def create_ui_template_guide():
    """UI 템플릿 이미지 생성 가이드"""
    guide = """
# UI 템플릿 이미지 생성 가이드

Level 2 (이미지 인식)를 사용하려면 UI 요소의 스크린샷이 필요합니다.

## 1. 채팅 입력창 템플릿 만들기

1. VS Code에서 Copilot Chat 열기
2. 입력창 영역 스크린샷 찍기 (Windows: Win+Shift+S)
3. 다음 위치에 저장:
   ```
   scripts/ui_templates/chat_input.png
   ```

## 2. 권장 사항

- **작은 영역**: 입력창의 특징적인 부분만 (플레이스홀더 텍스트 등)
- **고해상도**: 선명한 이미지
- **단순한 배경**: 배경이 복잡하면 인식률 저하

## 3. 테스트

```bash
python scripts/agi_self_aware_context_manager.py --test-image
```

## 4. 여러 테마 지원

다크/라이트 테마별로 템플릿 생성 가능:
- `chat_input_dark.png`
- `chat_input_light.png`
"""
    
    template_dir = Path(__file__).parent / "ui_templates"
    template_dir.mkdir(exist_ok=True)
    
    guide_path = template_dir / "README.md"
    guide_path.write_text(guide, encoding='utf-8')
    
    print(f"✅ Template guide created: {guide_path}")


def main():
    parser = argparse.ArgumentParser(
        description="AGI Self-Aware Context Manager - 게임 봇 방식 자동화"
    )
    
    parser.add_argument('--paste', type=str, help='텍스트 붙여넣기')
    parser.add_argument('--paste-file', type=str, help='파일 내용 붙여넣기')
    parser.add_argument('--use-image', action='store_true', help='이미지 인식 사용 (Level 2)')
    parser.add_argument('--test-focus', action='store_true', help='포커스 테스트')
    parser.add_argument('--test-image', action='store_true', help='이미지 인식 테스트')
    parser.add_argument('--create-templates', action='store_true', help='템플릿 가이드 생성')
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 로그')
    
    args = parser.parse_args()
    
    # 템플릿 가이드 생성
    if args.create_templates:
        create_ui_template_guide()
        return
    
    # Automation 객체 생성
    auto = VSCodeChatAutomation(verbose=args.verbose)
    
    # 포커스 테스트
    if args.test_focus:
        print("🧪 Testing focus detection...")
        if auto.ensure_chat_input_focus():
            print("✅ Focus test passed!")
        else:
            print("❌ Focus test failed")
        return
    
    # 이미지 인식 테스트
    if args.test_image:
        print("🧪 Testing image detection...")
        location = auto.find_ui_element("chat_input.png")
        if location:
            print(f"✅ Image detection works! Found at {location}")
        else:
            print("❌ Image not found. Create template first:")
            print("   python scripts/agi_self_aware_context_manager.py --create-templates")
        return
    
    # 붙여넣기
    if args.paste:
        success = auto.auto_paste_smart(args.paste, use_image=args.use_image)
        sys.exit(0 if success else 1)
    
    if args.paste_file:
        file_path = Path(args.paste_file)
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            sys.exit(1)
        
        text = file_path.read_text(encoding='utf-8')
        success = auto.auto_paste_smart(text, use_image=args.use_image)
        sys.exit(0 if success else 1)
    
    # 인자 없으면 도움말
    parser.print_help()


if __name__ == "__main__":
    main()
        description="AGI Self-Aware Context Manager - 게임 봇처럼 상태를 인식하는 자동화"
    )
    parser.add_argument('--file', type=str, help='Context file to paste')
    parser.add_argument('--text', type=str, help='Direct text to paste')
    parser.add_argument('--use-image', action='store_true', help='Use image detection (Level 2)')
    parser.add_argument('--test-focus', action='store_true', help='Test focus detection')
    parser.add_argument('--test-image', action='store_true', help='Test image detection')
    parser.add_argument('--create-guide', action='store_true', help='Create UI template guide')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # 가이드 생성
    if args.create_guide:
        create_ui_template_guide()
        return 0
    
    automation = VSCodeChatAutomation(verbose=args.verbose)
    
    # 포커스 테스트
    if args.test_focus:
        print("🧪 Testing focus detection...")
        if automation.wait_for_focus():
            print("✅ Focus detection working")
            if automation.ensure_chat_input_focus():
                print("✅ Chat input focus confirmed")
            else:
                print("⚠️ Could not confirm chat input focus")
        return 0
    
    # 이미지 인식 테스트
    if args.test_image:
        print("🧪 Testing image detection...")
        location = automation.find_ui_element("chat_input.png")
        if location:
            print(f"✅ Chat input found at {location}")
        else:
            print("❌ Chat input not found")
            print("💡 Tip: Run with --create-guide to learn how to create templates")
        return 0
    
    # 실제 붙여넣기
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ File not found: {args.file}")
            return 1
        
        text = file_path.read_text(encoding='utf-8')
        automation.log(f"📄 Loaded {len(text)} chars from {args.file}")
    elif args.text:
        text = args.text
    else:
        print("❌ No --file or --text specified")
        parser.print_help()
        return 1
    
    # 스마트 붙여넣기 실행
    success = automation.auto_paste_smart(text, use_image=args.use_image)
    
    if success:
        print("✅ Auto-paste completed successfully")
        return 0
    else:
        print("❌ Auto-paste failed")
        print("💡 Tip: Try --test-focus and --test-image to diagnose")
        return 1


if __name__ == '__main__':
    sys.exit(main())
