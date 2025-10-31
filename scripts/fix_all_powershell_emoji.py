#!/usr/bin/env python3
"""
PowerShell 스크립트의 이모지를 영문 태그로 일괄 변환
Windows PowerShell 5.1 + VS Code 터미널의 UTF-8 인코딩 이슈 우회
"""

import re
from pathlib import Path

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

def fix_emoji_in_file(ps1_file: Path) -> int:
    """단일 PS1 파일의 이모지를 영문 태그로 변환"""
    try:
        content = ps1_file.read_text(encoding='utf-8')
        original = content
        
        for emoji, replacement in EMOJI_REPLACEMENTS.items():
            content = content.replace(emoji, replacement)
        
        if content != original:
            ps1_file.write_text(content, encoding='utf-8')
            return 1
        return 0
    except Exception as e:
        print(f"[ERROR] Failed to process {ps1_file}: {e}")
        return 0

def main():
    workspace_root = Path(__file__).parent.parent
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
