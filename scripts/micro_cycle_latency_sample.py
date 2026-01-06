#!/usr/bin/env python
"""Micro-cycle latency sampling script.
Performs lightweight health endpoint requests to gather a baseline latency profile.
Writes results to outputs/latency_samples_micro_cycle.json.
"""
from __future__ import annotations
import time, json, statistics, pathlib, datetime
import urllib.request
import ssl

ENDPOINTS = [
    ("task_queue", "http://127.0.0.1:8091/api/health"),
    ("original_data", "http://127.0.0.1:8093/health"),
    ("observer", "http://127.0.0.1:8095/health"),
]
SAMPLES_PER_ENDPOINT = 3
TIMEOUT = 2.5

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

results = []
for name, url in ENDPOINTS:
    latencies = []
    status_codes = []
    for i in range(SAMPLES_PER_ENDPOINT):
        start = time.perf_counter()
        ok = False
        code = None
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT, context=ctx) as resp:
                code = resp.getcode()
                ok = True
        except Exception as e:
            code = getattr(e, 'code', None)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        latencies.append(elapsed_ms)
        status_codes.append(code if code is not None else (200 if ok else -1))
        # tiny pause to avoid hammering
        time.sleep(0.05)
    result = {
        "endpoint": name,
        "url": url,
        "samples_ms": latencies,
        "status_codes": status_codes,
        "min_ms": min(latencies),
        "max_ms": max(latencies),
        "p50_ms": statistics.median(latencies),
        "mean_ms": statistics.mean(latencies),
        "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z"
    }
    results.append(result)

out_path = pathlib.Path("outputs/latency_samples_micro_cycle.json")
out_path.parent.mkdir(parents=True, exist_ok=True)
with out_path.open("w", encoding="utf-8") as f:
    json.dump({"meta": {"script": "micro_cycle_latency_sample", "samples_per_endpoint": SAMPLES_PER_ENDPOINT}, "results": results}, f, ensure_ascii=False, indent=2)

print(f"Latency samples written to {out_path}")
