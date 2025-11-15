"""
Autonomous Executor Integration Module
=======================================

AGI 자율 목표 실행 시스템의 통합 모듈

Components:
    - goal_decomposer.py: 목표 분해기
    - task_scheduler.py: 작업 스케줄러
    - execution_monitor.py: 실행 모니터
    - autonomous_recovery.py: 자동 복구
    - executor_main.py: 통합 엔트리포인트

Philosophy: The Executor Executes Itself
"""

__version__ = "0.2.0"  # Phase 2
__author__ = "AGI Autonomous System"

from pathlib import Path
import sys

# 동적 workspace 탐색
workspace = Path(__file__).parent.parent.parent
if (workspace / '.git').exists():
    sys.path.insert(0, str(workspace))
    sys.path.insert(0, str(workspace / 'fdo_agi_repo'))
else:
    raise RuntimeError("Git workspace not found")

# 기존 시스템 import
try:
    from fdo_agi_repo.workspace_utils import find_workspace_root
    WORKSPACE_ROOT = find_workspace_root(Path(__file__).parent)
except ImportError:
    WORKSPACE_ROOT = workspace

__all__ = ['WORKSPACE_ROOT', '__version__']
