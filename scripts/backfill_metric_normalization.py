"""
Backfill Metric Field Normalization
===================================

Applies field name normalization to existing Ledger entries
WITHOUT modifying original data (adds new normalized fields).

Target: 34K events → 3.5K with metrics (10% coverage)
Time: ~10 minutes
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

WORKSPACE = Path(__file__).parent.parent
LEDGER_PATH = WORKSPACE / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
OUTPUT_PATH = WORKSPACE / "outputs" / "backfill_normalized_ledger.jsonl"

# Field mappings (from → to)
FIELD_MAPPINGS = {
    'agi_quality': 'quality',
    'lumen_quality': 'quality',
    'binoche_quality': 'quality',
    'lumen_latency_ms': 'latency_ms',
    'agi_latency_ms': 'latency_ms',
    'processing_time_ms': 'latency_ms',
    'duration_sec': 'latency_ms',  # Convert to ms
    'agi_citations': 'citations',
    'lumen_citations': 'citations'
}

def normalize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Add normalized fields to event (non-destructive)"""
    normalized = event.copy()
    
    # Already has normalized fields? Skip
    if 'quality' in event and 'latency_ms' in event:
        return normalized
    
    # Apply mappings
    for old_field, new_field in FIELD_MAPPINGS.items():
        if old_field in event and new_field not in event:
            value = event[old_field]
            
            # Convert duration_sec to latency_ms
            if old_field == 'duration_sec' and isinstance(value, (int, float)):
                value = value * 1000
            
            normalized[new_field] = value
    
    return normalized

def main():
    """Backfill normalization to existing Ledger"""
    stats = {
        'total': 0,
        'skipped': 0,
        'normalized': 0,
        'added_quality': 0,
        'added_latency': 0,
        'added_citations': 0
    }
    
    print(f"📖 Reading Ledger: {LEDGER_PATH}")
    print(f"💾 Output: {OUTPUT_PATH}")
    print()
    
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(LEDGER_PATH, 'r', encoding='utf-8') as f_in, \
         open(OUTPUT_PATH, 'w', encoding='utf-8') as f_out:
        
        for line in f_in:
            if not line.strip():
                continue
            
            stats['total'] += 1
            event = json.loads(line)
            
            # Normalize
            normalized = normalize_event(event)
            
            # Track what was added
            if normalized != event:
                stats['normalized'] += 1
                if 'quality' in normalized and 'quality' not in event:
                    stats['added_quality'] += 1
                if 'latency_ms' in normalized and 'latency_ms' not in event:
                    stats['added_latency'] += 1
                if 'citations' in normalized and 'citations' not in event:
                    stats['added_citations'] += 1
            else:
                stats['skipped'] += 1
            
            # Write
            f_out.write(json.dumps(normalized, ensure_ascii=False) + '\n')
            
            # Progress
            if stats['total'] % 5000 == 0:
                print(f"  Processed: {stats['total']:,} | Normalized: {stats['normalized']:,}")
    
    print()
    print("✅ Backfill Complete!")
    print(f"   Total Events: {stats['total']:,}")
    print(f"   Normalized: {stats['normalized']:,} ({100*stats['normalized']/stats['total']:.1f}%)")
    print(f"   Skipped (already normalized): {stats['skipped']:,}")
    print()
    print("📊 Fields Added:")
    print(f"   quality: +{stats['added_quality']:,}")
    print(f"   latency_ms: +{stats['added_latency']:,}")
    print(f"   citations: +{stats['added_citations']:,}")
    print()
    print(f"💾 Output saved: {OUTPUT_PATH}")
    
    # Coverage estimate
    if stats['total'] > 0:
        quality_before = 123  # from analysis
        latency_before = 85
        quality_after = quality_before + stats['added_quality']
        latency_after = latency_before + stats['added_latency']
        
        print()
        print("📈 Estimated Coverage:")
        print(f"   quality: {100*quality_before/stats['total']:.1f}% → {100*quality_after/stats['total']:.1f}%")
        print(f"   latency_ms: {100*latency_before/stats['total']:.1f}% → {100*latency_after/stats['total']:.1f}%")

if __name__ == "__main__":
    main()
