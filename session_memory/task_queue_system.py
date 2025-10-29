#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
작업 큐 시스템 - 작업의 생명주기 관리

이 모듈은 작업의 요청, 대기, 처리, 완료를 관리하는 큐 시스템을 제공합니다.
"""

import sys
import io
import time
import threading
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum
import queue
from dataclasses import dataclass

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================================
# 작업 큐 상태 정의
# ============================================================================

class QueueStatus(Enum):
    """큐 상태"""
    QUEUED = "queued"          # 대기중
    PROCESSING = "processing"  # 처리중
    COMPLETED = "completed"    # 완료
    FAILED = "failed"          # 실패
    CANCELLED = "cancelled"    # 취소


@dataclass
class QueuedTask:
    """큐에 저장된 작업"""
    task_id: str
    task_type: str
    description: str
    priority: int = 5
    data: Dict[str, Any] = None
    created_at: str = None
    status: str = QueueStatus.QUEUED.value
    retries: int = 0
    max_retries: int = 3

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.data is None:
            self.data = {}


# ============================================================================
# 작업 큐
# ============================================================================

class TaskQueue:
    """작업 큐"""

    def __init__(self, max_size: int = 1000):
        """큐 초기화"""
        self.max_size = max_size

        # 큐 (우선순위 큐)
        self.queue: queue.PriorityQueue = queue.PriorityQueue(maxsize=max_size)

        # 작업 추적
        self.tasks: Dict[str, QueuedTask] = {}
        self.lock = threading.Lock()

        # 통계
        self.enqueued_tasks = 0
        self.dequeued_tasks = 0
        self.processed_tasks = 0
        self.failed_tasks = 0

    def enqueue(self, task: QueuedTask) -> bool:
        """작업 추가"""
        try:
            with self.lock:
                if task.task_id in self.tasks:
                    return False

                self.tasks[task.task_id] = task
                self.enqueued_tasks += 1

            # 우선순위 큐에 추가 (낮은 값이 먼저 처리)
            self.queue.put((10 - task.priority, task.task_id, task))
            return True

        except queue.Full:
            return False

    def dequeue(self, timeout: float = 1.0) -> Optional[QueuedTask]:
        """작업 추출"""
        try:
            priority, task_id, task = self.queue.get(timeout=timeout)
            with self.lock:
                task.status = QueueStatus.PROCESSING.value
                self.dequeued_tasks += 1
            return task
        except queue.Empty:
            return None

    def mark_completed(self, task_id: str):
        """작업 완료 표시"""
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].status = QueueStatus.COMPLETED.value
                self.processed_tasks += 1

    def mark_failed(self, task_id: str):
        """작업 실패 표시"""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.retries < task.max_retries:
                    task.retries += 1
                    task.status = QueueStatus.QUEUED.value
                    # 다시 큐에 추가
                    self.queue.put((10 - task.priority, task_id, task))
                else:
                    task.status = QueueStatus.FAILED.value
                    self.failed_tasks += 1

    def get_task_status(self, task_id: str) -> Optional[str]:
        """작업 상태 조회"""
        with self.lock:
            if task_id in self.tasks:
                return self.tasks[task_id].status
        return None

    def get_queue_size(self) -> int:
        """큐 크기"""
        return self.queue.qsize()

    def get_statistics(self) -> Dict[str, Any]:
        """통계"""
        with self.lock:
            return {
                "enqueued_tasks": self.enqueued_tasks,
                "dequeued_tasks": self.dequeued_tasks,
                "processed_tasks": self.processed_tasks,
                "failed_tasks": self.failed_tasks,
                "current_queue_size": self.get_queue_size(),
                "max_queue_size": self.max_size
            }


# ============================================================================
# 작업 큐 관리자
# ============================================================================

class TaskQueueManager:
    """작업 큐 관리자"""

    def __init__(self, num_workers: int = 4, max_queue_size: int = 1000):
        """초기화"""
        self.queue = TaskQueue(max_queue_size)
        self.num_workers = num_workers
        self.workers = []
        self.running = False
        self.task_handlers: Dict[str, Callable] = {}
        self.results: Dict[str, Any] = {}
        self.lock = threading.Lock()

    def register_handler(self, task_type: str, handler: Callable):
        """작업 타입 핸들러 등록"""
        self.task_handlers[task_type] = handler

    def enqueue_task(self, task: QueuedTask) -> bool:
        """작업 큐에 추가"""
        return self.queue.enqueue(task)

    def start(self):
        """큐 처리 시작"""
        self.running = True

        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"Worker-{i+1}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)

        print(f"✓ 작업 큐 관리자 시작 ({self.num_workers}개 워커)")

    def stop(self):
        """큐 처리 중지"""
        self.running = False
        for worker in self.workers:
            worker.join(timeout=5)
        print("✓ 작업 큐 관리자 중지")

    def _worker_loop(self):
        """워커 루프"""
        worker_name = threading.current_thread().name

        while self.running:
            # 작업 추출
            task = self.queue.dequeue(timeout=1.0)

            if task is None:
                continue

            print(f"[{worker_name}] 작업 처리: {task.task_id} ({task.task_type})")

            try:
                # 핸들러 실행
                handler = self.task_handlers.get(task.task_type)
                if handler:
                    result = handler(task)
                    with self.lock:
                        self.results[task.task_id] = {
                            "status": "success",
                            "result": result,
                            "completed_at": datetime.now().isoformat()
                        }
                    self.queue.mark_completed(task.task_id)
                    print(f"[{worker_name}] ✓ {task.task_id} 완료")
                else:
                    raise Exception(f"No handler for task type: {task.task_type}")

            except Exception as e:
                print(f"[{worker_name}] ✗ {task.task_id} 실패: {e}")
                self.queue.mark_failed(task.task_id)

    def wait_for_completion(self, task_id: str, timeout: float = 10.0) -> Optional[Any]:
        """특정 작업 완료 대기"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            with self.lock:
                if task_id in self.results:
                    return self.results[task_id]

            status = self.queue.get_task_status(task_id)
            if status == QueueStatus.FAILED.value:
                return {"status": "failed", "error": "Max retries exceeded"}

            time.sleep(0.1)

        return None

    def get_statistics(self) -> Dict[str, Any]:
        """통계"""
        stats = self.queue.get_statistics()
        stats["num_workers"] = self.num_workers
        stats["results_count"] = len(self.results)
        return stats


