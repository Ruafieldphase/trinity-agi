#!/usr/bin/env python3
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def main() -> int:
    workspace_root = Path(__file__).resolve().parents[1]
    outputs = workspace_root / "outputs"
    state_path = outputs / "sync_cache" / "exploration_hint_state.json"
    out_path = outputs / "bridge" / "exploration_hint_latest.json"

    state = _load_json(state_path)
    last_ts = float(state.get("last_emit_epoch") or 0.0)
    now = time.time()
    if now - last_ts < 1800:
        return 0

    internal = _load_json(workspace_root / "memory" / "agi_internal_state.json")
    thought = _load_json(workspace_root / "outputs" / "thought_stream_latest.json")

    boredom = float(internal.get("boredom", 0.0) or 0.0)
    curiosity = float(internal.get("curiosity", 0.0) or 0.0)
    phase = str((thought.get("state") or {}).get("phase") or "")

    if not (boredom >= 0.9 and curiosity <= 0.1):
        return 0

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "boredom": round(boredom, 3),
        "curiosity": round(curiosity, 3),
        "phase": phase,
        "hints": [
            "Try a low-effort stimulus intake (short clip, quick scan).",
            "Prefer lightweight exploration to avoid breaking focus.",
            "Record the result and close the loop quickly.",
        ],
        "source": "auto_hint",
    }

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({"last_emit_epoch": now}, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0
    except Exception:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
