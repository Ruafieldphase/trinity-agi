#!/usr/bin/env python3
"""
Orchestration Bridge Performance Benchmark

벤치마크 항목:
1. OrchestrationBridge 초기화 시간
2. get_orchestration_context() 응답 시간
3. should_trigger_recovery() 판단 시간
4. get_channel_latency_map() 조회 시간
5. 메모리 사용량
"""

import sys
import time
import statistics
from pathlib import Path
from typing import List, Dict

# Add scripts to path
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from orchestration_bridge import OrchestrationBridge


def benchmark_initialization(iterations: int = 100) -> Dict:
    """OrchestrationBridge 초기화 벤치마크"""
    times = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        bridge = OrchestrationBridge()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # ms
    
    return {
        "operation": "initialization",
        "iterations": iterations,
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "min_ms": min(times),
        "max_ms": max(times),
        "stddev_ms": statistics.stdev(times) if len(times) > 1 else 0
    }


def benchmark_get_context(iterations: int = 100) -> Dict:
    """get_orchestration_context() 벤치마크"""
    bridge = OrchestrationBridge()
    times = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        context = bridge.get_orchestration_context()
        end = time.perf_counter()
        times.append((end - start) * 1000)
    
    return {
        "operation": "get_orchestration_context",
        "iterations": iterations,
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "min_ms": min(times),
        "max_ms": max(times),
        "stddev_ms": statistics.stdev(times) if len(times) > 1 else 0
    }


def benchmark_should_trigger(iterations: int = 100) -> Dict:
    """should_trigger_recovery() 벤치마크"""
    bridge = OrchestrationBridge()
    times = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        should_trigger, reason = bridge.should_trigger_recovery()
        end = time.perf_counter()
        times.append((end - start) * 1000)
    
    return {
        "operation": "should_trigger_recovery",
        "iterations": iterations,
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "min_ms": min(times),
        "max_ms": max(times),
        "stddev_ms": statistics.stdev(times) if len(times) > 1 else 0
    }


def benchmark_latency_map(iterations: int = 100) -> Dict:
    """get_channel_latency_map() 벤치마크"""
    bridge = OrchestrationBridge()
    times = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        latency_map = bridge.get_channel_latency_map()
        end = time.perf_counter()
        times.append((end - start) * 1000)
    
    return {
        "operation": "get_channel_latency_map",
        "iterations": iterations,
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "min_ms": min(times),
        "max_ms": max(times),
        "stddev_ms": statistics.stdev(times) if len(times) > 1 else 0
    }


def benchmark_end_to_end(iterations: int = 50) -> Dict:
    """End-to-end 시나리오 벤치마크"""
    times = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        
        # 1. 초기화
        bridge = OrchestrationBridge()
        
        # 2. 컨텍스트 조회
        context = bridge.get_orchestration_context()
        
        # 3. 복구 판단
        should_trigger, reason = bridge.should_trigger_recovery()
        
        # 4. 레이턴시 맵 조회
        latency_map = bridge.get_channel_latency_map()
        
        end = time.perf_counter()
        times.append((end - start) * 1000)
    
    return {
        "operation": "end_to_end_scenario",
        "iterations": iterations,
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "min_ms": min(times),
        "max_ms": max(times),
        "stddev_ms": statistics.stdev(times) if len(times) > 1 else 0
    }


def print_benchmark_result(result: Dict):
    """벤치마크 결과 출력"""
    print(f"\n{'='*60}")
    print(f"Operation: {result['operation']}")
    print(f"{'='*60}")
    print(f"Iterations: {result['iterations']}")
    print(f"Mean:       {result['mean_ms']:.2f} ms")
    print(f"Median:     {result['median_ms']:.2f} ms")
    print(f"Min:        {result['min_ms']:.2f} ms")
    print(f"Max:        {result['max_ms']:.2f} ms")
    print(f"Std Dev:    {result['stddev_ms']:.2f} ms")
    
    # 성능 평가
    if result['mean_ms'] < 10:
        grade = "⚡ EXCELLENT"
    elif result['mean_ms'] < 50:
        grade = "✅ GOOD"
    elif result['mean_ms'] < 100:
        grade = "⚠️  ACCEPTABLE"
    else:
        grade = "🔴 NEEDS OPTIMIZATION"
    
    print(f"Grade:      {grade}")


def main():
    print("╔════════════════════════════════════════════════════════╗")
    print("║  Orchestration Bridge Performance Benchmark           ║")
    print("╚════════════════════════════════════════════════════════╝")
    
    # 1. 초기화 벤치마크
    print("\n[1/5] Benchmarking initialization...")
    result_init = benchmark_initialization(100)
    print_benchmark_result(result_init)
    
    # 2. get_orchestration_context 벤치마크
    print("\n[2/5] Benchmarking get_orchestration_context...")
    result_context = benchmark_get_context(100)
    print_benchmark_result(result_context)
    
    # 3. should_trigger_recovery 벤치마크
    print("\n[3/5] Benchmarking should_trigger_recovery...")
    result_trigger = benchmark_should_trigger(100)
    print_benchmark_result(result_trigger)
    
    # 4. get_channel_latency_map 벤치마크
    print("\n[4/5] Benchmarking get_channel_latency_map...")
    result_latency = benchmark_latency_map(100)
    print_benchmark_result(result_latency)
    
    # 5. End-to-end 벤치마크
    print("\n[5/5] Benchmarking end-to-end scenario...")
    result_e2e = benchmark_end_to_end(50)
    print_benchmark_result(result_e2e)
    
    # 종합 평가
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    total_overhead = (result_init['mean_ms'] + result_context['mean_ms'] + 
                      result_trigger['mean_ms'] + result_latency['mean_ms'])
    
    print(f"Total Overhead (Individual Calls): {total_overhead:.2f} ms")
    print(f"End-to-End Overhead:                {result_e2e['mean_ms']:.2f} ms")
    print(f"Efficiency Factor:                  {(total_overhead / result_e2e['mean_ms']):.2f}x")
    
    if result_e2e['mean_ms'] < 100:
        print("\n✅ PERFORMANCE TARGET MET: <100ms")
        print("   System is ready for production use.")
    else:
        print("\n⚠️  PERFORMANCE TARGET MISSED: >100ms")
        print("   Consider optimization before production deployment.")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
