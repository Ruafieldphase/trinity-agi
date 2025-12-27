#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Red Line Monitor (stub v0.1)

문서 참조 복구 + 관측 가능성 확보용.
- 정책 파일을 읽어 "정책이 존재함"을 출력으로 고정한다.
- 강제 차단/격리/킬스위치 동작은 하지 않는다.
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
    policy = ws / "policy" / "red_line_monitor.yaml"
    out = ws / "outputs" / "safety" / "red_line_monitor_latest.json"
    now = time.time()

    report = {
        "ok": True,
        "version": "red_line_monitor_stub_v0_1",
        "generated_at": utc_iso(now),
        "policy": {"path": str(policy), "exists": policy.exists()},
        "enforcement": {"enabled": False, "reason": "stub_only"},
    }
    _atomic_write_json(out, report)
    print(json.dumps({"ok": True, "out": str(out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

