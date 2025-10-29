#!/usr/bin/env python3
"""
Concurrent Task Scheduler - 에이전트 간 동시 작업 조율

역할:
  1. BackgroundMonitor의 이벤트 처리
  2. 에이전트별 작업 큐 관리
  3. 동시 작업 스케줄링
  4. 자동 활성화/비활성화

구조:
  ┌─────────────────────────────────────┐
  │  COLLABORATION_STATE (감시 중)      │
  └─────────────────────────────────────┘
             ↓
  ┌─────────────────────────────────────┐
  │  BackgroundMonitor                  │
  │  (이벤트 감지)                      │
  └─────────────────────────────────────┘
             ↓
  ┌─────────────────────────────────────┐
  │  ConcurrentScheduler                │
  │  (작업 스케줄링)                    │
  └─────────────────────────────────────┘
         ↙        ↓        ↖
      [Sena]  [Lubit]  [GitCode]
     (작업중) (작업중)  (작업중)

Sena의 판단으로 구현됨 (2025-10-20)
"""

import json
import time
import threading
from typing import Dict, List, Callable, Optional, Set
from enum import Enum
from datetime import datetime, timezone
from background_monitor import BackgroundMonitor, EventBuffer


class TaskStatus(Enum):
    """작업 상태"""
    PENDING = "pending"        # 대기 중
    READY = "ready"            # 실행 준비됨
    RUNNING = "running"        # 실행 중
    BLOCKED = "blocked"        # 차단됨
    COMPLETED = "completed"    # 완료됨


class AgentTask:
    """에이전트의 작업"""

    def __init__(
        self,
        agent: str,
        task_id: str,
        task_name: str,
        execute_fn: Callable,
        dependencies: Optional[List[str]] = None
    ):
        self.agent = agent
        self.task_id = task_id
        self.task_name = task_name
        self.execute_fn = execute_fn
        self.dependencies = dependencies or []
        self.status = TaskStatus.PENDING
        self.progress = 0
        self.created_at = datetime.now(timezone.utc)
        self.started_at = None
        self.completed_at = None

    def __repr__(self):
        return f"Task({self.agent}:{self.task_name}, {self.status.value})"


