#!/usr/bin/env python3
"""
Cache Performance Timeline Monitor

Tracks cache hit rate evolution over time to validate TTL optimization.
Generates JSON + Markdown timeline for visualization.

Usage:
    python cache_monitor_timeline.py
    python cache_monitor_timeline.py --window-hours 24
    python cache_monitor_timeline.py --interval-hours 1
"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from collections import defaultdict
import sys

# Paths
REPO_ROOT = Path(__file__).parent.parent / "fdo_agi_repo"
LEDGER = REPO_ROOT / "memory" / "resonance_ledger.jsonl"
OUTPUTS = Path(__file__).parent.parent / "outputs"
OUTPUTS.mkdir(exist_ok=True)


def load_evidence_events() -> List[Dict[str, Any]]:
    """Load all evidence_correction events from ledger"""
    events = []
    if not LEDGER.exists():
        return events
    
    with open(LEDGER, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("event") == "evidence_correction":
                    events.append(entry)
            except json.JSONDecodeError:
                continue
    
    return events


def analyze_timeline(
    events: List[Dict[str, Any]],
    window_hours: int = 24,
    interval_hours: int = 1
) -> Dict[str, Any]:
    """
    Analyze cache performance in time windows
    
    Args:
        events: Evidence correction events
        window_hours: Total time window to analyze
        interval_hours: Time bucket size
    
    Returns:
        Timeline data with hit rate per interval
    """
    if not events:
        return {"error": "No events found"}
    
    # Sort by timestamp
    sorted_events = sorted(events, key=lambda e: e.get("ts", 0))
    
    # Find time range
    now = datetime.now(timezone.utc).timestamp()
    cutoff = now - (window_hours * 3600)
    
    # Filter to window
    windowed = [e for e in sorted_events if e.get("ts", 0) >= cutoff]
    
    if not windowed:
        return {
            "error": f"No events in last {window_hours} hours",
            "total_events": len(events),
            "oldest_ts": datetime.fromtimestamp(sorted_events[0]["ts"], timezone.utc).isoformat(),
            "newest_ts": datetime.fromtimestamp(sorted_events[-1]["ts"], timezone.utc).isoformat()
        }
    
    # Create time buckets
    start_ts = windowed[0]["ts"]
    end_ts = windowed[-1]["ts"]
    interval_sec = interval_hours * 3600
    
    buckets = defaultdict(lambda: {"hits": 0, "misses": 0, "events": []})
    
    for event in windowed:
        ts = event["ts"]
        bucket_idx = int((ts - start_ts) / interval_sec)
        bucket_key = f"bucket_{bucket_idx}"
        
        cache_hit = event.get("cache_hit", False)
        if cache_hit:
            buckets[bucket_key]["hits"] += 1
        else:
            buckets[bucket_key]["misses"] += 1
        
        buckets[bucket_key]["events"].append({
            "ts": ts,
            "cache_hit": cache_hit,
            "query": event.get("query", ""),
            "latency_ms": event.get("latency_ms", 0)
        })
    
    # Calculate stats per bucket
    timeline = []
    for bucket_key in sorted(buckets.keys()):
        data = buckets[bucket_key]
        hits = data["hits"]
        misses = data["misses"]
        total = hits + misses
        hit_rate = hits / total if total > 0 else 0.0
        
        # Bucket time range
        bucket_idx = int(bucket_key.split("_")[1])
        bucket_start = start_ts + (bucket_idx * interval_sec)
        bucket_end = bucket_start + interval_sec
        
        timeline.append({
            "bucket": bucket_key,
            "start_ts": bucket_start,
            "end_ts": bucket_end,
            "start_time": datetime.fromtimestamp(bucket_start, timezone.utc).isoformat(),
            "end_time": datetime.fromtimestamp(bucket_end, timezone.utc).isoformat(),
            "hits": hits,
            "misses": misses,
            "total": total,
            "hit_rate": round(hit_rate * 100, 2),
            "avg_latency_ms": round(
                sum(e["latency_ms"] for e in data["events"]) / len(data["events"]),
                3
            ) if data["events"] else 0.0
        })
    
    return {
        "window_hours": window_hours,
        "interval_hours": interval_hours,
        "total_events": len(windowed),
        "total_buckets": len(timeline),
        "timeline": timeline,
        "overall_hit_rate": round(
            sum(b["hits"] for b in timeline) / sum(b["total"] for b in timeline) * 100,
            2
        ) if timeline else 0.0,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


def generate_markdown(data: Dict[str, Any], out_path: Path) -> None:
    """Generate Markdown report"""
    lines = [
        "# Cache Performance Timeline",
        "",
        f"Generated: {data.get('generated_at', 'N/A')}",
        "",
        "## Overview",
        "",
        f"- Window: Last {data.get('window_hours', 0)} hours",
        f"- Interval: {data.get('interval_hours', 0)} hour(s) per bucket",
        f"- Total Events: {data.get('total_events', 0)}",
        f"- Total Buckets: {data.get('total_buckets', 0)}",
        f"- Overall Hit Rate: **{data.get('overall_hit_rate', 0.0)}%**",
        ""
    ]
    
    if "error" in data:
        lines.extend([
            "## Error",
            "",
            f"⚠️ {data['error']}",
            ""
        ])
        if "total_events" in data and data["total_events"] > 0:
            lines.extend([
                "### Data Range",
                "",
                f"- Oldest event: {data.get('oldest_ts', 'N/A')}",
                f"- Newest event: {data.get('newest_ts', 'N/A')}",
                f"- Total events: {data['total_events']}",
                ""
            ])
    else:
        lines.extend([
            "## Timeline",
            "",
            "| Bucket | Start Time | Hit Rate | Hits | Misses | Total | Avg Latency |",
            "|--------|------------|----------|------|--------|-------|-------------|"
        ])
        
        for bucket in data.get("timeline", []):
            start_time = bucket["start_time"].split("T")[1][:8]  # HH:MM:SS
            lines.append(
                f"| {bucket['bucket']} | {start_time} | "
                f"**{bucket['hit_rate']}%** | {bucket['hits']} | {bucket['misses']} | "
                f"{bucket['total']} | {bucket['avg_latency_ms']}ms |"
            )
        
        lines.extend([
            "",
            "## Interpretation",
            ""
        ])
        
        overall_rate = data.get("overall_hit_rate", 0.0)
        if overall_rate >= 40:
            lines.append("✅ **EXCELLENT** - Cache optimization successful! Hit rate ≥40%")
        elif overall_rate >= 20:
            lines.append("✅ **GOOD** - Cache showing improvement, hit rate 20-40%")
        elif overall_rate >= 5:
            lines.append("⚠️ **MODERATE** - Some cache benefit, but room for improvement (5-20%)")
        else:
            lines.append("⚠️ **LOW** - Cache not yet effective (<5%). Wait longer or increase TTL.")
        
        lines.extend([
            "",
            "## Next Steps",
            ""
        ])
        
        if overall_rate < 40:
            lines.extend([
                "1. Run AGI tasks for 6-12 more hours",
                "2. Re-run this timeline monitor",
                "3. If hit rate stays <40% after 24h, consider:",
                "   - Increasing TTL to 1200s (20 minutes)",
                "   - Adding query normalization",
                ""
            ])
        else:
            lines.extend([
                "1. Monitor over next 7 days for stability",
                "2. Check memory usage with cache stats",
                "3. Consider query normalization for further gains",
                ""
            ])
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Cache performance timeline monitor")
    parser.add_argument("--window-hours", type=int, default=24,
                        help="Time window to analyze (default: 24)")
    parser.add_argument("--interval-hours", type=int, default=1,
                        help="Time bucket size (default: 1)")
    args = parser.parse_args()
    
    print("🔍 Cache Performance Timeline Monitor")
    print(f"📂 Ledger: {LEDGER}")
    print()
    
    # Load and analyze
    events = load_evidence_events()
    print(f"📊 Total evidence events: {len(events)}")
    
    data = analyze_timeline(events, args.window_hours, args.interval_hours)
    
    # Save outputs
    json_out = OUTPUTS / "cache_timeline_latest.json"
    md_out = OUTPUTS / "cache_timeline_latest.md"
    
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    generate_markdown(data, md_out)
    
    print(f"✅ Timeline analysis complete")
    print(f"   JSON: {json_out}")
    print(f"   MD: {md_out}")
    print()
    
    if "error" not in data:
        print(f"📈 Overall Hit Rate: **{data['overall_hit_rate']}%**")
        print(f"📦 Time Buckets: {data['total_buckets']}")
    else:
        print(f"⚠️ {data['error']}")


if __name__ == "__main__":
    main()
