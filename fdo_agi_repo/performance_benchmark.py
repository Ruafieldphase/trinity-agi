#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hey Sena - Performance Benchmarking Tool
Measures and analyzes system performance
"""
import time
import statistics
from typing import List, Dict, Callable
from response_cache import ResponseCache

class PerformanceBenchmark:
    """
    Performance benchmarking and profiling for Hey Sena

    Measures:
    - LLM response time
    - TTS generation time
    - Total response latency
    - Cache hit rate
    - Memory usage
    """

    def __init__(self):
        self.measurements = {
            "llm_times": [],
            "tts_times": [],
            "total_times": [],
            "cache_hits": 0,
            "cache_misses": 0,
        }

    def measure_function(self, func: Callable, *args, **kwargs):
        """
        Measure execution time of a function

        Args:
            func: Function to measure
            *args, **kwargs: Function arguments

        Returns:
            tuple: (result, elapsed_time)
        """
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start

        return result, elapsed

    def record_llm_time(self, elapsed_time: float):
        """Record LLM response time"""
        self.measurements["llm_times"].append(elapsed_time)

    def record_tts_time(self, elapsed_time: float):
        """Record TTS generation time"""
        self.measurements["tts_times"].append(elapsed_time)

    def record_total_time(self, elapsed_time: float):
        """Record total response time (LLM + TTS)"""
        self.measurements["total_times"].append(elapsed_time)

    def record_cache_hit(self):
        """Record cache hit"""
        self.measurements["cache_hits"] += 1

    def record_cache_miss(self):
        """Record cache miss"""
        self.measurements["cache_misses"] += 1

    def get_stats(self, times: List[float]) -> Dict:
        """
        Calculate statistics for a list of times

        Returns:
            dict: min, max, mean, median, p95, p99
        """
        if not times:
            return {
                "min": 0,
                "max": 0,
                "mean": 0,
                "median": 0,
                "p95": 0,
                "p99": 0,
                "count": 0
            }

        sorted_times = sorted(times)
        n = len(sorted_times)

        return {
            "min": min(times),
            "max": max(times),
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "p95": sorted_times[int(n * 0.95)] if n > 0 else 0,
            "p99": sorted_times[int(n * 0.99)] if n > 0 else 0,
            "count": n
        }

    def print_report(self):
        """Print comprehensive performance report"""
        print("\n" + "=" * 70)
        print("HEY SENA - PERFORMANCE BENCHMARK REPORT")
        print("=" * 70)

        # LLM Performance
        print("\n[1] LLM Response Time")
        print("-" * 70)
        llm_stats = self.get_stats(self.measurements["llm_times"])
        if llm_stats["count"] > 0:
            print(f"  Samples: {llm_stats['count']}")
            print(f"  Mean: {llm_stats['mean']:.3f}s")
            print(f"  Median: {llm_stats['median']:.3f}s")
            print(f"  Min: {llm_stats['min']:.3f}s")
            print(f"  Max: {llm_stats['max']:.3f}s")
            print(f"  P95: {llm_stats['p95']:.3f}s")
            print(f"  P99: {llm_stats['p99']:.3f}s")
        else:
            print("  No measurements recorded")

        # TTS Performance
        print("\n[2] TTS Generation Time")
        print("-" * 70)
        tts_stats = self.get_stats(self.measurements["tts_times"])
        if tts_stats["count"] > 0:
            print(f"  Samples: {tts_stats['count']}")
            print(f"  Mean: {tts_stats['mean']:.3f}s")
            print(f"  Median: {tts_stats['median']:.3f}s")
            print(f"  Min: {tts_stats['min']:.3f}s")
            print(f"  Max: {tts_stats['max']:.3f}s")
            print(f"  P95: {tts_stats['p95']:.3f}s")
            print(f"  P99: {tts_stats['p99']:.3f}s")
        else:
            print("  No measurements recorded")

        # Total Response Time
        print("\n[3] Total Response Time (LLM + TTS)")
        print("-" * 70)
        total_stats = self.get_stats(self.measurements["total_times"])
        if total_stats["count"] > 0:
            print(f"  Samples: {total_stats['count']}")
            print(f"  Mean: {total_stats['mean']:.3f}s")
            print(f"  Median: {total_stats['median']:.3f}s")
            print(f"  Min: {total_stats['min']:.3f}s")
            print(f"  Max: {total_stats['max']:.3f}s")
            print(f"  P95: {total_stats['p95']:.3f}s")
            print(f"  P99: {total_stats['p99']:.3f}s")
        else:
            print("  No measurements recorded")

        # Cache Performance
        print("\n[4] Cache Performance")
        print("-" * 70)
        total_requests = self.measurements["cache_hits"] + self.measurements["cache_misses"]
        hit_rate = (self.measurements["cache_hits"] / total_requests * 100) if total_requests > 0 else 0

        print(f"  Cache hits: {self.measurements['cache_hits']}")
        print(f"  Cache misses: {self.measurements['cache_misses']}")
        print(f"  Hit rate: {hit_rate:.1f}%")

        # Estimated time saved by caching
        if self.measurements["cache_hits"] > 0:
            avg_time = total_stats["mean"] if total_stats["count"] > 0 else 3.0
            time_saved = self.measurements["cache_hits"] * avg_time
            print(f"  Time saved: ~{time_saved:.1f}s")

        # Performance Grade
        print("\n[5] Performance Grade")
        print("-" * 70)

        if total_stats["count"] > 0:
            avg_response = total_stats["mean"]

            if avg_response < 1.0:
                grade = "A+ (Excellent)"
            elif avg_response < 2.0:
                grade = "A (Great)"
            elif avg_response < 3.0:
                grade = "B (Good)"
            elif avg_response < 4.0:
                grade = "C (Acceptable)"
            else:
                grade = "D (Needs Improvement)"

            print(f"  Average response time: {avg_response:.2f}s")
            print(f"  Grade: {grade}")

            # Recommendations
            print("\n[6] Recommendations")
            print("-" * 70)
            if avg_response > 3.0:
                print("  [!] Consider upgrading to faster Gemini model")
                print("  [!] Implement response caching")
            elif hit_rate < 30:
                print("  [*] Increase cache TTL for better hit rate")
            else:
                print("  [OK] Performance is good!")

        print("\n" + "=" * 70)

    def save_report(self, filename: str):
        """Save performance report to file"""
        import json

        report = {
            "timestamp": time.time(),
            "llm_stats": self.get_stats(self.measurements["llm_times"]),
            "tts_stats": self.get_stats(self.measurements["tts_times"]),
            "total_stats": self.get_stats(self.measurements["total_times"]),
            "cache_hits": self.measurements["cache_hits"],
            "cache_misses": self.measurements["cache_misses"],
        }

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"[SAVED] Performance report: {filename}")


def benchmark_cache_performance():
    """Benchmark cache system performance"""
    print("\n" + "=" * 70)
    print("CACHE PERFORMANCE BENCHMARK")
    print("=" * 70)

    cache = ResponseCache()
    benchmark = PerformanceBenchmark()

    # Test questions
    questions = [
        "What is Python?",
        "How do I learn programming?",
        "Explain quantum mechanics",
        "What time is it?",
        "Tell me a joke",
    ]

    # Simulate responses
    responses = [
        "Python is a programming language known for simplicity.",
        "Start with Python tutorials and practice daily.",
        "Quantum mechanics describes physics at atomic scales.",
        "It's time to learn something new!",
        "Why did the programmer quit? No arrays!",
    ]

    print("\n[PHASE 1] Initial requests (all misses expected)")
    print("-" * 70)

    for q, r in zip(questions, responses):
        # First request - should miss
        start = time.time()
        cached = cache.get_text_response(q)
        elapsed = time.time() - start

        if cached:
            benchmark.record_cache_hit()
            benchmark.record_total_time(elapsed)
        else:
            benchmark.record_cache_miss()

            # Simulate LLM + TTS time
            llm_time = 2.0
            tts_time = 1.5
            total_time = llm_time + tts_time

            benchmark.record_llm_time(llm_time)
            benchmark.record_tts_time(tts_time)
            benchmark.record_total_time(total_time)

            # Cache the response
            cache.set_text_response(q, r)

        time.sleep(0.1)

    print("\n[PHASE 2] Repeated requests (hits expected)")
    print("-" * 70)

    for q in questions:
        # Second request - should hit
        start = time.time()
        cached = cache.get_text_response(q)
        elapsed = time.time() - start

        if cached:
            benchmark.record_cache_hit()
            benchmark.record_total_time(elapsed)
            print(f"  [HIT] {q[:40]}... ({elapsed*1000:.1f}ms)")
        else:
            benchmark.record_cache_miss()
            print(f"  [MISS] {q[:40]}...")

        time.sleep(0.1)

    # Print results
    benchmark.print_report()

    # Cache stats
    print("\n")
    cache.print_stats()

    return benchmark


def simulate_conversation_benchmark():
    """Simulate a full conversation with performance measurements"""
    print("\n" + "=" * 70)
    print("CONVERSATION SIMULATION BENCHMARK")
    print("=" * 70)

    benchmark = PerformanceBenchmark()

    # Simulate 10-turn conversation
    turns = [
        ("Hello", 0.8, 1.2),  # (query, llm_time, tts_time)
        ("What is Python?", 2.1, 1.5),
        ("How do I learn it?", 2.3, 1.6),
        ("What are good resources?", 2.0, 1.4),
        ("How long does it take?", 1.8, 1.3),
        ("Can you give me tips?", 2.2, 1.5),
        ("What projects should I build?", 2.4, 1.7),
        ("Thanks for your help!", 1.5, 1.2),
        ("Anything else I should know?", 2.1, 1.4),
        ("Goodbye!", 0.9, 1.0),
    ]

    print("\n[SIMULATION] 10-turn conversation")
    print("-" * 70)

    for i, (query, llm_time, tts_time) in enumerate(turns, 1):
        total_time = llm_time + tts_time

        benchmark.record_llm_time(llm_time)
        benchmark.record_tts_time(tts_time)
        benchmark.record_total_time(total_time)

        print(f"  Turn {i:2d}: {query:30s} | "
              f"LLM: {llm_time:.2f}s | TTS: {tts_time:.2f}s | "
              f"Total: {total_time:.2f}s")

    # Print results
    benchmark.print_report()

    return benchmark


if __name__ == "__main__":
    import sys

    print("\n" + "=" * 70)
    print("HEY SENA - PERFORMANCE BENCHMARKING TOOL")
    print("=" * 70)

    # Run cache benchmark
    print("\n[1/2] Running cache performance benchmark...")
    cache_benchmark = benchmark_cache_performance()

    # Run conversation simulation
    print("\n\n[2/2] Running conversation simulation...")
    conv_benchmark = simulate_conversation_benchmark()

    # Save reports
    print("\n[SAVING] Performance reports...")
    cache_benchmark.save_report("benchmark_cache.json")
    conv_benchmark.save_report("benchmark_conversation.json")

    print("\n[SUCCESS] Benchmarking complete!")
    print("\nNext steps:")
    print("  - Review performance metrics above")
    print("  - Integrate caching into hey_sena_v4_llm.py")
    print("  - Monitor improvements in production")
