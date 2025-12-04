#!/usr/bin/env python3
"""
Fix tasks.json encoding to UTF-8 with BOM for proper Korean/Emoji display in Windows PowerShell
"""
from pathlib import Path

tasks_file = Path(r"c:\workspace\agi\.vscode\tasks.json")

# Read current content
content = tasks_file.read_text(encoding='utf-8')

# Write with UTF-8 BOM
tasks_file.write_text(content, encoding='utf-8-sig')

print(f"✅ Fixed encoding: {tasks_file}")
print("   Encoding: UTF-8 with BOM")
print("   PowerShell will now display Korean/Emoji correctly")
