#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path
from workspace_root import get_workspace_root


def _read_snippet(path: Path, limit: int = 1200) -> str:
    if not path.exists():
        return ""
    try:
        if path.suffix.lower() == ".json":
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            text = json.dumps(data, ensure_ascii=False, indent=2)
        else:
            text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    text = (text or "").strip()
    if not text:
        return ""
    return text[:limit]


def main() -> int:
    workspace_root = get_workspace_root()
    outputs = workspace_root / "outputs"
    bridge = outputs / "bridge"
    out_path = bridge / "live_ops_dashboard.html"

    sources = [
        ("Rhythm Thermometer", bridge / "rhythm_thermometer_latest.json"),
        ("Trigger Report", bridge / "trigger_report_latest.json"),
        ("System Gaps", bridge / "system_gaps_report_latest.json"),
        ("Session Continuity", outputs / "session_continuity_latest.md"),
        ("Agent Brief", outputs / "coordination" / "agent_brief_latest.md"),
    ]

    sections = []
    for title, path in sources:
        snippet = _read_snippet(path)
        if not snippet:
            continue
        sections.append(f"<section><h2>{title}</h2><pre>{snippet}</pre></section>")

    updated = datetime.now(timezone.utc).isoformat()
    body = "\n".join(sections) if sections else "<p>No data available.</p>"

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Live Ops Dashboard</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #1a1a1a; }}
    h1 {{ margin-bottom: 4px; }}
    h2 {{ margin-top: 24px; }}
    pre {{ background: #f6f6f6; padding: 12px; white-space: pre-wrap; }}
    .meta {{ color: #555; font-size: 12px; }}
  </style>
</head>
<body>
  <h1>Live Ops Dashboard</h1>
  <div class="meta">updated_utc: {updated}</div>
  {body}
</body>
</html>
"""

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        return 0
    except Exception:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
