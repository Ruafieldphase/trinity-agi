#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hey Sena - Response Caching System
Caches LLM responses and TTS audio to reduce latency
"""
import os
import json
import hashlib
import time
from pathlib import Path
from typing import Optional, Dict, Tuple

class ResponseCache:
    """
    Smart caching system for Hey Sena responses

    Features:
    - LLM response caching (text)
    - TTS audio file caching
    - Context-aware cache keys
    - Configurable TTL (time-to-live)
    - Automatic cache cleanup
    """

    def __init__(self, cache_dir=".sena_cache", ttl_seconds=3600):
        """
        Initialize cache system

        Args:
            cache_dir: Directory to store cache files
            ttl_seconds: Time-to-live for cached items (default: 1 hour)
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_seconds

        # Create cache directories
        self.text_cache_dir = self.cache_dir / "text"
        self.audio_cache_dir = self.cache_dir / "audio"

        self.text_cache_dir.mkdir(parents=True, exist_ok=True)
        self.audio_cache_dir.mkdir(parents=True, exist_ok=True)

        # In-memory metadata cache
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict:
        """Load cache metadata from disk"""
        metadata_file = self.cache_dir / "metadata.json"

        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass

        return {
            "text_cache": {},
            "audio_cache": {},
            "stats": {
                "hits": 0,
                "misses": 0,
                "total_time_saved": 0.0
            }
        }

    def _save_metadata(self):
        """Save cache metadata to disk"""
        metadata_file = self.cache_dir / "metadata.json"

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2)

    def _generate_cache_key(self, query: str, context_summary: str = "") -> str:
        """
        Generate cache key from query and context

        Args:
            query: User's question
            context_summary: Summary of conversation context

        Returns:
            str: Hash-based cache key
        """
        # Normalize query
        normalized = query.lower().strip()

        # Add context if provided (for context-aware caching)
        if context_summary:
            cache_input = f"{normalized}|{context_summary}"
        else:
            cache_input = normalized

        # Generate SHA256 hash
        return hashlib.sha256(cache_input.encode()).hexdigest()[:16]

    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid (not expired)"""
        if "timestamp" not in cache_entry:
            return False

        age = time.time() - cache_entry["timestamp"]
        return age < self.ttl_seconds

    def get_text_response(self, query: str, context_summary: str = "") -> Optional[str]:
        """
        Get cached LLM text response

        Args:
            query: User's question
            context_summary: Conversation context summary

        Returns:
            str or None: Cached response text, or None if not cached
        """
        cache_key = self._generate_cache_key(query, context_summary)

        # Check if cached
        if cache_key in self.metadata["text_cache"]:
            cache_entry = self.metadata["text_cache"][cache_key]

            # Check if still valid
            if self._is_cache_valid(cache_entry):
                self.metadata["stats"]["hits"] += 1
                self.metadata["stats"]["total_time_saved"] += 2.5  # Avg LLM time

                print(f"[CACHE HIT] Text response (key: {cache_key[:8]}...)")
                return cache_entry["response"]

        # Cache miss
        self.metadata["stats"]["misses"] += 1
        return None

    def set_text_response(self, query: str, response: str, context_summary: str = ""):
        """
        Cache LLM text response

        Args:
            query: User's question
            response: LLM response text
            context_summary: Conversation context summary
        """
        cache_key = self._generate_cache_key(query, context_summary)

        self.metadata["text_cache"][cache_key] = {
            "query": query,
            "response": response,
            "context": context_summary,
            "timestamp": time.time()
        }

        self._save_metadata()
        print(f"[CACHE SET] Text response (key: {cache_key[:8]}...)")

    def get_audio_file(self, text: str) -> Optional[str]:
        """
        Get cached TTS audio file path

        Args:
            text: Text that was converted to speech

        Returns:
            str or None: Path to cached audio file, or None if not cached
        """
        cache_key = self._generate_cache_key(text)

        # Check if cached
        if cache_key in self.metadata["audio_cache"]:
            cache_entry = self.metadata["audio_cache"][cache_key]

            # Check if still valid
            if self._is_cache_valid(cache_entry):
                audio_path = cache_entry["audio_path"]

                # Verify file still exists
                if Path(audio_path).exists():
                    self.metadata["stats"]["hits"] += 1
                    self.metadata["stats"]["total_time_saved"] += 1.5  # Avg TTS time

                    print(f"[CACHE HIT] Audio file (key: {cache_key[:8]}...)")
                    return audio_path

        # Cache miss
        self.metadata["stats"]["misses"] += 1
        return None

    def set_audio_file(self, text: str, audio_path: str):
        """
        Cache TTS audio file

        Args:
            text: Text that was converted to speech
            audio_path: Path to audio file (will be copied to cache)
        """
        cache_key = self._generate_cache_key(text)

        # Copy audio file to cache directory
        cached_audio_path = self.audio_cache_dir / f"{cache_key}.wav"

        try:
            import shutil
            shutil.copy2(audio_path, cached_audio_path)

            self.metadata["audio_cache"][cache_key] = {
                "text": text,
                "audio_path": str(cached_audio_path),
                "timestamp": time.time()
            }

            self._save_metadata()
            print(f"[CACHE SET] Audio file (key: {cache_key[:8]}...)")

        except Exception as e:
            print(f"[CACHE ERROR] Failed to cache audio: {e}")

    def clear_expired(self):
        """Remove expired cache entries"""
        current_time = time.time()

        # Clear expired text cache
        expired_text = [
            key for key, entry in self.metadata["text_cache"].items()
            if not self._is_cache_valid(entry)
        ]

        for key in expired_text:
            del self.metadata["text_cache"][key]

        # Clear expired audio cache
        expired_audio = [
            key for key, entry in self.metadata["audio_cache"].items()
            if not self._is_cache_valid(entry)
        ]

        for key in expired_audio:
            # Delete audio file
            audio_path = self.metadata["audio_cache"][key].get("audio_path")
            if audio_path and Path(audio_path).exists():
                try:
                    os.remove(audio_path)
                except:
                    pass

            del self.metadata["audio_cache"][key]

        if expired_text or expired_audio:
            print(f"[CACHE CLEANUP] Removed {len(expired_text)} text + {len(expired_audio)} audio")
            self._save_metadata()

    def clear_all(self):
        """Clear entire cache"""
        # Delete all cached audio files
        for cache_entry in self.metadata["audio_cache"].values():
            audio_path = cache_entry.get("audio_path")
            if audio_path and Path(audio_path).exists():
                try:
                    os.remove(audio_path)
                except:
                    pass

        # Reset metadata
        self.metadata = {
            "text_cache": {},
            "audio_cache": {},
            "stats": {
                "hits": 0,
                "misses": 0,
                "total_time_saved": 0.0
            }
        }

        self._save_metadata()
        print("[CACHE] Cleared all cache")

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        stats = self.metadata["stats"].copy()

        stats["text_cache_size"] = len(self.metadata["text_cache"])
        stats["audio_cache_size"] = len(self.metadata["audio_cache"])

        total_requests = stats["hits"] + stats["misses"]
        if total_requests > 0:
            stats["hit_rate"] = stats["hits"] / total_requests
        else:
            stats["hit_rate"] = 0.0

        return stats

    def print_stats(self):
        """Print cache statistics"""
        stats = self.get_stats()

        print("\n" + "=" * 50)
        print("RESPONSE CACHE STATISTICS")
        print("=" * 50)
        print(f"Cache hits: {stats['hits']}")
        print(f"Cache misses: {stats['misses']}")
        print(f"Hit rate: {stats['hit_rate']:.1%}")
        print(f"Time saved: {stats['total_time_saved']:.1f}s")
        print(f"Text cache entries: {stats['text_cache_size']}")
        print(f"Audio cache entries: {stats['audio_cache_size']}")
        print("=" * 50)


# Singleton instance
_cache_instance = None

def get_cache() -> ResponseCache:
    """Get global cache instance"""
    global _cache_instance

    if _cache_instance is None:
        _cache_instance = ResponseCache()

    return _cache_instance


if __name__ == "__main__":
    # Test the cache system
    cache = ResponseCache()

    print("\n=== Testing Response Cache ===\n")

    # Test 1: Text caching
    print("[TEST 1] Text Response Caching")
    query1 = "What is Python?"
    response1 = "Python is a programming language known for its simplicity."

    # First request - should be a miss
    cached = cache.get_text_response(query1)
    print(f"First request: {'HIT' if cached else 'MISS'}")

    # Cache the response
    if not cached:
        cache.set_text_response(query1, response1)

    # Second request - should be a hit
    cached = cache.get_text_response(query1)
    print(f"Second request: {'HIT' if cached else 'MISS'}")
    print(f"Response: {cached}")

    # Test 2: Audio caching (simulated)
    print("\n[TEST 2] Audio File Caching")
    text1 = "Hello, how are you?"

    # First request - should be a miss
    audio_path = cache.get_audio_file(text1)
    print(f"First request: {'HIT' if audio_path else 'MISS'}")

    # Test 3: Stats
    print("\n[TEST 3] Cache Statistics")
    cache.print_stats()

    print("\n[SUCCESS] Cache system test complete!")
