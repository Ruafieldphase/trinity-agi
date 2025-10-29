"""
Agent Base Classes - INBOX 패턴 기반 Multi-Agent 통신
======================================================

목적: 모든 에이전트가 공통으로 사용하는 INBOX 읽기/쓰기 기능 제공

통합 구조:
1. INBOX 패턴 (naeda-ai-core)
2. Context Storage (local_file_agent)
3. TaskContext (gitko_integrated_orchestrator)
"""

import asyncio
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# ============================================================================
# INBOX 경로 설정
# ============================================================================

# 기존 구조 활용
REPO_ROOT = Path(__file__).parent.parent
AGENT_INBOX_PATH = REPO_ROOT / "agent_inbox_local"
CONTEXT_STORAGE = REPO_ROOT / "hybrid_context"
RESULTS_PATH = AGENT_INBOX_PATH / "results"

# 에이전트별 INBOX 폴더
AGENT_FOLDERS = {
    "gitko": AGENT_INBOX_PATH / "gitko",
    "lubit": AGENT_INBOX_PATH / "lubit",
    "sian": AGENT_INBOX_PATH / "sian",
}

# 초기화: 폴더 생성
for folder in [AGENT_INBOX_PATH, RESULTS_PATH, CONTEXT_STORAGE, *AGENT_FOLDERS.values()]:
    folder.mkdir(parents=True, exist_ok=True)


# ============================================================================
# 공통 데이터 구조
# ============================================================================


