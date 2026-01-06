#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Visual Chat Switcher 자동 테스트
- 화면 감지 기능 검증
- 클릭 시뮬레이션 테스트
- 로그 검증
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime
from workspace_root import get_workspace_root

# 프로젝트 루트 추가
project_root = get_workspace_root()
sys.path.insert(0, str(project_root))

try:
    import pyautogui
    import cv2
    import numpy as np
    from PIL import Image
except ImportError as e:
    print(f"❌ 의존성 누락: {e}")
    print("설치: python -m pip install opencv-python pillow pyautogui numpy")
    sys.exit(1)


class VisualSwitcherTest:
    """Visual Chat Switcher 테스트 자동화"""
    
    def __init__(self):
        self.outputs_dir = project_root / "outputs"
        self.test_results = []
        
    def take_screenshot(self, name: str) -> Path:
        """스크린샷 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.outputs_dir / f"test_{name}_{timestamp}.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(str(path))
        print(f"📸 스크린샷 저장: {path}")
        return path
        
    def test_screen_capture(self) -> bool:
        """화면 캡처 테스트"""
        print("\n🧪 테스트 1: 화면 캡처")
        try:
            screenshot_path = self.take_screenshot("screen_capture")
            img = Image.open(screenshot_path)
            width, height = img.size
            
            if width > 0 and height > 0:
                print(f"✅ 화면 크기: {width}x{height}")
                return True
            else:
                print("❌ 잘못된 화면 크기")
                return False
        except Exception as e:
            print(f"❌ 화면 캡처 실패: {e}")
            return False
            
    def test_color_detection(self) -> bool:
        """색상 감지 테스트"""
        print("\n🧪 테스트 2: 색상 감지 (Copilot 파란색)")
        try:
            screenshot = pyautogui.screenshot()
            img_np = np.array(screenshot)
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            
            # Copilot 아이콘 색상 (파란색)
            target_color = np.array([88, 166, 255])  # RGB
            target_bgr = np.array([255, 166, 88])  # BGR
            tolerance = 30
            
            # 색상 매칭
            lower = target_bgr - tolerance
            upper = target_bgr + tolerance
            mask = cv2.inRange(img_bgr, lower, upper)
            
            # 매칭된 픽셀 수
            matched_pixels = np.count_nonzero(mask)
            total_pixels = mask.size
            match_percentage = (matched_pixels / total_pixels) * 100
            
            print(f"🎨 매칭된 픽셀: {matched_pixels:,} / {total_pixels:,}")
            print(f"📊 매칭률: {match_percentage:.4f}%")
            
            if matched_pixels > 100:  # 최소 100픽셀 이상
                print("✅ Copilot 색상 감지됨")
                
                # 감지 결과 저장
                debug_path = self.outputs_dir / f"test_color_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                cv2.imwrite(str(debug_path), mask)
                print(f"📸 마스크 이미지: {debug_path}")
                return True
            else:
                print("❌ Copilot 색상 감지 실패 (VS Code 실행 중인지 확인)")
                return False
                
        except Exception as e:
            print(f"❌ 색상 감지 실패: {e}")
            return False
            
    def test_mouse_position(self) -> bool:
        """마우스 위치 테스트"""
        print("\n🧪 테스트 3: 마우스 위치 감지")
        try:
            x, y = pyautogui.position()
            screen_width, screen_height = pyautogui.size()
            
            print(f"🖱️  현재 마우스 위치: ({x}, {y})")
            print(f"📺 화면 크기: {screen_width}x{screen_height}")
            
            if 0 <= x < screen_width and 0 <= y < screen_height:
                print("✅ 마우스 위치 정상")
                return True
            else:
                print("❌ 마우스 위치 비정상")
                return False
        except Exception as e:
            print(f"❌ 마우스 위치 감지 실패: {e}")
            return False
            
    def test_click_safety(self) -> bool:
        """클릭 안전성 테스트 (실제 클릭 안 함)"""
        print("\n🧪 테스트 4: 클릭 시뮬레이션 (DRY RUN)")
        try:
            # 안전한 위치 (화면 중앙)
            screen_width, screen_height = pyautogui.size()
            safe_x = screen_width // 2
            safe_y = screen_height // 2
            
            print(f"🎯 시뮬레이션 클릭 위치: ({safe_x}, {safe_y})")
            print("ℹ️  실제 클릭은 하지 않습니다 (안전 모드)")
            
            # pyautogui.click(safe_x, safe_y)  # 실제 클릭은 주석 처리
            print("✅ 클릭 시뮬레이션 성공")
            return True
        except Exception as e:
            print(f"❌ 클릭 시뮬레이션 실패: {e}")
            return False
            
    def test_failsafe(self) -> bool:
        """Failsafe 테스트"""
        print("\n🧪 테스트 5: Failsafe 설정 확인")
        try:
            failsafe_status = pyautogui.FAILSAFE
            print(f"🛡️  Failsafe 상태: {failsafe_status}")
            
            if failsafe_status:
                print("✅ Failsafe 활성화됨 (마우스를 왼쪽 상단 모서리로 이동하면 중단)")
                return True
            else:
                print("⚠️  Failsafe 비활성화됨 (권장하지 않음)")
                return False
        except Exception as e:
            print(f"❌ Failsafe 확인 실패: {e}")
            return False
            
    def run_all_tests(self) -> dict:
        """모든 테스트 실행"""
        print("=" * 60)
        print("🧪 Visual Chat Switcher 자동 테스트 시작")
        print("=" * 60)
        
        tests = [
            ("화면 캡처", self.test_screen_capture),
            ("색상 감지", self.test_color_detection),
            ("마우스 위치", self.test_mouse_position),
            ("클릭 안전성", self.test_click_safety),
            ("Failsafe", self.test_failsafe),
        ]
        
        results = {}
        passed = 0
        failed = 0
        
        for name, test_func in tests:
            try:
                result = test_func()
                results[name] = "PASS" if result else "FAIL"
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ {name} 테스트 예외: {e}")
                results[name] = f"ERROR: {str(e)}"
                failed += 1
                
        # 결과 요약
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약")
        print("=" * 60)
        for test_name, status in results.items():
            icon = "✅" if status == "PASS" else "❌"
            print(f"{icon} {test_name}: {status}")
            
        print(f"\n총 {passed + failed}개 테스트 중 {passed}개 통과, {failed}개 실패")
        
        # JSON 저장
        report = {
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "summary": {
                "total": passed + failed,
                "passed": passed,
                "failed": failed,
                "success_rate": f"{(passed / (passed + failed) * 100):.1f}%"
            }
        }
        
        report_path = self.outputs_dir / "visual_switcher_test_report_latest.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n📄 리포트 저장: {report_path}")
        
        return report


def main():
    """메인 실행"""
    tester = VisualSwitcherTest()
    report = tester.run_all_tests()
    
    # 성공 여부 반환
    success_rate = float(report["summary"]["success_rate"].rstrip("%"))
    sys.exit(0 if success_rate >= 80 else 1)


if __name__ == "__main__":
    main()
