"""
ChatGPT-AGI Bridge Integration
================================

OpenAI ChatGPT와 AGI 시스템을 MCP(Model Context Protocol)로 연결하는 브릿지.

Architecture:
    ChatGPT (OpenAI API)
        ↕ (OpenAI Client)
    ChatGPT Bridge (this module)
        ↕ (MCP Adapter)
    Core MCP Server (existing)
        ↕ (Persona Orchestration)
    AGI Core System
        ↕ (Resonance Ledger)
    Self-Correction Loop

Components:
    - chatgpt_client.py: OpenAI API 클라이언트
    - mcp_adapter.py: 기존 Core MCP 서버 연결
    - bridge_server.py: FastAPI 게이트웨이
    
Philosophy: Connectivity > Depth
Author: AGI Autonomous System + GitHub Copilot
Date: 2025-11-15
"""

__version__ = "0.1.0"
__author__ = "AGI Autonomous System"

from pathlib import Path

# 동적 workspace 탐색
import sys
workspace = Path(__file__).parent.parent.parent
if (workspace / '.git').exists():
    sys.path.insert(0, str(workspace))
else:
    raise RuntimeError("Git workspace not found. This module requires AGI repository.")

# 기존 시스템 import
try:
    from fdo_agi_repo.workspace_utils import find_workspace_root
    WORKSPACE_ROOT = find_workspace_root(Path(__file__).parent)
except ImportError:
    WORKSPACE_ROOT = workspace

__all__ = ['WORKSPACE_ROOT', '__version__']
