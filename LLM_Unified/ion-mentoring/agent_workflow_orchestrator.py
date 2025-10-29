"""
Agent Workflow Orchestrator - Week 3
====================================

목적:
1. orchestrator_main.TaskScheduler와 Agent 시스템 통합
2. WorkflowOrchestrator: 복잡한 워크플로우 관리
3. EnhancedTaskContext: 의존성 그래프, 우선순위 스케줄링
4. 자동 작업 실행 및 상태 관리

통합:
- agent_base (TaskContext, TaskResult)
- agent_handoff_tools (Handoff 도구)
- orchestrator_main (TaskScheduler, TaskDefinition)
"""

import asyncio
import json

# orchestrator_main에서 가져오기
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

sys.path.append(str(Path(__file__).parent.parent.parent))

from orchestrator_main import (
    StateManager,
    TaskDefinition,
    TaskDependency,
    TaskPriority,
    TaskScheduler,
)
from orchestrator_main import TaskStatus as OrchestratorTaskStatus

from agent_base import AGENT_FOLDERS, TaskContext, TaskResult
from agent_base import TaskStatus as AgentTaskStatus

# ============================================================================
# EnhancedTaskContext - 향상된 작업 컨텍스트
# ============================================================================


@dataclass
class EnhancedTaskContext(TaskContext):
    """
    TaskContext + 의존성 그래프 + 우선순위 + 스케줄링

    확장 기능:
    - 의존성 그래프 관리
    - 우선순위 스케줄링
    - 리소스 할당
    - 병렬 실행 제어
    """

    # 우선순위 (0=긴급, 1=높음, 2=보통, 3=낮음)
    priority: int = 2

    # 의존성 작업 ID 리스트
    depends_on: List[str] = field(default_factory=list)

    # 재시도 정책
    max_retries: int = 3
    retry_count: int = 0

    # 타임아웃
    timeout_seconds: int = 300

    # 예상 실행 시간 (초)
    estimated_duration: int = 60

    # 리소스 요구사항
    required_cpu_percent: float = 10.0
    required_memory_mb: float = 512.0

    # 스케줄링 정보
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # 작업 그룹 (병렬 실행 제어)
    task_group: Optional[str] = None
    max_concurrent_in_group: int = 5


# ============================================================================
# WorkflowOrchestrator - 워크플로우 오케스트레이터
# ============================================================================


