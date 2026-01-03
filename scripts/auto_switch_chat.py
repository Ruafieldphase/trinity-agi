#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AGI 자동 채팅창 전환 시스템
게임 봇처럼 완전 자동으로 새 채팅창을 열고 컨텍스트를 로드합니다.
"""

import pyautogui
import time
import sys
import os
from pathlib import Path
from workspace_root import get_workspace_root

# 안전 설정: 마우스를 화면 모서리로 이동하면 중단
pyautogui.FAILSAFE = True
# 각 pyautogui 작업 사이 기본 대기 시간 (초)
pyautogui.PAUSE = 0.3


def load_context_from_file(context_file: str = None) -> str:
    """컨텍스트 파일 로드"""
    if context_file is None:
        workspace_root = get_workspace_root()
        context_file = workspace_root / "outputs" / ".copilot_context_summary.md"
    
    context_path = Path(context_file)
    if not context_path.exists():
        raise FileNotFoundError(f"컨텍스트 파일 없음: {context_file}")
    
    with open(context_path, 'r', encoding='utf-8') as f:
        return f.read()


def copy_to_clipboard(text: str):
    """텍스트를 클립보드에 복사"""
    try:
        import pyperclip
        pyperclip.copy(text)
        print("✅ 컨텍스트를 클립보드에 복사했습니다")
    except ImportError:
        print("⚠️ pyperclip 모듈이 필요합니다: pip install pyperclip")
        # 대안: PowerShell 사용
        import subprocess
        ps_cmd = f'Set-Clipboard -Value @"\n{text}\n"@'
        subprocess.run(['powershell', '-Command', ps_cmd], check=True)
        print("✅ 컨텍스트를 클립보드에 복사했습니다 (PowerShell)")


def open_new_copilot_chat():
    """새 Copilot 채팅창 열기"""
    print("📝 새 Copilot 채팅창 열기...")
    
    # Ctrl+Shift+I (Copilot Chat 단축키)
    pyautogui.hotkey('ctrl', 'shift', 'i')
    time.sleep(1.5)  # 채팅창이 열릴 때까지 대기
    
    print("✅ 새 채팅창이 열렸습니다")


def find_and_click_chat_input():
    """채팅 입력창 찾아서 클릭"""
    print("🎯 채팅 입력창 찾는 중...")
    
    # 방법 1: 화면 중앙 하단 클릭 (일반적인 채팅 입력창 위치)
    screen_width, screen_height = pyautogui.size()
    click_x = screen_width // 2
    click_y = int(screen_height * 0.85)  # 화면 하단 85% 지점
    
    print(f"   → 클릭 위치: ({click_x}, {click_y})")
    pyautogui.click(click_x, click_y)
    time.sleep(0.5)
    
    print("✅ 입력창 클릭 완료")


def paste_and_send():
    """붙여넣기 + 전송"""
    print("📋 컨텍스트 붙여넣기 중...")
    
    # Ctrl+V (붙여넣기)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.8)  # 붙여넣기 완료 대기
    
    print("✅ 붙여넣기 완료")
    
    # Enter (전송)
    print("📤 메시지 전송 중...")
    pyautogui.press('enter')
    time.sleep(0.5)
    
    print("✅ 전송 완료!")


def auto_switch_to_new_chat(context_file: str = None, verbose: bool = True):
    """
    완전 자동 채팅창 전환
    
    Args:
        context_file: 컨텍스트 파일 경로 (None이면 기본값 사용)
        verbose: 상세 로그 출력 여부
    """
    if verbose:
        print("=" * 60)
        print("🤖 AGI 자동 채팅창 전환 시작!")
        print("=" * 60)
        print()
    
    try:
        # 1. 컨텍스트 로드 및 클립보드 복사
        if verbose:
            print("📖 Step 1: 컨텍스트 로드")
        context = load_context_from_file(context_file)
        copy_to_clipboard(context)
        print()
        
        # 2. 새 채팅창 열기
        if verbose:
            print("📝 Step 2: 새 채팅창 열기")
        open_new_copilot_chat()
        print()
        
        # 3. 입력창 클릭
        if verbose:
            print("🎯 Step 3: 입력창 찾아서 클릭")
        find_and_click_chat_input()
        print()
        
        # 4. 붙여넣기 + 전송
        if verbose:
            print("📤 Step 4: 붙여넣기 + 전송")
        paste_and_send()
        print()
        
        if verbose:
            print("=" * 60)
            print("🎉 완전 자동 전환 완료!")
            print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='AGI 자동 채팅창 전환 (게임 봇 모드)'
    )
    parser.add_argument(
        '--context-file',
        type=str,
        help='컨텍스트 파일 경로 (기본: outputs/.copilot_context_summary.md)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='상세 로그 끄기'
    )
    parser.add_argument(
        '--delay',
        type=int,
        default=3,
        help='시작 전 대기 시간(초) - VS Code 창으로 전환할 시간'
    )
    
    args = parser.parse_args()
    
    if args.delay > 0:
        print(f"⏳ {args.delay}초 후 시작됩니다...")
        print("   (VS Code 창을 활성화하세요!)")
        time.sleep(args.delay)
    
    success = auto_switch_to_new_chat(
        context_file=args.context_file,
        verbose=not args.quiet
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
