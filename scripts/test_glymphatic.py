#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compatibility wrapper.

docs/AGENT_HANDOFF.md 등에서 참조하는 `scripts/test_glymphatic.py`가 누락되어 있어
기존 테스트 스크립트(`scripts/test_adaptive_glymphatic.py`)로 위임한다.
"""

from __future__ import annotations

import runpy
from pathlib import Path
import sys
from workspace_root import get_workspace_root


def main() -> int:
    root = get_workspace_root()
    target = root / "scripts" / "test_adaptive_glymphatic.py"
    if not target.exists():
        print(f"[error] missing target: {target}")
        return 1
    sys.path.insert(0, str(root))
    runpy.run_path(str(target), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

