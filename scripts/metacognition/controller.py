#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Metacognition Controller (stub v1)

문서 참조 복구용 최소 스크립트.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
import sys
from workspace_root import get_workspace_root
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))



def utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _atomic_write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def main() -> int:
    ws = get_workspace_root()
    out = ws / "outputs" / "metacognition_controller_latest.json"
    now = time.time()
    report = {
        "ok": False,
        "version": "metacognition_controller_stub_v1",
        "generated_at": utc_iso(now),
        "reason": "controller_not_connected",
        "note": "Stub only. Connect to rhythm/decision loops if needed.",
    }
    _atomic_write_json(out, report)
    print(json.dumps({"ok": False, "out": str(out)}, ensure_ascii=False))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

