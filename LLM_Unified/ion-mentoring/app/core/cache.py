"""
Cache Manager for ION API

Redis-based caching system for LLM responses to reduce costs and improve latency.

Features:
- Request-based cache key generation
- TTL management
- Hit rate tracking
- Graceful fallback on Redis failure
"""

import hashlib
import json
import logging
from typing import Any, Optional

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("redis package not installed - caching disabled")

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis cache manager for API responses"""

    def __init__(
        self,
        redis_host: Optional[str] = None,
        redis_port: int = 6379,
        enabled: bool = True,
        default_ttl: int = 3600,
    ):
        """
        Initialize cache manager
        
        Args:
            redis_host: Redis server hostname/IP
            redis_port: Redis server port (default: 6379)
            enabled: Enable/disable caching (default: True)
            default_ttl: Default TTL in seconds (default: 3600 = 1 hour)
        """
        self.enabled = enabled and REDIS_AVAILABLE and redis_host is not None
        self.default_ttl = default_ttl
        self.client: Optional[redis.Redis] = None
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - caching disabled")
            self.enabled = False
            return
        
        if not redis_host:
            logger.warning("Redis host not configured - caching disabled")
            self.enabled = False
            return
        
        try:
            self.client = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                socket_keepalive=True,
                health_check_interval=30,
            )
            # Test connection
            self.client.ping()
            logger.info(f"Redis cache connected: {redis_host}:{redis_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.enabled = False
            self.client = None

    def _generate_key(self, endpoint: str, request_data: dict) -> str:
        """
        Generate cache key from endpoint and request data
        
        Args:
            endpoint: API endpoint name (e.g., 'chat', 'persona')
            request_data: Request payload as dict
            
        Returns:
            Cache key string in format: cache:{endpoint}:{hash}
        """
        # Sort keys for consistent hashing
        data_str = json.dumps(request_data, sort_keys=True)
        hash_obj = hashlib.sha256(data_str.encode())
        return f"cache:{endpoint}:{hash_obj.hexdigest()[:12]}"

    def get(self, endpoint: str, request_data: dict) -> Optional[str]:
        """
        Get cached response
        
        Args:
            endpoint: API endpoint name
            request_data: Request payload as dict
            
        Returns:
            Cached response string or None if not found/error
        """
        if not self.enabled or not self.client:
            return None
        
        key = self._generate_key(endpoint, request_data)
        try:
            value = self.client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
            else:
                logger.debug(f"Cache MISS: {key}")
            return value
        except redis.RedisError as e:
            logger.warning(f"Cache get error: {e}")
            return None

    def set(
        self,
        endpoint: str,
        request_data: dict,
        response: str,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Cache response with TTL
        
        Args:
            endpoint: API endpoint name
            request_data: Request payload as dict
            response: Response to cache (JSON string)
            ttl: TTL in seconds (default: use default_ttl)
            
        Returns:
            True if cached successfully, False otherwise
        """
        if not self.enabled or not self.client:
            return False
        
        key = self._generate_key(endpoint, request_data)
        ttl = ttl or self.default_ttl
        
        try:
            self.client.setex(key, ttl, response)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except redis.RedisError as e:
            logger.warning(f"Cache set error: {e}")
            return False

    def invalidate(self, endpoint: str, request_data: dict) -> bool:
        """
        Invalidate specific cache entry
        
        Args:
            endpoint: API endpoint name
            request_data: Request payload as dict
            
        Returns:
            True if deleted, False otherwise
        """
        if not self.enabled or not self.client:
            return False
        
        key = self._generate_key(endpoint, request_data)
        try:
            deleted = self.client.delete(key)
            logger.debug(f"Cache INVALIDATE: {key}")
            return bool(deleted)
        except redis.RedisError as e:
            logger.warning(f"Cache invalidate error: {e}")
            return False

    def clear_pattern(self, pattern: str = "cache:*") -> int:
        """
        Clear cache entries matching pattern
        
        Args:
            pattern: Redis key pattern (default: 'cache:*' = all cache)
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.client:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"Cache CLEAR: {deleted} keys deleted")
                return deleted
            return 0
        except redis.RedisError as e:
            logger.warning(f"Cache clear error: {e}")
            return 0

    def get_stats(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            Dict with hit rate, keyspace hits/misses, memory usage
        """
        if not self.enabled or not self.client:
            return {
                "enabled": False,
                "keyspace_hits": 0,
                "keyspace_misses": 0,
                "hit_rate": 0.0,
                "keys_count": 0,
            }
        
        try:
            info = self.client.info("stats")
            keyspace = self.client.info("keyspace")
            
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            total = hits + misses
            hit_rate = (hits / total * 100) if total > 0 else 0.0
            
            # Count cache keys
            keys_count = 0
            if "db0" in keyspace:
                keys_count = keyspace["db0"].get("keys", 0)
            
            return {
                "enabled": True,
                "keyspace_hits": hits,
                "keyspace_misses": misses,
                "hit_rate": round(hit_rate, 2),
                "keys_count": keys_count,
                "memory_used_mb": round(
                    info.get("used_memory", 0) / (1024 * 1024), 2
                ),
            }
        except redis.RedisError as e:
            logger.warning(f"Cache stats error: {e}")
            return {
                "enabled": True,
                "error": str(e),
                "keyspace_hits": 0,
                "keyspace_misses": 0,
                "hit_rate": 0.0,
                "keys_count": 0,
            }

    def health_check(self) -> bool:
        """
        Check Redis connection health
        
        Returns:
            True if Redis is healthy, False otherwise
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            return self.client.ping()
        except redis.RedisError:
            return False


# Global cache manager instance (initialized in main.py)
cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> Optional[CacheManager]:
    """Get global cache manager instance"""
    return cache_manager


def init_cache_manager(
    redis_host: Optional[str] = None,
    redis_port: int = 6379,
    enabled: bool = True,
) -> CacheManager:
    """
    Initialize global cache manager
    
    Args:
        redis_host: Redis hostname/IP
        redis_port: Redis port
        enabled: Enable caching
        
    Returns:
        Initialized CacheManager instance
    """
    global cache_manager
    cache_manager = CacheManager(
        redis_host=redis_host,
        redis_port=redis_port,
        enabled=enabled,
    )
    return cache_manager
