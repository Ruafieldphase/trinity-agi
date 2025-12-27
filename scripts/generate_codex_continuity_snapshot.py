#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path


def _read_text(path: Path, limit: int) -> str:
    try:
        if not path.exists():
            return ""
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        if not text:
            return ""
        return text[:limit]
    except Exception:
        return ""


def _read_json_summary(path: Path, limit: int) -> str:
    try:
        if not path.exists():
            return ""
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return ""
    try:
        preview = json.dumps(data, ensure_ascii=False, indent=2)
        return preview[:limit]
    except Exception:
        return ""


def main() -> int:
    workspace_root = Path(__file__).resolve().parents[1]
    outputs = workspace_root / "outputs"
    snapshot_path = outputs / "sync_cache" / "codex_continuity_snapshot.md"
    max_chars = 6000
    per_source_limit = 1400

    sources = [
        ("agent_brief", outputs / "coordination" / "agent_brief_latest.md"),
        ("session_continuity", outputs / "session_continuity_latest.md"),
        ("copilot_context", outputs / ".copilot_context_summary.md"),
        ("trigger_report", outputs / "bridge" / "trigger_report_latest.txt"),
        ("system_gaps", outputs / "bridge" / "system_gaps_report_latest.txt"),
        ("antigravity_intake", outputs / "antigravity_intake_latest.json"),
    ]

    lines = []
    lines.append("# Codex Continuity Snapshot")
    lines.append("")
    lines.append(f"updated_utc: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")

    for label, path in sources:
        if path.suffix.lower() == ".json":
            body = _read_json_summary(path, per_source_limit)
        else:
            body = _read_text(path, per_source_limit)
        if not body:
            continue
        lines.append(f"[{label}] {path}")
        lines.append(body)
        lines.append("")

    content = "\n".join(lines).strip()
    if len(content) > max_chars:
        content = content[:max_chars]

    try:
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(content, encoding="utf-8")
        return 0
    except Exception:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
