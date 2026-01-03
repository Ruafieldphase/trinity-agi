#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Path Utility for AGI System
===================================
모든 스크립트에서 워크스페이스 루트를 일관되게 탐지하기 위한 단일 함수를 제공합니다.
"""

import sys
from pathlib import Path

def get_workspace_root() -> Path:
    """
    현재 파일의 위치와 상관없이 워크스페이스 루트(agi 폴더)를 탐지합니다.
    1. 환경 변수 AGI_WORKSPACE_ROOT 확인 (권장)
    2. 현재 파일의 상위 폴더 중 'agi' 폴더 또는 '.git'이 있는 곳 탐색
    3. 탐색 실패 시 실행 시점의 CWD 반환 (최후의 수단)
    """
    # 1. 파일 기준 탐색 (가장 정확)
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / "agi").exists() or (parent / ".git").exists() or parent.name == "agi":
            # 만약 부모 중 agi가 있으면 그게 루트일 가능성이 높음
            if parent.name == "agi":
                return parent
            if (parent / "agi").exists():
                return parent / "agi"
            return parent

    # 2. 최후의 수단: 현재 경로
    return Path.cwd()

def add_to_sys_path():
    """워크스페이스 루트를 sys.path에 추가하여 임포트 가능하게 함"""
    root = get_workspace_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root

if __name__ == "__main__":
    print(f"Detected Workspace Root: {get_workspace_root()}")
