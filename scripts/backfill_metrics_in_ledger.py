#!/usr/bin/env python3
"""
Backfill metrics in existing ledger entries.
Adds quality and latency_ms to events that have them in other field names.
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from workspace_root import get_workspace_root

# Add parent directory to path
sys.path.insert(0, str(get_workspace_root() / "fdo_agi_repo"))

from orchestrator.event_emitter import normalize_metric_fields

def backfill_ledger(
    ledger_path: Path,
    output_path: Path = None,
    dry_run: bool = False
):
    """
    Backfill metrics in ledger entries.
    
    Args:
        ledger_path: Path to resonance_ledger.jsonl
        output_path: Path to write updated ledger (default: overwrite original)
        dry_run: If True, only show what would be changed
    """
    if not ledger_path.exists():
        print(f"❌ Ledger not found: {ledger_path}")
        return 1
    
    output_path = output_path or ledger_path
    
    print(f"📖 Reading ledger: {ledger_path}")
    
    total = 0
    modified = 0
    already_has_quality = 0
    already_has_latency = 0
    added_quality = 0
    added_latency = 0
    
    updated_lines = []
    
    # Debug: check first few entries with quality_score
    debug_count = 0
    
    with open(ledger_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                updated_lines.append(line)
                continue
            
            try:
                entry = json.loads(line)
                total += 1
                
                # Debug: print first few quality_score entries
                if debug_count < 3 and 'quality_score' in entry and 'quality' not in entry:
                    print(f"DEBUG: Entry {line_num} before normalize:")
                    print(f"  has quality_score: {'quality_score' in entry}")
                    print(f"  has quality: {'quality' in entry}")
                    print(f"  quality_score value: {entry.get('quality_score')}")
                    debug_count += 1
                
                # Track original state
                had_quality = 'quality' in entry
                had_latency = 'latency_ms' in entry
                
                if had_quality:
                    already_has_quality += 1
                if had_latency:
                    already_has_latency += 1
                
                # Normalize fields
                original_entry = entry.copy()
                entry = normalize_metric_fields(entry)
                
                # Check if anything changed
                if entry != original_entry:
                    modified += 1
                    if 'quality' in entry and not had_quality:
                        added_quality += 1
                    if 'latency_ms' in entry and not had_latency:
                        added_latency += 1
                
                updated_lines.append(json.dumps(entry, ensure_ascii=False))
                
            except json.JSONDecodeError as e:
                print(f"⚠️  Line {line_num}: JSON decode error: {e}")
                updated_lines.append(line)
                continue
    
    # Print summary
    print(f"\n📊 Backfill Summary:")
    print(f"   Total entries: {total:,}")
    print(f"   Modified: {modified:,} ({100*modified/total if total else 0:.1f}%)")
    print(f"   Already had quality: {already_has_quality:,}")
    print(f"   Already had latency_ms: {already_has_latency:,}")
    print(f"   ✅ Added quality: {added_quality:,}")
    print(f"   ✅ Added latency_ms: {added_latency:,}")
    
    if dry_run:
        print(f"\n🔍 DRY RUN - No changes written")
        return 0
    
    # Write updated ledger
    print(f"\n💾 Writing to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        for line in updated_lines:
            f.write(line + '\n')
    
    print(f"✅ Backfill complete!")
    
    return 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Backfill metrics in ledger")
    parser.add_argument(
        "--ledger",
        type=Path,
        default=get_workspace_root() / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl",
        help="Path to ledger file (default: fdo_agi_repo/memory/resonance_ledger.jsonl)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path (default: overwrite original)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without writing"
    )
    
    args = parser.parse_args()
    
    sys.exit(backfill_ledger(args.ledger, args.output, args.dry_run))
