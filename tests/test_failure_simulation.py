"""
Phase 3 Day 3: 실전 장애 시뮬레이션 테스트
- 네트워크 장애 (타임아웃, 연결 실패)
- Task Queue/Worker 장애
- 리소스 부족 시나리오
- 자동 복구 메커니즘 검증
"""
import sys
import time
import random
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock
import requests

# Add fdo_agi_repo to path
sys.path.insert(0, str(Path(__file__).parent.parent / "fdo_agi_repo"))

from rpa.execution_engine import ExecutionEngine, ExecutionConfig, ExecutionMode
from rpa.actions import Action, ActionResult


class NetworkFailureSimulator:
    """네트워크 장애 시뮬레이터"""
    
    def __init__(self, failure_rate: float = 0.3, timeout_rate: float = 0.2):
        """
        Args:
            failure_rate: 연결 실패 확률 (0.0 ~ 1.0)
            timeout_rate: 타임아웃 확률 (0.0 ~ 1.0)
        """
        self.failure_rate = failure_rate
        self.timeout_rate = timeout_rate
        self.call_count = 0
        self.failure_count = 0
        self.timeout_count = 0
    
    def simulate_request(self, url: str, timeout: float = 5.0) -> Dict[str, Any]:
        """네트워크 요청 시뮬레이션"""
        self.call_count += 1
        
        # 타임아웃 시뮬레이션
        if random.random() < self.timeout_rate:
            self.timeout_count += 1
            time.sleep(timeout + 0.1)  # 타임아웃보다 약간 길게
            raise requests.exceptions.Timeout(f"Request to {url} timed out")
        
        # 연결 실패 시뮬레이션
        if random.random() < self.failure_rate:
            self.failure_count += 1
            raise requests.exceptions.ConnectionError(f"Failed to connect to {url}")
        
        # 정상 응답
        return {
            "status": "success",
            "data": f"Response from {url}",
            "timestamp": time.time()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 조회"""
        success_count = self.call_count - self.failure_count - self.timeout_count
        return {
            "total_calls": self.call_count,
            "success": success_count,
            "failures": self.failure_count,
            "timeouts": self.timeout_count,
            "success_rate": success_count / max(self.call_count, 1) * 100
        }


class TaskQueueFailureSimulator:
    """Task Queue 장애 시뮬레이터"""
    
    def __init__(self, queue_full_rate: float = 0.2, worker_down_rate: float = 0.1):
        """
        Args:
            queue_full_rate: 큐 오버플로우 확률
            worker_down_rate: Worker 다운 확률
        """
        self.queue_full_rate = queue_full_rate
        self.worker_down_rate = worker_down_rate
        self.enqueue_count = 0
        self.queue_full_count = 0
        self.worker_down_count = 0
        self.tasks = []
    
    def enqueue(self, task: Dict[str, Any]) -> bool:
        """태스크 큐에 추가 시뮬레이션"""
        self.enqueue_count += 1
        
        # 큐 오버플로우 시뮬레이션
        if random.random() < self.queue_full_rate:
            self.queue_full_count += 1
            raise Exception(f"Queue is full (size: {len(self.tasks)})")
        
        # Worker 다운 시뮬레이션
        if random.random() < self.worker_down_rate:
            self.worker_down_count += 1
            raise Exception("No workers available")
        
        # 정상 큐 추가
        self.tasks.append(task)
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 조회"""
        success_count = self.enqueue_count - self.queue_full_count - self.worker_down_count
        return {
            "total_enqueues": self.enqueue_count,
            "success": success_count,
            "queue_full": self.queue_full_count,
            "worker_down": self.worker_down_count,
            "success_rate": success_count / max(self.enqueue_count, 1) * 100,
            "tasks_in_queue": len(self.tasks)
        }


class ResourceConstraintSimulator:
    """리소스 제약 시뮬레이터"""
    
    def __init__(self, memory_limit_mb: int = 100, cpu_threshold: float = 90.0):
        """
        Args:
            memory_limit_mb: 메모리 제한 (MB)
            cpu_threshold: CPU 임계값 (%)
        """
        self.memory_limit_mb = memory_limit_mb
        self.cpu_threshold = cpu_threshold
        self.current_memory_mb = 0
        self.oom_count = 0
        self.cpu_throttle_count = 0
    
    def allocate_memory(self, size_mb: int) -> bool:
        """메모리 할당 시뮬레이션"""
        if self.current_memory_mb + size_mb > self.memory_limit_mb:
            self.oom_count += 1
            raise MemoryError(f"Out of memory: {self.current_memory_mb + size_mb}MB > {self.memory_limit_mb}MB")
        
        self.current_memory_mb += size_mb
        return True
    
    def check_cpu_usage(self, current_usage: float) -> bool:
        """CPU 사용률 체크 시뮬레이션"""
        if current_usage > self.cpu_threshold:
            self.cpu_throttle_count += 1
            return False  # CPU 제한 걸림
        return True
    
    def release_memory(self, size_mb: int):
        """메모리 해제"""
        self.current_memory_mb = max(0, self.current_memory_mb - size_mb)
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 조회"""
        return {
            "current_memory_mb": self.current_memory_mb,
            "memory_limit_mb": self.memory_limit_mb,
            "oom_count": self.oom_count,
            "cpu_throttle_count": self.cpu_throttle_count,
            "memory_utilization": self.current_memory_mb / self.memory_limit_mb * 100
        }


def test_network_failure_with_retry():
    """네트워크 장애 + 자동 재시도 테스트"""
    print("\n🧪 Test: Network Failure with Retry")
    print("="*70)
    
    simulator = NetworkFailureSimulator(failure_rate=0.3, timeout_rate=0.2)
    max_retries = 3
    success_count = 0
    total_attempts = 10
    
    for i in range(total_attempts):
        retries = 0
        success = False
        
        while retries < max_retries and not success:
            try:
                result = simulator.simulate_request(
                    f"http://test-api.com/task/{i}",
                    timeout=2.0
                )
                success = True
                success_count += 1
                print(f"  ✅ Attempt {i+1}: Success after {retries} retries")
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                retries += 1
                if retries < max_retries:
                    print(f"  ⚠️  Attempt {i+1}: {e.__class__.__name__}, retry {retries}/{max_retries}")
                    time.sleep(0.1 * retries)  # 지수 백오프
                else:
                    print(f"  ❌ Attempt {i+1}: Failed after {max_retries} retries")
    
    stats = simulator.get_statistics()
    print(f"\n  📊 Statistics:")
    print(f"    Total API calls: {stats['total_calls']}")
    print(f"    Successful tasks: {success_count}/{total_attempts} ({success_count/total_attempts*100:.1f}%)")
    print(f"    Failures: {stats['failures']}")
    print(f"    Timeouts: {stats['timeouts']}")
    print(f"    Initial success rate: {stats['success_rate']:.1f}%")
    
    # 재시도 덕분에 최종 성공률이 높아야 함
    assert success_count >= total_attempts * 0.7, f"Success rate too low: {success_count/total_attempts*100:.1f}%"
    
    print("  ✅ Network failure + retry test passed")
    print()


def test_task_queue_failure_with_fallback():
    """Task Queue 장애 + 폴백 메커니즘 테스트"""
    print("\n🧪 Test: Task Queue Failure with Fallback")
    print("="*70)
    
    primary_queue = TaskQueueFailureSimulator(queue_full_rate=0.3, worker_down_rate=0.1)
    fallback_queue = TaskQueueFailureSimulator(queue_full_rate=0.1, worker_down_rate=0.05)
    
    total_tasks = 20
    success_count = 0
    fallback_used_count = 0
    
    for i in range(total_tasks):
        task = {"id": i, "action": "test", "data": f"Task {i}"}
        
        try:
            # Primary queue 시도
            primary_queue.enqueue(task)
            success_count += 1
            print(f"  ✅ Task {i}: Enqueued to primary queue")
        except Exception as e:
            # Fallback queue 시도
            try:
                fallback_queue.enqueue(task)
                success_count += 1
                fallback_used_count += 1
                print(f"  🔄 Task {i}: Failed primary ({e}), using fallback")
            except Exception as e2:
                print(f"  ❌ Task {i}: Both queues failed")
    
    primary_stats = primary_queue.get_statistics()
    fallback_stats = fallback_queue.get_statistics()
    
    print(f"\n  📊 Primary Queue Statistics:")
    print(f"    Success: {primary_stats['success']}/{primary_stats['total_enqueues']}")
    print(f"    Queue full: {primary_stats['queue_full']}")
    print(f"    Worker down: {primary_stats['worker_down']}")
    
    print(f"\n  📊 Fallback Queue Statistics:")
    print(f"    Used: {fallback_used_count} times")
    print(f"    Success: {fallback_stats['success']}/{fallback_stats['total_enqueues']}")
    
    print(f"\n  📊 Overall:")
    print(f"    Total success: {success_count}/{total_tasks} ({success_count/total_tasks*100:.1f}%)")
    
    # 폴백 덕분에 높은 성공률
    assert success_count >= total_tasks * 0.8, f"Success rate too low: {success_count/total_tasks*100:.1f}%"
    
    print("  ✅ Task queue failure + fallback test passed")
    print()


def test_resource_constraint_with_graceful_degradation():
    """리소스 제약 + 우아한 성능 저하 테스트"""
    print("\n🧪 Test: Resource Constraint with Graceful Degradation")
    print("="*70)
    
    simulator = ResourceConstraintSimulator(memory_limit_mb=100, cpu_threshold=80.0)
    
    # 작은 태스크들 (각 10MB)
    small_tasks = 8
    # 큰 태스크들 (각 30MB)
    large_tasks = 2
    
    success_count = 0
    degraded_count = 0
    failed_count = 0
    
    print(f"  Running {small_tasks} small tasks (10MB each)...")
    for i in range(small_tasks):
        try:
            simulator.allocate_memory(10)
            success_count += 1
            print(f"  ✅ Small task {i+1}: Allocated 10MB (total: {simulator.current_memory_mb}MB)")
        except MemoryError as e:
            # 우아한 성능 저하: 일부 기능 비활성화
            try:
                simulator.allocate_memory(5)  # 절반만 할당
                degraded_count += 1
                print(f"  🔄 Small task {i+1}: Degraded mode (5MB instead of 10MB)")
            except MemoryError:
                failed_count += 1
                print(f"  ❌ Small task {i+1}: Failed - {e}")
    
    print(f"\n  Running {large_tasks} large tasks (30MB each)...")
    for i in range(large_tasks):
        try:
            simulator.allocate_memory(30)
            success_count += 1
            print(f"  ✅ Large task {i+1}: Allocated 30MB (total: {simulator.current_memory_mb}MB)")
        except MemoryError as e:
            # 우아한 성능 저하: 청크로 나눠서 처리
            try:
                chunks = 3
                for chunk in range(chunks):
                    simulator.allocate_memory(10)
                    time.sleep(0.05)
                    simulator.release_memory(10)
                degraded_count += 1
                print(f"  🔄 Large task {i+1}: Degraded mode (chunked processing)")
            except MemoryError:
                failed_count += 1
                print(f"  ❌ Large task {i+1}: Failed - {e}")
    
    stats = simulator.get_statistics()
    total_tasks = small_tasks + large_tasks
    
    print(f"\n  📊 Statistics:")
    print(f"    Memory utilization: {stats['memory_utilization']:.1f}%")
    print(f"    OOM errors: {stats['oom_count']}")
    print(f"    Success: {success_count}/{total_tasks}")
    print(f"    Degraded: {degraded_count}/{total_tasks}")
    print(f"    Failed: {failed_count}/{total_tasks}")
    print(f"    Overall completion: {(success_count + degraded_count)/total_tasks*100:.1f}%")
    
    # 우아한 성능 저하 덕분에 높은 완료율
    completion_rate = (success_count + degraded_count) / total_tasks
    assert completion_rate >= 0.7, f"Completion rate too low: {completion_rate*100:.1f}%"
    
    print("  ✅ Resource constraint + graceful degradation test passed")
    print()


def test_execution_engine_resilience():
    """ExecutionEngine 복원력 테스트"""
    print("\n🧪 Test: ExecutionEngine Resilience")
    print("="*70)
    
    # 실패 가능성 높은 튜토리얼
    tutorial = """
Test resilience:
1. Open nonexistent_app_xyz
2. Type 'Hello World'
3. Click on nonexistent_button
4. Press Enter
5. Type 'Test Complete'
    """.strip()
    
    config = ExecutionConfig(
        mode=ExecutionMode.DRY_RUN,
        enable_verification=False,
        enable_failsafe=True,
        timeout=5.0,
    )
    
    # 여러 번 실행하여 일관성 확인
    runs = 3
    results = []
    
    for i in range(runs):
        engine = ExecutionEngine(config)
        result = engine.execute_tutorial(tutorial)
        results.append(result)
        print(f"  Run {i+1}:")
        print(f"    Total: {result.total_actions}, Executed: {result.executed_actions}, Failed: {result.failed_actions}")
    
    # 일관성 확인
    total_actions_consistent = len(set(r.total_actions for r in results)) == 1
    executed_actions_similar = max(r.executed_actions for r in results) - min(r.executed_actions for r in results) <= 1
    
    print(f"\n  📊 Consistency Check:")
    print(f"    Total actions consistent: {total_actions_consistent}")
    print(f"    Executed actions similar: {executed_actions_similar}")
    print(f"    All runs completed: {all(r.total_actions > 0 for r in results)}")
    
    assert total_actions_consistent, "Total actions should be consistent across runs"
    assert executed_actions_similar, "Executed actions should be similar across runs"
    
    print("  ✅ ExecutionEngine resilience test passed")
    print()


def main():
    """Phase 3 Day 3 실전 장애 시뮬레이션 실행"""
    print("\n" + "🔥"*35)
    print("Phase 3 Day 3: Failure Simulation Tests")
    print("Network / Queue / Resource / Recovery")
    print("🔥"*35 + "\n")
    
    test_results = []
    
    tests = [
        ("Network Failure + Retry", test_network_failure_with_retry),
        ("Task Queue Failure + Fallback", test_task_queue_failure_with_fallback),
        ("Resource Constraint + Graceful Degradation", test_resource_constraint_with_graceful_degradation),
        ("ExecutionEngine Resilience", test_execution_engine_resilience),
    ]
    
    for name, test_func in tests:
        try:
            test_func()
            test_results.append((name, "✅ PASS"))
        except Exception as e:
            test_results.append((name, f"❌ FAIL: {e}"))
            print(f"  ❌ Test failed: {e}\n")
    
    # 요약
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    for name, status in test_results:
        print(f"  {status.split(':')[0]:3s} {name}")
    
    passed = sum(1 for _, s in test_results if "✅" in s)
    total = len(test_results)
    
    print()
    print(f"  Total: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {total - passed}")
    print(f"  Pass Rate: {passed/total*100:.0f}%")
    print("="*70 + "\n")
    
    if passed == total:
        print("🎉 ALL FAILURE SIMULATION TESTS PASSED! 🎉\n")
        return 0
    else:
        print(f"⚠️  {total - passed} TEST(S) FAILED\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
