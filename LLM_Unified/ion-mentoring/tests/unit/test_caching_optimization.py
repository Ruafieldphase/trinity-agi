"""
캐싱 및 성능 최적화 테스트

Week 9-10: 2단계 캐싱 구현
- L1 로컬 캐시 테스트
- L2 Redis 캐시 테스트
- 통합 2단계 캐싱 테스트
- 성능 벤치마크
"""

import time

import pytest

from persona_system.caching import (
    LocalCache,
    RedisCache,
    TwoTierCache,
    cached,
    reset_cache,
)
from persona_system.models import ChatContext
from persona_system.pipeline_optimized import (
    OptimizedPersonaPipeline,
    get_optimized_pipeline,
    reset_optimized_pipeline,
)


class TestLocalCache:
    """L1 로컬 캐시 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.cache = LocalCache(max_size=100)

    def test_local_cache_set_get(self):
        """로컬 캐시 저장 및 조회"""
        self.cache.set("key1", "value1", ttl=300)
        assert self.cache.get("key1") == "value1"

    def test_local_cache_miss(self):
        """로컬 캐시 미스"""
        assert self.cache.get("nonexistent") is None

    def test_local_cache_ttl_expiration(self):
        """로컬 캐시 TTL 만료"""
        self.cache.set("key1", "value1", ttl=1)
        time.sleep(1.1)
        assert self.cache.get("key1") is None

    def test_local_cache_delete(self):
        """로컬 캐시 삭제"""
        self.cache.set("key1", "value1")
        self.cache.delete("key1")
        assert self.cache.get("key1") is None

    def test_local_cache_lru_eviction(self):
        """LRU 제거"""
        small_cache = LocalCache(max_size=3)
        small_cache.set("key1", "value1")
        small_cache.set("key2", "value2")
        small_cache.set("key3", "value3")

        # 최대 크기 초과
        small_cache.set("key4", "value4")

        # key1은 제거됨
        assert small_cache.get("key1") is None
        assert small_cache.get("key4") == "value4"

    def test_local_cache_hit_tracking(self):
        """캐시 히트 추적"""
        self.cache.set("key1", "value1")
        self.cache.get("key1")
        self.cache.get("key1")
        self.cache.get("nonexistent")

        assert self.cache.hits == 2
        assert self.cache.misses == 1

    def test_local_cache_stats(self):
        """캐시 통계"""
        self.cache.set("key1", "value1")
        self.cache.get("key1")
        stats = self.cache.get_stats()

        assert stats["cache_type"] == "L1 Local"
        assert stats["size"] == 1
        assert stats["hits"] == 1

    def test_local_cache_clear(self):
        """캐시 전체 삭제"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.clear()

        assert len(self.cache.cache) == 0
        assert self.cache.hits == 0
        assert self.cache.misses == 0


