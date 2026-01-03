#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core Quick Test (integrated) — stub

문서 참조 복구용 최소 스크립트.
네트워크/모델 호출 없이 로컬 출력만 생성한다.
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
    ws = Path(__file__).resolve().parents[2]
    out = ws / "outputs" / "core_quick_test_integrated_latest.json"
    now = time.time()
    report = {
        "ok": True,
        "version": "core_quick_test_integrated_stub_v1",
        "generated_at": utc_iso(now),
        "note": "Stub only. Replace with real integrated test when Core pipeline is connected.",
    }
    _atomic_write_json(out, report)
    print(json.dumps({"ok": True, "out": str(out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