# ============================================================================
# 데모: 작업 큐 시스템
# ============================================================================

def demo_task_queue():
    """작업 큐 시스템 데모"""
    print("=" * 80)
    print("작업 큐 시스템 데모")
    print("=" * 80)

    # 작업 핸들러 정의
    def handle_analysis(task: QueuedTask) -> Dict[str, Any]:
        """분석 작업 처리"""
        time.sleep(0.5)
        return {"analyzed": task.data.get("problem")}

    def handle_validation(task: QueuedTask) -> Dict[str, Any]:
        """검증 작업 처리"""
        time.sleep(0.3)
        return {"validated": task.data.get("analysis")}

    def handle_execution(task: QueuedTask) -> Dict[str, Any]:
        """실행 작업 처리"""
        time.sleep(0.7)
        return {"executed": task.data.get("plan")}

    # 큐 관리자 생성
    print("\n[1단계] 작업 큐 관리자 초기화")
    print("-" * 80)

    manager = TaskQueueManager(num_workers=3)
    manager.register_handler("analysis", handle_analysis)
    manager.register_handler("validation", handle_validation)
    manager.register_handler("execution", handle_execution)

    # 큐 처리 시작
    manager.start()

    # 작업 추가
    print("\n[2단계] 작업 큐에 추가")
    print("-" * 80)

    tasks_to_enqueue = [
        QueuedTask("task_001", "analysis", "고객 데이터 분석", priority=8, data={"problem": "분석1"}),
        QueuedTask("task_002", "validation", "결과 검증", priority=6, data={"analysis": "분석1"}),
        QueuedTask("task_003", "execution", "계획 실행", priority=5, data={"plan": "계획1"}),
        QueuedTask("task_004", "analysis", "트래픽 분석", priority=7, data={"problem": "분석2"}),
        QueuedTask("task_005", "validation", "성능 검증", priority=6, data={"analysis": "분석2"}),
        QueuedTask("task_006", "execution", "배포 실행", priority=4, data={"plan": "계획2"}),
    ]

    enqueued = 0
    for task in tasks_to_enqueue:
        if manager.enqueue_task(task):
            enqueued += 1
            print(f"✓ {task.task_id} ({task.task_type}): 우선순위 {task.priority}")

    print(f"\n총 {enqueued}개 작업 큐에 추가됨")

    # 완료 대기
    print("\n[3단계] 작업 완료 대기")
    print("-" * 80)

    time.sleep(3)

    # 통계 출력
    print("\n[4단계] 작업 큐 통계")
    print("-" * 80)

    stats = manager.get_statistics()
    print(f"총 큐 추가: {stats['enqueued_tasks']}")
    print(f"총 추출: {stats['dequeued_tasks']}")
    print(f"완료: {stats['processed_tasks']}")
    print(f"실패: {stats['failed_tasks']}")
    print(f"현재 큐 크기: {stats['current_queue_size']}")
    print(f"워커 수: {stats['num_workers']}")
    print(f"결과 저장됨: {stats['results_count']}")

    # 중지
    manager.stop()

    print("\n" + "=" * 80)
    print("작업 큐 시스템 데모 완료!")
    print("=" * 80)


def demo_priority_queue():
    """우선순위 큐 데모"""
    print("\n" + "=" * 80)
    print("우선순위 큐 데모")
    print("=" * 80)

    manager = TaskQueueManager(num_workers=2)

    def simple_handler(task: QueuedTask) -> Dict[str, Any]:
        """간단한 핸들러"""
        return {"result": f"{task.task_id} processed"}

    manager.register_handler("task", simple_handler)
    manager.start()

    # 우선순위가 다른 작업 추가
    print("\n우선순위가 다른 작업 추가:")

    priorities = [3, 8, 5, 10, 2]
    for i, priority in enumerate(priorities):
        task = QueuedTask(
            f"priority_{priority:02d}_{i}",
            "task",
            f"작업 (우선순위: {priority})",
            priority=priority
        )
        manager.enqueue_task(task)
        print(f"  task {i+1}: 우선순위 {priority}")

    print("\n높은 우선순위부터 처리됩니다...")
    time.sleep(2)

    manager.stop()

    print("\n" + "=" * 80)
    print("우선순위 큐 데모 완료!")
    print("=" * 80)


if __name__ == "__main__":
    demo_task_queue()
    demo_priority_queue()
