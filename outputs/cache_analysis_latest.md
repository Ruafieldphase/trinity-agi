# Cache Effectiveness Analysis

Generated: 2025-10-29T11:31:26.267239+00:00

## Summary

- Total Evidence Events: 107
- Cache Hit Rate: **8.41%** (9 hits)
- Unique Query Patterns: 3
- Repeated Patterns: 3

## Temporal Analysis

- Current TTL: 300s (5min)
- Query Repetitions Within TTL: 68/104 (**65.38%**)
- Average Gap Between Repeated Queries: 1965.09s

## RAG Latency Distribution

- Min: 0.0ms
- Median: 0.13ms
- Avg: 0.09ms
- Max: 0.32ms

## Recommendations

⚠️ WARN: Cache hit rate <20% - moderate improvement possible
   ✅ Action: Increase TTL to 450-600s (7.5-10min)
ℹ️ INFO: Very few repeated queries detected
   ✅ Action: Consider query normalization (remove noise from cache keys)
ℹ️ INFO: Average query repetition gap is 1965s (>32min)
   ✅ Action: Consider increasing TTL to 2947s to capture patterns

## Top Repeated Query Patterns

- `h0_a0`: 50 times
- `h8_a3`: 5 times
- `h0_a1`: 52 times