#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binoche_Observer Persona Learner (stub v1)

문서 참조 복구 + 최소한의 "데이터 존재 확인"만 수행한다.
- 원문 저장/전송 없이 파일 개수/mtime만 요약해 outputs에 고정.
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
    src = ws / "ai_binoche_conversation_origin" / "Core"
    out = ws / "outputs" / "rune" / "binoche_persona_learner_latest.json"
    now = time.time()

    md_files = sorted(src.glob("*.md")) if src.exists() else []
    newest = None
    if md_files:
        newest_p = max(md_files, key=lambda p: p.stat().st_mtime)
        newest = {"relpath": str(newest_p.relative_to(ws)).replace("\\", "/"), "mtime_iso": utc_iso(newest_p.stat().st_mtime)}

    report = {
        "ok": True,
        "version": "binoche_persona_learner_stub_v1",
        "generated_at": utc_iso(now),
        "source": {"path": str(src), "exists": src.exists(), "md_count": len(md_files), "newest": newest},
        "note": "Stub: no learning performed. This output only confirms source visibility and freshness.",
    }
    _atomic_write_json(out, report)
    print(json.dumps({"ok": True, "out": str(out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

