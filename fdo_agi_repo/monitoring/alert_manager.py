"""
자동 알림 시스템
- 임계값 초과 시 자동 알림
- 콘솔 출력 및 로그 파일 기록
"""
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json


@dataclass
class AlertThreshold:
    """알림 임계값 설정"""
    name: str
    metric_name: str
    operator: str  # ">", "<", ">=", "<=", "=="
    value: float
    severity: str  # "critical", "warning", "info"
    message_template: str
    
    def check(self, current_value: float) -> bool:
        """임계값 초과 여부 확인"""
        if self.operator == ">":
            return current_value > self.value
        elif self.operator == "<":
            return current_value < self.value
        elif self.operator == ">=":
            return current_value >= self.value
        elif self.operator == "<=":
            return current_value <= self.value
        elif self.operator == "==":
            return abs(current_value - self.value) < 0.001
        else:
            raise ValueError(f"Unknown operator: {self.operator}")
    
    def format_message(self, current_value: float) -> str:
        """알림 메시지 생성"""
        return self.message_template.format(
            metric=self.metric_name,
            current=current_value,
            threshold=self.value,
        )


@dataclass
class Alert:
    """발생한 알림"""
    timestamp: float
    threshold_name: str
    severity: str
    metric_name: str
    current_value: float
    threshold_value: float
    message: str
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "timestamp": self.timestamp,
            "timestamp_str": datetime.fromtimestamp(self.timestamp).isoformat(),
            "threshold_name": self.threshold_name,
            "severity": self.severity,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "threshold_value": self.threshold_value,
            "message": self.message,
        }


class AlertManager:
    """알림 관리자"""
    
    # 심각도별 아이콘
    SEVERITY_ICONS = {
        "critical": "🚨",
        "warning": "⚠️",
        "info": "ℹ️",
    }
    
    # 심각도별 ANSI 색상
    SEVERITY_COLORS = {
        "critical": "\033[91m",  # Red
        "warning": "\033[93m",   # Yellow
        "info": "\033[94m",      # Blue
    }
    RESET_COLOR = "\033[0m"
    
    def __init__(self, alert_log_path: Optional[Path] = None):
        """
        Args:
            alert_log_path: 알림 로그를 저장할 파일 경로 (JSONL)
        """
        self.alert_log_path = alert_log_path
        self.thresholds: List[AlertThreshold] = []
        self.alert_history: List[Alert] = []
        self.alert_callbacks: List[Callable[[Alert], None]] = []
    
    def add_threshold(self, threshold: AlertThreshold):
        """임계값 추가"""
        self.thresholds.append(threshold)
    
    def add_callback(self, callback: Callable[[Alert], None]):
        """알림 발생 시 실행할 콜백 추가"""
        self.alert_callbacks.append(callback)
    
    def check_metrics(self, metrics: Dict[str, float]) -> List[Alert]:
        """메트릭을 확인하고 임계값 초과 시 알림 발생"""
        alerts = []
        
        for threshold in self.thresholds:
            if threshold.metric_name not in metrics:
                continue
            
            current_value = metrics[threshold.metric_name]
            
            if threshold.check(current_value):
                alert = Alert(
                    timestamp=datetime.now().timestamp(),
                    threshold_name=threshold.name,
                    severity=threshold.severity,
                    metric_name=threshold.metric_name,
                    current_value=current_value,
                    threshold_value=threshold.value,
                    message=threshold.format_message(current_value),
                )
                
                alerts.append(alert)
                self.alert_history.append(alert)
                
                # 콘솔 출력
                self._print_alert(alert)
                
                # 로그 파일 저장
                if self.alert_log_path:
                    self._save_alert(alert)
                
                # 콜백 실행
                for callback in self.alert_callbacks:
                    try:
                        callback(alert)
                    except Exception as e:
                        print(f"Alert callback error: {e}")
        
        return alerts
    
    def _print_alert(self, alert: Alert):
        """알림을 콘솔에 출력"""
        icon = self.SEVERITY_ICONS.get(alert.severity, "❓")
        color = self.SEVERITY_COLORS.get(alert.severity, "")
        timestamp_str = datetime.fromtimestamp(alert.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"\n{color}{icon} ALERT [{alert.severity.upper()}] - {timestamp_str}{self.RESET_COLOR}")
        print(f"  {alert.message}")
        print(f"  Threshold: {alert.threshold_name}")
        print(f"  Current: {alert.current_value:.2f}, Limit: {alert.threshold_value:.2f}")
        print()
    
    def _save_alert(self, alert: Alert):
        """알림을 JSONL 파일에 저장"""
        try:
            self.alert_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.alert_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(alert.to_dict()) + "\n")
        except Exception as e:
            print(f"Failed to save alert: {e}")
    
    def get_recent_alerts(self, count: int = 10) -> List[Alert]:
        """최근 N개의 알림 조회"""
        return self.alert_history[-count:]
    
    def get_alerts_by_severity(self, severity: str) -> List[Alert]:
        """심각도별 알림 조회"""
        return [a for a in self.alert_history if a.severity == severity]


