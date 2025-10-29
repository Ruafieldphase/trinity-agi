#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
캐싱 메커니즘 - 성능 최적화를 위한 캐싱 시스템

이 모듈은 에이전트 시스템의 성능을 향상시키기 위한 캐싱을 제공합니다.
"""

import sys
import io
import time
import threading
import hashlib
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================================
# 캐시 항목
# ============================================================================

class CachePolicy(Enum):
    """캐시 정책"""
    LRU = "lru"        # Least Recently Used
    LFU = "lfu"        # Least Frequently Used
    FIFO = "fifo"      # First In First Out


@dataclass
class CacheEntry:
    """캐시 항목"""
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    ttl: Optional[float] = None  # 초 단위

    def is_expired(self) -> bool:
        """만료 여부 확인"""
        if self.ttl is None:
            return False
        elapsed = (datetime.now() - self.created_at).total_seconds()
        return elapsed > self.ttl

    def touch(self):
        """마지막 접근 시간 업데이트"""
        self.accessed_at = datetime.now()
        self.access_count += 1


# ============================================================================
# 캐시
# ============================================================================

class Cache:
    """캐시"""

    def __init__(
        self,
        max_size: int = 1000,
        policy: CachePolicy = CachePolicy.LRU,
        default_ttl: Optional[float] = None
    ):
        """캐시 초기화"""
        self.max_size = max_size
        self.policy = policy
        self.default_ttl = default_ttl

        # 캐시 저장소
        self.cache: Dict[str, CacheEntry] = {}
        self.lock = threading.Lock()

        # 통계
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """캐시 설정"""
        with self.lock:
            # 만료된 항목 정리
            self._cleanup_expired()

            # 용량 확인
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict()

            # 캐시 항목 생성
            now = datetime.now()
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                accessed_at=now,
                ttl=ttl or self.default_ttl
            )
            self.cache[key] = entry

    def get(self, key: str) -> Optional[Any]:
        """캐시 조회"""
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None

            entry = self.cache[key]

            # 만료 확인
            if entry.is_expired():
                del self.cache[key]
                self.misses += 1
                return None

            # 접근 기록
            entry.touch()
            self.hits += 1
            return entry.value

    def delete(self, key: str) -> bool:
        """캐시 항목 삭제"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    def clear(self):
        """캐시 초기화"""
        with self.lock:
            self.cache.clear()

    def _cleanup_expired(self):
        """만료된 항목 정리"""
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self.cache[key]

    def _evict(self):
        """캐시 항목 제거"""
        if not self.cache:
            return

        if self.policy == CachePolicy.LRU:
            # 가장 최근에 접근하지 않은 항목 제거
            key_to_evict = min(
                self.cache.keys(),
                key=lambda k: self.cache[k].accessed_at
            )
        elif self.policy == CachePolicy.LFU:
            # 가장 적게 접근된 항목 제거
            key_to_evict = min(
                self.cache.keys(),
                key=lambda k: self.cache[k].access_count
            )
        else:  # FIFO
            # 가장 먼저 들어온 항목 제거
            key_to_evict = min(
                self.cache.keys(),
                key=lambda k: self.cache[k].created_at
            )

        del self.cache[key_to_evict]
        self.evictions += 1

    def get_size(self) -> int:
        """캐시 크기"""
        with self.lock:
            return len(self.cache)

    def get_hit_rate(self) -> float:
        """캐시 히트율"""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total * 100

    def get_statistics(self) -> Dict[str, Any]:
        """통계"""
        with self.lock:
            return {
                "current_size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": self.get_hit_rate(),
                "evictions": self.evictions,
                "policy": self.policy.value
            }


# ============================================================================
# 함수 캐싱 데코레이터
# ============================================================================

