# Cache Performance Timeline

Generated: 2025-10-28T03:08:50.779890+00:00

## Overview

- Window: Last 24 hours
- Interval: 2 hour(s) per bucket
- Total Events: 18
- Total Buckets: 3
- Overall Hit Rate: **0.0%**

## Timeline

| Bucket | Start Time | Hit Rate | Hits | Misses | Total | Avg Latency |
|--------|------------|----------|------|--------|-------|-------------|
| bucket_0 | 14:27:38 | **0.0%** | 0 | 2 | 2 | 0.0ms |
| bucket_4 | 22:27:38 | **0.0%** | 0 | 10 | 10 | 0.0ms |
| bucket_5 | 00:27:38 | **0.0%** | 0 | 6 | 6 | 0.0ms |

## Interpretation

⚠️ **LOW** - Cache not yet effective (<5%). Wait longer or increase TTL.

## Next Steps

1. Run AGI tasks for 6-12 more hours
2. Re-run this timeline monitor
3. If hit rate stays <40% after 24h, consider:
   - Increasing TTL to 1200s (20 minutes)
   - Adding query normalization
