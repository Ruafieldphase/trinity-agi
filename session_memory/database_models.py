#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터베이스 모델 - Agent System 데이터 영속성

이 모듈은 에이전트 시스템의 데이터를 영속적으로 저장하기 위한 ORM 모델입니다.
"""

import sys
import io
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.pool import StaticPool

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================================
# 데이터 모델
# ============================================================================

Base = declarative_base()


class AgentRole(Enum):
    """에이전트 역할"""
    SENA = "sena"
    LUBIT = "lubit"
    GITCODE = "gitcode"
    RUNE = "rune"


class TaskStatus(Enum):
    """작업 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class MessageType(Enum):
    """메시지 유형"""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    STATUS_UPDATE = "status_update"
    ERROR_REPORT = "error_report"


# ============================================================================
# 에이전트 모델
# ============================================================================

class Agent(Base):
    """에이전트 정보"""
    __tablename__ = 'agents'

    agent_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    role = Column(SQLEnum(AgentRole), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="inactive")
    initialized_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    tasks = relationship("Task", back_populates="agent")
    messages_sent = relationship("Message", foreign_keys="Message.from_agent_id", back_populates="sender")
    messages_received = relationship("Message", foreign_keys="Message.to_agent_id", back_populates="recipient")
    health_records = relationship("HealthRecord", back_populates="agent")
    metrics = relationship("AgentMetrics", back_populates="agent")

    def __repr__(self):
        return f"<Agent {self.name} ({self.role.value})>"


# ============================================================================
# 작업 모델
# ============================================================================

class Task(Base):
    """작업 정보"""
    __tablename__ = 'tasks'

    task_id = Column(String(100), primary_key=True)
    workflow_id = Column(String(100), nullable=False)
    agent_id = Column(String(50), ForeignKey('agents.agent_id'), nullable=False)

    description = Column(Text)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(Integer, default=5)

    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)

    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_ms = Column(Float, default=0.0)

    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    agent = relationship("Agent", back_populates="tasks")
    subtasks = relationship("SubTask", back_populates="task")
    dependencies = relationship("TaskDependency", back_populates="task")

    def __repr__(self):
        return f"<Task {self.task_id} - {self.status.value}>"


class SubTask(Base):
    """부분 작업 정보"""
    __tablename__ = 'subtasks'

    subtask_id = Column(String(100), primary_key=True)
    task_id = Column(String(100), ForeignKey('tasks.task_id'), nullable=False)

    description = Column(Text)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)

    input_data = Column(JSON)
    output_data = Column(JSON)

    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_ms = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    task = relationship("Task", back_populates="subtasks")

    def __repr__(self):
        return f"<SubTask {self.subtask_id}>"


class TaskDependency(Base):
    """작업 의존성"""
    __tablename__ = 'task_dependencies'

    dependency_id = Column(String(100), primary_key=True)
    task_id = Column(String(100), ForeignKey('tasks.task_id'), nullable=False)
    depends_on_task_id = Column(String(100), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계
    task = relationship("Task", back_populates="dependencies")

    def __repr__(self):
        return f"<TaskDependency {self.task_id} -> {self.depends_on_task_id}>"


# ============================================================================
# 메시지 모델
# ============================================================================

class Message(Base):
    """에이전트 간 메시지"""
    __tablename__ = 'messages'

    message_id = Column(String(100), primary_key=True)
    from_agent_id = Column(String(50), ForeignKey('agents.agent_id'), nullable=False)
    to_agent_id = Column(String(50), ForeignKey('agents.agent_id'), nullable=False)

    message_type = Column(SQLEnum(MessageType), nullable=False)
    content = Column(JSON)

    task_id = Column(String(100), nullable=True)

    status = Column(String(50), default="sent")
    sent_at = Column(DateTime, default=datetime.utcnow)
    received_at = Column(DateTime)
    processed_at = Column(DateTime)

    # 관계
    sender = relationship("Agent", foreign_keys=[from_agent_id], back_populates="messages_sent")
    recipient = relationship("Agent", foreign_keys=[to_agent_id], back_populates="messages_received")

    def __repr__(self):
        return f"<Message {self.message_id} - {self.from_agent_id} -> {self.to_agent_id}>"


# ============================================================================
# 헬스 체크 모델
# ============================================================================

class HealthRecord(Base):
    """헬스 체크 기록"""
    __tablename__ = 'health_records'

    health_id = Column(String(100), primary_key=True)
    agent_id = Column(String(50), ForeignKey('agents.agent_id'))
    component = Column(String(100), nullable=False)

    status = Column(String(50), nullable=False)  # healthy, warning, critical
    message = Column(Text)

    response_time_ms = Column(Float)
    details = Column(JSON)

    checked_at = Column(DateTime, default=datetime.utcnow)

    # 관계
    agent = relationship("Agent", back_populates="health_records")

    def __repr__(self):
        return f"<HealthRecord {self.component} - {self.status}>"


# ============================================================================
# 메트릭 모델
# ============================================================================

class AgentMetrics(Base):
    """에이전트 성능 메트릭"""
    __tablename__ = 'agent_metrics'

    metric_id = Column(String(100), primary_key=True)
    agent_id = Column(String(50), ForeignKey('agents.agent_id'), nullable=False)

    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)

    avg_response_time_ms = Column(Float, default=0.0)
    min_response_time_ms = Column(Float)
    max_response_time_ms = Column(Float)

    success_rate = Column(Float, default=0.0)
    error_rate = Column(Float, default=0.0)

    total_messages_sent = Column(Integer, default=0)
    total_messages_received = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    agent = relationship("Agent", back_populates="metrics")

    def __repr__(self):
        return f"<AgentMetrics {self.agent_id} - Success:{self.success_rate:.1%}>"