class CachedFunction:
    """캐시된 함수"""

    def __init__(self, func: Callable, cache: Cache, ttl: Optional[float] = None):
        """초기화"""
        self.func = func
        self.cache = cache
        self.ttl = ttl
        self.call_count = 0
        self.cached_call_count = 0

    def _make_key(self, args, kwargs) -> str:
        """함수 호출에 대한 캐시 키 생성"""
        key_data = f"{self.func.__name__}_{args}_{kwargs}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def __call__(self, *args, **kwargs) -> Any:
        """캐시된 함수 호출"""
        cache_key = self._make_key(args, kwargs)

        # 캐시 조회
        cached_value = self.cache.get(cache_key)
        if cached_value is not None:
            self.cached_call_count += 1
            return cached_value

        # 함수 실행
        self.call_count += 1
        result = self.func(*args, **kwargs)

        # 캐시 저장
        self.cache.set(cache_key, result, ttl=self.ttl)

        return result

    def get_stats(self) -> Dict[str, Any]:
        """통계"""
        return {
            "function": self.func.__name__,
            "call_count": self.call_count,
            "cached_call_count": self.cached_call_count,
            "total_calls": self.call_count + self.cached_call_count,
            "cache_efficiency": (
                self.cached_call_count / (self.call_count + self.cached_call_count) * 100
                if (self.call_count + self.cached_call_count) > 0 else 0
            )
        }


def cached(cache: Cache, ttl: Optional[float] = None):
    """캐싱 데코레이터"""
    def decorator(func: Callable) -> CachedFunction:
        return CachedFunction(func, cache, ttl)
    return decorator


# ============================================================================
# 데모: 캐싱 시스템
# ============================================================================

def demo_caching():
    """캐싱 시스템 데모"""
    print("=" * 80)
    print("캐싱 시스템 데모")
    print("=" * 80)

    # 캐시 생성
    print("\n[1단계] 캐시 생성")
    print("-" * 80)

    cache = Cache(max_size=100, policy=CachePolicy.LRU)
    print(f"✓ LRU 정책으로 캐시 생성 (최대 크기: 100)")

    # 기본 캐싱 테스트
    print("\n[2단계] 기본 캐싱 테스트")
    print("-" * 80)

    # 데이터 저장
    cache.set("key1", {"value": "data1"})
    cache.set("key2", {"value": "data2"})
    cache.set("key3", {"value": "data3"})

    print("3개 항목 캐시에 저장됨")

    # 데이터 조회
    result1 = cache.get("key1")
    result2 = cache.get("key1")  # 캐시 히트
    result3 = cache.get("key4")  # 캐시 미스

    print(f"✓ key1 조회 (캐시 미스)")
    print(f"✓ key1 조회 (캐시 히트)")
    print(f"✓ key4 조회 (미존재)")

    # 통계
    stats = cache.get_statistics()
    print(f"\n캐시 통계:")
    print(f"  현재 크기: {stats['current_size']}")
    print(f"  최대 크기: {stats['max_size']}")
    print(f"  히트: {stats['hits']}")
    print(f"  미스: {stats['misses']}")
    print(f"  히트율: {stats['hit_rate']:.1f}%")
    print(f"  제거: {stats['evictions']}")

    # TTL 테스트
    print("\n[3단계] TTL (만료시간) 테스트")
    print("-" * 80)

    cache.set("ttl_key", "expiring_value", ttl=1.0)
    print("✓ TTL 1초로 데이터 캐시 설정")

    result = cache.get("ttl_key")
    print(f"✓ 즉시 조회: {result}")

    time.sleep(1.1)
    result = cache.get("ttl_key")
    print(f"✓ 1.1초 후 조회: {result} (만료됨)")

    # 캐싱 정책 비교
    print("\n[4단계] 캐싱 정책 비교")
    print("-" * 80)

    policies = [CachePolicy.LRU, CachePolicy.LFU, CachePolicy.FIFO]

    for policy in policies:
        cache = Cache(max_size=3, policy=policy)
        print(f"\n{policy.value.upper()} 정책:")

        # 데이터 추가
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        print(f"  초기 항목: a, b, c")

        # 접근 패턴
        cache.get("a")  # a 접근
        cache.get("a")  # a 다시 접근
        cache.get("b")  # b 접근

        # 용량 초과시 제거 정책 테스트
        cache.set("d", 4)
        print(f"  항목 d 추가시 제거됨: {cache.get_statistics()['evictions']}개")
        print(f"  현재 항목: {list(cache.cache.keys())}")


