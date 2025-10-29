#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
병렬 작업 처리 시스템 - 여러 작업을 동시에 처리

이 모듈은 에이전트 시스템에서 여러 작업을 병렬로 처리할 수 있도록 합니다.
"""

import sys
import io
import time
import threading
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
import queue

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================================
# 병렬 작업 데이터 클래스
# ============================================================================

class TaskStatus(Enum):
    """작업 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """병렬 처리할 작업"""
    task_id: str
    task_type: str
    description: str
    priority: int = 5  # 1-10, 10이 가장 높음
    func: Optional[Callable] = None
    args: tuple = ()
    kwargs: dict = None
    created_at: str = None
    status: str = TaskStatus.PENDING.value

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.kwargs is None:
            self.kwargs = {}

    def execute(self) -> Dict[str, Any]:
        """작업 실행"""
        if self.func is None:
            return {"success": False, "error": "No function to execute"}

        try:
            result = self.func(*self.args, **self.kwargs)
            return {
                "success": True,
                "result": result,
                "task_id": self.task_id,
                "executed_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "task_id": self.task_id,
                "executed_at": datetime.now().isoformat()
            }


@dataclass
class TaskResult:
    """작업 결과"""
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    completed_at: str = None

    def __post_init__(self):
        if self.completed_at is None:
            self.completed_at = datetime.now().isoformat()


# ============================================================================
# 병렬 작업 처리 시스템
# ============================================================================

class ParallelTaskExecutor:
    """병렬 작업 처리기"""

    def __init__(self, max_workers: int = 4):
        """병렬 작업 처리기 초기화"""
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # 작업 관리
        self.tasks: Dict[str, Task] = {}
        self.results: Dict[str, TaskResult] = {}
        self.lock = threading.Lock()

        # 작업 큐
        self.task_queue: queue.PriorityQueue = queue.PriorityQueue()

        # 통계
        self.total_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0

    def submit_task(self, task: Task) -> str:
        """작업 제출"""
        with self.lock:
            self.tasks[task.task_id] = task
            self.total_tasks += 1

        # 우선순위 큐에 추가 (낮은 우선순위 값이 먼저 실행)
        self.task_queue.put((10 - task.priority, task.task_id, task))

        return task.task_id

    def execute_tasks(self) -> List[TaskResult]:
        """모든 작업 실행"""
        futures = {}

        # 큐에서 작업을 꺼내서 실행
        while not self.task_queue.empty():
            try:
                priority, task_id, task = self.task_queue.get_nowait()

                # 작업 상태 업데이트
                with self.lock:
                    task.status = TaskStatus.RUNNING.value

                # 작업 제출
                future = self.executor.submit(self._execute_task_with_timing, task)
                futures[future] = task_id

            except queue.Empty:
                break

        # 결과 수집
        results = []
        for future in as_completed(futures):
            task_id = futures[future]
            try:
                result = future.result()
                self.results[task_id] = result
                results.append(result)

                # 통계 업데이트
                with self.lock:
                    if result.status == TaskStatus.COMPLETED.value:
                        self.completed_tasks += 1
                    else:
                        self.failed_tasks += 1

            except Exception as e:
                print(f"Error executing task {task_id}: {e}")
                self.failed_tasks += 1

        return results

    def _execute_task_with_timing(self, task: Task) -> TaskResult:
        """시간 측정과 함께 작업 실행"""
        start_time = time.time()
        execution_result = task.execute()
        execution_time = time.time() - start_time

        if execution_result["success"]:
            status = TaskStatus.COMPLETED.value
        else:
            status = TaskStatus.FAILED.value

        return TaskResult(
            task_id=task.task_id,
            status=status,
            result=execution_result.get("result"),
            error=execution_result.get("error"),
            execution_time=execution_time
        )

    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """작업 결과 조회"""
        with self.lock:
            return self.results.get(task_id)

    def get_all_results(self) -> List[TaskResult]:
        """모든 결과 조회"""
        with self.lock:
            return list(self.results.values())

    def get_statistics(self) -> Dict[str, Any]:
        """통계 조회"""
        with self.lock:
            return {
                "total_tasks": self.total_tasks,
                "completed_tasks": self.completed_tasks,
                "failed_tasks": self.total_tasks - self.completed_tasks,
                "success_rate": (self.completed_tasks / self.total_tasks * 100) if self.total_tasks > 0 else 0,
                "max_workers": self.max_workers
            }

    def shutdown(self):
        """실행기 종료"""
        self.executor.shutdown(wait=True)


# ============================================================================
# 고급 병렬 실행 관리자
# ============================================================================

class AdvancedParallelExecutor:
    """고급 병렬 작업 실행 관리자"""

    def __init__(self, max_workers: int = 4):
        """초기화"""
        self.executor = ParallelTaskExecutor(max_workers)
        self.execution_history: List[Dict[str, Any]] = []

    def execute_workflow_tasks(self, tasks: List[Task]) -> Dict[str, Any]:
        """워크플로우 작업 병렬 실행"""
        print(f"\n병렬 작업 실행 시작 ({len(tasks)}개 작업)")
        print("-" * 80)

        start_time = time.time()

        # 작업 제출
        for task in tasks:
            self.executor.submit_task(task)

        # 작업 실행
        results = self.executor.execute_tasks()

        execution_time = time.time() - start_time

        # 결과 정리
        successful = sum(1 for r in results if r.status == TaskStatus.COMPLETED.value)
        failed = sum(1 for r in results if r.status == TaskStatus.FAILED.value)

        summary = {
            "total_tasks": len(tasks),
            "successful_tasks": successful,
            "failed_tasks": failed,
            "execution_time": execution_time,
            "results": results,
            "statistics": self.executor.get_statistics()
        }

        self.execution_history.append(summary)

        return summary

    def print_results(self, summary: Dict[str, Any]):
        """결과 출력"""
        print(f"\n작업 완료:")
        print(f"  총 작업: {summary['total_tasks']}")
        print(f"  성공: {summary['successful_tasks']}")
        print(f"  실패: {summary['failed_tasks']}")
        print(f"  총 실행 시간: {summary['execution_time']:.2f}초")
        print(f"  성공률: {summary['statistics']['success_rate']:.1f}%")

        print(f"\n개별 작업 결과:")
        for result in summary['results']:
            status_symbol = "✅" if result.status == TaskStatus.COMPLETED.value else "❌"
            print(f"  {status_symbol} {result.task_id}: {result.status} ({result.execution_time:.3f}초)")


