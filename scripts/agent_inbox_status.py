#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Inbox Status (v1)

목적
- 외부 에이전트(시안/세나)가 전달한 산출물이 '도착했는지/언제 도착했는지'를
  비노체가 로그/터미널 탐색 없이 확인할 수 있도록 outputs에 고정한다.

특징
- 네트워크/모델 호출 없음
- 원문 덤프 없음(파일명/mtime/크기 같은 메타만)
- 항상 파일을 생성(ok:false라도)
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _atomic_write_json(path: Path, obj: Dict[str, Any]) -> None:
    _atomic_write_text(path, json.dumps(obj, ensure_ascii=False, indent=2))


def _file_meta(ws: Path, p: Path) -> Dict[str, Any]:
    st = p.stat()
    rel = None
    try:
        rel = p.resolve().relative_to(ws.resolve()).as_posix()
    except Exception:
        rel = str(p)
    return {
        "relpath": rel,
        "mtime": float(st.st_mtime),
        "mtime_iso": utc_iso(st.st_mtime),
        "size": int(st.st_size),
    }


def _scan_dir(ws: Path, root: Path, max_items: int = 25) -> Dict[str, Any]:
    if not root.exists():
        return {"exists": False, "path": str(root), "files": [], "file_count": 0}
    files: List[Path] = []
    try:
        files = [p for p in root.rglob("*") if p.is_file()]
    except Exception:
        files = []
    files_sorted = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)
    latest = _file_meta(ws, files_sorted[0]) if files_sorted else None
    sample = [_file_meta(ws, p) for p in files_sorted[:max_items]]
    return {
        "exists": True,
        "path": str(root),
        "file_count": len(files),
        "latest": latest,
        "latest_5": sample[:5],
        "files": sample,
    }


def render_text(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("AGI Agent Inbox Status")
    lines.append(f"generated_at: {report.get('generated_at')}")
    lines.append("")
    agents = report.get("agents") if isinstance(report.get("agents"), dict) else {}
    for name in ("antigravity_sian", "claude_sena"):
        a = agents.get(name) if isinstance(agents.get(name), dict) else {}
        lines.append(f"[{name}]")
        if not a.get("exists"):
            lines.append("  - missing")
            lines.append("")
            continue
        lines.append(f"  - file_count: {a.get('file_count')}")
        latest = a.get("latest") if isinstance(a.get("latest"), dict) else None
        if latest:
            lines.append(f"  - latest: {latest.get('relpath')} ({latest.get('mtime_iso')})")
        else:
            lines.append("  - latest: -")
        lines.append("")
    return "\n".join(lines) + "\n"


def build_report(ws: Path) -> Dict[str, Any]:
    now = time.time()
    inbox = ws / "inputs" / "agent_inbox"
    report: Dict[str, Any] = {
        "ok": True,
        "version": "agent_inbox_status_v1",
        "generated_at": utc_iso(now),
        "agents": {},
        "note": "에이전트 인박스의 파일 메타만 기록한다(원문/PII 저장 금지).",
    }
    try:
        report["agents"]["antigravity_sian"] = _scan_dir(ws, inbox / "antigravity_sian")
        report["agents"]["claude_sena"] = _scan_dir(ws, inbox / "claude_sena")
    except Exception as e:
        report["ok"] = False
        report["error"] = str(e)
    return report


def main() -> int:
    ws = Path(__file__).resolve().parents[1]
    out_json = ws / "outputs" / "agent_inbox_status_latest.json"
    out_txt = ws / "outputs" / "agent_inbox_status_latest.txt"
    hist = ws / "outputs" / "agent_inbox_status_history.jsonl"

    report = build_report(ws)
    _atomic_write_json(out_json, report)
    _atomic_write_text(out_txt, render_text(report))
    try:
        hist.parent.mkdir(parents=True, exist_ok=True)
        with hist.open("a", encoding="utf-8") as f:
            f.write(json.dumps(report, ensure_ascii=False) + "\n")
    except Exception:
        pass

    print(json.dumps({"ok": bool(report.get("ok")), "out": str(out_json)}, ensure_ascii=False))
    return 0 if report.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())

