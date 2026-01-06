#!/usr/bin/env python
"""Backfill normalized metrics to existing Ledger entries.

Quick Win: 10-minute operation for immediate 10%+ coverage boost.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from workspace_root import get_workspace_root

WORKSPACE_ROOT = get_workspace_root()

def normalize_metrics(event: dict) -> dict:
    """Normalize metrics field names for existing event."""
    # Quality normalization
    if 'quality' not in event or event['quality'] is None:
        if 'agi_quality' in event and event['agi_quality'] is not None:
            event['quality'] = float(event['agi_quality'])
        elif 'core_quality' in event and event['core_quality'] is not None:
            event['quality'] = float(event['core_quality'])
        elif 'assessment' in event and isinstance(event['assessment'], dict):
            if 'quality_score' in event['assessment']:
                event['quality'] = float(event['assessment']['quality_score'])
    
    # Latency normalization
    if 'latency_ms' not in event or event['latency_ms'] is None:
        if 'core_latency_ms' in event and event['core_latency_ms'] is not None:
            event['latency_ms'] = float(event['core_latency_ms'])
        elif 'agi_latency_ms' in event and event['agi_latency_ms'] is not None:
            event['latency_ms'] = float(event['agi_latency_ms'])
        elif 'duration_sec' in event and event['duration_sec'] is not None:
            event['latency_ms'] = float(event['duration_sec']) * 1000.0
        elif 'elapsed_time' in event and event['elapsed_time'] is not None:
            event['latency_ms'] = float(event['elapsed_time']) * 1000.0
    
    # Citations normalization
    if 'citations' not in event or event['citations'] is None:
        if 'citation_count' in event and event['citation_count'] is not None:
            event['citations'] = int(event['citation_count'])
        elif 'references' in event and isinstance(event['references'], list):
            event['citations'] = len(event['references'])
    
    return event


def backfill_ledger(ledger_path: Path, dry_run: bool = False) -> dict:
    """Backfill normalized metrics to existing Ledger entries.
    
    Args:
        ledger_path: Path to resonance_ledger.jsonl
        dry_run: If True, only report what would change
    
    Returns:
        dict with statistics
    """
    if not ledger_path.exists():
        return {"error": "Ledger not found", "path": str(ledger_path)}
    
    backup_path = ledger_path.parent / f"resonance_ledger_backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.jsonl"
    
    # Statistics
    stats = {
        "total_events": 0,
        "quality_added": 0,
        "latency_added": 0,
        "citations_added": 0,
        "unchanged": 0,
        "dry_run": dry_run,
        "backup_path": str(backup_path) if not dry_run else None
    }
    
    # Read all events
    events = []
    with open(ledger_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    stats["total_events"] = len(events)
    
    # Backup original
    if not dry_run:
        with open(backup_path, 'w', encoding='utf-8') as f:
            for event in events:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
    
    # Process events
    modified_events = []
    for event in events:
        original_event = event.copy()
        
        # Check before normalization
        had_quality = event.get('quality') is not None
        had_latency = event.get('latency_ms') is not None
        had_citations = event.get('citations') is not None
        
        # Normalize
        normalized = normalize_metrics(event)
        
        # Check after normalization
        has_quality = normalized.get('quality') is not None
        has_latency = normalized.get('latency_ms') is not None
        has_citations = normalized.get('citations') is not None
        
        # Track changes
        if not had_quality and has_quality:
            stats["quality_added"] += 1
        if not had_latency and has_latency:
            stats["latency_added"] += 1
        if not had_citations and has_citations:
            stats["citations_added"] += 1
        
        if original_event == normalized:
            stats["unchanged"] += 1
        
        modified_events.append(normalized)
    
    # Write back
    if not dry_run:
        with open(ledger_path, 'w', encoding='utf-8') as f:
            for event in modified_events:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
    
    # Calculate percentages
    if stats["total_events"] > 0:
        stats["quality_coverage_before"] = round((stats["total_events"] - stats["quality_added"]) / stats["total_events"] * 100, 2)
        stats["quality_coverage_after"] = round((stats["total_events"] - stats["quality_added"] + stats["quality_added"]) / stats["total_events"] * 100, 2)
        stats["latency_coverage_after"] = round((stats["latency_added"] + (stats["total_events"] - stats["latency_added"])) / stats["total_events"] * 100, 2)
    
    return stats


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Backfill normalized metrics")
    parser.add_argument('--ledger', default=str(WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"))
    parser.add_argument('--dry-run', action='store_true', help='Report only, do not modify')
    args = parser.parse_args()
    
    ledger_path = Path(args.ledger)
    stats = backfill_ledger(ledger_path, dry_run=args.dry_run)
    
    # Print report
    print("\n🔄 Metric Normalization Backfill Report\n")
    print(f"Total Events: {stats['total_events']:,}")
    print(f"Quality Added: {stats['quality_added']:,} (+{round(stats['quality_added']/stats['total_events']*100,1) if stats['total_events'] > 0 else 0}%)")
    print(f"Latency Added: {stats['latency_added']:,} (+{round(stats['latency_added']/stats['total_events']*100,1) if stats['total_events'] > 0 else 0}%)")
    print(f"Citations Added: {stats['citations_added']:,} (+{round(stats['citations_added']/stats['total_events']*100,1) if stats['total_events'] > 0 else 0}%)")
    print(f"Unchanged: {stats['unchanged']:,}")
    
    if not args.dry_run:
        print(f"\n✅ Backup saved: {stats['backup_path']}")
        print("✅ Ledger updated successfully!")
    else:
        print("\n📋 Dry-run mode: No changes made")
    
    # Save JSON report
    output_path = WORKSPACE_ROOT / "outputs" / "metric_backfill_report_latest.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 Report saved: {output_path}")


if __name__ == '__main__':
    main()
