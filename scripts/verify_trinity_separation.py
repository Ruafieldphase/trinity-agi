#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wrapper: Trinity 신호 분리 검증

역할
- 문서/운영에서 `python scripts/verify_trinity_separation.py ...` 형태를 기대하는 경우를 위해,
  실제 구현이 있는 `fdo_agi_repo/scripts/verify_trinity_separation.py`로 위임한다.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    target = repo_root / "fdo_agi_repo" / "scripts" / "verify_trinity_separation.py"
    if not target.exists():
        print(f"[verify_trinity_separation] missing target: {target}", file=sys.stderr)
        return 2

    runpy.run_path(str(target), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

