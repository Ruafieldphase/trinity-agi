#!/usr/bin/env python3
"""Check metric coverage in resonance ledger"""
import json
from pathlib import Path
from collections import Counter
from workspace_root import get_workspace_root

ledger_path = get_workspace_root() / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"

total = 0
has_quality = 0
has_latency = 0
has_both = 0

field_counts = Counter()

with open(ledger_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        
        try:
            entry = json.loads(line)
            total += 1
            
            # Count all fields
            for key in entry.keys():
                field_counts[key] += 1
            
            # Check metrics
            q = 'quality' in entry
            l = 'latency_ms' in entry
            
            if q:
                has_quality += 1
            if l:
                has_latency += 1
            if q and l:
                has_both += 1
        
        except json.JSONDecodeError:
            continue

print(f"📊 Metric Coverage Report")
print(f"{'='*50}")
print(f"Total entries: {total:,}")
print(f"")
print(f"Metric Coverage:")
print(f"  quality:     {has_quality:>6,} ({100*has_quality/total:>5.1f}%)")
print(f"  latency_ms:  {has_latency:>6,} ({100*has_latency/total:>5.1f}%)")
print(f"  both:        {has_both:>6,} ({100*has_both/total:>5.1f}%)")
print(f"")
print(f"Top 10 Fields:")
for field, count in field_counts.most_common(10):
    print(f"  {field:20s}: {count:>6,} ({100*count/total:>5.1f}%)")
