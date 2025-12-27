#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visualize Trinity Manifold (stub v1)

문서 참조 복구용 최소 스크립트.
- 그래프/시각화 대신, 최신 Trinity 권장사항을 요약 MD로 고정한다.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> int:
    ws = Path(__file__).resolve().parents[1]
    src = ws / "outputs" / "trinity_synthesis_latest.json"
    out_md = ws / "outputs" / "trinity_manifold_latest.md"
    out_json = ws / "outputs" / "trinity_manifold_latest.json"
    now = time.time()

    data = _load_json(src) if src.exists() else {}
    recs = data.get("recommendations") if isinstance(data.get("recommendations"), list) else []

    report = {
        "ok": True,
        "version": "trinity_manifold_stub_v1",
        "generated_at": utc_iso(now),
        "source": {"path": str(src), "exists": src.exists()},
        "recommendations_count": len(recs),
    }
    _atomic_write_text(out_json, json.dumps(report, ensure_ascii=False, indent=2))

    lines: List[str] = []
    lines.append("# Trinity Manifold (stub)")
    lines.append("")
    lines.append(f"- generated_at: `{report['generated_at']}`")
    lines.append(f"- source: `{report['source']['path']}` exists={report['source']['exists']}")
    lines.append(f"- recommendations: `{report['recommendations_count']}`")
    lines.append("")
    if recs:
        lines.append("## Recommendations")
        for r in recs[:30]:
            title = (r.get("title") if isinstance(r, dict) else None) or "-"
            pri = (r.get("priority") if isinstance(r, dict) else None) or "LOW"
            lines.append(f"- [{pri}] {title}")
    else:
        lines.append("## Recommendations")
        lines.append("- (none)")
    _atomic_write_text(out_md, "\n".join(lines) + "\n")

    print(json.dumps({"ok": True, "out_md": str(out_md), "out_json": str(out_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