class WorkflowOrchestrator:
    """
    복잡한 Multi-Agent 워크플로우 관리

    기능:
    1. 의존성 그래프 자동 실행
    2. 우선순위 스케줄링
    3. 병렬 실행 최적화
    4. 자동 재시도 및 복구
    5. 실시간 상태 모니터링
    """

    def __init__(self):
        """초기화"""
        # orchestrator_main의 TaskScheduler 통합
        self.scheduler = TaskScheduler()
        self.state_manager = StateManager(self.scheduler)

        # Enhanced Task 관리
        self.enhanced_tasks: Dict[str, EnhancedTaskContext] = {}

        # 워크플로우 관리
        self.workflows: Dict[str, List[str]] = {}  # workflow_id -> task_ids

        # 실행 중인 작업
        self.running_task_ids: Set[str] = set()

        # 완료된 작업
        self.completed_task_ids: Set[str] = set()

        # 실패한 작업
        self.failed_task_ids: Set[str] = set()

        print("🔧 WorkflowOrchestrator 초기화 완료")

    # ========================================================================
    # 작업 등록
    # ========================================================================

    def register_enhanced_task(self, task: EnhancedTaskContext, handler: Optional[callable] = None):
        """
        향상된 작업 등록

        Args:
            task: EnhancedTaskContext 객체
            handler: 실행할 함수 (None이면 INBOX로 전달)
        """
        # EnhancedTask 저장
        self.enhanced_tasks[task.task_id] = task

        # orchestrator_main의 TaskDefinition으로 변환
        task_def = TaskDefinition(
            task_id=task.task_id,
            task_name=task.description[:50],  # 짧게 자르기
            priority=TaskPriority(task.priority),
            handler=handler,
            params=task.params,
            dependencies=[TaskDependency(depends_on_task_id=dep_id) for dep_id in task.depends_on],
            max_retries=task.max_retries,
            timeout_seconds=task.timeout_seconds,
            estimated_duration_seconds=task.estimated_duration,
        )

        # TaskScheduler에 등록
        self.scheduler.register_task(task_def)

        # 워크플로우 그룹에 추가
        if task.workflow_id:
            if task.workflow_id not in self.workflows:
                self.workflows[task.workflow_id] = []
            self.workflows[task.workflow_id].append(task.task_id)

        print(f"✅ 작업 등록: {task.task_id} (우선순위: {task.priority})")

    def register_task_from_dict(self, task_dict: Dict[str, Any]):
        """딕셔너리에서 작업 등록"""
        task = EnhancedTaskContext(**task_dict)
        self.register_enhanced_task(task)

    # ========================================================================
    # 워크플로우 실행
    # ========================================================================

    async def execute_workflow(
        self, workflow_id: str, parallel: bool = True, max_concurrent: int = 5
    ) -> Dict[str, TaskResult]:
        """
        워크플로우 실행

        Args:
            workflow_id: 워크플로우 ID
            parallel: 병렬 실행 여부
            max_concurrent: 최대 동시 실행 작업 수

        Returns:
            {task_id: TaskResult} 딕셔너리
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"워크플로우를 찾을 수 없습니다: {workflow_id}")

        task_ids = self.workflows[workflow_id]

        print(f"\n🚀 워크플로우 실행: {workflow_id}")
        print(f"   작업 수: {len(task_ids)}개")
        print(f"   병렬 실행: {'Yes' if parallel else 'No'}")
        print(f"   최대 동시 실행: {max_concurrent}개\n")

        results = {}

        if parallel:
            # 병렬 실행
            results = await self._execute_parallel(task_ids, max_concurrent)
        else:
            # 순차 실행
            results = await self._execute_sequential(task_ids)

        # 상태 기록
        self.state_manager.record_state()

        return results

    async def _execute_sequential(self, task_ids: List[str]) -> Dict[str, TaskResult]:
        """순차 실행"""
        results = {}

        for task_id in task_ids:
            result = await self._execute_single_task(task_id)
            results[task_id] = result

        return results

    async def _execute_parallel(
        self, task_ids: List[str], max_concurrent: int
    ) -> Dict[str, TaskResult]:
        """병렬 실행 (의존성 그래프 고려)"""
        results = {}

        # 실행 가능한 작업 큐
        ready_queue = []
        pending_queue = task_ids.copy()

        # 세마포어 (동시 실행 제한)
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_semaphore(task_id: str):
            async with semaphore:
                return await self._execute_single_task(task_id)

        # 의존성 그래프 기반 실행
        while pending_queue or ready_queue:
            # 실행 가능한 작업 찾기
            for task_id in pending_queue[:]:
                if self._is_task_ready(task_id, results):
                    ready_queue.append(task_id)
                    pending_queue.remove(task_id)

            if not ready_queue:
                if pending_queue:
                    # 순환 의존성 또는 모든 작업 실패
                    print(f"⚠️  대기 중인 작업: {pending_queue}")
                    await asyncio.sleep(1)
                break

            # 준비된 작업 병렬 실행
            tasks = [execute_with_semaphore(task_id) for task_id in ready_queue]

            task_results = await asyncio.gather(*tasks, return_exceptions=True)

            for task_id, result in zip(ready_queue, task_results):
                if isinstance(result, Exception):
                    results[task_id] = TaskResult(
                        task_id=task_id, status=AgentTaskStatus.FAILED, error_message=str(result)
                    )
                else:
                    results[task_id] = result

            ready_queue.clear()

        return results

    def _is_task_ready(self, task_id: str, completed_results: Dict[str, TaskResult]) -> bool:
        """작업 실행 가능 여부 확인"""
        task = self.enhanced_tasks.get(task_id)
        if not task:
            return False

        # 의존성 확인
        for dep_id in task.depends_on:
            # 의존 작업이 완료되지 않았거나 실패했으면 False
            if dep_id not in completed_results:
                return False

            dep_result = completed_results[dep_id]
            if dep_result.status == AgentTaskStatus.FAILED:
                return False

        return True

    async def _execute_single_task(self, task_id: str) -> TaskResult:
        """단일 작업 실행"""
        task = self.enhanced_tasks.get(task_id)
        if not task:
            return TaskResult(
                task_id=task_id,
                status=AgentTaskStatus.FAILED,
                error_message="작업을 찾을 수 없습니다",
            )

        # orchestrator_main의 TaskDefinition 가져오기
        task_def = self.scheduler.tasks.get(task_id)
        if not task_def:
            return TaskResult(
                task_id=task_id,
                status=AgentTaskStatus.FAILED,
                error_message="TaskDefinition을 찾을 수 없습니다",
            )

        print(f"⚙️  작업 실행: {task_id} ({task.description[:50]}...)")

        self.running_task_ids.add(task_id)
        task.started_at = datetime.now()

        try:
            # TaskScheduler로 실행
            execution = await self.scheduler.execute_task(task_def)

            # 결과 변환 (OrchestratorTaskStatus → AgentTaskStatus)
            if execution.status == OrchestratorTaskStatus.COMPLETED:
                agent_status = AgentTaskStatus.COMPLETED
            elif execution.status == OrchestratorTaskStatus.FAILED:
                agent_status = AgentTaskStatus.FAILED
            else:
                agent_status = AgentTaskStatus.PENDING

            result = TaskResult(
                task_id=task_id,
                status=agent_status,
                output=str(execution.result) if execution.result else None,
                error_message=execution.error_message,
                metrics={
                    "duration_seconds": execution.duration_seconds,
                    "retry_count": execution.retry_count,
                },
            )

            task.completed_at = datetime.now()

            if result.status == AgentTaskStatus.COMPLETED:
                self.completed_task_ids.add(task_id)
                print(f"   ✅ 완료: {task_id}")
            else:
                self.failed_task_ids.add(task_id)
                print(f"   ❌ 실패: {task_id} - {result.error_message}")

            return result

        except Exception as e:
            self.failed_task_ids.add(task_id)
            print(f"   ❌ 예외 발생: {task_id} - {e}")

            return TaskResult(task_id=task_id, status=AgentTaskStatus.FAILED, error_message=str(e))

        finally:
            self.running_task_ids.discard(task_id)

    # ========================================================================
    # Agent 통합
    # ========================================================================

    def create_agent_task(
        self,
        agent: str,
        description: str,
        workflow_id: Optional[str] = None,
        priority: int = 2,
        depends_on: Optional[List[str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> EnhancedTaskContext:
        """
        에이전트 작업 생성 및 INBOX에 전달

        Args:
            agent: 대상 에이전트 ("gitko", "sian", "lubit")
            description: 작업 설명
            workflow_id: 워크플로우 ID
            priority: 우선순위 (0-3)
            depends_on: 의존 작업 ID 리스트
            params: 추가 파라미터

        Returns:
            EnhancedTaskContext
        """
        # EnhancedTaskContext 생성
        task = EnhancedTaskContext(
            task_id=f"task_{uuid.uuid4().hex[:8]}",
            agent=agent,
            description=description,
            workflow_id=workflow_id or f"workflow_{uuid.uuid4().hex[:8]}",
            priority=priority,
            depends_on=depends_on or [],
            params=params or {},
            created_by="orchestrator",
        )

        # INBOX에 작업 파일 생성
        task_file = AGENT_FOLDERS[agent] / f"{task.task_id}.json"
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(asdict(task), f, indent=2, ensure_ascii=False, default=str)

        # 등록 (handler=None이면 INBOX 모니터링으로 처리)
        self.register_enhanced_task(task, handler=None)

        print(f"📮 [orchestrator] → [{agent}] 작업 전달: {description[:50]}...")

        return task

    # ========================================================================
    # 상태 조회
    # ========================================================================

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """워크플로우 상태 조회"""
        if workflow_id not in self.workflows:
            return {"error": "워크플로우를 찾을 수 없습니다"}

        task_ids = self.workflows[workflow_id]

        total = len(task_ids)
        completed = len([t for t in task_ids if t in self.completed_task_ids])
        failed = len([t for t in task_ids if t in self.failed_task_ids])
        running = len([t for t in task_ids if t in self.running_task_ids])
        pending = total - completed - failed - running

        return {
            "workflow_id": workflow_id,
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": pending,
            "progress_percent": int(completed / total * 100) if total > 0 else 0,
        }

    def print_workflow_status(self, workflow_id: str):
        """워크플로우 상태 출력"""
        status = self.get_workflow_status(workflow_id)

        if "error" in status:
            print(f"❌ {status['error']}")
            return

        print(f"\n📊 워크플로우 상태: {workflow_id}")
        print(f"   총 작업: {status['total_tasks']}개")
        print(f"   ✅ 완료: {status['completed']}개")
        print(f"   ❌ 실패: {status['failed']}개")
        print(f"   ⚙️  실행 중: {status['running']}개")
        print(f"   ⏳ 대기 중: {status['pending']}개")
        print(f"   진행률: {status['progress_percent']}%\n")


# ============================================================================
# 편의 함수
# ============================================================================


async def create_simple_workflow(
    tasks: List[Dict[str, Any]], parallel: bool = True
) -> Dict[str, TaskResult]:
    """
    간단한 워크플로우 생성 및 실행

    Args:
        tasks: 작업 정의 리스트 [{"agent": "sian", "description": "..."}, ...]
        parallel: 병렬 실행 여부

    Returns:
        실행 결과
    """
    orchestrator = WorkflowOrchestrator()

    workflow_id = f"simple_{uuid.uuid4().hex[:8]}"

    for task_dict in tasks:
        orchestrator.create_agent_task(
            agent=task_dict["agent"],
            description=task_dict["description"],
            workflow_id=workflow_id,
            priority=task_dict.get("priority", 2),
            depends_on=task_dict.get("depends_on", []),
            params=task_dict.get("params", {}),
        )

    results = await orchestrator.execute_workflow(workflow_id, parallel=parallel)

    return results


# ============================================================================
# 테스트 코드
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def test_workflow_orchestrator():
        print("\n" + "=" * 60)
        print("🧪 WorkflowOrchestrator 테스트")
        print("=" * 60 + "\n")

        orchestrator = WorkflowOrchestrator()

        workflow_id = "test_workflow_001"

        # 작업 1: Gitko가 Sian에게 리팩터링 요청
        task1 = orchestrator.create_agent_task(
            agent="sian", description="agent_base.py 리팩터링", workflow_id=workflow_id, priority=1
        )

        # 작업 2: Gitko가 Lubit에게 문서 리뷰 요청
        task2 = orchestrator.create_agent_task(
            agent="lubit",
            description="agent_handoff_tools.py 문서 리뷰",
            workflow_id=workflow_id,
            priority=1,
        )

        # 작업 3: Sian의 결과를 Lubit이 리뷰 (의존성)
        task3 = orchestrator.create_agent_task(
            agent="lubit",
            description="Sian의 리팩터링 결과 리뷰",
            workflow_id=workflow_id,
            priority=2,
            depends_on=[task1.task_id],
        )

        # 상태 출력
        orchestrator.print_workflow_status(workflow_id)

        print("✅ 워크플로우 생성 완료!")
        print(f"   작업 3개 생성: {task1.task_id}, {task2.task_id}, {task3.task_id}\n")

    asyncio.run(test_workflow_orchestrator())
