"""
Redis 2단계 캐싱 레이어

Week 9-10: 성능 최적화
L1 로컬 캐시 + L2 Redis 캐시 구현
- 응답시간 50% 단축 목표
- TTL 기반 자동 만료
- 캐시 무효화 전략
- 성능 모니터링
- 비동기 Redis 지원 (FastAPI 최적화)
"""

import asyncio
import logging
import os
import pickle
import re
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

_TRUTHY_VALUES = {"1", "true", "yes", "on"}


def _is_truthy(value: Optional[str]) -> bool:
    return str(value or "").strip().lower() in _TRUTHY_VALUES


class _InMemoryRedisClient:
    """Lightweight in-memory replacement for redis.StrictRedis used in tests."""

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._command_count = 0

    def _get_record(self, key: str) -> Optional[Dict[str, Any]]:
        record = self._store.get(key)
        if not record:
            return None

        expires_at = record["expires_at"]
        if expires_at is not None and time.time() > expires_at:
            self._store.pop(key, None)
            return None

        return record

    def setex(self, key: str, ttl: int, value: Any) -> None:
        self._command_count += 1
        expires_at = time.time() + ttl if ttl else None
        self._store[key] = {"expires_at": expires_at, "value": value}

    def get(self, key: str) -> Optional[Any]:
        self._command_count += 1
        record = self._get_record(key)
        if not record:
            return None
        return record["value"]

    def delete(self, key: str) -> None:
        self._command_count += 1
        self._store.pop(key, None)

    def flushdb(self) -> None:
        self._command_count += 1
        self._store.clear()

    def keys(self, pattern: str):
        self._command_count += 1
        regex = re.compile(f"^{pattern.replace('*', '.*')}$")
        keys = []
        current_time = time.time()
        for key, record in list(self._store.items()):
            expires_at = record["expires_at"]
            if expires_at is not None and current_time > expires_at:
                self._store.pop(key, None)
                continue
            if regex.match(key):
                keys.append(key)
        return keys

    def info(self) -> Dict[str, Any]:
        self._command_count += 1
        live_keys = sum(1 for key in list(self._store.keys()) if self._get_record(key))
        return {
            "used_memory_human": f"{live_keys} keys",
            "connected_clients": 1,
            "total_commands_processed": self._command_count,
        }


@dataclass
class CacheEntry:
    """캐시 엔트리"""

    key: str
    value: Any
    ttl: int  # seconds
    created_at: datetime
    hit_count: int = 0

    def is_expired(self) -> bool:
        """만료 여부 확인"""
        elapsed = (datetime.now() - self.created_at).total_seconds()
        return elapsed > self.ttl

    def mark_hit(self) -> None:
        """히트 기록"""
        self.hit_count += 1


class ICache(ABC):
    """캐시 인터페이스"""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """값 조회"""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """값 저장"""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """값 삭제"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """캐시 전체 삭제"""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        pass


class LocalCache(ICache):
    """L1 로컬 메모리 캐시 (LRU)"""

    def __init__(self, max_size: int = 1000):
        """
        초기화

        Args:
            max_size: 최대 캐시 항목 수
        """
        self.max_size = max_size
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """
        값 조회

        Args:
            key: 캐시 키

        Returns:
            캐시된 값 또는 None
        """
        if key not in self.cache:
            self.misses += 1
            return None

        entry = self.cache[key]

        # 만료 확인
        if entry.is_expired():
            del self.cache[key]
            self.misses += 1
            return None

        # LRU: 최근 사용 항목을 끝으로 이동
        self.cache.move_to_end(key)
        entry.mark_hit()
        self.hits += 1

        return entry.value

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """
        값 저장

        Args:
            key: 캐시 키
            value: 캐시할 값
            ttl: Time-to-live (초)
        """
        # 기존 키 제거
        if key in self.cache:
            del self.cache[key]

        # 크기 제한 확인
        if len(self.cache) >= self.max_size:
            # 가장 오래된 항목 제거
            self.cache.popitem(last=False)

        # 새 항목 추가
        entry = CacheEntry(key=key, value=value, ttl=ttl, created_at=datetime.now())
        self.cache[key] = entry

    def delete(self, key: str) -> None:
        """
        값 삭제

        Args:
            key: 캐시 키
        """
        if key in self.cache:
            del self.cache[key]

    def clear(self) -> None:
        """캐시 전체 삭제"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "cache_type": "L1 Local",
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "entries": [
                {
                    "key": entry.key,
                    "ttl": entry.ttl,
                    "hit_count": entry.hit_count,
                    "expired": entry.is_expired(),
                }
                for entry in list(self.cache.values())[:10]  # 최근 10개
            ],
        }


