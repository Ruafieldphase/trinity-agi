"""
통합 모니터링 데몬
- Task Queue Server와 통합하여 실제 RPA 작업 모니터링
- 실시간 대시보드 + 자동 알림
"""
import time
import argparse
import sys
from pathlib import Path
from typing import Optional
import psutil
import requests
from datetime import datetime

# 상대 경로로 임포트
sys.path.append(str(Path(__file__).parent))
from metrics_collector import MetricsCollector, DashboardRenderer
from alert_manager import AlertManager, DEFAULT_THRESHOLDS


class RPAMonitoringDaemon:
    """RPA 모니터링 데몬"""
    
    def __init__(
        self,
        server_url: str = "http://127.0.0.1:8091",
        interval_seconds: float = 5.0,
        output_dir: Optional[Path] = None,
    ):
        """
        Args:
            server_url: Task Queue Server URL
            interval_seconds: 모니터링 주기 (초)
            output_dir: 메트릭/알림 저장 디렉토리
        """
        self.server_url = server_url
        self.interval_seconds = interval_seconds
        self.output_dir = output_dir or Path(__file__).parent.parent / "outputs"
        
        # 메트릭 수집기
        self.collector = MetricsCollector(
            history_size=100,
            persist_path=self.output_dir / "rpa_monitoring_metrics.jsonl"
        )
        
        # 알림 관리자
        self.alert_manager = AlertManager(
            alert_log_path=self.output_dir / "rpa_monitoring_alerts.jsonl"
        )
        
        # 기본 임계값 추가
        for threshold in DEFAULT_THRESHOLDS:
            self.alert_manager.add_threshold(threshold)
        
        # 마지막 조회 상태
        self._last_total_tasks = 0
        self._last_successful_tasks = 0
        self._last_failed_tasks = 0
    
    def fetch_queue_stats(self) -> Optional[dict]:
        """Task Queue Server에서 통계 조회"""
        try:
            response = requests.get(
                f"{self.server_url}/api/stats",
                timeout=2.0
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to fetch queue stats: {e}")
            return None
    
    def fetch_results(self, count: int = 10) -> Optional[list]:
        """최근 작업 결과 조회"""
        try:
            response = requests.get(
                f"{self.server_url}/api/results?count={count}",
                timeout=2.0
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except requests.RequestException as e:
            print(f"Failed to fetch results: {e}")
            return None
    
    def update_metrics_from_queue(self):
        """Queue 통계로부터 메트릭 업데이트"""
        stats = self.fetch_queue_stats()
        if not stats:
            return
        
        # Task Queue 상태
        self.collector.update_queue_size(stats.get("pending", 0))
        self.collector.update_worker_count(stats.get("workers", 0))
        
        # 작업 결과 분석
        results = self.fetch_results(count=20)
        if results:
            for result in results:
                # 새로운 결과만 처리 (중복 방지)
                task_id = result.get("task_id", "")
                success = result.get("status") == "success"
                duration_ms = result.get("duration_ms", 0)
                
                # 간단한 중복 방지: 마지막 조회 이후 증가분만 기록
                # (실제로는 task_id 기반 중복 체크 필요)
                pass
        
        # 전체 통계로부터 작업 기록 (증가분만)
        total = stats.get("completed", 0)
        successful = stats.get("successful", 0)
        failed = stats.get("failed", 0)
        
        new_total = total - self._last_total_tasks
        new_successful = successful - self._last_successful_tasks
        new_failed = failed - self._last_failed_tasks
        
        # 새로운 작업이 있으면 기록
        if new_total > 0:
            avg_response_time = stats.get("avg_duration_ms", 0)
            
            # 성공/실패 각각 기록
            for _ in range(new_successful):
                self.collector.record_task(success=True, response_time_ms=avg_response_time)
            
            for _ in range(new_failed):
                self.collector.record_task(success=False, response_time_ms=avg_response_time)
        
        # 마지막 상태 업데이트
        self._last_total_tasks = total
        self._last_successful_tasks = successful
        self._last_failed_tasks = failed
    
    def run(self, duration_minutes: Optional[float] = None):
        """모니터링 데몬 실행
        
        Args:
            duration_minutes: 실행 시간 (분), None이면 무한 실행
        """
        print("🔍 RPA Monitoring Daemon Started")
        print(f"  Server: {self.server_url}")
        print(f"  Interval: {self.interval_seconds}s")
        print(f"  Output: {self.output_dir}")
        print()
        
        start_time = time.time()
        iteration = 0
        
        try:
            while True:
                # 경과 시간 확인
                if duration_minutes:
                    elapsed_minutes = (time.time() - start_time) / 60
                    if elapsed_minutes >= duration_minutes:
                        print(f"\n⏱️  Duration limit reached ({duration_minutes} minutes)")
                        break
                
                iteration += 1
                
                # Queue에서 메트릭 업데이트
                self.update_metrics_from_queue()
                
                # 시스템 리소스 측정
                memory_mb = psutil.Process().memory_info().rss / (1024 * 1024)
                cpu_percent = psutil.cpu_percent(interval=0.1)
                
                # 스냅샷 생성
                snapshot = self.collector.take_snapshot(memory_mb, cpu_percent)
                
                # 통계 조회
                stats = self.collector.get_statistics(window_seconds=60)
                
                # 알림 확인
                metrics = {
                    "error_rate": snapshot.error_rate,
                    "success_rate": snapshot.success_rate,
                    "avg_response_time_ms": snapshot.avg_response_time_ms,
                    "active_workers": snapshot.active_workers,
                    "queue_size": snapshot.queue_size,
                }
                self.alert_manager.check_metrics(metrics)
                
                # 대시보드 렌더링 (10초마다 상세, 나머지는 컴팩트)
                if iteration % 2 == 0:
                    print(DashboardRenderer.render(snapshot, stats))
                else:
                    print(DashboardRenderer.render_compact(snapshot))
                
                # 대기
                time.sleep(self.interval_seconds)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            raise
        finally:
            self._print_summary()
    
    def _print_summary(self):
        """최종 요약 출력"""
        print("\n" + "=" * 70)
        print("📊 Monitoring Summary")
        print("=" * 70)
        
        # 메트릭 통계
        stats = self.collector.get_statistics()
        print("\nMetrics:")
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
        
        # 알림 통계
        all_alerts = self.alert_manager.get_recent_alerts(1000)
        print(f"\nAlerts:")
        print(f"  Total: {len(all_alerts)}")
        for severity in ["critical", "warning", "info"]:
            count = len(self.alert_manager.get_alerts_by_severity(severity))
            icon = AlertManager.SEVERITY_ICONS[severity]
            print(f"  {icon} {severity.capitalize()}: {count}")
        
        print(f"\nOutput Files:")
        print(f"  Metrics: {self.collector.persist_path}")
        print(f"  Alerts: {self.alert_manager.alert_log_path}")


def main():
    parser = argparse.ArgumentParser(description="RPA Monitoring Daemon")
    parser.add_argument(
        "--server",
        default="http://127.0.0.1:8091",
        help="Task Queue Server URL"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Monitoring interval in seconds"
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Run duration in minutes (default: infinite)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for metrics and alerts"
    )
    
    args = parser.parse_args()
    
    daemon = RPAMonitoringDaemon(
        server_url=args.server,
        interval_seconds=args.interval,
        output_dir=args.output_dir,
    )
    
    daemon.run(duration_minutes=args.duration)


if __name__ == "__main__":
    main()