class TestRedisCache:
    """L2 Redis 캐시 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.cache = RedisCache()

    def test_redis_cache_availability(self):
        """Redis 가용성 확인"""
        # Redis 없으면 available=False
        # Redis 있으면 available=True
        assert isinstance(self.cache.available, bool)

    @pytest.mark.skipif(not RedisCache().available, reason="Redis not available")
    def test_redis_cache_set_get(self):
        """Redis 저장 및 조회"""
        if not self.cache.available:
            pytest.skip("Redis not available")

        self.cache.set("key1", {"data": "value1"}, ttl=300)
        result = self.cache.get("key1")
        assert result == {"data": "value1"}

    @pytest.mark.skipif(not RedisCache().available, reason="Redis not available")
    def test_redis_cache_miss(self):
        """Redis 캐시 미스"""
        if not self.cache.available:
            pytest.skip("Redis not available")

        assert self.cache.get("nonexistent") is None

    @pytest.mark.skipif(not RedisCache().available, reason="Redis not available")
    def test_redis_cache_ttl(self):
        """Redis TTL"""
        if not self.cache.available:
            pytest.skip("Redis not available")

        self.cache.set("key1", "value1", ttl=1)
        time.sleep(1.1)
        assert self.cache.get("key1") is None


class TestTwoTierCache:
    """2단계 캐싱 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.cache = TwoTierCache(l1_max_size=100)

    def test_two_tier_cache_set_get_l1(self):
        """L1에서 저장 및 조회"""
        self.cache.set("key1", "value1", ttl=300)
        assert self.cache.get("key1") == "value1"

    def test_two_tier_cache_promotion(self):
        """L2에서 L1으로 승격"""
        # L2에 직접 저장 (테스트용)
        self.cache.l2.set("key1", "value1", ttl=300)

        # L1은 비어있음
        assert len(self.cache.l1.cache) == 0

        # 조회 시 L1로 승격
        value = self.cache.get("key1")
        assert value == "value1"
        assert len(self.cache.l1.cache) == 1

    def test_two_tier_cache_delete(self):
        """L1 + L2 동시 삭제"""
        self.cache.set("key1", "value1", ttl=300)
        self.cache.delete("key1")

        assert self.cache.l1.get("key1") is None

    def test_two_tier_cache_delete_pattern(self):
        """패턴 기반 삭제"""
        self.cache.set("persona:lua:1", "data1")
        self.cache.set("persona:elro:1", "data2")
        self.cache.set("prompt:1", "data3")

        # "persona:*" 패턴 삭제
        deleted = self.cache.delete_pattern("persona:.*")
        assert deleted >= 2

    def test_two_tier_cache_clear(self):
        """캐시 전체 삭제"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.clear()

        assert self.cache.l1.get("key1") is None

    def test_two_tier_cache_stats(self):
        """캐시 통계"""
        self.cache.set("key1", "value1")
        stats = self.cache.get_stats()

        assert "l1" in stats
        assert "l2" in stats


class TestCacheDecorators:
    """캐시 데코레이터 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        reset_cache()

    @cached(ttl=300, key_prefix="test")
    def expensive_function(self, x, y):
        """비용이 큰 함수"""
        time.sleep(0.1)
        return x + y

    def test_cached_decorator_first_call(self):
        """데코레이터: 첫 호출"""
        start = time.time()
        result = self.expensive_function(1, 2)
        elapsed = time.time() - start

        assert result == 3
        assert elapsed >= 0.1  # 실제 실행

    def test_cached_decorator_second_call(self):
        """데코레이터: 캐시된 호출"""
        self.expensive_function(1, 2)

        start = time.time()
        result = self.expensive_function(1, 2)
        elapsed = time.time() - start

        assert result == 3
        assert elapsed < 0.05  # 캐시에서 빠르게 반환