class ConcurrentScheduler:
    """
    동시 작업 스케줄러

    에이전트별 작업 큐를 관리하고 동시에 실행
    """

    def __init__(self, monitor: BackgroundMonitor):
        self.monitor = monitor
        self.task_queues = {
            "sena": [],
            "lubit": [],
            "gitcode": []
        }
        self.task_history = []
        self.running_tasks = {}  # agent → current task
        self.agent_threads = {}
        self.running = False
        self.lock = threading.Lock()

        # 핸들러 등록
        self._register_handlers()

    def _register_handlers(self):
        """BackgroundMonitor 핸들러 등록"""
        def on_sena_update(event):
            self._handle_sena_event(event)

        def on_lubit_update(event):
            self._handle_lubit_event(event)

        def on_gitcode_update(event):
            self._handle_gitcode_event(event)

        self.monitor.register_handler("sena", on_sena_update)
        self.monitor.register_handler("lubit", on_lubit_update)
        self.monitor.register_handler("gitcode", on_gitcode_update)

    def add_task(
        self,
        agent: str,
        task_id: str,
        task_name: str,
        execute_fn: Callable,
        dependencies: Optional[List[str]] = None
    ):
        """
        작업 추가

        Args:
            agent: 에이전트 이름
            task_id: 작업 ID
            task_name: 작업 이름
            execute_fn: 실행 함수
            dependencies: 선행 작업 ID
        """
        task = AgentTask(agent, task_id, task_name, execute_fn, dependencies)

        with self.lock:
            self.task_queues[agent].append(task)

        print(f"[Scheduler] Added task: {task}")

    def start(self):
        """스케줄러 시작"""
        if self.running:
            print("[Scheduler] Already running")
            return

        self.running = True

        # 각 에이전트별 스레드 시작
        for agent in ["sena", "lubit", "gitcode"]:
            thread = threading.Thread(
                target=self._agent_worker,
                args=(agent,),
                daemon=True
            )
            self.agent_threads[agent] = thread
            thread.start()

        print("[Scheduler] Started with 3 concurrent worker threads")

    def stop(self):
        """스케줄러 중지"""
        self.running = False

        for agent, thread in self.agent_threads.items():
            thread.join(timeout=5)

        print("[Scheduler] Stopped")

    def _agent_worker(self, agent: str):
        """에이전트별 작업 워커"""
        print(f"[Scheduler] Worker started for {agent}")

        while self.running:
            try:
                # 실행할 작업 찾기
                task = self._get_next_task(agent)

                if task:
                    self._execute_task(task)
                else:
                    # 작업이 없으면 대기
                    time.sleep(1)

            except Exception as e:
                print(f"[Scheduler] Error in {agent} worker: {str(e)}")
                time.sleep(1)

    def _get_next_task(self, agent: str) -> Optional[AgentTask]:
        """실행할 수 있는 다음 작업 찾기"""
        with self.lock:
            for task in self.task_queues[agent]:
                if task.status == TaskStatus.PENDING:
                    # 의존성 확인
                    if self._check_dependencies(task):
                        task.status = TaskStatus.READY
                        return task

        return None

    def _check_dependencies(self, task: AgentTask) -> bool:
        """작업의 의존성이 모두 완료되었는지 확인"""
        for dep_id in task.dependencies:
            # 히스토리에서 해당 작업 찾기
            dep_task = next(
                (t for t in self.task_history if t.task_id == dep_id),
                None
            )

            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False

        return True

    def _execute_task(self, task: AgentTask):
        """작업 실행"""
        print(f"\n[Scheduler] Executing: {task.agent} - {task.task_name}")

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(timezone.utc)

        self.running_tasks[task.agent] = task

        try:
            # 작업 실행
            task.execute_fn()

            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)

            duration = (task.completed_at - task.started_at).total_seconds()
            print(f"[Scheduler] Completed: {task} (took {duration:.2f}s)")

        except Exception as e:
            task.status = TaskStatus.BLOCKED
            print(f"[Scheduler] Failed: {task} - {str(e)}")

        finally:
            with self.lock:
                self.task_history.append(task)
                if task.agent in self.running_tasks:
                    del self.running_tasks[task.agent]

    def _handle_sena_event(self, event: Dict):
        """Sena 이벤트 처리"""
        print(f"\n[Scheduler] Sena event: {event.get('event')}")

        # Sena의 진행에 따라 Lubit 작업 조정
        if event.get("progress", 0) >= 50:
            print(f"[Scheduler] → Suggest to Lubit: Start validation")

    def _handle_lubit_event(self, event: Dict):
        """Lubit 이벤트 처리"""
        print(f"\n[Scheduler] Lubit event: {event.get('event')}")

        if event.get("verdict") == "approved":
            print(f"[Scheduler] → Notify Sena: Can proceed!")

    def _handle_gitcode_event(self, event: Dict):
        """GitCode 이벤트 처리"""
        print(f"\n[Scheduler] GitCode event: {event.get('event')}")

    def get_status(self) -> Dict:
        """현재 상태"""
        with self.lock:
            return {
                "running_tasks": {
                    agent: str(task)
                    for agent, task in self.running_tasks.items()
                },
                "task_counts": {
                    agent: len(self.task_queues[agent])
                    for agent in ["sena", "lubit", "gitcode"]
                },
                "completed_count": len(self.task_history)
            }

    def print_status(self):
        """상태 출력"""
        status = self.get_status()

        print("\n" + "="*70)
        print("CONCURRENT SCHEDULER STATUS")
        print("="*70)

        print("\n[Running Tasks]")
        if status["running_tasks"]:
            for agent, task_str in status["running_tasks"].items():
                print(f"  {agent}: {task_str}")
        else:
            print("  (No running tasks)")

        print("\n[Task Queues]")
        for agent, count in status["task_counts"].items():
            print(f"  {agent}: {count} tasks pending")

        print(f"\n[Completed]: {status['completed_count']} tasks")
        print("="*70)


def demo():
    """데모: 동시 작업 스케줄러"""
    print("="*70)
    print("Concurrent Task Scheduler - Demo")
    print("="*70)

    collab_state_path = r"d:\nas_backup\session_memory\COLLABORATION_STATE.jsonl"

    # 1. 백그라운드 모니터 시작
    monitor = BackgroundMonitor(collab_state_path)
    monitor.start()

    # 2. 스케줄러 시작
    scheduler = ConcurrentScheduler(monitor)

    # 3. 작업 추가
    print("\n[SETUP] Adding concurrent tasks...\n")

    def sena_task():
        """Sena 작업: 메트릭 구현"""
        for i in range(1, 4):
            print(f"  [Sena] Step {i}/3 - Implementing metrics")
            time.sleep(1)

    def lubit_task():
        """Lubit 작업: 메트릭 검증"""
        for i in range(1, 3):
            print(f"  [Lubit] Step {i}/2 - Validating metrics")
            time.sleep(1.5)

    def gitcode_task():
        """GitCode 작업: 배포 준비"""
        for i in range(1, 3):
            print(f"  [GitCode] Step {i}/2 - Preparing deployment")
            time.sleep(1.2)

    # 작업 추가
    scheduler.add_task("sena", "sena_1", "Implement Metrics", sena_task)
    scheduler.add_task("lubit", "lubit_1", "Validate Metrics", lubit_task, dependencies=["sena_1"])
    scheduler.add_task("gitcode", "gitcode_1", "Prepare Deployment", gitcode_task)

    # 4. 스케줄러 시작 (동시 실행)
    print("[INFO] Starting concurrent execution...\n")
    scheduler.start()

    # 5. 실행 대기
    time.sleep(15)

    # 6. 상태 출력
    scheduler.print_status()

    # 7. 정리
    scheduler.stop()
    monitor.stop()

    print("\n" + "="*70)
    print("[SUCCESS] Concurrent Scheduler Demo Complete!")
    print("\n✅ Sena, Lubit, GitCode가 동시에 작업했습니다!")
    print("="*70)


if __name__ == "__main__":
    demo()