class SystemMetrics(Base):
    """시스템 성능 메트릭"""
    __tablename__ = 'system_metrics'

    system_metric_id = Column(String(100), primary_key=True)

    total_workflows = Column(Integer, default=0)
    completed_workflows = Column(Integer, default=0)
    failed_workflows = Column(Integer, default=0)

    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)

    avg_workflow_duration_ms = Column(Float, default=0.0)
    avg_task_duration_ms = Column(Float, default=0.0)

    system_uptime_hours = Column(Float, default=0.0)

    cpu_usage_percent = Column(Float)
    memory_usage_percent = Column(Float)
    disk_usage_percent = Column(Float)

    recorded_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SystemMetrics - Workflows:{self.completed_workflows}/{self.total_workflows}>"


# ============================================================================
# 워크플로우 모델
# ============================================================================

class Workflow(Base):
    """워크플로우 실행 기록"""
    __tablename__ = 'workflows'

    workflow_id = Column(String(100), primary_key=True)

    description = Column(Text)
    status = Column(String(50), default="pending")  # pending, running, completed, failed

    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)

    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_ms = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Workflow {self.workflow_id} - {self.status}>"


# ============================================================================
# 데이터베이스 연결 관리자
# ============================================================================

class DatabaseManager:
    """데이터베이스 관리자"""

    def __init__(self, database_url: str = None):
        """
        초기화

        Args:
            database_url: 데이터베이스 연결 문자열
                         기본값: sqlite:///agent_system.db (인메모리)
        """
        if database_url is None:
            # 테스트용 인메모리 SQLite
            database_url = "sqlite:///:memory:"

        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None

    def initialize(self):
        """데이터베이스 초기화"""
        # 엔진 생성
        if "sqlite:///:memory:" in self.database_url:
            # 인메모리 DB는 스레드 안전성을 위해 StaticPool 사용
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
        else:
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_recycle=3600
            )

        # 세션 팩토리 생성
        self.SessionLocal = sessionmaker(bind=self.engine)

        # 테이블 생성
        Base.metadata.create_all(self.engine)
        print(f"✓ 데이터베이스 초기화 완료: {self.database_url}")

    def get_session(self):
        """세션 획득"""
        if self.SessionLocal is None:
            raise RuntimeError("데이터베이스가 초기화되지 않았습니다.")
        return self.SessionLocal()

    def close(self):
        """데이터베이스 종료"""
        if self.engine:
            self.engine.dispose()
            print("✓ 데이터베이스 연결 종료")


# ============================================================================
# 저장소 클래스
# ============================================================================

