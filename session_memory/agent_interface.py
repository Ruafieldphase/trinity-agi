#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Interface - 모든 에이전트가 구현해야 할 표준 인터페이스

이 모듈은 Sena, Lubit, GitCode, RUNE이 메시지 라우터와 통신할 때
사용해야 할 기본 인터페이스를 정의합니다.
"""

import sys
import io
import json
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

# UTF-8 인코딩 강제 설정 (Windows 호환)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class AgentRole(Enum):
    """에이전트 역할"""
    SENA = "sena"  # 분석가
    LUBIT = "lubit"  # 게이트키퍼/검증자
    GITCODE = "gitcode"  # 실행자
    RUNE = "rune"  # 윤리 검증자


class MessageType(Enum):
    """메시지 타입"""
    ANALYSIS_SUBMISSION = "analysis_submission"
    VALIDATION_RESULT = "validation_result"
    EXECUTION_RESULT = "execution_result"
    FINAL_VERDICT = "final_verdict"
    TASK_REQUEST = "task_request"
    ERROR = "error"


@dataclass
class AgentConfig:
    """에이전트 설정"""
    role: AgentRole
    name: str
    description: str
    version: str = "1.0"
    enabled: bool = True
    timeout_seconds: int = 300
    max_retries: int = 3

    def to_dict(self) -> Dict[str, Any]:
        """설정을 딕셔너리로 변환"""
        return {
            "role": self.role.value,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries
        }


@dataclass
class TaskContext:
    """작업 컨텍스트 - 에이전트가 작업 수행 시 필요한 정보"""
    task_id: str
    task_type: str
    description: str
    priority: int = 5  # 1-10, 10이 가장 높음
    created_at: str = None
    deadline: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ExecutionResult:
    """실행 결과"""
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """결과를 딕셔너리로 변환"""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata
        }


class BaseAgent(ABC):
    """
    모든 에이전트가 상속해야 할 기본 클래스

    에이전트는 다음을 구현해야 함:
    1. initialize() - 에이전트 초기화
    2. process_message() - 메시지 처리
    3. execute_task() - 작업 실행
    4. validate_input() - 입력 검증
    5. generate_response() - 응답 생성
    """

    def __init__(self, config: AgentConfig):
        """에이전트 초기화"""
        self.config = config
        self.role = config.role
        self.name = config.name
        self.agent_id = str(uuid.uuid4())
        self.is_initialized = False
        self.message_history: List[Dict[str, Any]] = []
        self.task_history: List[Dict[str, Any]] = []

    @abstractmethod
    def initialize(self) -> bool:
        """
        에이전트 초기화

        Returns:
            bool: 초기화 성공 여부
        """
        pass

    @abstractmethod
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        메시지 처리

        Args:
            message: 수신한 메시지

        Returns:
            처리 결과 메시지
        """
        pass

    @abstractmethod
    def execute_task(self, task_context: TaskContext) -> ExecutionResult:
        """
        작업 실행

        Args:
            task_context: 작업 컨텍스트

        Returns:
            실행 결과
        """
        pass

    @abstractmethod
    def validate_input(self, input_data: Any) -> Tuple[bool, Optional[str]]:
        """
        입력 검증

        Args:
            input_data: 검증할 입력 데이터

        Returns:
            (검증 성공 여부, 에러 메시지)
        """
        pass

    @abstractmethod
    def generate_response(self, task_result: ExecutionResult) -> Dict[str, Any]:
        """
        응답 생성

        Args:
            task_result: 작업 실행 결과

        Returns:
            응답 메시지
        """
        pass

    def log_message(self, message: Dict[str, Any], direction: str = "received"):
        """메시지 로깅"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "direction": direction,
            "from": message.get("from", "unknown"),
            "to": message.get("to", "unknown"),
            "message_type": message.get("message_type", "unknown"),
            "task_id": message.get("task_id", "unknown")
        }
        self.message_history.append(log_entry)

    def log_task(self, task_id: str, status: str, result: Optional[Dict[str, Any]] = None):
        """작업 로깅"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "status": status,
            "result": result
        }
        self.task_history.append(log_entry)

    def get_status(self) -> Dict[str, Any]:
        """에이전트 상태 조회"""
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "name": self.name,
            "is_initialized": self.is_initialized,
            "config": self.config.to_dict(),
            "message_count": len(self.message_history),
            "task_count": len(self.task_history)
        }


