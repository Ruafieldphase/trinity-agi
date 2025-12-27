#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Persona Orchestrator (stub v1)

문서 참조 복구용 최소 파일.
현재 레포의 실제 오케스트레이션은 `fdo_agi_repo/orchestrator/`를 중심으로 돌아가며,
이 파일은 "통합 설계 문서"에 등장하는 경로를 끊김 없이 유지하기 위한 스텁이다.
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
    out = ws / "outputs" / "persona_orchestrator_stub_latest.json"
    now = time.time()
    report = {
        "ok": False,
        "version": "persona_orchestrator_stub_v1",
        "generated_at": utc_iso(now),
        "reason": "not_implemented_in_this_repo_layout",
        "hint": "See fdo_agi_repo/orchestrator/ for the active pipeline.",
    }
    _atomic_write_json(out, report)
    print(json.dumps({"ok": False, "out": str(out)}, ensure_ascii=False))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