class AgentRepository:
    """에이전트 저장소"""

    def __init__(self, session):
        """초기화"""
        self.session = session

    def create_agent(self, agent_id: str, name: str, role: AgentRole, description: str = "") -> Agent:
        """에이전트 생성"""
        agent = Agent(
            agent_id=agent_id,
            name=name,
            role=role,
            description=description
        )
        self.session.add(agent)
        self.session.commit()
        return agent

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """에이전트 조회"""
        return self.session.query(Agent).filter_by(agent_id=agent_id).first()

    def update_agent_status(self, agent_id: str, status: str):
        """에이전트 상태 업데이트"""
        agent = self.get_agent(agent_id)
        if agent:
            agent.status = status
            agent.last_activity = datetime.now(timezone.utc)
            self.session.commit()

    def list_agents(self) -> List[Agent]:
        """모든 에이전트 조회"""
        return self.session.query(Agent).all()


class TaskRepository:
    """작업 저장소"""

    def __init__(self, session):
        """초기화"""
        self.session = session

    def create_task(
        self,
        task_id: str,
        workflow_id: str,
        agent_id: str,
        description: str = "",
        priority: int = 5,
        input_data: Dict[str, Any] = None
    ) -> Task:
        """작업 생성"""
        task = Task(
            task_id=task_id,
            workflow_id=workflow_id,
            agent_id=agent_id,
            description=description,
            priority=priority,
            input_data=input_data or {}
        )
        self.session.add(task)
        self.session.commit()
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """작업 조회"""
        return self.session.query(Task).filter_by(task_id=task_id).first()

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        output_data: Dict[str, Any] = None,
        error_message: str = None,
        duration_ms: float = 0.0
    ):
        """작업 상태 업데이트"""
        task = self.get_task(task_id)
        if task:
            task.status = status
            if output_data:
                task.output_data = output_data
            if error_message:
                task.error_message = error_message
            task.duration_ms = duration_ms
            task.updated_at = datetime.now(timezone.utc)

            if status == TaskStatus.PROCESSING and not task.started_at:
                task.started_at = datetime.now(timezone.utc)
            elif status == TaskStatus.COMPLETED or status == TaskStatus.FAILED:
                task.completed_at = datetime.now(timezone.utc)

            self.session.commit()

    def list_tasks_by_workflow(self, workflow_id: str) -> List[Task]:
        """워크플로우별 작업 조회"""
        return self.session.query(Task).filter_by(workflow_id=workflow_id).all()

    def list_failed_tasks(self) -> List[Task]:
        """실패한 작업 조회"""
        return self.session.query(Task).filter_by(status=TaskStatus.FAILED).all()


class MessageRepository:
    """메시지 저장소"""

    def __init__(self, session):
        """초기화"""
        self.session = session

    def create_message(
        self,
        message_id: str,
        from_agent_id: str,
        to_agent_id: str,
        message_type: MessageType,
        content: Dict[str, Any],
        task_id: str = None
    ) -> Message:
        """메시지 생성"""
        message = Message(
            message_id=message_id,
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            message_type=message_type,
            content=content,
            task_id=task_id
        )
        self.session.add(message)
        self.session.commit()
        return message

    def get_message(self, message_id: str) -> Optional[Message]:
        """메시지 조회"""
        return self.session.query(Message).filter_by(message_id=message_id).first()

    def update_message_status(self, message_id: str, status: str, received_at: bool = False, processed_at: bool = False):
        """메시지 상태 업데이트"""
        message = self.get_message(message_id)
        if message:
            message.status = status
            if received_at:
                message.received_at = datetime.now(timezone.utc)
            if processed_at:
                message.processed_at = datetime.now(timezone.utc)
            self.session.commit()

    def list_messages_for_agent(self, agent_id: str) -> List[Message]:
        """에이전트 메시지 조회"""
        return self.session.query(Message).filter_by(to_agent_id=agent_id).all()


# ============================================================================
# 데모: 데이터베이스 모델
# ============================================================================

