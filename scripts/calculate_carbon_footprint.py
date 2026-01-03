#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Carbon Footprint Calculator (stub v1)

문서 참조 복구용 최소 스크립트.
실제 전력/탄소 계산은 데이터 소스(전력계/클라우드 사용량)가 필요하므로 현재는 스텁.
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
    out = ws / "outputs" / "carbon_footprint_latest.json"
    now = time.time()
    report = {
        "ok": False,
        "version": "carbon_footprint_stub_v1",
        "generated_at": utc_iso(now),
        "reason": "no_metering_data_source",
        "note": "Stub only. Provide metering data sources to compute real footprint.",
    }
    _atomic_write_json(out, report)
    print(json.dumps({"ok": False, "out": str(out)}, ensure_ascii=False))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

