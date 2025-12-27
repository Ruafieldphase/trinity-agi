#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wrapper: Task Watchdog

문서/운영에서 `python scripts/task_watchdog.py ...` 형태를 기대하는 경우를 위해,
실제 구현이 있는 `fdo_agi_repo/scripts/task_watchdog.py`로 위임한다.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    target = repo_root / "fdo_agi_repo" / "scripts" / "task_watchdog.py"
    if not target.exists():
        print(f"[task_watchdog] missing target: {target}", file=sys.stderr)
        return 2
    runpy.run_path(str(target), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

