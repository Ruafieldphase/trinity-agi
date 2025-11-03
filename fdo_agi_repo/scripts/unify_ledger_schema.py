#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unify resonance_ledger.jsonl schemas into a standardized format.

This script addresses the schema fragmentation issue where 19+ different
event schemas coexist, causing performance degradation.

Strategy:
1. Define a base schema with required fields: event, task_id, ts, timestamp
2. Map all variants to this base + optional extension fields
3. Preserve all data but normalize structure
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timezone
from collections import defaultdict

HERE = Path(__file__).parent
DEFAULT_IN = HERE.parent / "memory" / "resonance_ledger.jsonl"
DEFAULT_OUT = HERE.parent / "memory" / "resonance_ledger_unified.jsonl"
DEFAULT_REPORT = HERE.parent / "outputs" / "schema_unification_report.json"


def ensure_base_fields(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all events have base required fields."""
    unified = {}
    
    # 1. event (required)
    unified["event"] = obj.get("event", "unknown")
    
    # 2. task_id (required, may be null for system events)
    unified["task_id"] = obj.get("task_id")
    
    # 3. ts (timestamp in ISO format, required)
    if "ts" in obj:
        unified["ts"] = obj["ts"]
    elif "timestamp" in obj:
        unified["ts"] = obj["timestamp"]
    else:
        # Fallback to current time if missing
        unified["ts"] = datetime.now(timezone.utc).isoformat()
    
    # 4. timestamp (deprecated but keep for compatibility)
    if "timestamp" in obj:
        unified["timestamp"] = obj["timestamp"]
    
    return unified


def unify_event_schema(obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Unify event schema while preserving all data.
    
    Strategy:
    - Start with base fields
    - Add event-specific fields in sorted order
    - Group related fields under namespaces when possible
    """
    unified = ensure_base_fields(obj)
    
    # Copy all other fields (preserving data)
    for key, value in obj.items():
        if key not in unified:
            unified[key] = value
    
    # Sort keys for consistency (base fields first, then alphabetical)
    base_order = ["event", "task_id", "ts", "timestamp"]
    other_keys = sorted([k for k in unified.keys() if k not in base_order])
    
    result = {}
    for key in base_order:
        if key in unified:
            result[key] = unified[key]
    for key in other_keys:
        result[key] = unified[key]
    
    return result


def analyze_schemas(ledger_path: Path) -> Dict[str, Any]:
    """Analyze current schema diversity."""
    schema_counts = defaultdict(int)
    event_types = defaultdict(int)
    total = 0
    
    with open(ledger_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                total += 1
                
                # Track schema
                schema = tuple(sorted(obj.keys()))
                schema_counts[schema] += 1
                
                # Track event types
                event_type = obj.get("event", "unknown")
                event_types[event_type] += 1
                
            except Exception:
                continue
    
    return {
        "total_events": total,
        "unique_schemas": len(schema_counts),
        "schemas": [
            {"fields": list(schema), "count": count}
            for schema, count in sorted(
                schema_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
        ],
        "event_types": dict(sorted(
            event_types.items(),
            key=lambda x: x[1],
            reverse=True
        ))
    }


def unify_ledger(
    in_path: Path,
    out_path: Path,
    report_path: Path
) -> Dict[str, Any]:
    """
    Unify ledger schemas and generate report.
    
    Returns summary statistics.
    """
    # Analyze before
    print("[unify_ledger] Analyzing current schemas...")
    before = analyze_schemas(in_path)
    print(f"  Found {before['unique_schemas']} unique schemas in {before['total_events']} events")
    
    # Unify
    print("[unify_ledger] Unifying schemas...")
    unified_count = 0
    error_count = 0
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(in_path, "r", encoding="utf-8") as fin, \
         open(out_path, "w", encoding="utf-8", newline="\n") as fout:
        
        for idx, line in enumerate(fin, start=1):
            line = line.strip()
            if not line:
                continue
            
            try:
                obj = json.loads(line)
                unified = unify_event_schema(obj)
                
                # Write as compact JSON
                fout.write(json.dumps(unified, ensure_ascii=False, separators=(",", ":")) + "\n")
                unified_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"  Warning: Failed to unify line {idx}: {e}")
                # Write original line to preserve data
                fout.write(line + "\n")
    
    # Analyze after
    print("[unify_ledger] Analyzing unified schemas...")
    after = analyze_schemas(out_path)
    
    # Generate report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "before": before,
        "after": after,
        "unified_count": unified_count,
        "error_count": error_count,
        "schema_reduction": {
            "before": before['unique_schemas'],
            "after": after['unique_schemas'],
            "reduction_pct": (
                (before['unique_schemas'] - after['unique_schemas']) / 
                before['unique_schemas'] * 100
                if before['unique_schemas'] > 0 else 0
            )
        }
    }
    
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n[unify_ledger] Summary:")
    print(f"  Total events: {unified_count}")
    print(f"  Errors: {error_count}")
    print(f"  Schema reduction: {before['unique_schemas']} → {after['unique_schemas']}")
    print(f"  Improvement: {report['schema_reduction']['reduction_pct']:.1f}%")
    print(f"\n  Output: {out_path}")
    print(f"  Report: {report_path}")
    
    return report


def main() -> int:
    import argparse
    
    ap = argparse.ArgumentParser(
        description="Unify resonance ledger schemas for better performance"
    )
    ap.add_argument(
        "--in",
        dest="in_path",
        default=str(DEFAULT_IN),
        help="Input ledger path"
    )
    ap.add_argument(
        "--out",
        dest="out_path",
        default=str(DEFAULT_OUT),
        help="Output unified ledger path"
    )
    ap.add_argument(
        "--report",
        dest="report_path",
        default=str(DEFAULT_REPORT),
        help="Output report path"
    )
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Replace original ledger with unified version (BACKUP FIRST!)"
    )
    
    args = ap.parse_args()
    
    in_path = Path(args.in_path)
    out_path = Path(args.out_path)
    report_path = Path(args.report_path)
    
    if not in_path.exists():
        print(f"[unify_ledger] Error: Input not found: {in_path}")
        return 1
    
    # Create backup
    backup_path = in_path.parent / f"{in_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    print(f"[unify_ledger] Creating backup: {backup_path}")
    import shutil
    shutil.copy2(in_path, backup_path)
    
    # Unify
    report = unify_ledger(in_path, out_path, report_path)
    
    # Apply if requested
    if args.apply:
        print(f"\n[unify_ledger] Applying unified ledger...")
        shutil.copy2(out_path, in_path)
        print(f"  ✅ Original ledger replaced with unified version")
        print(f"  📁 Backup available at: {backup_path}")
    else:
        print(f"\n[unify_ledger] Unified ledger ready at: {out_path}")
        print(f"  To apply, run with --apply flag")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