# ============================================================================
# 데모: 병렬 작업 처리
# ============================================================================

def demo_parallel_execution():
    """병렬 작업 처리 데모"""
    print("=" * 80)
    print("병렬 작업 처리 시스템 데모")
    print("=" * 80)

    # 테스트 함수 정의
    def sample_task(task_id: str, duration: float, should_fail: bool = False) -> str:
        """샘플 작업"""
        time.sleep(duration)
        if should_fail:
            raise Exception(f"Task {task_id} failed")
        return f"Task {task_id} completed"

    # 작업 생성
    print("\n[1단계] 작업 생성")
    print("-" * 80)

    tasks = []
    task_configs = [
        ("task_001", "분석", 0.5, False),
        ("task_002", "검증", 0.3, False),
        ("task_003", "실행", 0.7, False),
        ("task_004", "검증_2", 0.4, False),
        ("task_005", "완료", 0.2, False),
    ]

    for task_id, task_type, duration, should_fail in task_configs:
        task = Task(
            task_id=task_id,
            task_type=task_type,
            description=f"{task_type} 작업",
            priority=5,
            func=sample_task,
            args=(task_id, duration, should_fail)
        )
        tasks.append(task)
        print(f"✓ {task_id} ({task_type}): {duration}초")

    # 병렬 실행
    print("\n[2단계] 병렬 작업 실행 (4개 워커)")
    print("-" * 80)

    executor = AdvancedParallelExecutor(max_workers=4)
    summary = executor.execute_workflow_tasks(tasks)

    # 결과 출력
    print("\n[3단계] 결과 분석")
    print("-" * 80)
    executor.print_results(summary)

    # 순차 실행과 비교
    print("\n[4단계] 순차 실행과 비교")
    print("-" * 80)

    sequential_time = sum(config[2] for config in task_configs)
    speedup = sequential_time / summary['execution_time']

    print(f"순차 실행 예상 시간: {sequential_time:.2f}초")
    print(f"병렬 실행 실제 시간: {summary['execution_time']:.2f}초")
    print(f"속도 향상: {speedup:.2f}배")

    executor.executor.shutdown()

    print("\n" + "=" * 80)
    print("병렬 작업 처리 시스템 데모 완료!")
    print("=" * 80)


# ============================================================================
# 에이전트 시스템과 통합
# ============================================================================

def demo_agent_parallel_processing():
    """에이전트 시스템에서 병렬 처리 데모"""
    print("\n" + "=" * 80)
    print("에이전트 병렬 처리 데모")
    print("=" * 80)

    from agent_sena import SenaAgent
    from agent_lubit import LubitAgent
    from agent_interface import AgentConfig, AgentRole

    def analyze_problem(problem: str) -> Dict[str, Any]:
        """문제 분석"""
        sena = SenaAgent(AgentConfig(
            role=AgentRole.SENA,
            name="Sena",
            description="분석가"
        ))
        sena.initialize()
        return sena.perform_analysis(problem)

    def validate_analysis(analysis: Dict[str, Any]) -> Dict[str, Any]:
        """분석 검증"""
        lubit = LubitAgent(AgentConfig(
            role=AgentRole.LUBIT,
            name="Lubit",
            description="게이트키퍼"
        ))
        lubit.initialize()
        return lubit.validate_analysis({
            "analysis": analysis.get("problem"),
            "selected_tools": analysis.get("tools"),
            "sub_problems": analysis.get("sub_problems"),
            "confidence": 0.85
        })

    # 병렬 처리할 작업들
    print("\n[1단계] 여러 문제 병렬 분석")
    print("-" * 80)

    problems = [
        "고객 데이터 분석",
        "웹 크롤링",
        "텍스트 처리",
        "이미지 분류",
        "시계열 예측"
    ]

    tasks = []
    for i, problem in enumerate(problems):
        task = Task(
            task_id=f"analysis_{i+1}",
            task_type="analysis",
            description=f"문제 분석: {problem}",
            priority=5,
            func=analyze_problem,
            args=(problem,)
        )
        tasks.append(task)

    executor = AdvancedParallelExecutor(max_workers=4)
    summary = executor.execute_workflow_tasks(tasks)

    print(f"\n분석 결과:")
    print(f"  총 문제: {len(problems)}")
    print(f"  성공: {summary['successful_tasks']}")
    print(f"  실패: {summary['failed_tasks']}")
    print(f"  총 시간: {summary['execution_time']:.2f}초")

    executor.executor.shutdown()


if __name__ == "__main__":
    # 기본 병렬 처리 데모
    demo_parallel_execution()

    # 에이전트 시스템 통합 데모
    demo_agent_parallel_processing()
