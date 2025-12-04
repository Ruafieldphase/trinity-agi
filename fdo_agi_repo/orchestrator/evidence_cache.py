#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evidence Gate Cache
Caches RAG results for evidence_gate_correction to reduce latency and API calls
"""
import hashlib
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class CacheEntry:
    """Single cache entry with TTL and metadata"""
    data: Dict[str, Any]
    timestamp: float
    hits: int = 0
    
    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if this entry has expired"""
        return (time.time() - self.timestamp) > ttl_seconds


class EvidenceCache:
    """
    In-memory cache for evidence_gate RAG results
    
    Features:
    - Query-based cache keys (normalized task goals)
    - Configurable TTL (default: 1800s = 30 minutes, increased from 900s based on analysis)
    - Automatic expiration on access
    - Hit/miss statistics
    - Memory-efficient (limits max entries)
    """
    
    def __init__(self, ttl_seconds: int = 1800, max_entries: int = 1000):
        """
        Initialize evidence cache
        
        Args:
            ttl_seconds: Time-to-live for cached items (default: 30 minutes, optimized for query pattern)
            max_entries: Maximum number of cache entries before cleanup
        """
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        
        # In-memory cache storage
        self._cache: Dict[str, CacheEntry] = {}
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_time_saved_ms": 0.0
        }
    
    def _generate_key(self, query: str) -> str:
        """
        Generate cache key from query
        
        Normalizes query to improve cache hit rate:
        - Lowercase
        - Strip whitespace
        - Hash for consistent length
        
        Args:
            query: Task goal or search query
            
        Returns:
            str: 16-character hash key
        """
        normalized = query.lower().strip()
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get cached RAG result if available and not expired
        
        Args:
            query: Task goal to look up
            
        Returns:
            Cached RAG result dict or None if miss/expired
        """
        key = self._generate_key(query)
        
        if key not in self._cache:
            self.stats["misses"] += 1
            return None
        
        entry = self._cache[key]
        
        # Check expiration
        if entry.is_expired(self.ttl_seconds):
            del self._cache[key]
            self.stats["misses"] += 1
            self.stats["evictions"] += 1
            return None
        
        # Cache hit!
        entry.hits += 1
        self.stats["hits"] += 1
        return entry.data
    
    def put(self, query: str, rag_result: Dict[str, Any], latency_ms: float = 0.0):
        """
        Store RAG result in cache
        
        Args:
            query: Task goal that was searched
            rag_result: RAG response dict to cache
            latency_ms: Original RAG call latency (for stats)
        """
        key = self._generate_key(query)
        
        # Enforce max entries limit (simple LRU-like: remove oldest)
        if len(self._cache) >= self.max_entries:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].timestamp)
            del self._cache[oldest_key]
            self.stats["evictions"] += 1
        
        self._cache[key] = CacheEntry(
            data=rag_result,
            timestamp=time.time()
        )
        
        # Track time saved for future cache hits
        if latency_ms > 0:
            self.stats["total_time_saved_ms"] += latency_ms
    
    def clear(self):
        """Clear all cache entries"""
        self._cache.clear()
    
    def cleanup_expired(self):
        """Remove all expired entries (manual cleanup)"""
        now = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if (now - entry.timestamp) > self.ttl_seconds
        ]
        for key in expired_keys:
            del self._cache[key]
            self.stats["evictions"] += 1
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dict with hits, misses, hit_rate, size, etc.
        """
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total * 100) if total > 0 else 0.0
        
        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate_percent": round(hit_rate, 2),
            "cache_size": len(self._cache),
            "evictions": self.stats["evictions"],
            "total_time_saved_ms": round(self.stats["total_time_saved_ms"], 2),
            "ttl_seconds": self.ttl_seconds,
            "max_entries": self.max_entries
        }
    
    def __len__(self) -> int:
        """Get current cache size"""
        return len(self._cache)


# Global singleton instance
_evidence_cache: Optional[EvidenceCache] = None


def get_evidence_cache(ttl_seconds: int = 900, max_entries: int = 1000) -> EvidenceCache:
    """
    Get or create the global evidence cache singleton
    
    Args:
        ttl_seconds: TTL for cache entries (default: 15 minutes, increased for better hit rate)
        max_entries: Max cache size (default: 1000)
        
    Returns:
        EvidenceCache: Global cache instance
    """
    global _evidence_cache
    if _evidence_cache is None:
        _evidence_cache = EvidenceCache(ttl_seconds=ttl_seconds, max_entries=max_entries)
    return _evidence_cache
