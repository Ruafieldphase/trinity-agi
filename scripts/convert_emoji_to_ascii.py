#!/usr/bin/env python3
"""
PowerShell ?¤í¬ë¦½íŠ¸?ì„œ ?´ëª¨ì§€ë¥?ASCIIë¡??¼ê´„ ë³€??

PowerShell 5.1 ì½˜ì†” ?¸ì½”??ë¬¸ì œë¥?ë°©ì??˜ê¸° ?„í•´ 
?´ëª¨ì§€ë¥?ASCII ê¸°ë°˜ ?œì‹œë¡?ë³€?˜í•©?ˆë‹¤.
"""

import os
import sys
import re
from pathlib import Path
from workspace_root import get_workspace_root
from typing import Dict, List, Tuple

# ?´ëª¨ì§€ ??ASCII ë§¤í•‘
EMOJI_REPLACEMENTS: Dict[str, str] = {
    '??: '[OK]',
    '??: '[ERROR]',
    '? ï¸': '[WARN]',
    '??: '[WARN]',  # ë³€??ë²„ì „
    '?“Š': '[INFO]',
    '??': '[START]',
    '?’¡': '[TIP]',
    '?”': '[SEARCH]',
    '??: '[TIME]',
    '?Ž¯': '[TARGET]',
    '?“ˆ': '[UP]',
    '?“‰': '[DOWN]',
    '?”„': '[RELOAD]',
    '??: '[NEW]',
    '?Ž‰': '[DONE]',
    '?›‘': '[STOP]',
    '??: '[FAST]',
    '?“': '[NOTE]',
    '?¤–': '[BOT]',
    '?Œ': '[WEB]',
    '?”‘': '[KEY]',
    '?“¡': '[SIGNAL]',
    '?¹ï¸': '[END]',
    '??: '[END]',  # ë³€??ë²„ì „
    '?Ž¬': '[SCENE]',
    '?Ž™ï¸?: '[MIC]',
    '?Ž™': '[MIC]',  # ë³€??ë²„ì „
}


def convert_emojis_in_file(file_path: Path, dry_run: bool = True) -> Tuple[int, List[str]]:
    """
    ?Œì¼ ???´ëª¨ì§€ë¥?ASCIIë¡?ë³€??
    
    Returns:
        (replacement_count, list_of_emoji_names)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        replacement_count = 0
        found_emojis = []
        
        for emoji, ascii_replacement in EMOJI_REPLACEMENTS.items():
            if emoji in content:
                count = content.count(emoji)
                content = content.replace(emoji, ascii_replacement)
                replacement_count += count
                found_emojis.append(f"{emoji} ??{ascii_replacement} ({count}x)")
        
        if replacement_count > 0 and not dry_run:
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                f.write(content)
        
        return replacement_count, found_emojis
    
    except Exception as e:
        print(f"[ERROR] {file_path.name}: {e}", file=sys.stderr)
        return 0, []


def main(target_dir: str = None, dry_run: bool = True):
    if not target_dir:
        target_dir = str(get_workspace_root() / "scripts")
    """ë©”ì¸ ?¤í–‰ ?¨ìˆ˜"""
    
    print("\n" + "="*50)
    print("  Emoji to ASCII Converter (Python)")
    print("="*50 + "\n")
    
    if dry_run:
        print("[DRY-RUN MODE] No files will be modified\n")
    
    target_path = Path(target_dir)
    if not target_path.exists():
        print(f"[ERROR] Directory not found: {target_dir}")
        return 1
    
    scripts = list(target_path.glob("*.ps1"))
    total_files_modified = 0
    total_replacements = 0
    
    for script in scripts:
        count, emojis = convert_emojis_in_file(script, dry_run)
        
        if count > 0:
            total_files_modified += 1
            total_replacements += count
            
            print(f"[MODIFIED] {script.name}")
            for emoji_info in emojis:
                print(f"           {emoji_info}")
            
            if not dry_run:
                print(f"           [SAVED]")
            print()
    
    print("="*50)
    print("Summary:")
    print(f"  Files scanned:      {len(scripts)}")
    print(f"  Files modified:     {total_files_modified}")
    print(f"  Total replacements: {total_replacements}")
    
    if dry_run:
        print("\n[TIP] Run with --execute to apply changes")
    else:
        print("\n[DONE] All emojis converted to ASCII")
    
    print("="*50 + "\n")
    return 0


if __name__ == "__main__":
    dry_run = "--execute" not in sys.argv
    target = str(get_workspace_root() / "scripts")
    
    if len(sys.argv) > 1 and sys.argv[1].startswith("--dir="):
        target = sys.argv[1].split("=", 1)[1]
    
    sys.exit(main(target, dry_run))
