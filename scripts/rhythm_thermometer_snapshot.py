#!/usr/bin/env python3
import json
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    workspace_root = Path(__file__).resolve().parents[1]
    script = workspace_root / "scripts" / "rhythm_check.py"
    out_path = workspace_root / "outputs" / "bridge" / "rhythm_thermometer_latest.json"

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "error",
        "error": "unknown",
    }

    if not script.exists():
        payload["error"] = "missing_rhythm_check"
    else:
        try:
            proc = subprocess.run(
                [sys.executable, str(script), "--json"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
                cwd=workspace_root,
            )
            if proc.returncode == 0:
                payload = json.loads(proc.stdout)
            else:
                payload["error"] = "rhythm_check_failed"
                payload["stderr"] = (proc.stderr or "").strip()[:800]
        except Exception as exc:
            payload["error"] = f"exception:{exc.__class__.__name__}"

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0
    except Exception:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
