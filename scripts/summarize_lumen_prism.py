#!/usr/bin/env python3
"""
Summarize Lumen Prism resonance events from the standard ledger.

Outputs a JSON summary and a Markdown report for quick inspection.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from statistics import fmean
from typing import Any, Dict, List, Optional


def load_events(path: Path, key: str) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    if not path.exists():
        return events
    with path.open("r", encoding="utf-8") as ledger:
        for line in ledger:
            line = line.strip()
            if not line or not line.startswith("{"):
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if payload.get("resonance_key") == key:
                events.append(payload)
    return events


def parse_timestamp(ts: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def summarize(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not events:
        return {
            "count": 0,
            "first_timestamp": None,
            "last_timestamp": None,
            "amplification": {},
            "quality_pass_rate": None,
        }

    timestamps = [
        parse_timestamp(evt.get("timestamp", ""))
        for evt in events
        if evt.get("timestamp")
    ]
    timestamps = [ts for ts in timestamps if ts is not None]

    amplifications: List[float] = []
    quality_pass = 0
    for evt in events:
        metrics = evt.get("metrics") or {}
        amp = metrics.get("amplification")
        if isinstance(amp, (int, float)):
            amplifications.append(float(amp))
        if metrics.get("quality_gate") == 1.0:
            quality_pass += 1

    summary: Dict[str, Any] = {
        "count": len(events),
        "first_timestamp": timestamps[0].isoformat() if timestamps else None,
        "last_timestamp": timestamps[-1].isoformat() if timestamps else None,
        "amplification": {},
        "quality_pass_rate": quality_pass / len(events) if events else None,
    }
    if amplifications:
        summary["amplification"] = {
            "min": min(amplifications),
            "avg": fmean(amplifications),
            "max": max(amplifications),
        }
    return summary


def markdown_report(summary: Dict[str, Any], count: int) -> str:
    lines = [
        "# Lumen Prism Ledger Summary",
        "",
        f"- Events analysed: {count}",
        f"- First timestamp: {summary.get('first_timestamp') or '-'}",
        f"- Last timestamp: {summary.get('last_timestamp') or '-'}",
        "",
        "## Amplification",
        "",
        "| metric | value |",
        "|---|---:|",
    ]
    amp = summary.get("amplification") or {}
    lines.append(f"| min | {amp.get('min', '-') if amp else '-'} |")
    lines.append(f"| avg | {amp.get('avg', '-') if amp else '-'} |")
    lines.append(f"| max | {amp.get('max', '-') if amp else '-'} |")
    lines.append("")
    quality = summary.get("quality_pass_rate")
    quality_pct = f"{quality*100:.1f}%" if isinstance(quality, float) else "-"
    lines.append(f"- Quality pass rate: {quality_pct}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize Lumen Prism ledger events.")
    parser.add_argument(
        "--ledger",
        default="fdo_agi_repo/memory/resonance_ledger.jsonl",
        help="Path to the resonance ledger JSONL file.",
    )
    parser.add_argument(
        "--out-json",
        default="outputs/lumen_prism_summary.json",
        help="Path to write the JSON summary.",
    )
    parser.add_argument(
        "--out-md",
        default="outputs/lumen_prism_summary.md",
        help="Path to write the Markdown report.",
    )
    parser.add_argument(
        "--resonance-key",
        default="lumen:prism:gaze",
        help="Resonance key to filter in the ledger.",
    )
    args = parser.parse_args()

    ledger_path = Path(args.ledger)
    events = load_events(ledger_path, args.resonance_key)
    summary = summarize(events)

    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_json, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    report = markdown_report(summary, len(events))
    with open(args.out_md, "w", encoding="utf-8") as fh:
        fh.write(report)

    print(f"Summarized {len(events)} events from {ledger_path}")
    print(f"JSON summary written to {args.out_json}")
    print(f"Markdown report written to {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

