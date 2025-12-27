#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kill Switch (stub v0.1)

문서 참조 복구용 스텁.
- 이 파일은 어떤 프로세스도 종료하지 않는다.
- 실제 킬스위치는 운영 승인 및 안전 설계 확정 후 구현한다.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path


def utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _atomic_write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def main() -> int:
    ws = Path(__file__).resolve().parents[1]
    out = ws / "outputs" / "safety" / "kill_switch_latest.json"
    now = time.time()
    report = {
        "ok": False,
        "version": "kill_switch_stub_v0_1",
        "generated_at": utc_iso(now),
        "enforced": False,
        "reason": "stub_only",
        "note": "No processes were killed. This is a non-destructive placeholder.",
    }
    _atomic_write_json(out, report)
    print(json.dumps({"ok": False, "out": str(out)}, ensure_ascii=False))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

