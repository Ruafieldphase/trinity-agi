#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Program Learning Agent - 사람처럼 프로그램 배우기
인간이 새 프로그램을 익히는 방식:
1. 열기, 수정, 저장 (기본 작업)
2. Export/Import 확장자 파악 (프로그램 간 연결)
3. 도움말 찾기 (Help, F1, YouTube)
4. API/MCP 없이도 작동
"""

import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import pyautogui
    import cv2
    import numpy as np
    from PIL import Image
    import pytesseract  # OCR
except ImportError as e:
    print(f"❌ 의존성 누락: {e}")
    print("설치: python -m pip install opencv-python pillow pyautogui numpy pytesseract")
    sys.exit(1)


class ProgramLearningAgent:
    """프로그램 학습 에이전트"""
    
    def __init__(self, program_name: str):
        self.program_name = program_name
        self.outputs_dir = project_root / "outputs" / "program_learning"
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        
        self.learning_log = []
        self.discovered_features = {
            "menus": [],
            "file_formats": {"import": [], "export": []},
            "shortcuts": {},
            "help_sources": []
        }
        
        # 안전 설정
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
        
    def log(self, message: str, level: str = "INFO"):
        """로그 기록"""
        timestamp = datetime.now().isoformat()
        entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        self.learning_log.append(entry)
        icon = "🔍" if level == "INFO" else "⚠️" if level == "WARN" else "❌"
        print(f"{icon} {message}")
        
    def take_screenshot(self, name: str) -> Path:
        """스크린샷 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.outputs_dir / f"{self.program_name}_{name}_{timestamp}.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(str(path))
        self.log(f"스크린샷 저장: {path}")
        return path
        
    def find_text_on_screen(self, text: str, screenshot_path: Optional[Path] = None) -> Optional[Tuple[int, int]]:
        """화면에서 텍스트 찾기 (OCR)"""
        try:
            if screenshot_path is None:
                screenshot_path = self.take_screenshot("ocr_search")
                
            # OCR 실행
            img = Image.open(screenshot_path)
            ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, lang='eng+kor')
            
            # 텍스트 검색
            for i, detected_text in enumerate(ocr_data['text']):
                if text.lower() in detected_text.lower():
                    x = ocr_data['left'][i] + ocr_data['width'][i] // 2
                    y = ocr_data['top'][i] + ocr_data['height'][i] // 2
                    self.log(f"텍스트 '{text}' 발견: ({x}, {y})")
                    return (x, y)
                    
            self.log(f"텍스트 '{text}' 못 찾음", "WARN")
            return None
        except Exception as e:
            self.log(f"OCR 실패: {e}", "ERROR")
            return None
            
    def explore_menu(self, menu_name: str = "File") -> List[str]:
        """메뉴 탐색 (File, Edit, Help 등)"""
        self.log(f"'{menu_name}' 메뉴 탐색 시작")
        
        # 1. 메뉴 찾기
        screenshot_before = self.take_screenshot(f"before_{menu_name}_menu")
        menu_pos = self.find_text_on_screen(menu_name, screenshot_before)
        
        if menu_pos is None:
            self.log(f"'{menu_name}' 메뉴 못 찾음", "WARN")
            return []
            
        # 2. 메뉴 클릭
        pyautogui.click(*menu_pos)
        time.sleep(1)
        
        # 3. 메뉴 항목 캡처
        screenshot_after = self.take_screenshot(f"after_{menu_name}_menu")
        
        # 4. OCR로 메뉴 항목 추출
        try:
            img = Image.open(screenshot_after)
            ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, lang='eng+kor')
            
            menu_items = []
            for text in ocr_data['text']:
                if text.strip() and len(text) > 1:
                    menu_items.append(text.strip())
                    
            self.discovered_features["menus"].append({
                "menu": menu_name,
                "items": menu_items
            })
            
            self.log(f"'{menu_name}' 메뉴 항목 {len(menu_items)}개 발견")
            return menu_items
        except Exception as e:
            self.log(f"메뉴 항목 추출 실패: {e}", "ERROR")
            return []
        finally:
            # ESC로 메뉴 닫기
            pyautogui.press('esc')
            time.sleep(0.5)
            
    def discover_file_formats(self) -> Dict[str, List[str]]:
        """파일 포맷 탐지 (Save As 대화상자)"""
        self.log("파일 포맷 탐지 시작")
        
        # 1. Save As 대화상자 열기 (Ctrl+Shift+S)
        pyautogui.hotkey('ctrl', 'shift', 's')
        time.sleep(2)
        
        # 2. 스크린샷
        screenshot = self.take_screenshot("save_as_dialog")
        
        # 3. OCR로 파일 형식 추출
        try:
            img = Image.open(screenshot)
            ocr_text = pytesseract.image_to_string(img, lang='eng+kor')
            
            # 확장자 패턴 찾기 (*.txt, *.png 등)
            import re
            extensions = re.findall(r'\*\.(\w+)', ocr_text)
            
            self.discovered_features["file_formats"]["export"] = list(set(extensions))
            self.log(f"Export 가능 확장자: {extensions}")
            
            return {"export": extensions, "import": []}  # Import는 Open 대화상자에서
        except Exception as e:
            self.log(f"파일 포맷 추출 실패: {e}", "ERROR")
            return {"export": [], "import": []}
        finally:
            # ESC로 대화상자 닫기
            pyautogui.press('esc')
            time.sleep(0.5)
            
    def find_help(self) -> List[str]:
        """도움말 찾기"""
        self.log("도움말 소스 탐색")
        
        help_sources = []
        
        # 1. F1 키 시도
        pyautogui.press('f1')
        time.sleep(2)
        screenshot_f1 = self.take_screenshot("help_f1")
        
        # 도움말 창이 열렸는지 확인 (OCR)
        try:
            img = Image.open(screenshot_f1)
            ocr_text = pytesseract.image_to_string(img, lang='eng+kor')
            
            if "help" in ocr_text.lower() or "도움말" in ocr_text.lower():
                help_sources.append("F1 키 (내장 도움말)")
                self.log("F1 도움말 발견")
        except:
            pass
        finally:
            pyautogui.press('esc')
            time.sleep(0.5)
            
        # 2. Help 메뉴 탐색
        help_menu_items = self.explore_menu("Help")
        if help_menu_items:
            help_sources.append(f"Help 메뉴 ({len(help_menu_items)}개 항목)")
            
        self.discovered_features["help_sources"] = help_sources
        return help_sources
        
    def search_youtube_tutorial(self) -> Optional[str]:
        """YouTube에서 튜토리얼 검색"""
        self.log(f"'{self.program_name}' YouTube 튜토리얼 검색")
        
        # YouTube Learner 통합 (이미 구현된 기능 활용)
        youtube_learner_script = project_root / "scripts" / "enqueue_youtube_learn.ps1"
        
        if not youtube_learner_script.exists():
            self.log("YouTube Learner 스크립트 없음", "WARN")
            return None
            
        # 검색어 생성
        search_query = f"{self.program_name} tutorial how to use"
        youtube_search_url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
        
        self.log(f"YouTube 검색 URL: {youtube_search_url}")
        self.discovered_features["help_sources"].append(f"YouTube: {youtube_search_url}")
        
        return youtube_search_url
        
    def learn_program(self, dry_run: bool = True) -> Dict:
        """프로그램 학습 실행"""
        self.log("=" * 60)
        self.log(f"🎓 '{self.program_name}' 학습 시작")
        self.log("=" * 60)
        
        if dry_run:
            self.log("⚠️  DRY RUN 모드 (실제 클릭 안 함)")
            
        # 1. 기본 메뉴 탐색
        self.log("\n📋 Step 1: 메뉴 탐색")
        for menu in ["File", "Edit", "Help"]:
            if not dry_run:
                self.explore_menu(menu)
            else:
                self.log(f"[DRY RUN] '{menu}' 메뉴 탐색 생략")
                
        # 2. 파일 포맷 탐지
        self.log("\n📁 Step 2: 파일 포맷 탐지")
        if not dry_run:
            self.discover_file_formats()
        else:
            self.log("[DRY RUN] 파일 포맷 탐지 생략")
            
        # 3. 도움말 찾기
        self.log("\n❓ Step 3: 도움말 찾기")
        if not dry_run:
            self.find_help()
        else:
            self.log("[DRY RUN] 도움말 찾기 생략")
            
        # 4. YouTube 튜토리얼
        self.log("\n🎥 Step 4: YouTube 튜토리얼 검색")
        youtube_url = self.search_youtube_tutorial()
        
        # 5. 학습 리포트 생성
        report = {
            "program": self.program_name,
            "timestamp": datetime.now().isoformat(),
            "discovered_features": self.discovered_features,
            "learning_log": self.learning_log
        }
        
        # 저장
        report_path = self.outputs_dir / f"{self.program_name}_learning_report_latest.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        self.log(f"\n📊 학습 리포트 저장: {report_path}")
        
        # Markdown 리포트
        md_path = self.outputs_dir / f"{self.program_name}_learning_report_latest.md"
        self.generate_markdown_report(md_path, report)
        
        return report
        
    def generate_markdown_report(self, path: Path, report: Dict):
        """Markdown 리포트 생성"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# 🎓 {self.program_name} 학습 리포트\n\n")
            f.write(f"**생성 시각:** {report['timestamp']}\n\n")
            
            f.write("## 📋 발견한 메뉴\n\n")
            for menu in report['discovered_features'].get('menus', []):
                f.write(f"### {menu['menu']} 메뉴\n")
                for item in menu['items']:
                    f.write(f"- {item}\n")
                f.write("\n")
                
            f.write("## 📁 파일 포맷\n\n")
            formats = report['discovered_features'].get('file_formats', {})
            f.write(f"**Export 가능:** {', '.join(formats.get('export', []))}\n\n")
            f.write(f"**Import 가능:** {', '.join(formats.get('import', []))}\n\n")
            
            f.write("## ❓ 도움말 소스\n\n")
            for source in report['discovered_features'].get('help_sources', []):
                f.write(f"- {source}\n")
            f.write("\n")
            
            f.write("## 📝 학습 로그\n\n")
            for log_entry in report['learning_log']:
                f.write(f"**[{log_entry['timestamp']}]** {log_entry['message']}\n\n")
                
        self.log(f"Markdown 리포트 저장: {path}")


def main():
    """메인 실행"""
    import argparse
    parser = argparse.ArgumentParser(description="Program Learning Agent")
    parser.add_argument("--program", default="Notepad", help="학습할 프로그램 이름")
    parser.add_argument("--dry-run", action="store_true", help="DRY RUN 모드")
    args = parser.parse_args()
    
    agent = ProgramLearningAgent(args.program)
    report = agent.learn_program(dry_run=args.dry_run)
    
    print("\n" + "=" * 60)
    print("✅ 학습 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
