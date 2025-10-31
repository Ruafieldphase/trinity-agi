"""
실시간 메트릭 수집기
- RPA 작업 성공률, 응답시간, 에러율 등 수집
- 시계열 데이터로 저장하여 트렌드 분석 가능
"""
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import deque
from threading import Lock


@dataclass
class MetricSnapshot:
    """메트릭 스냅샷"""
    timestamp: float
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    avg_response_time_ms: float
    error_rate: float
    active_workers: int
    queue_size: int
    memory_usage_mb: float
    cpu_usage_percent: float
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)
    
    @property
    def success_rate(self) -> float:
        """성공률 (%)"""
        if self.total_tasks == 0:
            return 0.0
        return (self.successful_tasks / self.total_tasks) * 100


class MetricsCollector:
    """실시간 메트릭 수집기"""
    
    def __init__(self, history_size: int = 100, persist_path: Optional[Path] = None):
        """
        Args:
            history_size: 메모리에 보관할 최대 스냅샷 개수
            persist_path: 메트릭을 저장할 파일 경로 (JSONL)
        """
        self.history_size = history_size
        self.persist_path = persist_path
        
        # 메트릭 히스토리 (deque for O(1) append/pop)
        self._snapshots: deque[MetricSnapshot] = deque(maxlen=history_size)
        self._lock = Lock()
        
        # 누적 통계
        self._total_tasks = 0
        self._successful_tasks = 0
        self._failed_tasks = 0
        self._response_times: deque[float] = deque(maxlen=1000)  # 최근 1000개
        
        # 현재 상태
        self._active_workers = 0
        self._queue_size = 0
    
    def record_task(self, success: bool, response_time_ms: float):
        """작업 실행 결과 기록"""
        with self._lock:
            self._total_tasks += 1
            if success:
                self._successful_tasks += 1
            else:
                self._failed_tasks += 1
            
            self._response_times.append(response_time_ms)
    
    def update_worker_count(self, count: int):
        """활성 Worker 수 업데이트"""
        with self._lock:
            self._active_workers = count
    
    def update_queue_size(self, size: int):
        """Queue 크기 업데이트"""
        with self._lock:
            self._queue_size = size
    
    def take_snapshot(self, memory_mb: float = 0.0, cpu_percent: float = 0.0) -> MetricSnapshot:
        """현재 상태의 스냅샷 생성"""
        with self._lock:
            # 평균 응답 시간 계산
            avg_response = sum(self._response_times) / len(self._response_times) if self._response_times else 0.0
            
            # 에러율 계산
            error_rate = (self._failed_tasks / max(self._total_tasks, 1)) * 100
            
            snapshot = MetricSnapshot(
                timestamp=time.time(),
                total_tasks=self._total_tasks,
                successful_tasks=self._successful_tasks,
                failed_tasks=self._failed_tasks,
                avg_response_time_ms=avg_response,
                error_rate=error_rate,
                active_workers=self._active_workers,
                queue_size=self._queue_size,
                memory_usage_mb=memory_mb,
                cpu_usage_percent=cpu_percent,
            )
            
            # 히스토리에 추가
            self._snapshots.append(snapshot)
            
            # 파일에 저장 (옵션)
            if self.persist_path:
                self._persist_snapshot(snapshot)
            
            return snapshot
    
    def _persist_snapshot(self, snapshot: MetricSnapshot):
        """스냅샷을 JSONL 파일에 저장"""
        try:
            self.persist_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.persist_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(snapshot.to_dict()) + "\n")
        except Exception as e:
            print(f"Failed to persist snapshot: {e}")
    
    def get_recent_snapshots(self, count: int = 10) -> List[MetricSnapshot]:
        """최근 N개의 스냅샷 조회"""
        with self._lock:
            # deque는 FIFO이므로 마지막 N개가 최신
            return list(self._snapshots)[-count:]
    
    def get_statistics(self, window_seconds: Optional[float] = None) -> Dict[str, Any]:
        """통계 조회
        
        Args:
            window_seconds: 지정 시 해당 시간 내의 스냅샷만 사용
        """
        with self._lock:
            if window_seconds:
                cutoff = time.time() - window_seconds
                snapshots = [s for s in self._snapshots if s.timestamp >= cutoff]
            else:
                snapshots = list(self._snapshots)
            
            if not snapshots:
                return {
                    "count": 0,
                    "avg_success_rate": 0.0,
                    "avg_error_rate": 0.0,
                    "avg_response_time_ms": 0.0,
                    "max_response_time_ms": 0.0,
                    "min_response_time_ms": 0.0,
                }
            
            success_rates = [s.success_rate for s in snapshots]
            error_rates = [s.error_rate for s in snapshots]
            response_times = [s.avg_response_time_ms for s in snapshots]
            
            return {
                "count": len(snapshots),
                "window_seconds": window_seconds,
                "avg_success_rate": sum(success_rates) / len(success_rates),
                "avg_error_rate": sum(error_rates) / len(error_rates),
                "avg_response_time_ms": sum(response_times) / len(response_times),
                "max_response_time_ms": max(response_times),
                "min_response_time_ms": min(response_times),
                "total_tasks": snapshots[-1].total_tasks if snapshots else 0,
                "successful_tasks": snapshots[-1].successful_tasks if snapshots else 0,
                "failed_tasks": snapshots[-1].failed_tasks if snapshots else 0,
            }
    
    def reset(self):
        """모든 메트릭 초기화"""
        with self._lock:
            self._total_tasks = 0
            self._successful_tasks = 0
            self._failed_tasks = 0
            self._response_times.clear()
            self._snapshots.clear()
            self._active_workers = 0
            self._queue_size = 0


