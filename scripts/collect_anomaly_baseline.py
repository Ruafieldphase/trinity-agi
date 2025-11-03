#!/usr/bin/env python3
"""
Anomaly Detection Baseline Collector

지난 N일간의 시스템 메트릭을 수집하여 Normal behavior baseline을 구축합니다.
이 baseline은 이후 Anomaly Detection에서 사용됩니다.

Author: GitHub Copilot
Created: 2025-11-03
Phase: 7 (System Stabilization)
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

# 프로젝트 루트 경로
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


def load_monitoring_metrics(days: int = 7) -> pd.DataFrame:
    """
    지난 N일간의 monitoring_metrics.json 파일을 로드합니다.
    
    Args:
        days: 수집할 날짜 범위 (일)
        
    Returns:
        DataFrame with columns: timestamp, cpu_percent, memory_percent, 
                                success_rate, avg_latency_ms, queue_size
    """
    metrics_list = []
    
    # outputs/monitoring_metrics_*.json 패턴 파일 수집
    outputs_dir = WORKSPACE_ROOT / "outputs"
    
    # 최신 파일 우선
    for json_file in sorted(outputs_dir.glob("monitoring_metrics_*.json"), reverse=True):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # timestamp 확인
            timestamp_str = data.get("timestamp")
            if not timestamp_str:
                continue
                
            timestamp = datetime.fromisoformat(timestamp_str)
            cutoff = datetime.now() - timedelta(days=days)
            
            if timestamp < cutoff:
                continue
                
            # 메트릭 추출
            metrics = {
                "timestamp": timestamp,
                "cpu_percent": data.get("system_metrics", {}).get("cpu_percent", 0),
                "memory_percent": data.get("system_metrics", {}).get("memory_percent", 0),
                "success_rate": data.get("agi_metrics", {}).get("success_rate", 0),
                "avg_latency_ms": data.get("lumen_metrics", {}).get("avg_latency_ms", 0),
                "queue_size": data.get("queue_metrics", {}).get("pending", 0),
            }
            metrics_list.append(metrics)
            
        except Exception as e:
            print(f"⚠️  Skipping {json_file.name}: {e}", file=sys.stderr)
            continue
    
    if not metrics_list:
        print(f"⚠️  No metrics found in the last {days} days", file=sys.stderr)
        return pd.DataFrame()
    
    df = pd.DataFrame(metrics_list)
    df = df.sort_values("timestamp")
    df = df.reset_index(drop=True)
    
    return df


def calculate_baseline_stats(df: pd.DataFrame) -> Dict:
    """
    Baseline 통계 계산 (평균, 표준편차, threshold)
    
    Args:
        df: 메트릭 DataFrame
        
    Returns:
        Baseline 통계 딕셔너리
    """
    if df.empty:
        return {}
    
    stats = {}
    
    for col in ["cpu_percent", "memory_percent", "success_rate", "avg_latency_ms", "queue_size"]:
        if col not in df.columns:
            continue
            
        values = df[col].dropna()
        if len(values) == 0:
            continue
        
        mean = float(values.mean())
        std = float(values.std())
        
        # Threshold = mean ± 3σ (99.7% coverage)
        if col == "success_rate":
            # Success rate는 높을수록 좋음 → lower threshold만 설정
            lower_threshold = max(0, mean - 3 * std)
            upper_threshold = 100.0
        else:
            # CPU, Memory, Latency, Queue는 낮을수록 좋음 → upper threshold만 중요
            lower_threshold = 0.0
            upper_threshold = min(100.0, mean + 3 * std)
        
        stats[col] = {
            "mean": mean,
            "std": std,
            "min": float(values.min()),
            "max": float(values.max()),
            "median": float(values.median()),
            "q25": float(values.quantile(0.25)),
            "q75": float(values.quantile(0.75)),
            "lower_threshold": lower_threshold,
            "upper_threshold": upper_threshold,
        }
    
    return stats


def save_baseline(baseline: Dict, output_path: Path):
    """Baseline을 JSON 파일로 저장"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(baseline, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Baseline saved to: {output_path}")


def print_baseline_summary(baseline: Dict):
    """Baseline 요약 출력"""
    print("\n" + "="*60)
    print("📊 Anomaly Detection Baseline Summary")
    print("="*60)
    
    for metric, stats in baseline.items():
        print(f"\n🔹 {metric}")
        print(f"   Mean:       {stats['mean']:.2f}")
        print(f"   Std Dev:    {stats['std']:.2f}")
        print(f"   Min/Max:    {stats['min']:.2f} / {stats['max']:.2f}")
        print(f"   Thresholds: {stats['lower_threshold']:.2f} ~ {stats['upper_threshold']:.2f}")


def main():
    parser = argparse.ArgumentParser(description="Collect Anomaly Detection Baseline")
    parser.add_argument("--days", type=int, default=7, help="Number of days to collect (default: 7)")
    parser.add_argument("--output", type=str, default="outputs/anomaly_baseline.json", 
                        help="Output JSON path (default: outputs/anomaly_baseline.json)")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    print(f"🔍 Collecting baseline from last {args.days} days...")
    
    # 메트릭 수집
    df = load_monitoring_metrics(days=args.days)
    
    if df.empty:
        print("❌ No metrics collected. Cannot create baseline.", file=sys.stderr)
        return 1
    
    print(f"✅ Collected {len(df)} data points")
    
    if args.verbose:
        print(f"\n📈 Raw data preview:")
        print(df.head(10))
    
    # Baseline 통계 계산
    baseline = calculate_baseline_stats(df)
    
    if not baseline:
        print("❌ Failed to calculate baseline statistics.", file=sys.stderr)
        return 1
    
    # 메타데이터 추가
    baseline["_metadata"] = {
        "created_at": datetime.now().isoformat(),
        "days_collected": args.days,
        "data_points": len(df),
        "start_date": df["timestamp"].min().isoformat(),
        "end_date": df["timestamp"].max().isoformat(),
    }
    
    # 저장
    output_path = WORKSPACE_ROOT / args.output
    save_baseline(baseline, output_path)
    
    # 요약 출력
    print_baseline_summary(baseline)
    
    print("\n" + "="*60)
    print("✅ Baseline collection complete!")
    print("="*60)
    print(f"\nNext step:")
    print(f"  .\\scripts\\start_anomaly_monitor.ps1")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