class RedisCache(ICache):
    """L2 Redis 캐시"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        decode_responses: bool = False,
    ):
        """Initialize the Redis cache backend."""
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.decode_responses = decode_responses
        self.redis_client = None
        self.available = False
        self._in_memory_mode = False

        env = (os.getenv("ENVIRONMENT") or "").strip().lower()
        force_in_memory = _is_truthy(os.getenv("ION_USE_IN_MEMORY_REDIS"))
        use_in_memory = force_in_memory or env == "test"

        if use_in_memory:
            self._init_in_memory()
            return

        try:
            import redis

            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=decode_responses,
            )
            self.redis_client.ping()
            self.available = True
            logger.info(f"Redis connected: {host}:{port}/{db}")
        except Exception as e:
            logger.warning(f"Redis unavailable: {str(e)}")
            allow_fallback = _is_truthy(os.getenv("ION_ALLOW_IN_MEMORY_REDIS_FALLBACK", "1"))
            if allow_fallback or env == "test":
                logger.info("Redis fallback: using in-memory cache")
                self._init_in_memory()
            else:
                self.available = False
                self.redis_client = None

    def _init_in_memory(self) -> None:
        """Use in-memory client for test environments."""
        self.redis_client = _InMemoryRedisClient()
        self.available = True
        self._in_memory_mode = True
        logger.debug("RedisCache initialized with in-memory backend")

    def get(self, key: str) -> Optional[Any]:
        """
        값 조회

        Args:
            key: 캐시 키

        Returns:
            캐시된 값 또는 None
        """
        if not self.available or not self.redis_client:
            return None

        try:
            value = self.redis_client.get(key)
            if value:
                return pickle.loads(value)
        except Exception as e:
            logger.warning(f"Redis get error: {str(e)}")

        return None

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """
        값 저장

        Args:
            key: 캐시 키
            value: 캐시할 값
            ttl: Time-to-live (초)
        """
        if not self.available or not self.redis_client:
            return

        try:
            payload = pickle.dumps(value)
            self.redis_client.setex(key, ttl, payload)
        except Exception as e:
            logger.warning(f"Redis set error: {str(e)}")

    def delete(self, key: str) -> None:
        """
        값 삭제

        Args:
            key: 캐시 키
        """
        if not self.available or not self.redis_client:
            return

        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.warning(f"Redis delete error: {str(e)}")

    def clear(self) -> None:
        """캐시 전체 삭제"""
        if not self.available or not self.redis_client:
            return

        try:
            self.redis_client.flushdb()
        except Exception as e:
            logger.warning(f"Redis clear error: {str(e)}")

    def get_stats(self) -> Dict[str, Any]:
        """Return cache statistics."""
        if not self.available or not self.redis_client:
            mode = "in_memory" if getattr(self, "_in_memory_mode", False) else "unavailable"
            return {
                "cache_type": "L2 Redis",
                "available": False,
                "status": "Unavailable",
                "mode": mode,
            }

        try:
            info = self.redis_client.info()
            return {
                "cache_type": "L2 Redis",
                "available": True,
                "mode": "in_memory" if getattr(self, "_in_memory_mode", False) else "redis",
                "memory_used": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands": info.get("total_commands_processed", 0),
            }
        except Exception as e:
            logger.warning(f"Redis stats error: {str(e)}")
            return {
                "cache_type": "L2 Redis",
                "available": False,
                "mode": "in_memory" if getattr(self, "_in_memory_mode", False) else "redis",
                "error": str(e),
            }



class TwoTierCache:
    """2단계 캐싱 시스템 (L1 로컬 + L2 Redis)"""

    def __init__(
        self,
        l1_max_size: int = 1000,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
    ):
        """
        초기화

        Args:
            l1_max_size: L1 캐시 최대 크기
            redis_host: Redis 호스트
            redis_port: Redis 포트
            redis_db: Redis DB
        """
        self.l1 = LocalCache(max_size=l1_max_size)
        self.l2 = RedisCache(host=redis_host, port=redis_port, db=redis_db)

    def get(self, key: str) -> Optional[Any]:
        """
        값 조회 (L1 → L2 순서)

        Args:
            key: 캐시 키

        Returns:
            캐시된 값 또는 None
        """
        # L1 확인
        value = self.l1.get(key)
        if value is not None:
            return value

        # L2 확인
        value = self.l2.get(key)
        if value is not None:
            # L1에 반영
            # TTL은 작은 값으로 설정 (L1은 임시)
            self.l1.set(key, value, ttl=60)
            return value

        return None

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """
        값 저장 (L1 + L2)

        Args:
            key: 캐시 키
            value: 캐시할 값
            ttl: Time-to-live (초)
        """
        # L1에 저장 (짧은 TTL)
        self.l1.set(key, value, ttl=min(ttl, 60))

        # L2에 저장 (긴 TTL)
        self.l2.set(key, value, ttl=ttl)

    def delete(self, key: str) -> None:
        """
        값 삭제 (L1 + L2)

        Args:
            key: 캐시 키
        """
        self.l1.delete(key)
        self.l2.delete(key)

    def delete_pattern(self, pattern: str) -> int:
        """
        패턴 기반 삭제 (캐시 무효화)

        Args:
            pattern: 키 패턴 (예: "persona:*")

        Returns:
            삭제된 항목 수
        """
        count = 0

        # L1에서 패턴 매칭 삭제
        import re

        regex = re.compile(pattern.replace("*", ".*"))
        keys_to_delete = [key for key in self.l1.cache.keys() if regex.match(key)]
        for key in keys_to_delete:
            self.l1.delete(key)
            count += 1

        # L2에서 패턴 매칭 삭제 (Redis 가능 시)
        if self.l2.available and self.l2.redis_client:
            try:
                redis_keys = self.l2.redis_client.keys(pattern)
                for key in redis_keys:
                    self.l2.delete(key)
                    count += len(redis_keys)
            except Exception as e:
                logger.warning(f"Redis pattern delete error: {str(e)}")

        return count

    def clear(self) -> None:
        """캐시 전체 삭제"""
        self.l1.clear()
        self.l2.clear()

    def get_stats(self) -> Dict[str, Any]:
        """통합 캐시 통계"""
        return {
            "l1": self.l1.get_stats(),
            "l2": self.l2.get_stats(),
            "total_hits": self.l1.hits,
            "total_misses": self.l1.misses,
        }


# 싱글톤 인스턴스
_cache_instance: Optional[TwoTierCache] = None


def get_cache() -> TwoTierCache:
    """2단계 캐시 싱글톤 반환"""
    global _cache_instance
    if _cache_instance is None:
        import os
        
        # 환경변수에서 Redis 설정 가져오기
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_db = int(os.getenv("REDIS_DB", "0"))
        
        logger.info(f"Initializing TwoTierCache with Redis: {redis_host}:{redis_port}/{redis_db}")
        _cache_instance = TwoTierCache(
            redis_host=redis_host,
            redis_port=redis_port,
            redis_db=redis_db
        )
    return _cache_instance


def reset_cache() -> None:
    """캐시 리셋 (테스트용)"""
    global _cache_instance
    if _cache_instance:
        _cache_instance.clear()
    _cache_instance = None


# 캐시 데코레이터
def cached(ttl: int = 300, key_prefix: str = ""):
    """
    캐시 데코레이터

    Usage:
    @cached(ttl=600)
    def expensive_function(arg1, arg2):
        return result

    Args:
        ttl: Time-to-live (초)
        key_prefix: 키 프리픽스
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            cache = get_cache()

            # 캐시 키 생성
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)

            # 캐시 조회
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value

            # 캐시 미스: 함수 실행
            logger.debug(f"Cache miss: {cache_key}")
            result = func(*args, **kwargs)

            # 캐시 저장
            cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper

    return decorator


