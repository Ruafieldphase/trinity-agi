#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dispute Workflow Handler (stub v1)

문서 참조 복구용 최소 스크립트.
- 실제 분쟁/이의제기 워크플로우는 운영 규칙/승인 체계와 함께 설계되어야 한다.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from workspace_root import get_workspace_root


def utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _atomic_write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def main() -> int:
    ws = get_workspace_root()
    out = ws / "outputs" / "dispute_workflow_latest.json"
    now = time.time()
    report = {
        "ok": False,
        "version": "dispute_workflow_stub_v1",
        "generated_at": utc_iso(now),
        "reason": "workflow_not_defined",
        "note": "Stub only. Define dispute workflow states/owners/SLAs to activate.",
    }
    _atomic_write_json(out, report)
    print(json.dumps({"ok": False, "out": str(out)}, ensure_ascii=False))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

