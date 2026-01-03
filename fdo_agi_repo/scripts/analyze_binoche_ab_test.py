#!/usr/bin/env python3
"""
Binoche_Observer A/B Test Analysis Script

Analyzes resonance_ledger.jsonl for binoche_ab_comparison events,
comparing legacy Ensemble vs enhanced BinocheDecisionEngine performance.

Usage:
    python analyze_binoche_ab_test.py [--hours 24] [--out report.json]
"""
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import Dict, List, Any


def parse_timestamp(ts_str: str) -> datetime:
    """Parse ISO timestamp string"""
    try:
        return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
    except:
        return datetime.now()


def load_ab_comparisons(ledger_path: Path, hours: int) -> List[Dict[str, Any]]:
    """Load binoche_ab_comparison events from ledger"""
    cutoff = datetime.now() - timedelta(hours=hours)
    comparisons = []
    
    if not ledger_path.exists():
        print(f"❌ Ledger not found: {ledger_path}")
        return []
    
    with open(ledger_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get("event") == "binoche_ab_comparison":
                    ts = parse_timestamp(entry.get("timestamp", ""))
                    if ts > cutoff:
                        comparisons.append(entry)
            except json.JSONDecodeError:
                continue
    
    return comparisons


def analyze_comparisons(comparisons: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze A/B comparison events"""
    if not comparisons:
        return {
            "total": 0,
            "match_rate": 0.0,
            "message": "No A/B comparison events found"
        }
    
    total = len(comparisons)
    matches = sum(1 for c in comparisons if c.get("decisions_match"))
    match_rate = matches / total if total > 0 else 0.0
    
    # Decision distribution
    legacy_decisions = Counter(c.get("legacy_decision") for c in comparisons)
    enhanced_decisions = Counter(c.get("enhanced_decision") for c in comparisons)
    
    # Confidence comparison
    confidence_diffs = [c.get("confidence_diff", 0.0) for c in comparisons]
    avg_confidence_diff = sum(confidence_diffs) / len(confidence_diffs) if confidence_diffs else 0.0
    
    # Find disagreements
    disagreements = [c for c in comparisons if not c.get("decisions_match")]
    
    return {
        "total": total,
        "matches": matches,
        "match_rate": match_rate,
        "legacy_decisions": dict(legacy_decisions),
        "enhanced_decisions": dict(enhanced_decisions),
        "avg_confidence_diff": avg_confidence_diff,
        "disagreements_count": len(disagreements),
        "disagreements": disagreements[:10]  # Top 10
    }


def generate_report(analysis: Dict[str, Any], hours: int) -> str:
    """Generate markdown report"""
    lines = [
        f"# Binoche_Observer A/B Test Analysis ({hours}h)",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Summary",
        f"- Total comparisons: {analysis['total']}",
        f"- Decision match rate: {analysis['match_rate']:.1%}",
        f"- Disagreements: {analysis['disagreements_count']}",
        f"- Avg confidence diff (enhanced - legacy): {analysis.get('avg_confidence_diff', 0):.3f}",
        "",
        "## Decision Distribution",
        "",
        "### Legacy Ensemble",
    ]
    
    for decision, count in analysis.get("legacy_decisions", {}).items():
        lines.append(f"- {decision}: {count}")
    
    lines.extend([
        "",
        "### Enhanced BinocheDecisionEngine",
    ])
    
    for decision, count in analysis.get("enhanced_decisions", {}).items():
        lines.append(f"- {decision}: {count}")
    
    if analysis.get("disagreements"):
        lines.extend([
            "",
            "## Disagreements (Top 10)",
            ""
        ])
        for i, d in enumerate(analysis["disagreements"], 1):
            lines.append(f"### {i}. Task {d.get('task_id', 'unknown')}")
            lines.append(f"- Legacy: {d.get('legacy_decision')} (conf: {d.get('legacy_confidence', 0):.2f})")
            lines.append(f"- Enhanced: {d.get('enhanced_decision')} (conf: {d.get('enhanced_confidence', 0):.2f})")
            lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Analyze Binoche_Observer A/B test results")
    parser.add_argument("--hours", type=int, default=24, help="Hours to analyze (default: 24)")
    parser.add_argument("--out", type=str, help="Output JSON file path")
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from workspace_utils import find_fdo_root
    
    default_ledger = str(find_fdo_root(Path(__file__).parent) / "memory" / "resonance_ledger.jsonl")
    parser.add_argument("--ledger", type=str, default=default_ledger,
                        help="Path to resonance_ledger.jsonl")
    args = parser.parse_args()
    
    ledger_path = Path(args.ledger)
    
    print(f"🔍 Analyzing {args.hours}h of A/B test data...")
    comparisons = load_ab_comparisons(ledger_path, args.hours)
    
    if not comparisons:
        print("⚠️ No A/B comparison events found")
        print("   Make sure tasks have been executed with the new pipeline.py")
        return
    
    analysis = analyze_comparisons(comparisons)
    
    # Generate markdown report
    report = generate_report(analysis, args.hours)
    
    # Print summary
    print(f"\n✅ Analysis Complete")
    print(f"   Total comparisons: {analysis['total']}")
    print(f"   Match rate: {analysis['match_rate']:.1%}")
    print(f"   Disagreements: {analysis['disagreements_count']}")
    
    # Save JSON if requested
    if args.out:
        out_path = Path(args.out)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        print(f"   JSON saved: {out_path}")
    
    # Save markdown report
    report_path = Path("outputs/binoche_ab_report_latest.md")
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"   Report saved: {report_path}")


if __name__ == "__main__":
    main()