class TaskStatus(Enum):
    """작업 상태"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class TaskContext:
    """작업 컨텍스트 (기존 gitko_integrated_orchestrator와 호환)"""

    task_id: str
    agent: str
    description: str
    params: Dict[str, Any] = field(default_factory=dict)

    # 메타데이터
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by: Optional[str] = None  # 작업을 생성한 에이전트
    workflow_id: Optional[str] = None  # 여러 작업을 묶는 워크플로우 ID

    # 의존성
    depends_on: List[str] = field(default_factory=list)  # 이전 작업 ID들
    depends_on_results: Dict[str, Any] = field(default_factory=dict)  # 이전 작업 결과들

    # 재시도
    max_retries: int = 3
    retry_count: int = 0
    timeout_seconds: int = 300


@dataclass
class TaskResult:
    """작업 결과"""

    task_id: str
    status: TaskStatus

    # 결과 데이터
    output: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)  # 생성된 파일 경로들
    metrics: Dict[str, Any] = field(default_factory=dict)  # 실행 메트릭

    # 에러 정보
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

    # 다음 작업 전달 (Handoff)
    next_agent: Optional[str] = None
    next_task: Optional[str] = None

    # 타임스탬프
    completed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ============================================================================
# AgentBase: 모든 에이전트의 기반 클래스
# ============================================================================


class AgentBase:
    """
    모든 에이전트의 기반 클래스

    주요 기능:
    1. INBOX에서 작업 읽기
    2. 작업 실행 (추상 메서드)
    3. 결과를 INBOX에 쓰기
    4. 다른 에이전트에게 작업 전달 (Handoff)
    """

    def __init__(self, agent_name: str):
        """
        Args:
            agent_name: 'gitko', 'lubit', 'sian' 중 하나
        """
        self.agent_name = agent_name.lower()
        self.inbox_path = AGENT_FOLDERS[self.agent_name]
        self.results_path = RESULTS_PATH

        # 폴더 확인
        self.inbox_path.mkdir(parents=True, exist_ok=True)
        self.results_path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------------
    # INBOX 읽기/쓰기
    # ------------------------------------------------------------------------

    def read_inbox(self) -> List[TaskContext]:
        """
        INBOX에서 대기 중인 작업들을 읽기

        Returns:
            TaskContext 리스트
        """
        tasks = []
        for task_file in self.inbox_path.glob("*.json"):
            try:
                with open(task_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    task = TaskContext(**data)
                    tasks.append(task)
            except Exception as e:
                print(f"⚠️  작업 파일 읽기 실패: {task_file.name} - {e}")

        return tasks

    def write_result(self, result: TaskResult) -> Path:
        """
        작업 결과를 INBOX에 쓰기

        Args:
            result: TaskResult 객체

        Returns:
            결과 파일 경로
        """
        result_file = self.results_path / f"{result.task_id}_result.json"

        # Enum을 문자열로 변환
        result_dict = asdict(result)
        result_dict["status"] = result.status.value

        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)

        return result_file

    def delete_task_file(self, task_id: str):
        """
        처리 완료된 작업 파일 삭제

        Args:
            task_id: 작업 ID
        """
        task_file = self.inbox_path / f"{task_id}.json"
        if task_file.exists():
            task_file.unlink()

    # ------------------------------------------------------------------------
    # Handoff: 다른 에이전트에게 작업 전달
    # ------------------------------------------------------------------------

    def dispatch_to_agent(self, agent_name: str, task: TaskContext) -> Path:
        """
        다른 에이전트에게 작업 전달

        Args:
            agent_name: 'gitko', 'lubit', 'sian' 중 하나
            task: 전달할 작업

        Returns:
            생성된 작업 파일 경로
        """
        target_agent = agent_name.lower()
        if target_agent not in AGENT_FOLDERS:
            raise ValueError(f"Unknown agent: {agent_name}")

        target_inbox = AGENT_FOLDERS[target_agent]
        task_file = target_inbox / f"{task.task_id}.json"

        # created_by 자동 설정
        if not task.created_by:
            task.created_by = self.agent_name

        task_dict = asdict(task)
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(task_dict, f, indent=2, ensure_ascii=False)

        print(f"✅ {self.agent_name} → {target_agent}: {task.description}")
        return task_file

    # ------------------------------------------------------------------------
    # Context Storage (Level 2) 활용
    # ------------------------------------------------------------------------

    def save_to_context(self, workflow_id: str, data: Dict[str, Any]):
        """
        워크플로우 컨텍스트를 Context Storage에 저장

        Args:
            workflow_id: 워크플로우 ID
            data: 저장할 데이터
        """
        context_file = CONTEXT_STORAGE / f"workflow_{workflow_id}.json"

        # 기존 데이터 로드
        if context_file.exists():
            with open(context_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
        else:
            existing = {}

        # 업데이트
        existing.update(data)
        existing["updated_at"] = datetime.now(timezone.utc).isoformat()
        existing["updated_by"] = self.agent_name

        with open(context_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

    def load_from_context(self, workflow_id: str) -> Dict[str, Any]:
        """
        워크플로우 컨텍스트를 Context Storage에서 로드

        Args:
            workflow_id: 워크플로우 ID

        Returns:
            컨텍스트 데이터
        """
        context_file = CONTEXT_STORAGE / f"workflow_{workflow_id}.json"

        if not context_file.exists():
            return {}

        with open(context_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # ------------------------------------------------------------------------
    # 작업 실행 (추상 메서드 - 각 에이전트가 구현)
    # ------------------------------------------------------------------------

    async def execute_task(self, task: TaskContext) -> TaskResult:
        """
        작업 실행 (하위 클래스에서 구현)

        Args:
            task: 실행할 작업

        Returns:
            실행 결과
        """
        raise NotImplementedError("Subclass must implement execute_task()")

    # ------------------------------------------------------------------------
    # 작업 처리 루프
    # ------------------------------------------------------------------------

    async def process_inbox_once(self) -> int:
        """
        INBOX를 한 번 스캔하여 모든 작업 처리

        Returns:
            처리한 작업 개수
        """
        tasks = self.read_inbox()

        if not tasks:
            return 0

        print(f"\n📬 {self.agent_name}: {len(tasks)}개 작업 발견")

        processed = 0
        for task in tasks:
            try:
                print(f"⚙️  {self.agent_name}: {task.description} 시작...")

                # 작업 실행
                result = await self.execute_task(task)

                # 결과 저장
                self.write_result(result)

                # 작업 파일 삭제
                self.delete_task_file(task.task_id)

                print(f"✅ {self.agent_name}: {task.task_id} 완료 ({result.status.value})")
                processed += 1

                # Handoff가 있으면 다음 에이전트에게 전달
                if result.next_agent and result.next_task:
                    next_task = TaskContext(
                        task_id=str(uuid.uuid4()),
                        agent=result.next_agent,
                        description=result.next_task,
                        created_by=self.agent_name,
                        workflow_id=task.workflow_id,
                        depends_on=[task.task_id],
                        depends_on_results={task.task_id: result.output},
                    )
                    self.dispatch_to_agent(result.next_agent, next_task)

            except Exception as e:
                print(f"❌ {self.agent_name}: {task.task_id} 실패 - {e}")

                # 에러 결과 저장
                error_result = TaskResult(
                    task_id=task.task_id, status=TaskStatus.FAILED, error_message=str(e)
                )
                self.write_result(error_result)
                self.delete_task_file(task.task_id)

        return processed


# ============================================================================
# 유틸리티 함수
# ============================================================================


def create_task(
    agent: str,
    description: str,
    params: Optional[Dict[str, Any]] = None,
    workflow_id: Optional[str] = None,
    created_by: Optional[str] = None,
) -> TaskContext:
    """
    새 작업 생성 (편의 함수)

    Args:
        agent: 대상 에이전트 ('gitko', 'lubit', 'sian')
        description: 작업 설명
        params: 작업 파라미터
        workflow_id: 워크플로우 ID (옵션)
        created_by: 생성자 (옵션)

    Returns:
        TaskContext 객체
    """
    return TaskContext(
        task_id=str(uuid.uuid4()),
        agent=agent,
        description=description,
        params=params or {},
        workflow_id=workflow_id,
        created_by=created_by,
    )


def wait_for_result(task_id: str, timeout_seconds: int = 60) -> Optional[TaskResult]:
    """
    작업 결과 대기 (동기 버전)

    Args:
        task_id: 작업 ID
        timeout_seconds: 타임아웃 (초)

    Returns:
        TaskResult 또는 None (타임아웃)
    """
    import time

    result_file = RESULTS_PATH / f"{task_id}_result.json"
    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        if result_file.exists():
            with open(result_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # status를 Enum으로 변환
                data["status"] = TaskStatus(data["status"])
                return TaskResult(**data)

        time.sleep(0.5)

    return None


async def wait_for_result_async(task_id: str, timeout_seconds: int = 60) -> Optional[TaskResult]:
    """
    작업 결과 대기 (비동기 버전)

    Args:
        task_id: 작업 ID
        timeout_seconds: 타임아웃 (초)

    Returns:
        TaskResult 또는 None (타임아웃)
    """
    result_file = RESULTS_PATH / f"{task_id}_result.json"
    start_time = asyncio.get_event_loop().time()

    while asyncio.get_event_loop().time() - start_time < timeout_seconds:
        if result_file.exists():
            with open(result_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["status"] = TaskStatus(data["status"])
                return TaskResult(**data)

        await asyncio.sleep(0.5)

    return None
