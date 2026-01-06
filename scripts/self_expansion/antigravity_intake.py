#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Intake (read-only)

목표:
- AntiGravity 쪽(예: Google AI Studio/antigravity agent)이 생성한 산출물 디렉터리
  `~/.gemini/antigravity/brain/` 를 읽어, 사람이 볼 수 있는 요약/메타데이터를
  워크스페이스 `outputs/` 아래로 고정한다.
- "구현은 AntiGravity, 연결/보고는 루빛" 분리를 안정적으로 지원한다.

중요:
- 기본은 read-only 인테이크(워크스페이스 core memory에 쓰지 않음)
- 외부 네트워크 사용 없음

출력:
- `<workspace>/outputs/antigravity_intake_latest.json`
- `<workspace>/outputs/antigravity_intake_history.jsonl`
"""

from __future__ import annotations

import argparse
import json
import os
import time
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import sys
from workspace_root import get_workspace_root
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))



def utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def safe_read_text(path: Path, limit: int = 1200) -> str:
    try:
        s = path.read_text(encoding="utf-8", errors="replace")[: max(0, int(limit))]
        # Best-effort redaction (avoid leaking PII/links/paths into outputs)
        s = re.sub(r"https?://[^\s)\]]+", "[REDACTED_URL]", s, flags=re.IGNORECASE)
        s = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", s)
        # Windows paths (redact user/home-ish)
        s = re.sub(r"\b[A-Za-z]:\\Users\\[^\s]+", "[REDACTED_PATH]", s, flags=re.IGNORECASE)
        s = re.sub(r"\b[A-Za-z]:\\[^\s]+", "[REDACTED_PATH]", s)
        # Linux/Mac paths
        s = re.sub(r"/(home|Users|var|etc|opt|tmp|usr)/[^\s]+", "[REDACTED_PATH]", s)
        return s
    except Exception:
        return ""


@dataclass
class AntigravityArtifact:
    name: str
    relpath: str
    size: int
    mtime: float
    mtime_iso: str
    preview: str


@dataclass
class AntigravitySession:
    session_id: str
    path: str
    mtime: float
    mtime_iso: str
    artifacts: list[AntigravityArtifact]
    completed_tasks: list[str]


def extract_completed_tasks(task_md: Path, max_items: int = 20) -> list[str]:
    items: list[str] = []
    try:
        with task_md.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                s = line.strip()
                if s.startswith("- [x]"):
                    txt = s[6:].strip()
                    if txt:
                        items.append(txt)
                if len(items) >= max_items:
                    break
    except Exception:
        return items
    return items


def load_latest(latest_path: Path) -> dict[str, Any]:
    if not latest_path.exists():
        return {}
    try:
        obj = json.loads(latest_path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def run_antigravity_intake(workspace_root: Path) -> dict[str, Any]:
    workspace_root = workspace_root.resolve()
    out_latest = workspace_root / "outputs" / "antigravity_intake_latest.json"
    prev = load_latest(out_latest)
    prev_id = str(prev.get("latest_session_id") or "")

    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    if not brain_dir.exists():
        return {
            "ok": True,
            "scanned_at": utc_iso(time.time()),
            "brain_dir": str(brain_dir),
            "exists": False,
            "session_count": 0,
            "latest_session_id": None,
            "new_session_detected": False,
            "sessions": [],
            "note": "No ~/.gemini/antigravity/brain found on this host.",
        }

    session_dirs: list[Path] = []
    try:
        for d in brain_dir.iterdir():
            try:
                if d.is_dir():
                    session_dirs.append(d)
            except Exception:
                continue
    except Exception:
        session_dirs = []

    # newest first
    session_dirs.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0.0, reverse=True)

    sessions: list[AntigravitySession] = []
    for d in session_dirs[:50]:
        try:
            mtime = float(d.stat().st_mtime)
        except Exception:
            mtime = 0.0

        artifacts: list[AntigravityArtifact] = []
        for name in ("task.md", "implementation_plan.md", "walkthrough.md"):
            p = d / name
            if not p.exists():
                continue
            try:
                st = p.stat()
                artifacts.append(
                    AntigravityArtifact(
                        name=name,
                        relpath=str(p.relative_to(brain_dir)),
                        size=int(st.st_size),
                        mtime=float(st.st_mtime),
                        mtime_iso=utc_iso(float(st.st_mtime)),
                        preview=safe_read_text(p, limit=900),
                    )
                )
            except Exception:
                continue

        task_md = d / "task.md"
        completed = extract_completed_tasks(task_md) if task_md.exists() else []
        sessions.append(
            AntigravitySession(
                session_id=d.name,
                path=str(d),
                mtime=mtime,
                mtime_iso=utc_iso(mtime) if mtime else "",
                artifacts=artifacts,
                completed_tasks=completed,
            )
        )

    latest = sessions[0] if sessions else None
    latest_id = latest.session_id if latest else None
    new_session = bool(latest_id and latest_id != prev_id)

    now = time.time()
    return {
        "ok": True,
        "scanned_at": utc_iso(now),
        "brain_dir": str(brain_dir),
        "exists": True,
        "session_count": len(session_dirs),
        "latest_session_id": latest_id,
        "new_session_detected": new_session,
        "latest": asdict(latest) if latest else None,
        "sessions": [asdict(s) for s in sessions[:10]],
        "note": "sessions에는 최신 10개만 포함(요약).",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=str, default=str(get_workspace_root()))
    ap.add_argument("--out", type=str, default=str(Path("outputs") / "antigravity_intake_latest.json"))
    ap.add_argument("--history", type=str, default=str(Path("outputs") / "antigravity_intake_history.jsonl"))
    args = ap.parse_args()

    workspace_root = Path(args.workspace).resolve()
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = (workspace_root / out_path).resolve()
    hist_path = Path(args.history)
    if not hist_path.is_absolute():
        hist_path = (workspace_root / hist_path).resolve()

    result = run_antigravity_intake(workspace_root)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        with hist_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
    except Exception:
        pass

    print(json.dumps({"ok": True, "out": str(out_path), "latest_session_id": result.get("latest_session_id")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
