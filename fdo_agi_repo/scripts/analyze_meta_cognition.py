#!/usr/bin/env python3
"""
Meta-Cognition Analysis Script

Scans resonance_ledger.jsonl for meta-cognition events and summarizes:
- counts by level (critical/warning)
- sources (enhanced_binoche/legacy_ensemble)
- recent top items for operator attention

Usage:
  python analyze_meta_cognition.py --hours 24 --out outputs/meta_cognition_latest.json
"""
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import Dict, List, Any

EVENT_KEYS = {"meta_cognition_warning", "meta_cognition_low_confidence"}


def parse_timestamp(ts_str: str) -> datetime:
    try:
        return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
    except Exception:
        return datetime.now()


def load_events(ledger: Path, hours: int) -> List[Dict[str, Any]]:
    cutoff = datetime.now() - timedelta(hours=hours)
    items = []
    if not ledger.exists():
        print(f"❌ Ledger not found: {ledger}")
        return items
    with open(ledger, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                row = json.loads(line.strip())
                if row.get("event") in EVENT_KEYS:
                    ts = parse_timestamp(row.get("timestamp", ""))
                    if ts > cutoff:
                        items.append(row)
            except json.JSONDecodeError:
                continue
    return items


def analyze(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not items:
        return {
            "total": 0,
            "levels": {},
            "sources": {},
            "by_pattern": {},
            "recent": [],
            "message": "No meta-cognition events in window"
        }

    levels = Counter(i.get("level", "unknown") for i in items)
    sources = Counter(i.get("source", "unknown") for i in items)
    by_pattern = Counter(i.get("bqi_pattern", "unknown") for i in items)

    # recent top 10 by severity then confidence ascending
    def sev(i):
        return 0 if i.get("level") == "critical" else 1
    recent = sorted(items, key=lambda x: (sev(x), x.get("confidence", 1.0)))[:10]

    return {
        "total": len(items),
        "levels": dict(levels),
        "sources": dict(sources),
        "by_pattern": dict(by_pattern),
        "recent": recent,
    }


def render_markdown(analysis: Dict[str, Any], hours: int) -> str:
    lines = [
        f"# Meta-Cognition Report ({hours}h)",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Summary",
        f"- Total events: {analysis.get('total', 0)}",
    ]
    levels = analysis.get("levels", {})
    if levels:
        lines.append("- Levels:")
        for k, v in levels.items():
            lines.append(f"  - {k}: {v}")
    sources = analysis.get("sources", {})
    if sources:
        lines.append("- Sources:")
        for k, v in sources.items():
            lines.append(f"  - {k}: {v}")
    lines.append("")

    recent = analysis.get("recent", [])
    if recent:
        lines.extend(["## Recent (Top 10)", ""]) 
        for i, r in enumerate(recent, 1):
            lines.append(f"### {i}. Task {r.get('task_id')}")
            lines.append(f"- Level: {r.get('level')}")
            lines.append(f"- Source: {r.get('source')}")
            lines.append(f"- Action: {r.get('action', r.get('decision'))}")
            lines.append(f"- Confidence: {r.get('confidence')}")
            lines.append(f"- Pattern: {r.get('bqi_pattern')}")
            if r.get('reason'):
                lines.append(f"- Reason: {r.get('reason')}")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Analyze meta-cognition events")
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--ledger", type=str, default="D:/nas_backup/fdo_agi_repo/memory/resonance_ledger.jsonl")
    parser.add_argument("--out", type=str, help="Output JSON file")
    args = parser.parse_args()

    ledger = Path(args.ledger)
    rows = load_events(ledger, args.hours)
    res = analyze(rows)

    print(f"\n✅ Meta-Cognition Analysis: {res.get('total',0)} events in last {args.hours}h")
    if res.get("total", 0) == 0:
        print("   Hint: ensure pipeline is running and generating decisions.")

    # write markdown
    md = render_markdown(res, args.hours)
    md_path = Path("outputs/meta_cognition_report_latest.md")
    md_path.parent.mkdir(exist_ok=True)
    md_path.write_text(md, encoding="utf-8")
    print(f"   Markdown saved: {md_path}")

    # optional JSON
    if args.out:
        out = Path(args.out)
        out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"   JSON saved: {out}")


if __name__ == "__main__":
    main()
