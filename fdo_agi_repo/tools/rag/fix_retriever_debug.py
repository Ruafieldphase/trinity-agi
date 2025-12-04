#!/usr/bin/env python3
"""Add debug warning to _build_docs when memory files not found."""
import os

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from workspace_utils import find_fdo_root

path = find_fdo_root(Path(__file__).parent) / 'tools' / 'rag' / 'retriever.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find line 'if not os.path.exists(path):' and add print after it
new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    if i == 98 and 'if not os.path.exists(path):' in line:  # Line 99 (0-indexed)
        indent = ' ' * 8  # Match function body indentation
        warn_line = indent + 'print(f"[WARN _build_docs] File not found: {path} (cwd={os.getcwd()})")\n'
        new_lines.append(warn_line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Added file not found warning to _build_docs')
