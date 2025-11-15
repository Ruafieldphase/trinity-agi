"""
RPA System Completion Module
=============================

AGI의 자율적 RPA 시스템 완성 프로젝트

Philosophy: 80% Freedom, 20% Guidance
"""

__version__ = "0.1.0"
__author__ = "AGI Autonomous System"
__freedom_level__ = 0.8  # 자율성 80%

from pathlib import Path
import sys

# 동적 workspace 탐색
workspace = Path(__file__).parent.parent.parent
if (workspace / '.git').exists():
    sys.path.insert(0, str(workspace))
    sys.path.insert(0, str(workspace / 'fdo_agi_repo'))
else:
    raise RuntimeError("Git workspace not found")

# workspace_utils import
try:
    from fdo_agi_repo.workspace_utils import find_workspace_root
    WORKSPACE_ROOT = find_workspace_root(Path(__file__).parent)
except ImportError:
    WORKSPACE_ROOT = workspace

__all__ = ['WORKSPACE_ROOT', '__version__', '__freedom_level__']
