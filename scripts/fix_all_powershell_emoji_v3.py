#!/usr/bin/env python3
"""
PowerShell 스크립트의 이모지를 영문 태그로 일괄 변환 (multi-encoding fallback)
Windows PowerShell 5.1 + VS Code 터미널의 UTF-8 인코딩 이슈 우회
"""

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

def read_with_fallback(file_path: Path) -> tuple[str, str]:
    """Try multiple encodings to read file"""
    for encoding in ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr', 'latin-1']:
        try:
            content = file_path.read_text(encoding=encoding)
            return content, encoding
        except (UnicodeDecodeError, LookupError):
            continue
    
    # Last resort: read as binary and decode with errors='ignore'
    raw = file_path.read_bytes()
    content = raw.decode('utf-8', errors='ignore')
    return content, 'utf-8-ignore'

def fix_emoji_in_file(ps1_file: Path) -> int:
    """단일 PS1 파일의 이모지를 영문 태그로 변환"""
    try:
        content, original_encoding = read_with_fallback(ps1_file)
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
