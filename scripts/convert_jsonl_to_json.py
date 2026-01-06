from __future__ import annotations

"""
Utility script to convert a Lubit system run JSONL log into the
structured JSON format expected by visualize_lubit_data.py.

Usage:
    python scripts/convert_jsonl_to_json.py \
        --input docs/phase_injection_paper/system_c_run_20251014.jsonl \
        --output docs/phase_injection_paper/system_c_run_20251014_converted.json
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Lubit JSONL log into visualize_lubit_data format."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to JSONL log produced by persona_orchestrator.py.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Destination JSON file (loops/events structure).",
    )
    parser.add_argument(
        "--loop-period",
        type=int,
        default=280,
        help="Loop period in seconds. Default: 280.",
    )
    return parser.parse_args()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    lines: List[Dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            lines.append(json.loads(raw))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse line: {raw[:80]}...") from exc
    return lines


def convert(events: List[Dict[str, Any]], loop_period: int) -> Dict[str, Any]:
    cycles: List[Dict[str, Any]] = []
    current_cycle: Optional[Dict[str, Any]] = None

    for event in events:
        phase = event.get("phase", {})
        loop_index = phase.get("loop_count")
        if loop_index is None:
            continue

        if current_cycle is None or current_cycle["loop"] != loop_index:
            current_cycle = {
                "loop": loop_index,
                "phase": phase.get("phase_name", "run"),
                "start": event.get("timestamp"),
                "events": [],
            }
            cycles.append(current_cycle)

        persona = event.get("persona", {}).get("id")
        entry = {
            "time": event.get("timestamp"),
            "event": persona,
            "affect": phase.get("affect_after"),
            "response_complexity": event.get("response_complexity", {}),
            "stability": phase.get("stability"),
            "strategy": phase.get("strategy"),
        }
        current_cycle["events"].append(entry)

    payload: Dict[str, Any] = {
        "generated_at": cycles[0]["start"] if cycles else None,
        "loop_period_seconds": loop_period,
        "cycles": cycles,
    }
    return payload


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input}")

    events = load_jsonl(args.input)
    payload = convert(events, loop_period=args.loop_period)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Converted {args.input} → {args.output}")


if __name__ == "__main__":
    main()
