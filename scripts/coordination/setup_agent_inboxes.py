#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Inbox/Outbox layout

목표:
- 외부 에이전트가 결과물을 '한 곳에' 떨어뜨릴 수 있게 디렉토리를 고정한다.
- 루빛은 self_acquire에서 이 디렉토리를 읽어 압축/통합할 수 있다.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def ensure_dirs(workspace_root: Path) -> dict:
    workspace_root = workspace_root.resolve()
    base_in = workspace_root / "inputs" / "agent_inbox"
    base_out = workspace_root / "outputs" / "agent_outbox"
    for d in [
        base_in / "antigravity_sian",
        base_in / "claude_sena",
        base_in / "rua",
        base_out / "antigravity_sian",
        base_out / "claude_sena",
        base_out / "rua",
    ]:
        d.mkdir(parents=True, exist_ok=True)
    return {"ok": True, "inbox": str(base_in), "outbox": str(base_out)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=str, default=str(Path(__file__).resolve().parents[2]))
    args = ap.parse_args()
    res = ensure_dirs(Path(args.workspace))
    print(json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