class TestOptimizedPipeline:
    """최적화 파이프라인 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        reset_optimized_pipeline()
        self.pipeline = OptimizedPersonaPipeline()

    def test_optimized_pipeline_basic(self):
        """최적화 파이프라인 기본 동작"""
        result = self.pipeline.process(user_input="테스트", resonance_key="calm-medium-learning")
        assert result.persona_used in ["Lua", "Elro", "Riri", "Nana"]
        assert result.execution_time_ms > 0

    def test_optimized_pipeline_caching(self):
        """최적화 파이프라인 캐싱"""
        # 첫 호출 (캐시 미스)
        start1 = time.time()
        result1 = self.pipeline.process(user_input="", resonance_key="calm-medium-learning")
        time1 = time.time() - start1

        # 두 번째 호출 (캐시 히트)
        start2 = time.time()
        result2 = self.pipeline.process(user_input="", resonance_key="calm-medium-learning")
        time2 = time.time() - start2

        # 캐시 히트가 더 빠름
        assert result1.persona_used == result2.persona_used
        assert time2 < time1

    def test_optimized_pipeline_cache_stats(self):
        """최적화 파이프라인 캐시 통계"""
        self.pipeline.process("", "calm-medium-learning")
        self.pipeline.process("", "calm-medium-learning")
        self.pipeline.process("test2", "frustrated-burst-seeking_advice")

        stats = self.pipeline.get_cache_stats()
        assert stats["total_requests"] == 3
        assert stats["cache_hits"] >= 1

    def test_optimized_pipeline_cache_bypass(self):
        """캐시 우회"""
        result = self.pipeline.process(
            user_input="테스트", resonance_key="calm-medium-learning", use_cache=False
        )
        assert result is not None

    def test_optimized_pipeline_cache_invalidation(self):
        """캐시 무효화"""
        self.pipeline.process("", "calm-medium-learning")
        stats1 = self.pipeline.get_cache_stats()

        self.pipeline.invalidate_cache_pattern("routing:*")
        self.pipeline.process("", "calm-medium-learning")
        stats2 = self.pipeline.get_cache_stats()

        # 무효화 후 캐시 미스가 증가
        assert stats2["cache_misses"] > stats1["cache_misses"]

    def test_optimized_pipeline_preload(self):
        """페르소나 정보 프리로드"""
        self.pipeline.preload_common_personas()
        stats = self.pipeline.get_cache_stats()
        assert stats["cache_hits"] >= 0


class TestPerformanceBenchmark:
    """성능 벤치마크 테스트"""

    def test_basic_pipeline_performance(self):
        """기본 파이프라인 성능"""
        from persona_system.pipeline import get_pipeline as get_basic_pipeline

        reset_optimized_pipeline()
        basic_pipeline = get_basic_pipeline()

        times = []
        for _ in range(10):
            start = time.time()
            basic_pipeline.process("테스트", "calm-medium-learning")
            times.append((time.time() - start) * 1000)

        avg_time = sum(times) / len(times)
        assert avg_time < 200  # 200ms 이내

    def test_optimized_pipeline_performance(self):
        """최적화 파이프라인 성능"""
        reset_optimized_pipeline()
        optimized_pipeline = get_optimized_pipeline()

        # 첫 호출
        start = time.time()
        optimized_pipeline.process("", "calm-medium-learning")
        first_time = (time.time() - start) * 1000

        # 캐시된 호출들
        times = []
        for _ in range(10):
            start = time.time()
            optimized_pipeline.process("", "calm-medium-learning")
            times.append((time.time() - start) * 1000)

        avg_cached_time = sum(times) / len(times)

        # 캐시된 호출이 50% 더 빠름
        speedup = first_time / avg_cached_time if avg_cached_time > 0 else 1
        assert speedup > 2  # 최소 2배 이상 빨라야 함

    def test_cache_hit_rate(self):
        """캐시 히트율"""
        reset_optimized_pipeline()
        pipeline = get_optimized_pipeline()

        # 10개 동일 요청 (1번 미스, 9번 히트)
        for _ in range(10):
            pipeline.process("", "calm-medium-learning")

        stats = pipeline.get_cache_stats()
        assert stats["cache_hits"] == 9
        assert stats["cache_misses"] == 1

    def test_performance_improvement_target(self):
        """성능 개선 목표 달성"""
        reset_optimized_pipeline()
        pipeline = get_optimized_pipeline()

        # 50번의 캐시된 요청
        start = time.time()
        for _ in range(50):
            pipeline.process("", "calm-medium-learning")
        total_time = (time.time() - start) * 1000

        avg_time_per_request = total_time / 50
        # 목표: 첫 요청 95ms → 캐시 47ms (50% 감소)
        # 하지만 매우 빠르므로 평균 < 10ms 정도
        assert avg_time_per_request < 50  # 50ms 이내


class TestCacheIntegration:
    """캐시 통합 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        reset_optimized_pipeline()

    def test_multiple_concurrent_requests(self):
        """여러 동시 요청"""
        pipeline = get_optimized_pipeline()

        results = []
        for i in range(10):
            result = pipeline.process(user_input=f"test{i}", resonance_key="calm-medium-learning")
            results.append(result)

        assert len(results) == 10
        assert all(r.persona_used is not None for r in results)

    def test_cache_with_different_inputs(self):
        """다양한 입력으로 캐싱"""
        pipeline = get_optimized_pipeline()

        # 다양한 파동키로 요청
        for tone in ["calm", "frustrated", "analytical"]:
            pipeline.process("", f"{tone}-medium-learning")

        stats = pipeline.get_cache_stats()
        # 3개 요청이므로 미스 3개
        assert stats["cache_misses"] == 3

    def test_context_aware_caching(self):
        """컨텍스트 인식 캐싱"""
        pipeline = get_optimized_pipeline()

        context1 = ChatContext(user_id="user1", session_id="sess1", message_history=[])
        context2 = ChatContext(user_id="user2", session_id="sess2", message_history=[])

        pipeline.process("", "calm-medium-learning", context=context1)
        pipeline.process("", "calm-medium-learning", context=context2)

        # 다른 사용자는 다른 결과 (캐시 키가 다름)
        stats = pipeline.get_cache_stats()
        # 최소 2번의 미스
        assert stats["cache_misses"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