# 기본 임계값 프리셋
DEFAULT_THRESHOLDS = [
    AlertThreshold(
        name="high_error_rate",
        metric_name="error_rate",
        operator=">",
        value=20.0,
        severity="critical",
        message_template="Error rate is critically high: {current:.1f}% (threshold: {threshold:.1f}%)",
    ),
    AlertThreshold(
        name="low_success_rate",
        metric_name="success_rate",
        operator="<",
        value=80.0,
        severity="warning",
        message_template="Success rate is below target: {current:.1f}% (threshold: {threshold:.1f}%)",
    ),
    AlertThreshold(
        name="high_response_time",
        metric_name="avg_response_time_ms",
        operator=">",
        value=1000.0,
        severity="warning",
        message_template="Average response time is high: {current:.0f}ms (threshold: {threshold:.0f}ms)",
    ),
    AlertThreshold(
        name="no_active_workers",
        metric_name="active_workers",
        operator="==",
        value=0.0,
        severity="critical",
        message_template="No active workers detected! Current: {current}, Expected: > 0",
    ),
    AlertThreshold(
        name="high_queue_size",
        metric_name="queue_size",
        operator=">",
        value=50.0,
        severity="info",
        message_template="Queue size is growing: {current:.0f} tasks (threshold: {threshold:.0f})",
    ),
]


def demo_alert_system():
    """알림 시스템 데모"""
    import time
    import random
    from metrics_collector import MetricsCollector
    
    print("🚨 Alert System Demo\n")
    
    # 출력 디렉토리
    output_dir = Path(__file__).parent.parent / "outputs"
    
    # 알림 관리자 초기화
    alert_manager = AlertManager(alert_log_path=output_dir / "alerts_demo.jsonl")
    
    # 기본 임계값 추가
    for threshold in DEFAULT_THRESHOLDS:
        alert_manager.add_threshold(threshold)
    
    # 커스텀 콜백 추가
    def custom_callback(alert: Alert):
        if alert.severity == "critical":
            print(f"  🔔 Custom action: Sending notification for critical alert...")
    
    alert_manager.add_callback(custom_callback)
    
    # 메트릭 수집기
    collector = MetricsCollector(history_size=10)
    
    print("Simulating metrics with alert triggers...\n")
    
    # 시뮬레이션: 다양한 시나리오
    scenarios = [
        {"name": "Normal operation", "success_rate": 0.95, "response_time": (100, 300), "workers": 3},
        {"name": "Degraded performance", "success_rate": 0.75, "response_time": (500, 1500), "workers": 2},
        {"name": "System failure", "success_rate": 0.50, "response_time": (1000, 2000), "workers": 0},
        {"name": "Recovery", "success_rate": 0.90, "response_time": (200, 400), "workers": 3},
    ]
    
    for scenario in scenarios:
        print(f"--- Scenario: {scenario['name']} ---")
        
        # 작업 실행 시뮬레이션
        for _ in range(10):
            success = random.random() < scenario["success_rate"]
            response_time = random.uniform(*scenario["response_time"])
            collector.record_task(success, response_time)
        
        collector.update_worker_count(scenario["workers"])
        collector.update_queue_size(random.randint(5, 60))
        
        # 스냅샷 생성
        snapshot = collector.take_snapshot()
        
        # 알림 확인
        metrics = {
            "error_rate": snapshot.error_rate,
            "success_rate": snapshot.success_rate,
            "avg_response_time_ms": snapshot.avg_response_time_ms,
            "active_workers": snapshot.active_workers,
            "queue_size": snapshot.queue_size,
        }
        
        alerts = alert_manager.check_metrics(metrics)
        
        if not alerts:
            print("  ✅ All metrics within thresholds")
        
        print()
        time.sleep(1)
    
    # 알림 요약
    print("=" * 70)
    print("📊 Alert Summary")
    print("=" * 70)
    
    all_alerts = alert_manager.get_recent_alerts(100)
    print(f"Total alerts: {len(all_alerts)}")
    
    for severity in ["critical", "warning", "info"]:
        count = len(alert_manager.get_alerts_by_severity(severity))
        icon = AlertManager.SEVERITY_ICONS[severity]
        print(f"  {icon} {severity.capitalize()}: {count}")
    
    print(f"\nAlerts saved to: {alert_manager.alert_log_path}")


if __name__ == "__main__":
    demo_alert_system()
