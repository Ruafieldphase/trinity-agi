#!/usr/bin/env python3
import json
import sys
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


def _fallback_state(workspace_root: Path) -> Dict[str, Any]:
    internal = _load_json(workspace_root / "memory" / "agi_internal_state.json")
    thought = _load_json(workspace_root / "outputs" / "thought_stream_latest.json")

    energy = float(internal.get("energy", 0.5) or 0.5)
    boredom = float(internal.get("boredom", 0.0) or 0.0)
    curiosity = float(internal.get("curiosity", 0.0) or 0.0)
    atp = float((thought.get("state") or {}).get("atp", 50.0) or 50.0)

    fear_level = 0.4 + max(0.0, 0.6 - energy) * 0.3 + min(1.0, boredom) * 0.2
    fear_level = max(0.1, min(0.9, fear_level))
    strategy = "RECOVERY" if energy < 0.35 or boredom > 0.8 else "STEADY"

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fear": {"level": round(fear_level, 3), "reasons": ["fallback"]},
        "strategy": strategy,
        "body_signals": {
            "energy": round(energy, 3),
            "boredom": round(boredom, 3),
            "curiosity": round(curiosity, 3),
            "atp": round(atp, 2),
        },
        "background_self": {
            "interpretation": "fallback_estimate",
            "strategy": strategy,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "recommended_actions": ["observe", "stabilize"],
        "source": "fallback",
    }


def _build_lumen_state(workspace_root: Path) -> Dict[str, Any]:
    try:
        from fdo_agi_repo.orchestrator.lumen_system import LumenSystem
    except Exception:
        return _fallback_state(workspace_root)

    try:
        lumen = LumenSystem(workspace_root=workspace_root)
        result = lumen.process_emotion_signal()
        background = result.get("background_self", {})
        fear_signal = result.get("fear_signal", {})
        payload = {
            "timestamp": result.get("timestamp") or datetime.now(timezone.utc).isoformat(),
            "fear": {
                "level": fear_signal.get("level", 0.4),
                "reasons": fear_signal.get("reasons", []),
            },
            "strategy": background.get("strategy", "STEADY"),
            "body_signals": result.get("body_signals", {}),
            "background_self": background,
            "recommended_actions": result.get("recommended_actions", []),
            "source": "lumen_system",
        }
        return payload
    except Exception:
        return _fallback_state(workspace_root)


def _write_json(path: Path, payload: Dict[str, Any]) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def main() -> int:
    workspace_root = Path(__file__).resolve().parents[1]
    if str(workspace_root) not in sys.path:
        sys.path.append(str(workspace_root))
    payload = _build_lumen_state(workspace_root)

    outputs_path = workspace_root / "outputs" / "lumen_state.json"
    memory_path = workspace_root / "fdo_agi_repo" / "memory" / "lumen_state.json"

    ok_outputs = _write_json(outputs_path, payload)
    ok_memory = _write_json(memory_path, payload)

    return 0 if ok_outputs or ok_memory else 1


if __name__ == "__main__":
    raise SystemExit(main())
