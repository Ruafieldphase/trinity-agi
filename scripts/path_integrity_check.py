#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Path Integrity Check
====================
하드코딩된 절대 경로(C:/, /home/ 등)를 탐지하여 워크스페이스 상대 경로 사용을 권장합니다.
"""

import os
import re
from pathlib import Path
from workspace_root import get_workspace_root

WORKSPACE = get_workspace_root()

# 검사 제외 대상
EXCLUDE_DIRS = {".git", "node_modules", ".venv", "__pycache__", "backups", "logs", "outputs", "session_memory", "tests"}
EXCLUDE_FILES = {"config.py", "path_integrity_check.py", "identity_check.py"}

# 하드코딩된 경로 패턴 (윈도우 절대 경로 및 리눅스 루트 경로 일부)
# 주의: 정합성을 위해 너무 광범위한 패턴은 피하고, 코드 내 문자열 형태를 주로 탐색
FORBIDDEN_PATHS = [
    r'[a-zA-Z]:/(?!workspace/agi)[^"\'>\s]+',  # C:/... (workspace/agi 제외)
    r'"/home/[^"\'>\s]+"',                   # "/home/..."
    r"'/home/[^\"'>\s]+'",                   # '/home/...'
    r'"/usr/[^"\'>\s]+"',                    # "/usr/..."
]

def check_path_integrity():
    print(f"🔍 Checking Path Integrity in {WORKSPACE}...")
    violations = []

    for root, dirs, files in os.walk(WORKSPACE):
        # 제외 디렉토리 건너뛰기
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            if file in EXCLUDE_FILES or not file.endswith((".py", ".ps1", ".json")):
                continue
            
            path = Path(root) / file
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                
                for pattern in FORBIDDEN_PATHS:
                    matches = list(re.finditer(pattern, content))
                    if matches:
                        line_count = content[:matches[0].start()].count('\n') + 1
                        violations.append({
                            "file": str(path.relative_to(WORKSPACE)),
                            "line": line_count,
                            "match": matches[0].group()
                        })
            except Exception:
                continue

    if violations:
        print(f"❌ Found {len(violations)} path integrity violations:")
        for v in violations:
            print(f"  {v['file']}:L{v['line']} -> '{v['match']}'")
        return False
    else:
        print("✅ Path integrity is clean (No hardcoded absolute paths).")
        return True

if __name__ == "__main__":
    success = check_path_integrity()
    exit(0 if success else 1)