def demo_cached_function():
    """함수 캐싱 데모"""
    print("\n" + "=" * 80)
    print("함수 캐싱 데모")
    print("=" * 80)

    cache = Cache(max_size=100)

    # 캐시된 함수 생성
    @cached(cache, ttl=60)
    def expensive_function(x: int) -> int:
        """비용이 많이 드는 함수"""
        time.sleep(0.1)
        return x * 2

    print("\n[1단계] 캐시된 함수 호출")
    print("-" * 80)

    # 첫 호출 (캐시 미스)
    start = time.time()
    result1 = expensive_function(5)
    time1 = time.time() - start
    print(f"✓ expensive_function(5) = {result1} (시간: {time1:.3f}초)")

    # 두 번째 호출 (캐시 히트)
    start = time.time()
    result2 = expensive_function(5)
    time2 = time.time() - start
    print(f"✓ expensive_function(5) = {result2} (시간: {time2:.3f}초) [캐시됨]")

    # 다른 인자로 호출
    start = time.time()
    result3 = expensive_function(10)
    time3 = time.time() - start
    print(f"✓ expensive_function(10) = {result3} (시간: {time3:.3f}초)")

    # 함수 통계
    print(f"\n함수 통계:")
    stats = expensive_function.get_stats()
    print(f"  함수 호출: {stats['total_calls']}")
    print(f"  실제 실행: {stats['call_count']}")
    print(f"  캐시 히트: {stats['cached_call_count']}")
    print(f"  캐시 효율성: {stats['cache_efficiency']:.1f}%")

    print(f"\n캐시 성능:")
    print(f"  속도 향상: {time1 / time2:.1f}배 (첫 호출 vs 캐시된 호출)")

    print("\n" + "=" * 80)
    print("함수 캐싱 데모 완료!")
    print("=" * 80)


def demo_agent_caching():
    """에이전트 시스템에서의 캐싱 데모"""
    print("\n" + "=" * 80)
    print("에이전트 캐싱 데모")
    print("=" * 80)

    from agent_sena import SenaAgent
    from agent_interface import AgentConfig, AgentRole

    cache = Cache(max_size=100, default_ttl=300)  # 5분 TTL

    @cached(cache, ttl=300)
    def analyze_and_cache(problem: str) -> Dict[str, Any]:
        """분석 결과 캐싱"""
        sena = SenaAgent(AgentConfig(
            role=AgentRole.SENA,
            name="Sena",
            description="분석가"
        ))
        sena.initialize()
        return sena.perform_analysis(problem)

    print("\n[에이전트 캐싱]")
    print("-" * 80)

    problems = [
        "데이터 분석",
        "웹 크롤링",
        "데이터 분석",  # 캐시 히트
        "텍스트 처리",
        "데이터 분석",  # 캐시 히트
    ]

    for problem in problems:
        start = time.time()
        result = analyze_and_cache(problem)
        elapsed = (time.time() - start) * 1000

        if analyze_and_cache.get_stats()['cached_call_count'] > 0:
            print(f"  {problem}: {elapsed:.1f}ms [캐시됨]")
        else:
            print(f"  {problem}: {elapsed:.1f}ms")

    print(f"\n캐싱 효율성: {analyze_and_cache.get_stats()['cache_efficiency']:.1f}%")


if __name__ == "__main__":
    demo_caching()
    demo_cached_function()
    demo_agent_caching()