# ===== 비동기 Redis 지원 (FastAPI 최적화) =====


class AsyncRedisCache:
    """L2 비동기 Redis 캐시 (FastAPI 최적화)"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        decode_responses: bool = True,
    ):
        """
        초기화

        Args:
            host: Redis 호스트
            port: Redis 포트
            db: Redis DB 번호
            password: Redis 비밀번호
            decode_responses: 응답 디코딩 여부
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.decode_responses = decode_responses
        self.redis_client = None
        self.available = False
        self._connection_lock = asyncio.Lock()

    async def connect(self) -> bool:
        """Redis 연결 (async)"""
        if self.redis_client:
            return True

        async with self._connection_lock:
            if self.redis_client:
                return True

            try:
                import redis.asyncio as aioredis

                self.redis_client = await aioredis.from_url(
                    f"redis://{self.host}:{self.port}/{self.db}",
                    password=self.password,
                    decode_responses=False,
                )

                # 연결 테스트
                await self.redis_client.ping()
                self.available = True
                logger.info(f"Async Redis connected: {self.host}:{self.port}/{self.db}")
                return True

            except Exception as e:
                self.available = False
                logger.warning(f"Async Redis connection failed: {str(e)}")
                self.redis_client = None
                return False

    async def disconnect(self) -> None:
        """Redis 연결 종료"""
        if self.redis_client:
            try:
                await self.redis_client.close()
                logger.info("Async Redis disconnected")
            except Exception as e:
                logger.warning(f"Redis disconnect error: {str(e)}")
            finally:
                self.redis_client = None
                self.available = False

    async def get(self, key: str) -> Optional[Any]:
        """
        값 조회 (비동기)

        Args:
            key: 캐시 키

        Returns:
            캐시된 값 또는 None
        """
        if not self.available:
            await self.connect()

        if not self.available or not self.redis_client:
            return None

        try:
            value = await self.redis_client.get(key)
            if value:
                return pickle.loads(value)
        except Exception as e:
            logger.warning(f"Async Redis get error: {str(e)}")

        return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        값 저장 (비동기)

        Args:
            key: 캐시 키
            value: 캐시할 값
            ttl: Time-to-live (초)

        Returns:
            성공 여부
        """
        if not self.available:
            await self.connect()

        if not self.available or not self.redis_client:
            return False

        try:
            payload = pickle.dumps(value)
            await self.redis_client.setex(key, ttl, payload)
            return True
        except Exception as e:
            logger.warning(f"Async Redis set error: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """
        값 삭제 (비동기)

        Args:
            key: 캐시 키

        Returns:
            성공 여부
        """
        if not self.available:
            await self.connect()

        if not self.available or not self.redis_client:
            return False

        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Async Redis delete error: {str(e)}")
            return False

    async def clear(self) -> bool:
        """캐시 전체 삭제 (비동기)"""
        if not self.available:
            await self.connect()

        if not self.available or not self.redis_client:
            return False

        try:
            await self.redis_client.flushdb()
            return True
        except Exception as e:
            logger.warning(f"Async Redis clear error: {str(e)}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환 (비동기)"""
        if not self.available:
            await self.connect()

        if not self.available or not self.redis_client:
            return {"cache_type": "L2 Async Redis", "available": False, "status": "Unavailable"}

        try:
            info = await self.redis_client.info()
            return {
                "cache_type": "L2 Async Redis",
                "available": True,
                "memory_used": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands": info.get("total_commands_processed", 0),
            }
        except Exception as e:
            logger.warning(f"Async Redis stats error: {str(e)}")
            return {"cache_type": "L2 Async Redis", "available": False, "error": str(e)}


