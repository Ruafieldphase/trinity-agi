import json
from statistics import mean, median

with open("summary_light_sample_metrics.json", encoding="utf-8") as f:
    data = json.load(f)

records = data["records"]
lengths = [r["running_summary_len"] for r in records if r["running_summary_len"] is not None]
bullets = [r["running_summary_bullets"] for r in records if r["running_summary_bullets"] is not None]
latencies = [r["execution_time_ms"] for r in records]
cache_hits = sum(1 for r in records if r["cached"])

summary = {
    "call_count": len(records),
    "cache_hits": cache_hits,
    "cache_hit_rate_percent": round(cache_hits / len(records) * 100, 2) if records else 0,
    "avg_running_summary_len": round(mean(lengths), 1) if lengths else 0,
    "avg_running_summary_bullets": round(mean(bullets), 2) if bullets else 0,
    "running_summary_len_range": [min(lengths), max(lengths)] if lengths else [0, 0],
    "latency_ms": {
        "min": round(min(latencies), 3) if latencies else 0,
        "p50": round(median(latencies), 3) if latencies else 0,
        "max": round(max(latencies), 3) if latencies else 0,
    },
    "cache_keys": [r["cache_key"] for r in records],
}

print(json.dumps(summary, ensure_ascii=False, indent=2))
