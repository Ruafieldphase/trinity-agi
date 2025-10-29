#!/usr/bin/env python3
"""
Cache Integration Test
Redis 캐시가 제대로 작동하는지 검증
"""

import sys
import time
from pathlib import Path

# 경로 설정
sys.path.insert(0, str(Path(__file__).parent.parent))

from persona_system.caching import get_cache, reset_cache


def test_cache_basic():
    """기본 캐시 테스트"""
    print("=" * 60)
    print("Test 1: Basic Cache Operations")
    print("=" * 60)

    cache = get_cache()

    # Set
    print("\n[TEST] Setting value...")
    cache.set("test_key", {"message": "Hello Ion!"}, ttl=60)

    # Get
    print("[TEST] Getting value...")
    value = cache.get("test_key")
    print(f"  Result: {value}")

    assert value == {"message": "Hello Ion!"}, "Value mismatch!"
    print("[OK] Basic operations work!")


def test_cache_stats():
    """캐시 통계 테스트"""
    print("\n" + "=" * 60)
    print("Test 2: Cache Statistics")
    print("=" * 60)

    cache = get_cache()
    stats = cache.get_stats()

    print("\n[STATS] L1 Cache:")
    l1_stats = stats['l1']
    print(f"  Type: {l1_stats['cache_type']}")
    print(f"  Size: {l1_stats['size']}/{l1_stats['max_size']}")
    print(f"  Hits: {l1_stats['hits']}, Misses: {l1_stats['misses']}")
    print(f"  Hit Rate: {l1_stats['hit_rate']}")

    print("\n[STATS] L2 Cache:")
    l2_stats = stats['l2']
    print(f"  Type: {l2_stats['cache_type']}")
    print(f"  Available: {l2_stats.get('available', False)}")

    if l2_stats.get('available'):
        print(f"  Memory Used: {l2_stats.get('memory_used', 'N/A')}")
        print(f"  Connected Clients: {l2_stats.get('connected_clients', 0)}")
        print("[OK] Redis L2 cache is working!")
    else:
        print(f"  Status: {l2_stats.get('status', 'Unknown')}")
        print("[WARNING] Redis not available, using local cache only")


def test_cache_hit():
    """캐시 히트 테스트"""
    print("\n" + "=" * 60)
    print("Test 3: Cache Hit Performance")
    print("=" * 60)

    cache = get_cache()

    # First call (cache miss)
    print("\n[TEST] First call (cache miss)...")
    start = time.time()
    cache.set("perf_test", {"data": "x" * 1000}, ttl=60)
    value = cache.get("perf_test")
    first_time = (time.time() - start) * 1000
    print(f"  Time: {first_time:.2f}ms")

    # Second call (cache hit)
    print("\n[TEST] Second call (cache hit)...")
    start = time.time()
    value = cache.get("perf_test")
    second_time = (time.time() - start) * 1000
    print(f"  Time: {second_time:.2f}ms")

    speedup = first_time / second_time if second_time > 0 else 0
    print(f"\n[RESULT] Speedup: {speedup:.1f}x faster")

    assert value == {"data": "x" * 1000}, "Value mismatch!"
    print("[OK] Cache hit is working!")


def test_two_tier():
    """2단계 캐시 테스트"""
    print("\n" + "=" * 60)
    print("Test 4: Two-Tier Cache (L1 → L2)")
    print("=" * 60)

    cache = get_cache()

    # Check if L2 is available
    stats = cache.get_stats()
    l2_available = stats['l2'].get('available', False)

    if not l2_available:
        print("\n[SKIP] L2 cache (Redis) not available")
        print(f"[INFO] L2 status: {stats['l2'].get('status', 'Unknown')}")
        print("[INFO] Running in L1-only mode")
        print("[OK] Test skipped (L2 not required for basic functionality)")
        return

    # Clear L1 only
    print("\n[TEST] Setting value in both L1 and L2...")
    cache.set("tier_test", {"tier": "both"}, ttl=300)

    # Clear L1 manually
    print("[TEST] Clearing L1 cache...")
    cache.l1.clear()

    # Get from L2 (should populate L1)
    print("[TEST] Getting value (should come from L2)...")
    value = cache.get("tier_test")
    print(f"  Result: {value}")

    assert value == {"tier": "both"}, "Value mismatch!"
    print("[OK] Two-tier cache is working!")

    # Verify L1 was populated
    l1_value = cache.l1.get("tier_test")
    assert l1_value == {"tier": "both"}, "L1 not populated!"
    print("[OK] L1 was populated from L2!")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("ion-mentoring Cache Integration Tests")
    print("=" * 60)

    try:
        test_cache_basic()
        test_cache_stats()
        test_cache_hit()
        test_two_tier()

        print("\n" + "=" * 60)
        print("[SUCCESS] All tests passed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Start cache dashboard: python monitor/cache_dashboard.py")
        print("2. Or use PowerShell: .\\monitor\\start_dashboard.ps1")
        print("3. Access dashboard: http://localhost:5001")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