class AnalysisAgent(BaseAgent):
    """
    분석 에이전트를 위한 기본 인터페이스
    Sena가 상속할 기본 클래스
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.current_analysis: Optional[Dict[str, Any]] = None

    @abstractmethod
    def perform_analysis(self, problem: str) -> Dict[str, Any]:
        """
        문제 분석 수행

        Args:
            problem: 분석할 문제

        Returns:
            분석 결과
        """
        pass

    @abstractmethod
    def identify_tools(self, problem: str) -> List[str]:
        """
        필요한 도구 식별

        Args:
            problem: 문제

        Returns:
            필요한 도구 목록
        """
        pass

    @abstractmethod
    def decompose_task(self, problem: str, tools: List[str]) -> List[Dict[str, Any]]:
        """
        작업 분해

        Args:
            problem: 문제
            tools: 사용할 도구

        Returns:
            분해된 부분 작업 목록
        """
        pass

    @abstractmethod
    def evaluate_confidence(self, analysis: Dict[str, Any]) -> float:
        """
        분석 신뢰도 평가

        Args:
            analysis: 분석 결과

        Returns:
            신뢰도 (0.0-1.0)
        """
        pass


class ValidationAgent(BaseAgent):
    """
    검증 에이전트를 위한 기본 인터페이스
    Lubit이 상속할 기본 클래스
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.validation_rules: Dict[str, Any] = {}
        self.current_validation: Optional[Dict[str, Any]] = None

    @abstractmethod
    def validate_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        분석 검증

        Args:
            analysis: 검증할 분석

        Returns:
            검증 결과 (verdict, reasons, score)
        """
        pass

    @abstractmethod
    def identify_risks(self, analysis: Dict[str, Any]) -> List[str]:
        """
        위험 식별

        Args:
            analysis: 분석

        Returns:
            식별된 위험 목록
        """
        pass

    @abstractmethod
    def assess_strengths(self, analysis: Dict[str, Any]) -> List[str]:
        """
        강점 평가

        Args:
            analysis: 분석

        Returns:
            강점 목록
        """
        pass

    @abstractmethod
    def make_decision(self, validation_result: Dict[str, Any]) -> str:
        """
        최종 판정

        Args:
            validation_result: 검증 결과

        Returns:
            판정 (approved/needs_revision/rejected)
        """
        pass


class ExecutionAgent(BaseAgent):
    """
    실행 에이전트를 위한 기본 인터페이스
    GitCode가 상속할 기본 클래스
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.execution_log: List[Dict[str, Any]] = []
        self.active_tasks: Dict[str, Any] = {}

    @abstractmethod
    def execute_subtask(self, subtask: Dict[str, Any]) -> ExecutionResult:
        """
        부분 작업 실행

        Args:
            subtask: 실행할 부분 작업

        Returns:
            실행 결과
        """
        pass

    @abstractmethod
    def handle_dependencies(self, subtasks: List[Dict[str, Any]]) -> bool:
        """
        부분 작업들 간 의존성 처리

        Args:
            subtasks: 부분 작업 목록

        Returns:
            처리 성공 여부
        """
        pass

    @abstractmethod
    def monitor_execution(self, task_id: str) -> Dict[str, Any]:
        """
        실행 모니터링

        Args:
            task_id: 작업 ID

        Returns:
            모니터링 정보
        """
        pass

    @abstractmethod
    def handle_failure(self, subtask: Dict[str, Any], error: str) -> bool:
        """
        실패 처리

        Args:
            subtask: 실패한 부분 작업
            error: 에러 메시지

        Returns:
            복구 시도 성공 여부
        """
        pass


