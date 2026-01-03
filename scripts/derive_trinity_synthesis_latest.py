#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trinity Synthesis Deriver (v1)

목적
- `outputs/core_enhanced_synthesis_latest.md`에서 사람이 읽는 권장사항을 추출해
  `outputs/trinity_synthesis_latest.json`로 고정한다.

배경
- `scripts/load_trinity_feedback.py`는 `outputs/trinity_synthesis_latest.json`을 기대한다.
- 기존 Trinity 사이클은 Core 산출물은 있으나, 위 파일이 항상 생성되지는 않았다.

제약
- 외부 네트워크/모델 호출 없이 로컬 파일만 사용한다.
- 실패해도 예외를 던지지 않고, `ok:false`로 반환한다.
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from workspace_root import get_workspace_root


def utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _atomic_write_json(path: Path, obj: Dict[str, Any]) -> None:
    _atomic_write_text(path, json.dumps(obj, ensure_ascii=False, indent=2))


def _strip_md(s: str) -> str:
    s = s.strip()
    s = re.sub(r"`([^`]+)`", r"\1", s)
    s = s.replace("**", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _parse_core_md(md_text: str) -> List[Dict[str, Any]]:
    lines = md_text.splitlines()
    recs: List[Dict[str, Any]] = []

    insight_header = re.compile(r"^###\s+.*\b(HIGH|MEDIUM|LOW)\b\s*-\s*([A-Za-z0-9_.-]+)\s*$", re.IGNORECASE)
    for idx, ln in enumerate(lines):
        m = insight_header.match(ln.strip())
        if not m:
            continue
        priority = m.group(1).upper()
        tag = m.group(2)
        title: Optional[str] = None
        for nxt in lines[idx + 1 : idx + 12]:
            s = nxt.strip()
            if s.startswith("**") and s.endswith("**") and len(s) >= 4:
                title = _strip_md(s)
                break
        if title:
            recs.append({"title": title, "priority": priority, "tags": [tag], "source": "core_md_insight"})

    in_actions = False
    for ln in lines:
        s = ln.strip()
        if s.startswith("##") and "실행 가능한 권장사항" in s:
            in_actions = True
            continue
        if in_actions and s.startswith("##") and "실행 가능한 권장사항" not in s:
            break
        if not in_actions:
            continue
        m = re.match(r"^\d+\.\s*(.+)$", s)
        if m:
            title = _strip_md(m.group(1))
            if title:
                recs.append({"title": title, "priority": "HIGH", "tags": ["actionable"], "source": "core_md_action"})

    pr_rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    merged: Dict[str, Dict[str, Any]] = {}
    for r in recs:
        t = r.get("title") or ""
        if not t:
            continue
        cur = merged.get(t)
        if not cur:
            merged[t] = r
            continue
        if pr_rank.get(r.get("priority", "LOW"), 1) > pr_rank.get(cur.get("priority", "LOW"), 1):
            merged[t] = r
        else:
            tags = set((cur.get("tags") or []) + (r.get("tags") or []))
            cur["tags"] = sorted(tags)
            merged[t] = cur

    return list(merged.values())


def build_trinity_synthesis(workspace: Path) -> Dict[str, Any]:
    now = time.time()
    out_path = workspace / "outputs" / "trinity_synthesis_latest.json"
    src_md = workspace / "outputs" / "core_enhanced_synthesis_latest.md"
    src_json = workspace / "outputs" / "core_enhanced_synthesis_latest.json"

    sources: Dict[str, Any] = {}
    try:
        if src_md.exists():
            st = src_md.stat()
            sources["core_md"] = {"path": str(src_md), "mtime_iso": utc_iso(st.st_mtime), "size": st.st_size}
        if src_json.exists():
            st = src_json.stat()
            sources["core_json"] = {"path": str(src_json), "mtime_iso": utc_iso(st.st_mtime), "size": st.st_size}
    except Exception:
        pass

    if not src_md.exists() and not src_json.exists():
        return {
            "ok": False,
            "version": "trinity_synthesis_from_core_v1",
            "generated_at": utc_iso(now),
            "sources": sources,
            "recommendations": [],
            "error": "missing_core_enhanced_synthesis_latest.(md|json)",
        }

    try:
        if src_md.exists():
            md_text = src_md.read_text(encoding="utf-8", errors="replace")
            recs = _parse_core_md(md_text)
        else:
            recs = []
    except Exception as e:
        return {
            "ok": False,
            "version": "trinity_synthesis_from_core_v1",
            "generated_at": utc_iso(now),
            "sources": sources,
            "recommendations": [],
            "error": f"parse_failed:{e}",
        }

    report: Dict[str, Any] = {
        "ok": True,
        "version": "trinity_synthesis_from_core_v1",
        "generated_at": utc_iso(now),
        "sources": sources,
        "recommendations": sorted(
            recs,
            key=lambda r: (
                {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(r.get("priority", "LOW"), 9),
                r.get("title", ""),
            ),
        ),
        "note": "이 파일은 Core 통합 보고서에서 '권장사항'을 추출한 파생 산출물이며, load_trinity_feedback.py 소비를 위해 존재한다.",
    }

    try:
        _atomic_write_json(out_path, report)
        report["output"] = {"path": str(out_path), "mtime_iso": utc_iso(out_path.stat().st_mtime)}
    except Exception as e:
        report["ok"] = False
        report["error"] = f"write_failed:{e}"
    return report


def main() -> int:
    workspace = get_workspace_root()
    report = build_trinity_synthesis(workspace)
    print(json.dumps({"ok": bool(report.get("ok")), "out": str(workspace / "outputs" / "trinity_synthesis_latest.json")}, ensure_ascii=False))
    return 0 if report.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())

