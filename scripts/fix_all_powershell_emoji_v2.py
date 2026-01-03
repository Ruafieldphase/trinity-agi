#!/usr/bin/env python3
"""
PowerShell 스크립트의 이모지를 영문 태그로 일괄 변환 (인코딩 자동 감지 버전)
Windows PowerShell 5.1 + VS Code 터미널의 UTF-8 인코딩 이슈 우회
"""

import chardet
from pathlib import Path
from workspace_root import get_workspace_root

EMOJI_REPLACEMENTS = {
    "🚨": "[ALERT]",
    "✅": "[OK]",
    "❌": "[ERROR]",
    "⏳": "[WAIT]",
    "🎯": "[TARGET]",
    "📊": "[METRICS]",
    "🔍": "[SEARCH]",
    "🚀": "[DEPLOY]",
    "📝": "[LOG]",
    "⚠️": "[WARN]",
    "🔄": "[SYNC]",
    "💡": "[INFO]",
    "🎉": "[SUCCESS]",
    "🔧": "[CONFIG]",
    "📦": "[PACKAGE]",
    "🌐": "[WEB]",
    "🤖": "[BOT]",
    "📺": "[STREAM]",
    "🎬": "[VIDEO]",
    "⚙️": "[SETTINGS]",
    "📈": "[STATS]",
    "🔥": "[HOT]",
    "🧪": "[TEST]",
    "🧩": "[MODULE]",
}

def detect_encoding(file_path: Path) -> str:
    """파일 인코딩 자동 감지"""
    with open(file_path, 'rb') as f:
        raw = f.read()
        result = chardet.detect(raw)
        return result['encoding'] or 'utf-8'

def fix_emoji_in_file(ps1_file: Path) -> int:
    """단일 PS1 파일의 이모지를 영문 태그로 변환 (인코딩 자동 감지)"""
    try:
        # 인코딩 자동 감지
        encoding = detect_encoding(ps1_file)
        
        # 읽기
        try:
            content = ps1_file.read_text(encoding=encoding)
        except:
            # 감지 실패 시 CP949 시도
            content = ps1_file.read_text(encoding='cp949')
            encoding = 'cp949'
        
        original = content
        
        # 이모지 치환
        for emoji, replacement in EMOJI_REPLACEMENTS.items():
            content = content.replace(emoji, replacement)
        
        # 변경사항이 있으면 UTF-8로 저장
        if content != original:
            ps1_file.write_text(content, encoding='utf-8')
            return 1
        return 0
    except Exception as e:
        print(f"[ERROR] Failed to process {ps1_file}: {e}")
        return 0

def main():
    workspace_root = get_workspace_root()
    ps1_files = list(workspace_root.rglob("*.ps1"))
    
    print(f"[INFO] Found {len(ps1_files)} PowerShell scripts")
    
    modified_count = 0
    for ps1_file in ps1_files:
        result = fix_emoji_in_file(ps1_file)
        if result:
            print(f"[OK] Fixed: {ps1_file.relative_to(workspace_root)}")
            modified_count += result
    
    print(f"\n[SUCCESS] Modified {modified_count} files")

if __name__ == "__main__":
    main()
