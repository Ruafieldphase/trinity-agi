#!/usr/bin/env python3
"""
Analyze latency warnings from resonance ledger
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def analyze_latency():
    ledger_path = Path("fdo_agi_repo/memory/resonance_ledger.jsonl")
    
    if not ledger_path.exists():
        print(f"Error: {ledger_path} not found")
        return 1
    
    warnings = []
    latency_by_task = defaultdict(list)
    
    with open(ledger_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line)
                
                # Check for resonance_policy warnings
                if entry.get('event') == 'resonance_policy':
                    if entry.get('action') == 'warn':
                        warnings.append(entry)
                        task_id = entry.get('task_id', 'unknown')
                        observed = entry.get('observed', {})
                        latency_ms = observed.get('latency_ms', 0)
                        latency_by_task[task_id].append(latency_ms)
                
            except json.JSONDecodeError:
                continue
    
    print(f"\n=== Latency Warning Analysis ===")
    print(f"Total warnings: {len(warnings)}")
    print(f"Unique tasks: {len(latency_by_task)}")
    
    if not warnings:
        print("\nNo latency warnings found")
        return 0
    
    print(f"\n=== Warnings by Task ===")
    for task_id, latencies in sorted(latency_by_task.items(), key=lambda x: max(x[1]), reverse=True):
        avg_lat = sum(latencies) / len(latencies)
        max_lat = max(latencies)
        print(f"\nTask: {task_id}")
        print(f"  Count: {len(latencies)}")
        print(f"  Avg: {avg_lat:.1f}ms ({avg_lat/1000:.1f}s)")
        print(f"  Max: {max_lat:.1f}ms ({max_lat/1000:.1f}s)")
    
    print(f"\n=== Recent Warnings (last 10) ===")
    for w in warnings[-10:]:
        task_id = w.get('task_id', 'unknown')
        observed = w.get('observed', {})
        latency_ms = observed.get('latency_ms', 0)
        quality = observed.get('quality', 0)
        evidence_ok = observed.get('evidence_ok', False)
        ts = w.get('ts', 0)
        
        print(f"\n{datetime.fromtimestamp(ts).isoformat()}")
        print(f"  Task: {task_id}")
        print(f"  Latency: {latency_ms:.1f}ms ({latency_ms/1000:.1f}s)")
        print(f"  Quality: {quality:.2f}, Evidence: {evidence_ok}")
    
    # Statistics
    all_latencies = [lat for lats in latency_by_task.values() for lat in lats]
    if all_latencies:
        print(f"\n=== Overall Statistics ===")
        print(f"Min: {min(all_latencies):.1f}ms ({min(all_latencies)/1000:.1f}s)")
        print(f"Max: {max(all_latencies):.1f}ms ({max(all_latencies)/1000:.1f}s)")
        print(f"Avg: {sum(all_latencies)/len(all_latencies):.1f}ms ({sum(all_latencies)/len(all_latencies)/1000:.1f}s)")
        
        # Percentiles
        sorted_lats = sorted(all_latencies)
        p50 = sorted_lats[len(sorted_lats)//2]
        p95 = sorted_lats[int(len(sorted_lats)*0.95)]
        print(f"P50: {p50:.1f}ms ({p50/1000:.1f}s)")
        print(f"P95: {p95:.1f}ms ({p95/1000:.1f}s)")
    
    # Recommendations
    print(f"\n=== Recommendations ===")
    if max(all_latencies) > 30000:
        print("- HIGH: Latency >30s detected. Check for:")
        print("  * Network timeouts")
        print("  * Model cold starts")
        print("  * API rate limits")
    if sum(all_latencies)/len(all_latencies) > 15000:
        print("- MEDIUM: Avg latency >15s. Consider:")
        print("  * Caching frequently used results")
        print("  * Async processing for non-critical paths")
        print("  * Increase timeout thresholds if acceptable")
    
    return 0

if __name__ == "__main__":
    sys.exit(analyze_latency())
