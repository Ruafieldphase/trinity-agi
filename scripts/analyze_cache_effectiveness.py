#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cache Effectiveness Analysis
Analyzes resonance_ledger.jsonl to understand cache usage patterns and suggest improvements
"""
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Any

BASE = r"C:\workspace\agi"
LEDGER_PATH = os.path.join(BASE, "fdo_agi_repo", "memory", "resonance_ledger.jsonl")
OUT_JSON = os.path.join(BASE, "outputs", "cache_analysis_latest.json")
OUT_MD = os.path.join(BASE, "outputs", "cache_analysis_latest.md")


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    if not os.path.exists(path):
        return items
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                items.append(obj)
            except Exception:
                continue
    return items


def analyze_cache_patterns(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze cache usage patterns from evidence_correction events"""
    
    # Extract evidence_correction events
    evidence_events = [e for e in entries if e.get("event") == "evidence_correction"]
    
    if not evidence_events:
        return {
            "error": "No evidence_correction events found",
            "total_events": len(entries)
        }
    
    # Cache statistics
    cache_hit_count = sum(1 for e in evidence_events if e.get("cache_hit"))
    total_events = len(evidence_events)
    cache_hit_rate = (cache_hit_count / total_events * 100) if total_events > 0 else 0.0
    
    # Query pattern analysis
    query_counter = Counter()
    query_temporal_gaps = defaultdict(list)  # query -> [time_gaps_between_occurrences]
    last_seen = {}  # query -> timestamp
    
    for e in evidence_events:
        # Reconstruct query (simplified - we don't have exact query in ledger)
        # Use hits/added as proxy for query uniqueness
        query_signature = f"h{e.get('hits',0)}_a{e.get('added',0)}"
        query_counter[query_signature] += 1
        
        ts = e.get("ts")
        if ts and query_signature in last_seen:
            gap = ts - last_seen[query_signature]
            query_temporal_gaps[query_signature].append(gap)
        
        if ts:
            last_seen[query_signature] = ts
    
    # Find repeated query patterns
    repeated_queries = {q: count for q, count in query_counter.items() if count > 1}
    
    # Analyze temporal gaps (cache TTL effectiveness)
    avg_gaps = {}
    for q, gaps in query_temporal_gaps.items():
        if gaps:
            avg_gaps[q] = sum(gaps) / len(gaps)
    
    # Current cache settings from ledger
    cache_stats = None
    for e in reversed(evidence_events):
        if e.get("cache"):
            cache_stats = e["cache"]
            break
    
    # TTL effectiveness analysis
    ttl_seconds = 300  # default from evidence_cache.py
    gaps_within_ttl = sum(1 for gaps in query_temporal_gaps.values() 
                          for gap in gaps if gap <= ttl_seconds)
    total_gaps = sum(len(gaps) for gaps in query_temporal_gaps.values())
    ttl_effectiveness = (gaps_within_ttl / total_gaps * 100) if total_gaps > 0 else 0.0
    
    # RAG latency analysis
    rag_latencies = [e.get("rag_latency_ms", 0.0) for e in evidence_events 
                     if e.get("rag_latency_ms") is not None]
    
    return {
        "summary": {
            "total_evidence_events": total_events,
            "cache_hit_count": cache_hit_count,
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "unique_query_patterns": len(query_counter),
            "repeated_query_patterns": len(repeated_queries),
        },
        "cache_current_stats": cache_stats,
        "temporal_analysis": {
            "ttl_seconds": ttl_seconds,
            "gaps_within_ttl": gaps_within_ttl,
            "total_query_repetitions": total_gaps,
            "ttl_effectiveness_percent": round(ttl_effectiveness, 2),
            "avg_gap_seconds": round(sum(avg_gaps.values()) / len(avg_gaps), 2) if avg_gaps else 0,
        },
        "rag_latency": {
            "min_ms": round(min(rag_latencies), 2) if rag_latencies else 0,
            "max_ms": round(max(rag_latencies), 2) if rag_latencies else 0,
            "avg_ms": round(sum(rag_latencies) / len(rag_latencies), 2) if rag_latencies else 0,
            "median_ms": round(sorted(rag_latencies)[len(rag_latencies)//2], 2) if rag_latencies else 0,
        },
        "top_repeated_patterns": dict(list(repeated_queries.items())[:10]),
        "recommendations": generate_recommendations(
            cache_hit_rate, ttl_effectiveness, avg_gaps, total_gaps
        )
    }


def generate_recommendations(hit_rate: float, ttl_eff: float, 
                             avg_gaps: Dict, total_reps: int) -> List[str]:
    """Generate actionable cache improvement recommendations"""
    recs = []
    
    if hit_rate < 5.0:
        recs.append("CRITICAL: Cache hit rate <5% - queries are too diverse or TTL too short")
        recs.append("Action: Increase TTL from 300s to 600-900s (10-15min)")
    elif hit_rate < 20.0:
        recs.append("WARN: Cache hit rate <20% - moderate improvement possible")
        recs.append("Action: Increase TTL to 450-600s (7.5-10min)")
    
    if ttl_eff < 30.0 and total_reps > 0:
        recs.append("CRITICAL: <30% of repeated queries happen within TTL window")
        recs.append("Action: Increase TTL to match average query gap patterns")
    
    if not avg_gaps or len(avg_gaps) < 5:
        recs.append("INFO: Very few repeated queries detected")
        recs.append("Action: Consider query normalization (remove noise from cache keys)")
    
    avg_gap_val = sum(avg_gaps.values()) / len(avg_gaps) if avg_gaps else 0
    if avg_gap_val > 600:
        recs.append(f"INFO: Average query repetition gap is {int(avg_gap_val)}s (>{int(avg_gap_val/60)}min)")
        recs.append(f"Action: Consider increasing TTL to {int(avg_gap_val * 1.5)}s to capture patterns")
    
    if not recs:
        recs.append("OK: Cache configuration appears reasonable for current workload")
    
    return recs


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
    
    entries = load_jsonl(LEDGER_PATH)
    analysis = analyze_cache_patterns(entries)
    
    out = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "ledger_path": LEDGER_PATH,
        "analysis": analysis
    }
    
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    
    # Generate markdown report
    lines = [
        "# Cache Effectiveness Analysis",
        "",
        f"Generated: {out['generated']}",
        "",
        "## Summary",
        "",
    ]
    
    if "error" in analysis:
        lines.append(f"**Error**: {analysis['error']}")
    else:
        s = analysis["summary"]
        lines.extend([
            f"- Total Evidence Events: {s['total_evidence_events']}",
            f"- Cache Hit Rate: **{s['cache_hit_rate_percent']}%** ({s['cache_hit_count']} hits)",
            f"- Unique Query Patterns: {s['unique_query_patterns']}",
            f"- Repeated Patterns: {s['repeated_query_patterns']}",
            "",
            "## Temporal Analysis",
            "",
        ])
        
        t = analysis["temporal_analysis"]
        lines.extend([
            f"- Current TTL: {t['ttl_seconds']}s ({int(t['ttl_seconds']/60)}min)",
            f"- Query Repetitions Within TTL: {t['gaps_within_ttl']}/{t['total_query_repetitions']} (**{t['ttl_effectiveness_percent']}%**)",
            f"- Average Gap Between Repeated Queries: {t['avg_gap_seconds']}s",
            "",
            "## RAG Latency Distribution",
            "",
        ])
        
        r = analysis["rag_latency"]
        lines.extend([
            f"- Min: {r['min_ms']}ms",
            f"- Median: {r['median_ms']}ms",
            f"- Avg: {r['avg_ms']}ms",
            f"- Max: {r['max_ms']}ms",
            "",
            "## Recommendations",
            "",
        ])
        
        for rec in analysis["recommendations"]:
            if rec.startswith("CRITICAL:"):
                lines.append(f"-- **{rec}**")
            elif rec.startswith("WARN:"):
                lines.append(f"-- {rec}")
            elif rec.startswith("Action:"):
                lines.append(f"   >> {rec}")
            else:
                lines.append(f"-- {rec}")
        
        lines.append("")
        lines.append("## Top Repeated Query Patterns")
        lines.append("")
        for pattern, count in analysis.get("top_repeated_patterns", {}).items():
            lines.append(f"- `{pattern}`: {count} times")
    
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(">> Cache analysis complete")
    print(f"   JSON: {OUT_JSON}")
    print(f"   MD: {OUT_MD}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