class DashboardRenderer:
    """콘솔 기반 대시보드 렌더러"""
    
    @staticmethod
    def render(snapshot: MetricSnapshot, stats: Dict[str, Any]) -> str:
        """스냅샷과 통계를 콘솔 친화적으로 렌더링"""
        timestamp_str = datetime.fromtimestamp(snapshot.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        
        # 성공률에 따른 색상 (터미널 ANSI 코드)
        success_rate = snapshot.success_rate
        if success_rate >= 95:
            status_icon = "✅"
            status_color = "\033[92m"  # Green
        elif success_rate >= 80:
            status_icon = "⚠️"
            status_color = "\033[93m"  # Yellow
        else:
            status_icon = "❌"
            status_color = "\033[91m"  # Red
        
        reset_color = "\033[0m"
        
        lines = [
            "=" * 70,
            f"🔍 RPA Monitoring Dashboard - {timestamp_str}",
            "=" * 70,
            "",
            f"{status_icon} System Status: {status_color}{success_rate:.1f}% Success Rate{reset_color}",
            "",
            "📊 Current Metrics:",
            f"  Total Tasks:     {snapshot.total_tasks}",
            f"  Successful:      {snapshot.successful_tasks} ✅",
            f"  Failed:          {snapshot.failed_tasks} ❌",
            f"  Success Rate:    {success_rate:.1f}%",
            f"  Error Rate:      {snapshot.error_rate:.1f}%",
            f"  Avg Response:    {snapshot.avg_response_time_ms:.2f}ms",
            "",
            "🔧 Infrastructure:",
            f"  Active Workers:  {snapshot.active_workers}",
            f"  Queue Size:      {snapshot.queue_size}",
            f"  Memory Usage:    {snapshot.memory_usage_mb:.1f}MB",
            f"  CPU Usage:       {snapshot.cpu_usage_percent:.1f}%",
            "",
            "📈 Statistics (Recent Window):",
            f"  Snapshots:       {stats['count']}",
            f"  Avg Success:     {stats['avg_success_rate']:.1f}%",
            f"  Avg Error:       {stats['avg_error_rate']:.1f}%",
            f"  Avg Response:    {stats['avg_response_time_ms']:.2f}ms",
            f"  Max Response:    {stats['max_response_time_ms']:.2f}ms",
            f"  Min Response:    {stats['min_response_time_ms']:.2f}ms",
            "=" * 70,
        ]
        
        return "\n".join(lines)
    
    @staticmethod
    def render_compact(snapshot: MetricSnapshot) -> str:
        """컴팩트한 한 줄 요약"""
        timestamp_str = datetime.fromtimestamp(snapshot.timestamp).strftime("%H:%M:%S")
        return (
            f"[{timestamp_str}] "
            f"Tasks: {snapshot.total_tasks} "
            f"| Success: {snapshot.success_rate:.1f}% "
            f"| Errors: {snapshot.error_rate:.1f}% "
            f"| Response: {snapshot.avg_response_time_ms:.0f}ms "
            f"| Workers: {snapshot.active_workers} "
            f"| Queue: {snapshot.queue_size}"
        )


def demo_metrics_collector():
    """메트릭 수집기 데모"""
    import random
    
    print("🔍 Metrics Collector Demo\n")
    
    # 수집기 초기화
    output_dir = Path(__file__).parent.parent / "outputs"
    collector = MetricsCollector(
        history_size=50,
        persist_path=output_dir / "metrics_demo.jsonl"
    )
    
    # 시뮬레이션: 10초간 작업 실행
    print("Simulating RPA tasks for 10 seconds...\n")
    
    for i in range(20):
        # 작업 실행 시뮬레이션
        num_tasks = random.randint(1, 5)
        for _ in range(num_tasks):
            success = random.random() > 0.1  # 90% 성공률
            response_time = random.uniform(50, 500)  # 50-500ms
            collector.record_task(success, response_time)
        
        # 인프라 상태 업데이트
        collector.update_worker_count(random.randint(1, 3))
        collector.update_queue_size(random.randint(0, 10))
        
        # 스냅샷 생성
        memory = random.uniform(50, 150)
        cpu = random.uniform(20, 80)
        snapshot = collector.take_snapshot(memory, cpu)
        
        # 통계 조회
        stats = collector.get_statistics(window_seconds=60)
        
        # 대시보드 렌더링 (5초마다 상세, 나머지는 컴팩트)
        if i % 5 == 0:
            print(DashboardRenderer.render(snapshot, stats))
        else:
            print(DashboardRenderer.render_compact(snapshot))
        
        time.sleep(0.5)
    
    # 최종 통계
    print("\n" + "=" * 70)
    print("📊 Final Statistics")
    print("=" * 70)
    
    final_stats = collector.get_statistics()
    for key, value in final_stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    print(f"\nMetrics saved to: {collector.persist_path}")
    print(f"Total snapshots collected: {len(collector.get_recent_snapshots(100))}")


if __name__ == "__main__":
    demo_metrics_collector()