class AsyncTwoTierCache:
    """비동기 2단계 캐싱 시스템 (L1 로컬 + L2 Async Redis)"""

    def __init__(
        self,
        l1_max_size: int = 1000,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None,
    ):
        """
        초기화

        Args:
            l1_max_size: L1 캐시 최대 크기
            redis_host: Redis 호스트
            redis_port: Redis 포트
            redis_db: Redis DB
            redis_password: Redis 비밀번호
        """
        self.l1 = LocalCache(max_size=l1_max_size)
        self.l2 = AsyncRedisCache(
            host=redis_host, port=redis_port, db=redis_db, password=redis_password
        )

    async def connect(self) -> bool:
        """Redis L2 연결"""
        return await self.l2.connect()

    async def disconnect(self) -> None:
        """Redis L2 연결 종료"""
        await self.l2.disconnect()

    async def get(self, key: str) -> Optional[Any]:
        """
        값 조회 (L1 → L2 순서, 비동기)

        Args:
            key: 캐시 키

        Returns:
            캐시된 값 또는 None
        """
        # L1 확인 (동기)
        value = self.l1.get(key)
        if value is not None:
            return value

        # L2 확인 (비동기)
        value = await self.l2.get(key)
        if value is not None:
            # L1에 반영 (동기)
            self.l1.set(key, value, ttl=60)
            return value

        return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        값 저장 (L1 + L2, 비동기)

        Args:
            key: 캐시 키
            value: 캐시할 값
            ttl: Time-to-live (초)

        Returns:
            성공 여부
        """
        # L1에 저장 (동기, 짧은 TTL)
        self.l1.set(key, value, ttl=min(ttl, 60))

        # L2에 저장 (비동기, 긴 TTL)
        return await self.l2.set(key, value, ttl=ttl)

    async def delete(self, key: str) -> bool:
        """
        값 삭제 (L1 + L2, 비동기)

        Args:
            key: 캐시 키

        Returns:
            성공 여부
        """
        # L1 삭제 (동기)
        self.l1.delete(key)

        # L2 삭제 (비동기)
        return await self.l2.delete(key)

    async def clear(self) -> bool:
        """캐시 전체 삭제 (비동기)"""
        # L1 삭제 (동기)
        self.l1.clear()

        # L2 삭제 (비동기)
        return await self.l2.clear()

    async def get_stats(self) -> Dict[str, Any]:
        """통합 캐시 통계 (비동기)"""
        l2_stats = await self.l2.get_stats()

        return {
            "l1": self.l1.get_stats(),
            "l2": l2_stats,
            "total_hits": self.l1.hits,
            "total_misses": self.l1.misses,
        }


# 비동기 캐시 싱글톤
_async_cache_instance: Optional[AsyncTwoTierCache] = None


def get_async_cache(
    redis_host: str = "localhost",
    redis_port: int = 6379,
    redis_db: int = 0,
    redis_password: Optional[str] = None,
) -> AsyncTwoTierCache:
    """비동기 2단계 캐시 싱글톤 반환"""
    global _async_cache_instance
    if _async_cache_instance is None:
        _async_cache_instance = AsyncTwoTierCache(
            redis_host=redis_host,
            redis_port=redis_port,
            redis_db=redis_db,
            redis_password=redis_password,
        )
    return _async_cache_instance


async def reset_async_cache() -> None:
    """비동기 캐시 리셋 (테스트용)"""
    global _async_cache_instance
    if _async_cache_instance:
        await _async_cache_instance.clear()
        await _async_cache_instance.disconnect()
    _async_cache_instance = None


# 캐시 무효화 데코레이터
def invalidate_cache(pattern: str):
    """
    캐시 무효화 데코레이터

    Usage:
    @invalidate_cache("persona:*")
    def update_persona(persona_id):
        ...

    Args:
        pattern: 무효화할 키 패턴
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            result = func(*args, **kwargs)

            # 함수 실행 후 캐시 무효화
            cache = get_cache()
            deleted = cache.delete_pattern(pattern)
            logger.info(f"Cache invalidated: {pattern} ({deleted} items)")

            return result

        return wrapper

    return decorator
