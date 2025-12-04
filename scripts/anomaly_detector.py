#!/usr/bin/env python3
"""
Anomaly Detector with Machine Learning

실시간으로 시스템 메트릭을 모니터링하고 ML 기반으로 이상 패턴을 감지합니다.

Features:
- Isolation Forest 기반 이상 감지
- Sliding window (1시간) 분석
- Multi-level severity (Critical, Warning, Info)
- Alert 생성 및 로깅

Author: GitHub Copilot
Created: 2025-11-03
Phase: 7 (System Stabilization)
"""

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import psutil
from sklearn.ensemble import IsolationForest

# 프로젝트 루트 경로
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


class AnomalyDetector:
    """실시간 Anomaly Detection 시스템"""
    
    def __init__(self, baseline_path: Path, dry_run: bool = False):
        """
        Args:
            baseline_path: Baseline JSON 파일 경로
            dry_run: Dry-run 모드 (Alert 생성 안 함)
        """
        self.baseline_path = baseline_path
        self.dry_run = dry_run
        self.baseline = self._load_baseline()
        self.history = []  # Sliding window
        self.model = None
        self._init_model()
        
    def _load_baseline(self) -> Dict:
        """Baseline JSON 로드"""
        if not self.baseline_path.exists():
            raise FileNotFoundError(f"Baseline not found: {self.baseline_path}")
        
        with open(self.baseline_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _init_model(self):
        """Isolation Forest 모델 초기화"""
        # contamination: 예상 이상치 비율 (기본 5%)
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42,
            n_jobs=-1
        )
        print("✅ Isolation Forest initialized (contamination=0.05)")
    
    def collect_current_metrics(self) -> Dict:
        """현재 시스템 메트릭 수집"""
        try:
            # CPU & Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Monitoring metrics (최신 파일)
            monitoring_path = WORKSPACE_ROOT / "outputs" / "monitoring_metrics_latest.json"
            if monitoring_path.exists():
                # UTF-8 BOM 대응
                with open(monitoring_path, 'r', encoding='utf-8-sig') as f:
                    monitoring = json.load(f)
                    
                agi_metrics = monitoring.get("agi_metrics", {})
                lumen_metrics = monitoring.get("lumen_metrics", {})
                queue_metrics = monitoring.get("queue_metrics", {})
                
                success_rate = agi_metrics.get("success_rate", 0)
                avg_latency_ms = lumen_metrics.get("avg_latency_ms", 0)
                queue_size = queue_metrics.get("pending", 0)
            else:
                success_rate = 0
                avg_latency_ms = 0
                queue_size = 0
            
            return {
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "success_rate": success_rate,
                "avg_latency_ms": avg_latency_ms,
                "queue_size": queue_size,
            }
        except Exception as e:
            print(f"⚠️  Failed to collect metrics: {e}", file=sys.stderr)
            return {}
    
    def check_threshold_anomaly(self, metrics: Dict) -> List[Dict]:
        """Threshold 기반 이상 감지 (간단한 룰 기반)"""
        anomalies = []
        
        for key in ["cpu_percent", "memory_percent", "success_rate", "avg_latency_ms", "queue_size"]:
            if key not in metrics or key not in self.baseline:
                continue
            
            value = metrics[key]
            baseline_stats = self.baseline[key]
            
            lower = baseline_stats["lower_threshold"]
            upper = baseline_stats["upper_threshold"]
            
            # Success rate는 낮으면 이상
            if key == "success_rate":
                if value < lower:
                    severity = "Critical" if value < lower - 10 else "Warning"
                    anomalies.append({
                        "metric": key,
                        "value": value,
                        "baseline_range": f"{lower:.2f}~{upper:.2f}",
                        "severity": severity,
                        "message": f"Success rate too low: {value:.2f}% (expected >{lower:.2f}%)"
                    })
            # 나머지는 높으면 이상
            else:
                if value > upper:
                    # Critical: threshold + 2σ 초과
                    mean = baseline_stats["mean"]
                    std = baseline_stats["std"]
                    critical_threshold = mean + 5 * std
                    
                    severity = "Critical" if value > critical_threshold else "Warning"
                    anomalies.append({
                        "metric": key,
                        "value": value,
                        "baseline_range": f"{lower:.2f}~{upper:.2f}",
                        "severity": severity,
                        "message": f"{key} too high: {value:.2f} (expected <{upper:.2f})"
                    })
        
        return anomalies
    
    def check_ml_anomaly(self, metrics: Dict) -> Optional[Dict]:
        """ML 기반 이상 감지 (Isolation Forest)"""
        # Sliding window에 추가
        self.history.append(metrics)
        
        # 1시간 (60개) 이상 유지
        cutoff = datetime.now() - timedelta(hours=1)
        self.history = [
            m for m in self.history
            if datetime.fromisoformat(m["timestamp"]) > cutoff
        ]
        
        # 최소 10개 데이터 필요
        if len(self.history) < 10:
            return None
        
        # Feature matrix 생성
        features = []
        for m in self.history:
            features.append([
                m.get("cpu_percent", 0),
                m.get("memory_percent", 0),
                m.get("success_rate", 0),
                m.get("avg_latency_ms", 0),
                m.get("queue_size", 0),
            ])
        
        X = np.array(features)
        
        # 모델 학습 (매번 재학습)
        try:
            self.model.fit(X)
            predictions = self.model.predict(X)
            
            # 마지막 데이터포인트가 이상인지 확인
            if predictions[-1] == -1:
                # Anomaly score 계산
                scores = self.model.score_samples(X)
                current_score = scores[-1]
                mean_score = np.mean(scores[:-1])
                
                return {
                    "metric": "ml_composite",
                    "anomaly_score": float(current_score),
                    "mean_score": float(mean_score),
                    "severity": "Info",
                    "message": f"ML detected anomaly (score: {current_score:.3f}, mean: {mean_score:.3f})"
                }
        except Exception as e:
            print(f"⚠️  ML anomaly check failed: {e}", file=sys.stderr)
        
        return None
    
    def create_alert(self, anomalies: List[Dict], metrics: Dict):
        """Alert 생성 및 저장"""
        if not anomalies:
            return
        
        alert = {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "anomalies": anomalies,
            "total_anomalies": len(anomalies),
            "max_severity": max(a["severity"] for a in anomalies),
        }
        
        # Alert 로그 저장
        alert_log_path = WORKSPACE_ROOT / "outputs" / "anomaly_alerts.jsonl"
        alert_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(alert_log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(alert, ensure_ascii=False) + '\n')
        
        # 최신 Alert 저장
        latest_path = WORKSPACE_ROOT / "outputs" / "anomaly_alert_latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(alert, f, indent=2, ensure_ascii=False)
        
        # Console 출력
        severity_color = {
            "Critical": "\033[91m",  # Red
            "Warning": "\033[93m",   # Yellow
            "Info": "\033[94m",      # Blue
        }
        reset = "\033[0m"
        
        max_severity = alert["max_severity"]
        color = severity_color.get(max_severity, "")
        
        print(f"\n{color}🚨 [{max_severity}] Anomaly Detected!{reset}")
        for anomaly in anomalies:
            print(f"   • {anomaly['message']}")
        print(f"   📝 Saved to: {latest_path}\n")
    
    def run_once(self):
        """1회 검사 실행"""
        print(f"🔍 [{datetime.now().strftime('%H:%M:%S')}] Checking for anomalies...")
        
        # 메트릭 수집
        metrics = self.collect_current_metrics()
        if not metrics:
            print("   ⚠️  No metrics collected")
            return
        
        # Threshold 기반 검사
        threshold_anomalies = self.check_threshold_anomaly(metrics)
        
        # ML 기반 검사
        ml_anomaly = self.check_ml_anomaly(metrics)
        
        # 통합
        all_anomalies = threshold_anomalies[:]
        if ml_anomaly:
            all_anomalies.append(ml_anomaly)
        
        # Alert 생성
        if all_anomalies:
            if self.dry_run:
                print(f"   [DRY-RUN] Would create alert for {len(all_anomalies)} anomalies")
                for a in all_anomalies:
                    print(f"      • [{a['severity']}] {a['message']}")
            else:
                self.create_alert(all_anomalies, metrics)
        else:
            print("   ✅ No anomalies detected")
    
    def run_loop(self, interval: int):
        """반복 검사 실행"""
        print(f"🚀 Starting anomaly detection loop (interval: {interval}s)")
        print(f"   Baseline: {self.baseline_path}")
        print(f"   Dry-run: {self.dry_run}")
        print(f"\nPress Ctrl+C to stop\n")
        
        try:
            while True:
                self.run_once()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n✅ Anomaly detection stopped by user")


def main():
    parser = argparse.ArgumentParser(description="Anomaly Detector with ML")
    parser.add_argument("--baseline", type=str, required=True, help="Baseline JSON path")
    parser.add_argument("--interval", type=int, default=60, help="Check interval (seconds, default: 60)")
    parser.add_argument("--dry-run", action="store_true", help="Dry-run mode (no alerts)")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    
    args = parser.parse_args()
    
    baseline_path = Path(args.baseline)
    if not baseline_path.is_absolute():
        baseline_path = WORKSPACE_ROOT / baseline_path
    
    # Detector 초기화
    try:
        detector = AnomalyDetector(baseline_path=baseline_path, dry_run=args.dry_run)
    except Exception as e:
        print(f"❌ Failed to initialize detector: {e}", file=sys.stderr)
        return 1
    
    # 실행
    if args.once:
        detector.run_once()
    else:
        detector.run_loop(interval=args.interval)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
