#!/usr/bin/env python3
"""
LDPM v0.1 Multivariate Resonance summarizer.

- Loads the resonance ledger (default: fdo_agi_repo/memory/resonance_ledger.jsonl)
- Filters events by participants / order / resonance_key
- Produces aggregate statistics (count, average synergy, participants breakdown)
- Writes JSON + Markdown summary

This is a lightweight skeleton to support further development.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List


def load_ledger(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or not line.startswith("{"):
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def filter_events(
    events: Iterable[Dict[str, Any]],
    key: str,
    min_order: int,
    participants_filter: List[str] | None,
) -> List[Dict[str, Any]]:
    selected: List[Dict[str, Any]] = []
    for evt in events:
        if evt.get("resonance_key") != key:
            continue
        order = evt.get("order")
        if min_order and (not isinstance(order, int) or order < min_order):
            continue
        participants = evt.get("participants") or []
        if participants_filter:
            # require that all filter participants are present
            if not set(participants_filter).issubset(set(participants)):
                continue
        selected.append(evt)
    return selected


def summarize(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    count = len(events)
    if count == 0:
        return {
            "count": 0,
            "order_stats": {},
            "participant_stats": {},
            "avg_synergy": None,
        }

    order_counter: Counter[int] = Counter()
    participant_counter: Counter[str] = Counter()
    synergy_values: List[float] = []

    for evt in events:
        order = evt.get("order")
        if isinstance(order, int):
            order_counter[order] += 1
        participants = evt.get("participants") or []
        for p in participants:
            participant_counter[p] += 1
        metrics = evt.get("metrics") or {}
        sy = metrics.get("synergy_score")
        if isinstance(sy, (int, float)):
            synergy_values.append(float(sy))

    avg_synergy = sum(synergy_values) / len(synergy_values) if synergy_values else None

    return {
        "count": count,
        "order_stats": dict(order_counter),
        "participant_stats": dict(participant_counter),
        "avg_synergy": avg_synergy,
    }


def to_markdown(summary: Dict[str, Any]) -> str:
    lines = ["# Multivariate Resonance Summary", ""]
    lines.append(f"- Events analysed: {summary.get('count', 0)}")
    avg_synergy = summary.get("avg_synergy")
    lines.append(f"- Average synergy score: {avg_synergy if avg_synergy is not None else '-'}")
    lines.append("")

    order_stats = summary.get("order_stats") or {}
    if order_stats:
        lines.append("## Order distribution")
        lines.append("")
        lines.append("| order | count |")
        lines.append("|---:|---:|")
        for order, cnt in sorted(order_stats.items()):
            lines.append(f"| {order} | {cnt} |")
        lines.append("")

    participant_stats = summary.get("participant_stats") or {}
    if participant_stats:
        lines.append("## Participant involvement")
        lines.append("")
        lines.append("| participant | events |")
        lines.append("|---|---:|")
        for name, cnt in sorted(participant_stats.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"| {name} | {cnt} |")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute multivariate resonance summary (LDPM v0.1 skeleton).")
    parser.add_argument(
        "--ledger-in",
        default="fdo_agi_repo/memory/resonance_ledger.jsonl",
        help="Ledger JSONL path.",
    )
    parser.add_argument(
        "--resonance-key",
        default="multi:prism:gaze",
        help="Resonance key filter.",
    )
    parser.add_argument(
        "--min-order",
        type=int,
        default=3,
        help="Minimum order (participants count) to include.",
    )
    parser.add_argument(
        "--participants",
        default="",
        help="Comma-separated participants that must be present (e.g. Core,Binoche_Observer,rio).",
    )
    parser.add_argument(
        "--out-json",
        default="outputs/mv_resonance_summary.json",
        help="Output JSON summary path.",
    )
    parser.add_argument(
        "--out-md",
        default="outputs/mv_resonance_summary.md",
        help="Output Markdown summary path.",
    )
    args = parser.parse_args()

    participants_filter = [p.strip() for p in args.participants.split(",") if p.strip()] or None

    ledger_events = load_ledger(Path(args.ledger_in))
    selected_events = filter_events(
        ledger_events,
        key=args.resonance_key,
        min_order=args.min_order,
        participants_filter=participants_filter,
    )
    summary = summarize(selected_events)

    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_json, "w", encoding="utf-8") as f_json:
        json.dump(summary, f_json, ensure_ascii=False, indent=2)

    md_content = to_markdown(summary)
    with open(args.out_md, "w", encoding="utf-8") as f_md:
        f_md.write(md_content)

    print(f"Analysed {summary['count']} events (min_order={args.min_order}, key={args.resonance_key}).")
    print(f"JSON summary written to {args.out_json}")
    print(f"Markdown summary written to {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

