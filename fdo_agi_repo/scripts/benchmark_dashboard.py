#!/usr/bin/env python3
"""
Dashboard 로딩 시간 벤치마크

각 단계별 시간을 측정하여 병목 지점 식별
"""

import sys
import time
from pathlib import Path

# Repo root 경로 추가
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from monitor.metrics_collector import MetricsCollector


def benchmark_dashboard():
    """Dashboard 로딩 시간 측정"""

    print("="*60)
    print("Dashboard Loading Benchmark")
    print("="*60)

    collector = MetricsCollector()
    results = {}

    # 1. read_events (24시간)
    print("\n[1/6] read_events(24h)...")
    start = time.perf_counter()
    events_24h = collector.read_events(hours=24.0)
    duration = time.perf_counter() - start
    results['read_events_24h'] = duration
    print(f"  Duration: {duration:.3f}s ({len(events_24h)} events)")

    # 2. read_events (1시간)
    print("\n[2/6] read_events(1h)...")
    start = time.perf_counter()
    events_1h = collector.read_events(hours=1.0)
    duration = time.perf_counter() - start
    results['read_events_1h'] = duration
    print(f"  Duration: {duration:.3f}s ({len(events_1h)} events)")

    # 3. get_realtime_metrics
    print("\n[3/6] get_realtime_metrics(1h)...")
    start = time.perf_counter()
    metrics = collector.get_realtime_metrics(hours=1.0)
    duration = time.perf_counter() - start
    results['realtime_metrics'] = duration
    print(f"  Duration: {duration:.3f}s")

    # 4. get_timeline_data
    print("\n[4/6] get_timeline_data(6h, 30min)...")
    start = time.perf_counter()
    timeline = collector.get_timeline_data(hours=6.0, interval_minutes=30)
    duration = time.perf_counter() - start
    results['timeline_data'] = duration
    print(f"  Duration: {duration:.3f}s ({len(timeline)} intervals)")

    # 5. External services (분리 측정)
    print("\n[5/6] External services check...")

    # Lumen
    print("  [5a] Lumen gateway...")
    start = time.perf_counter()
    lumen_status = collector._check_lumen_gateway()
    lumen_duration = time.perf_counter() - start
    results['lumen_check'] = lumen_duration
    print(f"    Duration: {lumen_duration:.3f}s (ok: {lumen_status.get('ok')})")

    # Proxy
    print("  [5b] Local proxy...")
    start = time.perf_counter()
    proxy_port = collector._resolve_proxy_port()
    proxy_status = collector._check_local_proxy(port=proxy_port)
    proxy_duration = time.perf_counter() - start
    results['proxy_check'] = proxy_duration
    print(f"    Duration: {proxy_duration:.3f}s (ok: {proxy_status.get('ok')})")

    # System
    print("  [5c] System resources...")
    start = time.perf_counter()
    system_status = collector._check_system_resources()
    system_duration = time.perf_counter() - start
    results['system_check'] = system_duration
    print(f"    Duration: {system_duration:.3f}s (ok: {system_status.get('ok')})")

    results['external_services_total'] = lumen_duration + proxy_duration + system_duration

    # 6. Full get_health_status
    print("\n[6/6] Full get_health_status()...")
    start = time.perf_counter()
    health = collector.get_health_status()
    duration = time.perf_counter() - start
    results['full_health_status'] = duration
    print(f"  Duration: {duration:.3f}s")

    # 분석
    print("\n" + "="*60)
    print("Analysis")
    print("="*60)

    # 총 시간 (ops_dashboard.print_dashboard 시뮬레이션)
    estimated_total = (
        results['realtime_metrics'] +  # get_realtime_metrics
        results['timeline_data'] +      # get_timeline_data
        results['full_health_status']   # get_health_status (includes external)
    )

    print(f"\nEstimated total dashboard load time: {estimated_total:.3f}s")
    print(f"\nBreakdown:")
    print(f"  Ledger reading:       {results['read_events_1h']:.3f}s")
    print(f"  Metrics calculation:  {results['realtime_metrics'] - results['read_events_1h']:.3f}s")
    print(f"  Timeline generation:  {results['timeline_data']:.3f}s")
    print(f"  External services:    {results['external_services_total']:.3f}s")
    print(f"    - Lumen:            {results['lumen_check']:.3f}s")
    print(f"    - Proxy:            {results['proxy_check']:.3f}s")
    print(f"    - System:           {results['system_check']:.3f}s")

    # 최적화 제안
    print(f"\n" + "="*60)
    print("Optimization Opportunities")
    print("="*60)

    slowest = []
    if results['lumen_check'] > 1.0:
        slowest.append(f"Lumen gateway check: {results['lumen_check']:.3f}s (consider async or caching)")
    if results['proxy_check'] > 0.5:
        slowest.append(f"Proxy check: {results['proxy_check']:.3f}s (consider async)")
    if results['read_events_24h'] > 1.0:
        slowest.append(f"Ledger reading (24h): {results['read_events_24h']:.3f}s (consider indexing or streaming)")
    if results['timeline_data'] > 0.5:
        slowest.append(f"Timeline generation: {results['timeline_data']:.3f}s (consider caching)")

    if slowest:
        for i, issue in enumerate(slowest, 1):
            print(f"{i}. {issue}")
    else:
        print("No major bottlenecks detected (all < 1s)")

    # 목표 달성 여부
    print(f"\n" + "="*60)
    if estimated_total <= 1.0:
        print(f"PASS: Total load time {estimated_total:.3f}s <= 1s target")
    elif estimated_total <= 3.0:
        print(f"ACCEPTABLE: Total load time {estimated_total:.3f}s (current)")
        print(f"GOAL: Reduce to <= 1s (improvement: {estimated_total - 1.0:.3f}s)")
    else:
        print(f"NEEDS WORK: Total load time {estimated_total:.3f}s >> 3s")
        print(f"GOAL: Reduce to <= 1s (improvement: {estimated_total - 1.0:.3f}s)")

    return results


if __name__ == '__main__':
    benchmark_dashboard()
