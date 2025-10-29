#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Cache Verification
Checks current cache statistics from resonance_ledger.jsonl
Useful for immediate verification after TTL changes
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

BASE = Path(r"C:\workspace\agi")
LEDGER = BASE / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"

def load_recent_events(hours: int = 1) -> List[Dict[str, Any]]:
    """Load evidence_correction events from the last N hours"""
    if not LEDGER.exists():
        return []
    
    cutoff = datetime.now(timezone.utc).timestamp() - (hours * 3600)
    events = []
    
    with open(LEDGER, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if obj.get("event") == "evidence_correction" and obj.get("ts", 0) > cutoff:
                    events.append(obj)
            except:
                continue
    
    return events

def analyze_recent_cache(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze cache performance from recent events"""
    if not events:
        return {"error": "No recent events found"}
    
    cache_hits = sum(1 for e in events if e.get("cache_hit"))
    total = len(events)
    hit_rate = (cache_hits / total * 100) if total > 0 else 0.0
    
    # Aggregate cache stats from latest event
    latest_cache = None
    for e in reversed(events):
        if e.get("cache"):
            latest_cache = e["cache"]
            break
    
    return {
        "recent_events": total,
        "cache_hits": cache_hits,
        "hit_rate_percent": round(hit_rate, 2),
        "latest_cache_stats": latest_cache,
        "time_window_hours": 1,
    }

def main():
    print("?îç Quick Cache Verification\n")
    print(f"?ìÇ Ledger: {LEDGER}\n")
    
    if not LEDGER.exists():
        print("??Ledger file not found!")
        return 1
    
    # Check last 1 hour
    events = load_recent_events(hours=1)
    analysis = analyze_recent_cache(events)
    
    if "error" in analysis:
        print(f"?†Ô∏è  {analysis['error']}")
        print("\n?í° This is normal if no AGI tasks ran in the last hour.")
        print("   Run an AGI task and check again.")
        return 0
    
    print(f"??Time Window: Last {analysis['time_window_hours']} hour(s)")
    print(f"?ìä Recent Evidence Events: {analysis['recent_events']}")
    print(f"??Cache Hits: {analysis['cache_hits']}")
    print(f"?ìà Hit Rate: **{analysis['hit_rate_percent']}%**")
    
    if analysis['latest_cache_stats']:
        stats = analysis['latest_cache_stats']
        print(f"\n?ì¶ Latest Cache Stats:")
        print(f"   Hits: {stats.get('hits', 0)}")
        print(f"   Misses: {stats.get('misses', 0)}")
        print(f"   Hit Rate: {stats.get('hit_rate_percent', 0)}%")
        print(f"   Evictions: {stats.get('evictions', 0)}")
        print(f"   Time Saved: {stats.get('total_time_saved_ms', 0):.1f}ms")
    
    print("\n?í° Interpretation:")
    if analysis['hit_rate_percent'] >= 40:
        print("   ??EXCELLENT - Cache is performing well!")
    elif analysis['hit_rate_percent'] >= 20:
        print("   ??GOOD - Cache is helping, room for improvement")
    elif analysis['hit_rate_percent'] >= 5:
        print("   ?†Ô∏è  MODERATE - Cache needs tuning")
    else:
        print("   ?†Ô∏è  LOW - Consider increasing TTL or query normalization")
    
    print("\n?îÑ To see improvement over time:")
    print("   1. Run AGI tasks for 6-12 hours")
    print("   2. Re-run this script")
    print("   3. Compare with full analysis: py -3 scripts/analyze_cache_effectiveness.py")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
