"""
Workspace Utilities - 공통 유틸리티 함수
=========================================

워크스페이스 루트 탐색 등 여러 스크립트에서 공통으로 사용하는 함수들을 제공합니다.
"""

from pathlib import Path


def find_workspace_root(start_path: Path) -> Path:
    """
    Workspace root를 찾습니다 (.git 또는 특정 마커 파일 기준)
    
    검색 순서:
    1. .git 디렉토리
    2. agi 디렉토리 (프로젝트 구조상)
    3. 최대 5단계 상위 디렉토리까지 검색
    
    Args:
        start_path: 검색을 시작할 경로
        
    Returns:
        워크스페이스 루트 경로
    """
    current = start_path.resolve()
    
    for _ in range(5):  # 최대 5단계 상위까지
        # .git 디렉토리 확인
        if (current / '.git').exists():
            return current
        
        # agi 디렉토리인 경우
        if current.name == 'agi':
            return current
            
        # fdo_agi_repo 하위인 경우, 상위로 올라가서 agi 찾기
        if current.name == 'fdo_agi_repo':
            parent = current.parent
            if parent.name == 'agi':
                return parent
        
        # 상위 디렉토리로 이동
        parent = current.parent
        if parent == current:  # 루트에 도달
            break
        current = parent
    
    # 찾지 못한 경우 현재 스크립트의 1단계 상위 (fdo_agi_repo -> agi)
    # 또는 fdo_agi_repo가 아니면 3단계 상위
    if start_path.name == 'fdo_agi_repo' or 'fdo_agi_repo' in str(start_path):
        # fdo_agi_repo 내부에서 실행된 경우
        parts = start_path.parts
        if 'fdo_agi_repo' in parts:
            idx = parts.index('fdo_agi_repo')
            return Path(*parts[:idx+1]).parent
    
    return start_path.parent.parent.parent


def find_fdo_root(start_path: Path) -> Path:
    """
    fdo_agi_repo 루트를 찾습니다.
    
    Args:
        start_path: 검색을 시작할 경로
        
    Returns:
        fdo_agi_repo 루트 경로
    """
    current = start_path.resolve()
    
    for _ in range(5):
        if current.name == 'fdo_agi_repo':
            return current
        
        parent = current.parent
        if parent == current:  # 루트에 도달
            break
        current = parent
    
    # 찾지 못한 경우 현재 경로 반환
    return start_path
