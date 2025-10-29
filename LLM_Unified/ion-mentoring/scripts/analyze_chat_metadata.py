#!/usr/bin/env python
"""
ChatResponse metadata analyzer.

이 스크립트는 `/chat` API 응답(JSONL 형식)을 읽어
페르소나 분포, Phase Snapshot, RUNE 품질 지표를 집계합니다.

Usage:
    python scripts/analyze_chat_metadata.py --input responses.jsonl
    cat responses.jsonl | python scripts/analyze_chat_metadata.py
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from typing import Any, Dict, Iterable, Optional


def load_records(handle: Iterable[str]) -> Iterable[Dict[str, Any]]:
    """Yield parsed JSON objects per line; ignore blanks and malformed entries."""
    for line in handle:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        yield record


def summarize(records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute aggregate statistics from ChatResponse records."""
    persona_counter: Counter[str] = Counter()
    phase_counter: Counter[str] = Counter()
    rune_qualities: list[float] = []
    rune_regenerates = 0
    total_records = 0

    for record in records:
        total_records += 1

        persona_counter.update([record.get("persona_used", "UNKNOWN")])

        metadata: Dict[str, Any] = record.get("metadata") or {}

        phase = metadata.get("phase") or {}
        phase_label = phase.get("phase_label", "unknown")
        phase_counter.update([phase_label])

        rune = metadata.get("rune") or {}
        quality = rune.get("overall_quality")
        if isinstance(quality, (int, float)):
            rune_qualities.append(float(quality))
        if rune.get("regenerate"):
            rune_regenerates += 1

    average_quality: Optional[float] = statistics.fmean(rune_qualities) if rune_qualities else None

    return {
        "total_records": total_records,
        "persona_distribution": persona_counter,
        "phase_distribution": phase_counter,
        "rune_quality_average": average_quality,
        "rune_regenerate_count": rune_regenerates,
    }


def format_summary(summary: Dict[str, Any], output_json: bool = False) -> str:
    """Convert summary dictionary to text or JSON string."""
    if output_json:
        serialisable = {
            "total_records": summary["total_records"],
            "persona_distribution": dict(summary["persona_distribution"]),
            "phase_distribution": dict(summary["phase_distribution"]),
            "rune_quality_average": summary["rune_quality_average"],
            "rune_regenerate_count": summary["rune_regenerate_count"],
        }
        return json.dumps(serialisable, ensure_ascii=False, indent=2)

    lines = [
        "=== ChatResponse Metadata Summary ===",
        f"Total records: {summary['total_records']}",
        "",
        "Persona distribution:",
    ]
    for persona, count in summary["persona_distribution"].most_common():
        lines.append(f"  - {persona}: {count}")

    lines.append("")
    lines.append("Phase distribution:")
    for phase, count in summary["phase_distribution"].most_common():
        lines.append(f"  - {phase}: {count}")

    avg_quality = summary["rune_quality_average"]
    lines.append("")
    if avg_quality is not None:
        lines.append(f"Average RUNE quality: {avg_quality:.3f}")
    else:
        lines.append("Average RUNE quality: N/A")
    lines.append(f"RUNE regenerate count: {summary['rune_regenerate_count']}")

    return "\n".join(lines)


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        help="JSONL input file (default: stdin)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output summary in JSON format",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    if args.input:
        with open(args.input, "r", encoding="utf-8") as handle:
            summary = summarize(load_records(handle))
    else:
        summary = summarize(load_records(sys.stdin))

    output = format_summary(summary, output_json=args.json)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
