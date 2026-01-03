#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Response Cache Unit Test
Tests cache hit/miss behavior without full pipeline
"""
import sys
import os
from pathlib import Path
from workspace_root import get_workspace_root

# Add project root to path
_root = get_workspace_root()
sys.path.insert(0, str(_root))
sys.path.insert(0, str(_root / "fdo_agi_repo"))

from fdo_agi_repo.orchestrator.response_cache import get_response_cache, ResponseCache
from fdo_agi_repo.orchestrator.contracts import TaskSpec, PersonaOutput

def test_cache_hit_miss():
    """Test basic cache hit/miss logic"""
    print("=== Response Cache Unit Test ===")
    print()
    
    # Initialize cache
    cache = get_response_cache(ttl_seconds=3600, max_entries=100)
    cache.clear()  # Fresh start
    
    # Mock task
    task = TaskSpec(
        task_id="test-001",
        title="Response Cache Test",
        goal="AGI 자기교정 루프 설명 3문장",
        scope="doc"
    )
    
    # Mock response
    mock_response = {
        "task_id": "test-001",
        "persona": "thesis",
        "summary": "AGI 자기교정 루프는 세 단계로 구성됩니다.",
        "rationale": "Test rationale",
        "actions": [],
        "citations": []
    }
    
    print("[Test 1] Cache miss (first call)")
    result1 = cache.get("thesis", task.goal, "")
    assert result1 is None, "Expected cache miss"
    print("✅ PASS: Cache miss as expected")
    
    print()
    print("[Test 2] Store in cache")
    cache.put("thesis", task.goal, mock_response, "", latency_ms=1500.0)
    print("✅ PASS: Stored in cache")
    
    print()
    print("[Test 3] Cache hit (second call)")
    result2 = cache.get("thesis", task.goal, "")
    assert result2 is not None, "Expected cache hit"
    assert result2["summary"] == mock_response["summary"], "Cached data mismatch"
    print("✅ PASS: Cache hit with correct data")
    
    print()
    print("[Test 4] Cache hit (third call)")
    result3 = cache.get("thesis", task.goal, "")
    assert result3 is not None, "Expected cache hit"
    print("✅ PASS: Cache hit again")
    
    print()
    print("[Test 5] Different goal = cache miss")
    result4 = cache.get("thesis", "다른 goal", "")
    assert result4 is None, "Expected cache miss for different goal"
    print("✅ PASS: Different goal = cache miss")
    
    print()
    print("[Test 6] Different persona = cache miss")
    result5 = cache.get("antithesis", task.goal, "")
    assert result5 is None, "Expected cache miss for different persona"
    print("✅ PASS: Different persona = cache miss")
    
    print()
    print("=== Cache Statistics ===")
    stats = cache.get_stats()
    print(f"Cache size: {stats['cache_size']}")
    print(f"Thesis hits: {stats['thesis_hits']}")
    print(f"Thesis misses: {stats['thesis_misses']}")
    print(f"Thesis hit rate: {stats['thesis_hit_rate']}%")
    print(f"Antithesis misses: {stats['antithesis_misses']}")
    print(f"Total time saved: {stats['total_time_saved_sec']}s")
    
    print()
    print("✅ ALL TESTS PASSED")
    return 0

if __name__ == "__main__":
    sys.exit(test_cache_hit_miss())