def demo_database_models():
    """데이터베이스 모델 데모"""
    print("=" * 80)
    print("데이터베이스 모델 데모")
    print("=" * 80)

    # 데이터베이스 초기화
    print("\n[1단계] 데이터베이스 초기화")
    print("-" * 80)
    db = DatabaseManager()
    db.initialize()

    # 에이전트 생성
    print("\n[2단계] 에이전트 생성")
    print("-" * 80)
    session = db.get_session()
    agent_repo = AgentRepository(session)

    sena = agent_repo.create_agent("agent_sena", "Sena", AgentRole.SENA, "분석 에이전트")
    lubit = agent_repo.create_agent("agent_lubit", "Lubit", AgentRole.LUBIT, "검증 에이전트")
    gitcode = agent_repo.create_agent("agent_gitcode", "GitCode", AgentRole.GITCODE, "실행 에이전트")
    rune = agent_repo.create_agent("agent_rune", "RUNE", AgentRole.RUNE, "윤리 검증 에이전트")

    print(f"✓ {len(agent_repo.list_agents())} 개의 에이전트 생성됨")

    # 작업 생성
    print("\n[3단계] 작업 생성")
    print("-" * 80)
    task_repo = TaskRepository(session)

    task1 = task_repo.create_task(
        task_id="task_001",
        workflow_id="wf_001",
        agent_id="agent_sena",
        description="데이터 분석",
        priority=10,
        input_data={"problem": "데이터 분석 요청"}
    )

    task2 = task_repo.create_task(
        task_id="task_002",
        workflow_id="wf_001",
        agent_id="agent_lubit",
        description="분석 검증",
        priority=9,
        input_data={"analysis": "검증 요청"}
    )

    print(f"✓ {len(task_repo.list_tasks_by_workflow('wf_001'))} 개의 작업 생성됨")

    # 작업 상태 업데이트
    print("\n[4단계] 작업 상태 업데이트")
    print("-" * 80)

    task_repo.update_task_status(
        task_id="task_001",
        status=TaskStatus.COMPLETED,
        output_data={"result": "분석 완료"},
        duration_ms=150.5
    )
    print("✓ task_001 완료")

    task_repo.update_task_status(
        task_id="task_002",
        status=TaskStatus.PROCESSING
    )
    print("✓ task_002 처리 중")

    # 메시지 생성
    print("\n[5단계] 메시지 생성")
    print("-" * 80)
    message_repo = MessageRepository(session)

    msg1 = message_repo.create_message(
        message_id="msg_001",
        from_agent_id="agent_sena",
        to_agent_id="agent_lubit",
        message_type=MessageType.TASK_RESPONSE,
        content={"status": "분석 완료", "confidence": 0.92},
        task_id="task_001"
    )

    msg2 = message_repo.create_message(
        message_id="msg_002",
        from_agent_id="agent_lubit",
        to_agent_id="agent_gitcode",
        message_type=MessageType.TASK_REQUEST,
        content={"action": "실행", "priority": "high"},
        task_id="task_002"
    )

    print(f"✓ {len(message_repo.list_messages_for_agent('agent_lubit'))} 개의 메시지 생성됨")

    # 헬스 체크 기록
    print("\n[6단계] 헬스 체크 기록")
    print("-" * 80)

    health = HealthRecord(
        health_id="health_001",
        agent_id="agent_sena",
        component="agent_sena",
        status="healthy",
        message="정상 작동",
        response_time_ms=2.5,
        details={"uptime": 3600}
    )
    session.add(health)
    session.commit()
    print("✓ 헬스 체크 기록 생성됨")

    # 메트릭 기록
    print("\n[7단계] 메트릭 기록")
    print("-" * 80)

    metrics = AgentMetrics(
        metric_id="metric_sena_001",
        agent_id="agent_sena",
        total_tasks=10,
        completed_tasks=9,
        failed_tasks=1,
        avg_response_time_ms=2.5,
        success_rate=0.9
    )
    session.add(metrics)
    session.commit()
    print("✓ 에이전트 메트릭 기록 생성됨")

    # 데이터 조회
    print("\n[8단계] 저장된 데이터 조회")
    print("-" * 80)

    all_agents = agent_repo.list_agents()
    print(f"에이전트 목록: {len(all_agents)} 개")
    for agent in all_agents:
        print(f"  • {agent.name} ({agent.role.value})")

    workflow_tasks = task_repo.list_tasks_by_workflow("wf_001")
    print(f"\n워크플로우 작업: {len(workflow_tasks)} 개")
    for task in workflow_tasks:
        print(f"  • {task.description} ({task.status.value})")

    print("\n" + "=" * 80)
    print("데이터베이스 모델 데모 완료!")
    print("=" * 80)

    session.close()


if __name__ == "__main__":
    demo_database_models()