class EthicsAgent(BaseAgent):
    """
    윤리 검증 에이전트를 위한 기본 인터페이스
    RUNE이 상속할 기본 클래스
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.ethics_principles: Dict[str, float] = {
            "transparency": 1.0,      # 투명성
            "collaboration": 1.0,     # 협력성
            "autonomy": 1.0,          # 자율성
            "fairness": 1.0           # 공정성
        }
        self.current_verification: Optional[Dict[str, Any]] = None

    @abstractmethod
    def verify_transparency(self, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        투명성 검증

        Args:
            execution_data: 실행 데이터

        Returns:
            검증 결과 (score, comments)
        """
        pass

    @abstractmethod
    def verify_collaboration(self, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        협력성 검증

        Args:
            execution_data: 실행 데이터

        Returns:
            검증 결과 (score, comments)
        """
        pass

    @abstractmethod
    def verify_autonomy(self, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        자율성 검증

        Args:
            execution_data: 실행 데이터

        Returns:
            검증 결과 (score, comments)
        """
        pass

    @abstractmethod
    def verify_fairness(self, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        공정성 검증

        Args:
            execution_data: 실행 데이터

        Returns:
            검증 결과 (score, comments)
        """
        pass

    @abstractmethod
    def calculate_ethical_score(self, verification_results: Dict[str, Any]) -> float:
        """
        최종 윤리 점수 계산

        Args:
            verification_results: 검증 결과들

        Returns:
            윤리 점수 (0.0-1.0)
        """
        pass


class AgentFactory:
    """에이전트 팩토리 - 에이전트 생성"""

    _agents: Dict[str, type] = {}

    @classmethod
    def register(cls, role: AgentRole, agent_class: type):
        """에이전트 등록"""
        cls._agents[role.value] = agent_class

    @classmethod
    def create(cls, role: AgentRole, config: AgentConfig) -> BaseAgent:
        """
        에이전트 생성

        Args:
            role: 에이전트 역할
            config: 에이전트 설정

        Returns:
            생성된 에이전트

        Raises:
            ValueError: 등록되지 않은 역할
        """
        if role.value not in cls._agents:
            raise ValueError(f"Unknown agent role: {role.value}")

        agent_class = cls._agents[role.value]
        return agent_class(config)

    @classmethod
    def get_registered_roles(cls) -> List[str]:
        """등록된 역할 목록 조회"""
        return list(cls._agents.keys())


# ============================================================================
# 데모: Agent Interface 사용 예시
# ============================================================================

def demo_agent_interface():
    """Agent Interface 데모"""
    print("=" * 80)
    print("Agent Interface 표준 정의 및 데모")
    print("=" * 80)

    # 1. 에이전트 설정 생성
    print("\n[1단계] 에이전트 설정 정의")
    print("-" * 80)

    sena_config = AgentConfig(
        role=AgentRole.SENA,
        name="Sena",
        description="분석가 - 문제를 분석하고 도구를 선택하는 에이전트"
    )
    print(f"Sena 설정: {json.dumps(sena_config.to_dict(), indent=2, ensure_ascii=False)}")

    lubit_config = AgentConfig(
        role=AgentRole.LUBIT,
        name="Lubit",
        description="게이트키퍼 - 분석을 검증하는 에이전트"
    )
    print(f"\nLubit 설정: {json.dumps(lubit_config.to_dict(), indent=2, ensure_ascii=False)}")

    gitcode_config = AgentConfig(
        role=AgentRole.GITCODE,
        name="GitCode",
        description="실행자 - 작업을 실행하는 에이전트"
    )
    print(f"\nGitCode 설정: {json.dumps(gitcode_config.to_dict(), indent=2, ensure_ascii=False)}")

    rune_config = AgentConfig(
        role=AgentRole.RUNE,
        name="RUNE",
        description="윤리 검증자 - 윤리적 검증을 수행하는 에이전트"
    )
    print(f"\nRUNE 설정: {json.dumps(rune_config.to_dict(), indent=2, ensure_ascii=False)}")

    # 2. 에이전트 인터페이스 설명
    print("\n[2단계] 에이전트 인터페이스 정의")
    print("-" * 80)

    interfaces = {
        "BaseAgent": [
            "initialize() - 에이전트 초기화",
            "process_message() - 메시지 처리",
            "execute_task() - 작업 실행",
            "validate_input() - 입력 검증",
            "generate_response() - 응답 생성",
            "get_status() - 상태 조회"
        ],
        "AnalysisAgent (Sena)": [
            "perform_analysis() - 문제 분석",
            "identify_tools() - 필요한 도구 식별",
            "decompose_task() - 작업 분해",
            "evaluate_confidence() - 신뢰도 평가"
        ],
        "ValidationAgent (Lubit)": [
            "validate_analysis() - 분석 검증",
            "identify_risks() - 위험 식별",
            "assess_strengths() - 강점 평가",
            "make_decision() - 최종 판정"
        ],
        "ExecutionAgent (GitCode)": [
            "execute_subtask() - 부분 작업 실행",
            "handle_dependencies() - 의존성 처리",
            "monitor_execution() - 실행 모니터링",
            "handle_failure() - 실패 처리"
        ],
        "EthicsAgent (RUNE)": [
            "verify_transparency() - 투명성 검증",
            "verify_collaboration() - 협력성 검증",
            "verify_autonomy() - 자율성 검증",
            "verify_fairness() - 공정성 검증",
            "calculate_ethical_score() - 윤리 점수 계산"
        ]
    }

    for interface_name, methods in interfaces.items():
        print(f"\n{interface_name}:")
        for method in methods:
            print(f"  • {method}")

    # 3. 데이터 클래스 설명
    print("\n[3단계] 데이터 클래스 정의")
    print("-" * 80)

    task_context = TaskContext(
        task_id="task_001",
        task_type="analysis",
        description="복잡한 데이터 분석",
        priority=8
    )
    print(f"\nTaskContext 예시:")
    print(f"  - task_id: {task_context.task_id}")
    print(f"  - task_type: {task_context.task_type}")
    print(f"  - description: {task_context.description}")
    print(f"  - priority: {task_context.priority}")
    print(f"  - created_at: {task_context.created_at}")

    exec_result = ExecutionResult(
        success=True,
        output={"analysis": "완료", "confidence": 0.92},
        execution_time_ms=1234.5
    )
    print(f"\nExecutionResult 예시:")
    print(f"  - success: {exec_result.success}")
    print(f"  - output: {exec_result.output}")
    print(f"  - execution_time_ms: {exec_result.execution_time_ms}")

    # 4. 워크플로우 설명
    print("\n[4단계] 에이전트 협력 워크플로우")
    print("-" * 80)

    workflow = """
    [작업 요청]
        ↓
    [1] Sena (분석가)
        - 문제 분석
        - 도구 선택
        - 작업 분해
        - 신뢰도 평가
        ↓ analysis_submission 메시지
    [2] Lubit (게이트키퍼)
        - 분석 검증
        - 위험 식별
        - 강점 평가
        - 최종 판정
        ↓ validation_result 메시지
    [3] GitCode (실행자)
        - 부분 작업 실행
        - 의존성 처리
        - 실행 모니터링
        - 실패 처리
        ↓ execution_result 메시지
    [4] RUNE (윤리 검증자)
        - 투명성 검증
        - 협력성 검증
        - 자율성 검증
        - 공정성 검증
        - 최종 윤리 점수
        ↓ final_verdict 메시지
    [작업 완료]
    """
    print(workflow)

    # 5. 메시지 라우터와의 통합
    print("\n[5단계] 메시지 라우터와의 통합")
    print("-" * 80)
    print("""
    에이전트 워크플로우:

    1. 각 에이전트는 BaseAgent를 상속
    2. process_message()에서 메시지 수신
    3. 해당 작업 수행 (execute_task)
    4. generate_response()로 응답 생성
    5. 메시지 라우터로 응답 전송

    메시지 라우터:
    - 에이전트로부터 메시지 수신
    - 메시지 검증
    - 작업 상태 업데이트
    - 다음 에이전트에게 전달
    """)

    print("\n" + "=" * 80)
    print("Agent Interface 정의 완료!")
    print("=" * 80)


if __name__ == "__main__":
    demo_agent_interface()
