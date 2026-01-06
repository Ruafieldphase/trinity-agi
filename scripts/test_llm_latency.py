#!/usr/bin/env python3
"""
Quick LLM Latency Test (ASCII-safe)
===================================

Measures response time for Local LLM endpoint.

Notes
- Defaults to http://localhost:8080/v1/chat/completions
- Can be overridden via env vars:
  * LOCAL_LLM_BASE (e.g., http://localhost:8080)
  * LOCAL_LLM_PATH (e.g., /v1/chat/completions)
  * LOCAL_LLM_MODEL (default: "local")
  * LOCAL_LLM_TIMEOUT (seconds, default: 30)
  * LLM_LATENCY_TARGET_MS (default: 1500)
"""

import os
import time
import requests
from statistics import mean, stdev


def _llm_url() -> str:
    base = os.environ.get("LOCAL_LLM_BASE", "http://localhost:8080")
    path = os.environ.get("LOCAL_LLM_PATH", "/v1/chat/completions")
    return base.rstrip("/") + "/" + path.lstrip("/")


def test_single_request(prompt: str, max_tokens: int = 50, temperature: float = 0.7):
    """Send single request and return (latency_ms, content)."""
    url = _llm_url()
    start = time.time()

    response = requests.post(
        url,
        json={
            "model": os.environ.get("LOCAL_LLM_MODEL", "local"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=float(os.environ.get("LOCAL_LLM_TIMEOUT", "30")),
        headers={"Accept": "application/json", "Accept-Encoding": "gzip, deflate"},
    )

    elapsed = (time.time() - start) * 1000

    if response.status_code == 200:
        data = response.json()
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        return elapsed, content
    else:
        raise Exception(f"API Error: {response.status_code}")


def main():
    print("=" * 60)
    print("LOCAL LLM LATENCY TEST")
    print("Endpoint:", _llm_url())
    print("=" * 60)

    test_prompts = [
        "What is 2+2?",
        "Explain caching in 20 words.",
        "What is RAG?",
        "Define AGI briefly.",
        "What is BM25 algorithm?",
    ]

    latencies = []

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n[{i}/{len(test_prompts)}] Testing: {prompt[:40]}...")
        try:
            # Use slightly optimized defaults
            elapsed, content = test_single_request(prompt, max_tokens=150, temperature=0.5)
            latencies.append(elapsed)
            print(f"  OK  {elapsed:.0f}ms")
            print(f"  Response: {content[:60]}...")
        except Exception as e:
            print(f"  FAIL: {e}")

    if latencies:
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        print(f"  Tests: {len(latencies)}/{len(test_prompts)}")
        print(f"  Avg Latency: {mean(latencies):.0f}ms")
        print(f"  Min: {min(latencies):.0f}ms")
        print(f"  Max: {max(latencies):.0f}ms")
        if len(latencies) > 1:
            print(f"  StdDev: {stdev(latencies):.0f}ms")

        target = int(os.environ.get("LLM_LATENCY_TARGET_MS", "1500"))
        current = mean(latencies)
        if current <= target:
            print(f"\n  OK  Target achieved (<= {target}ms)")
        else:
            gap = current - target
            print(f"\n  WARN Gap: +{gap:.0f}ms above target")


if __name__ == "__main__":
    main()

