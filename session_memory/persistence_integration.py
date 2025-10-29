#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
영속성 통합 레이어 - Agent System과 데이터베이스 연동

이 모듈은 에이전트 시스템의 모든 활동을 데이터베이스에 자동으로 저장합니다.
"""

import sys
import io
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

from database_models import (
    DatabaseManager, Agent, Task, Message, HealthRecord, AgentMetrics,
    SystemMetrics, Workflow, SubTask, TaskStatus, MessageType, AgentRole,
    AgentRepository, TaskRepository, MessageRepository
)
from database_migration import MigrationManager

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================================
# 영속성 통합 레이어
# ============================================================================

class PersistenceService:
    """에이전트 시스템 영속성 서비스"""

    def __init__(self, database_url: str = None):
        """
        초기화

        Args:
            database_url: 데이터베이스 연결 문자열
        """
        self.db_manager = DatabaseManager(database_url or "sqlite:///agent_system.db")
        self.db_manager.initialize()

        # 마이그레이션 적용
        migration_manager = MigrationManager(
            database_url or "sqlite:///agent_system.db"
        )
        migration_manager.migrate_up()

        self.session = self.db_manager.get_session()
        self.agent_repo = AgentRepository(self.session)
        self.task_repo = TaskRepository(self.session)
        self.message_repo = MessageRepository(self.session)

    def close(self):
        """서비스 종료"""
        if self.session:
            self.session.close()
        self.db_manager.close()

    # ========================================================================
    # 에이전트 관련 메서드
    # ========================================================================

    def register_agent(self, agent_id: str, name: str, role_str: str, description: str = "") -> Dict[str, Any]:
        """에이전트 등록"""
        try:
            # 역할 문자열을 Enum으로 변환
            role = AgentRole(role_str.lower())
            agent = self.agent_repo.create_agent(agent_id, name, role, description)

            return {
                "success": True,
                "agent_id": agent.agent_id,
                "message": f"에이전트 {name} 등록 완료"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def update_agent_status(self, agent_id: str, status: str) -> Dict[str, Any]:
        """에이전트 상태 업데이트"""
        try:
            self.agent_repo.update_agent_status(agent_id, status)
            return {
                "success": True,
                "message": f"에이전트 {agent_id} 상태 업데이트: {status}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """에이전트 정보 조회"""
        try:
            agent = self.agent_repo.get_agent(agent_id)
            if agent:
                return {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "role": agent.role.value,
                    "status": agent.status,
                    "initialized_at": agent.initialized_at.isoformat(),
                    "last_activity": agent.last_activity.isoformat()
                }
            return None
        except Exception as e:
            print(f"에러: {e}")
            return None

    def get_all_agents(self) -> List[Dict[str, Any]]:
        """모든 에이전트 정보 조회"""
        try:
            agents = self.agent_repo.list_agents()
            return [
                {
                    "agent_id": a.agent_id,
                    "name": a.name,
                    "role": a.role.value,
                    "status": a.status
                }
                for a in agents
            ]
        except Exception as e:
            print(f"에러: {e}")
            return []

    # ========================================================================
    # 작업 관련 메서드
    # ========================================================================

    def create_task(
        self,
        workflow_id: str,
        agent_id: str,
        description: str = "",
        priority: int = 5,
        input_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """작업 생성"""
        try:
            task_id = f"task_{uuid.uuid4().hex[:12]}"
            task = self.task_repo.create_task(
                task_id=task_id,
                workflow_id=workflow_id,
                agent_id=agent_id,
                description=description,
                priority=priority,
                input_data=input_data or {}
            )

            return {
                "success": True,
                "task_id": task_id,
                "message": "작업 생성 완료"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def update_task_status(
        self,
        task_id: str,
        status: str,
        output_data: Dict[str, Any] = None,
        error_message: str = None,
        duration_ms: float = 0.0
    ) -> Dict[str, Any]:
        """작업 상태 업데이트"""
        try:
            task_status = TaskStatus(status.lower())
            self.task_repo.update_task_status(
                task_id=task_id,
                status=task_status,
                output_data=output_data,
                error_message=error_message,
                duration_ms=duration_ms
            )

            return {
                "success": True,
                "message": f"작업 {task_id} 상태 업데이트: {status}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_workflow_tasks(self, workflow_id: str) -> List[Dict[str, Any]]:
        """워크플로우 작업 조회"""
        try:
            tasks = self.task_repo.list_tasks_by_workflow(workflow_id)
            return [
                {
                    "task_id": t.task_id,
                    "description": t.description,
                    "status": t.status.value,
                    "priority": t.priority,
                    "duration_ms": t.duration_ms,
                    "created_at": t.created_at.isoformat()
                }
                for t in tasks
            ]
        except Exception as e:
            print(f"에러: {e}")
            return []

    def get_failed_tasks(self) -> List[Dict[str, Any]]:
        """실패한 작업 조회"""
        try:
            tasks = self.task_repo.list_failed_tasks()
            return [
                {
                    "task_id": t.task_id,
                    "description": t.description,
                    "error_message": t.error_message,
                    "retry_count": t.retry_count,
                    "failed_at": t.completed_at.isoformat() if t.completed_at else None
                }
                for t in tasks
            ]
        except Exception as e:
            print(f"에러: {e}")
            return []

    # ========================================================================
    # 메시지 관련 메서드
    # ========================================================================

    def log_message(
        self,
        from_agent_id: str,
        to_agent_id: str,
        message_type: str,
        content: Dict[str, Any],
        task_id: str = None
    ) -> Dict[str, Any]:
        """메시지 로깅"""
        try:
            message_id = f"msg_{uuid.uuid4().hex[:12]}"
            msg_type = MessageType(message_type.lower())

            self.message_repo.create_message(
                message_id=message_id,
                from_agent_id=from_agent_id,
                to_agent_id=to_agent_id,
                message_type=msg_type,
                content=content,
                task_id=task_id
            )

            return {
                "success": True,
                "message_id": message_id,
                "message": "메시지 로깅 완료"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def update_message_status(
        self,
        message_id: str,
        status: str,
        received_at: bool = False,
        processed_at: bool = False
    ) -> Dict[str, Any]:
        """메시지 상태 업데이트"""
        try:
            self.message_repo.update_message_status(
                message_id=message_id,
                status=status,
                received_at=received_at,
                processed_at=processed_at
            )

            return {
                "success": True,
                "message": "메시지 상태 업데이트 완료"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_agent_messages(self, agent_id: str) -> List[Dict[str, Any]]:
        """에이전트 메시지 조회"""
        try:
            messages = self.message_repo.list_messages_for_agent(agent_id)
            return [
                {
                    "message_id": m.message_id,
                    "from_agent": m.from_agent_id,
                    "message_type": m.message_type.value,
                    "status": m.status,
                    "sent_at": m.sent_at.isoformat()
                }
                for m in messages
            ]
        except Exception as e:
            print(f"에러: {e}")
            return []

    # ========================================================================
    # 헬스 체크 관련 메서드
    # ========================================================================

    def log_health_check(
        self,
        component: str,
        status: str,
        message: str = "",
        response_time_ms: float = 0.0,
        agent_id: str = None,
        details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """헬스 체크 기록"""
        try:
            health_id = f"health_{uuid.uuid4().hex[:12]}"
            health = HealthRecord(
                health_id=health_id,
                agent_id=agent_id,
                component=component,
                status=status,
                message=message,
                response_time_ms=response_time_ms,
                details=details or {}
            )
            self.session.add(health)
            self.session.commit()

            return {
                "success": True,
                "health_id": health_id,
                "message": "헬스 체크 기록 완료"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    # ========================================================================
    # 메트릭 관련 메서드
    # ========================================================================

    def update_agent_metrics(
        self,
        agent_id: str,
        total_tasks: int = None,
        completed_tasks: int = None,
        failed_tasks: int = None,
        avg_response_time_ms: float = None,
        success_rate: float = None
    ) -> Dict[str, Any]:
        """에이전트 메트릭 업데이트"""
        try:
            metric_id = f"metric_{uuid.uuid4().hex[:12]}"
            metrics = AgentMetrics(
                metric_id=metric_id,
                agent_id=agent_id,
                total_tasks=total_tasks or 0,
                completed_tasks=completed_tasks or 0,
                failed_tasks=failed_tasks or 0,
                avg_response_time_ms=avg_response_time_ms or 0.0,
                success_rate=success_rate or 0.0
            )
            self.session.add(metrics)
            self.session.commit()

            return {
                "success": True,
                "metric_id": metric_id,
                "message": "메트릭 업데이트 완료"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def log_system_metrics(
        self,
        total_workflows: int = 0,
        completed_workflows: int = 0,
        total_tasks: int = 0,
        completed_tasks: int = 0,
        avg_workflow_duration_ms: float = 0.0,
        cpu_usage_percent: float = None,
        memory_usage_percent: float = None,
        disk_usage_percent: float = None
    ) -> Dict[str, Any]:
        """시스템 메트릭 로깅"""
        try:
            system_metric_id = f"sys_metric_{uuid.uuid4().hex[:12]}"
            metrics = SystemMetrics(
                system_metric_id=system_metric_id,
                total_workflows=total_workflows,
                completed_workflows=completed_workflows,
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
                avg_workflow_duration_ms=avg_workflow_duration_ms,
                cpu_usage_percent=cpu_usage_percent,
                memory_usage_percent=memory_usage_percent,
                disk_usage_percent=disk_usage_percent
            )
            self.session.add(metrics)
            self.session.commit()

            return {
                "success": True,
                "system_metric_id": system_metric_id,
                "message": "시스템 메트릭 로깅 완료"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    # ========================================================================
    # 워크플로우 관련 메서드
    # ========================================================================

    def create_workflow(
        self,
        description: str = "",
        input_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """워크플로우 생성"""
        try:
            workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
            workflow = Workflow(
                workflow_id=workflow_id,
                description=description,
                status="pending",
                input_data=input_data or {}
            )
            self.session.add(workflow)
            self.session.commit()

            return {
                "success": True,
                "workflow_id": workflow_id,
                "message": "워크플로우 생성 완료"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def update_workflow_status(
        self,
        workflow_id: str,
        status: str,
        output_data: Dict[str, Any] = None,
        error_message: str = None,
        duration_ms: float = 0.0
    ) -> Dict[str, Any]:
        """워크플로우 상태 업데이트"""
        try:
            workflow = self.session.query(Workflow).filter_by(workflow_id=workflow_id).first()
            if workflow:
                workflow.status = status
                if output_data:
                    workflow.output_data = output_data
                if error_message:
                    workflow.error_message = error_message
                workflow.duration_ms = duration_ms

                if status == "running" and not workflow.started_at:
                    workflow.started_at = datetime.utcnow()
                elif status in ["completed", "failed"]:
                    workflow.completed_at = datetime.utcnow()

                self.session.commit()

                return {
                    "success": True,
                    "message": f"워크플로우 {workflow_id} 상태 업데이트: {status}"
                }
            else:
                return {
                    "success": False,
                    "error": "워크플로우를 찾을 수 없습니다."
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# ============================================================================
# 데모: 영속성 통합
# ============================================================================

def demo_persistence_integration():
    """영속성 통합 데모"""
    print("=" * 80)
    print("영속성 통합 레이어 데모")
    print("=" * 80)

    # 서비스 초기화
    print("\n[1단계] 영속성 서비스 초기화")
    print("-" * 80)

    persistence = PersistenceService()
    print("✓ 영속성 서비스 초기화 완료")

    # 에이전트 등록
    print("\n[2단계] 에이전트 등록")
    print("-" * 80)

    agents_data = [
        ("agent_sena", "Sena", "sena", "분석 에이전트"),
        ("agent_lubit", "Lubit", "lubit", "검증 에이전트"),
        ("agent_gitcode", "GitCode", "gitcode", "실행 에이전트"),
        ("agent_rune", "RUNE", "rune", "윤리 검증 에이전트")
    ]

    for agent_id, name, role, desc in agents_data:
        result = persistence.register_agent(agent_id, name, role, desc)
        if result["success"]:
            print(f"✓ {name} 등록 완료")
        else:
            print(f"✗ {name} 등록 실패: {result['error']}")

    # 모든 에이전트 조회
    print("\n[3단계] 등록된 에이전트 조회")
    print("-" * 80)

    agents = persistence.get_all_agents()
    print(f"등록된 에이전트: {len(agents)} 개")
    for agent in agents:
        print(f"  • {agent['name']} ({agent['role']})")

    # 워크플로우 생성
    print("\n[4단계] 워크플로우 생성")
    print("-" * 80)

    workflow_result = persistence.create_workflow(
        description="데이터 분석 워크플로우",
        input_data={"problem": "데이터 분석 요청"}
    )
    workflow_id = workflow_result["workflow_id"]
    print(f"✓ 워크플로우 생성: {workflow_id}")

    # 작업 생성
    print("\n[5단계] 작업 생성 및 상태 업데이트")
    print("-" * 80)

    task_result = persistence.create_task(
        workflow_id=workflow_id,
        agent_id="agent_sena",
        description="분석 수행",
        priority=10,
        input_data={"action": "analyze"}
    )
    task_id = task_result["task_id"]
    print(f"✓ 작업 생성: {task_id}")

    # 작업 상태 업데이트
    persistence.update_task_status(
        task_id=task_id,
        status="completed",
        output_data={"result": "분석 완료"},
        duration_ms=123.45
    )
    print("✓ 작업 상태 업데이트: completed")

    # 메시지 로깅
    print("\n[6단계] 메시지 로깅")
    print("-" * 80)

    msg_result = persistence.log_message(
        from_agent_id="agent_sena",
        to_agent_id="agent_lubit",
        message_type="task_response",
        content={"status": "분석 완료", "confidence": 0.92},
        task_id=task_id
    )
    print(f"✓ 메시지 로깅: {msg_result['message_id']}")

    # 헬스 체크 로깅
    print("\n[7단계] 헬스 체크 로깅")
    print("-" * 80)

    health_result = persistence.log_health_check(
        component="agent_sena",
        status="healthy",
        message="정상 작동",
        response_time_ms=2.5,
        agent_id="agent_sena",
        details={"uptime": 3600}
    )
    print(f"✓ 헬스 체크 로깅: {health_result['health_id']}")

    # 메트릭 업데이트
    print("\n[8단계] 메트릭 업데이트")
    print("-" * 80)

    metric_result = persistence.update_agent_metrics(
        agent_id="agent_sena",
        total_tasks=10,
        completed_tasks=9,
        failed_tasks=1,
        avg_response_time_ms=2.5,
        success_rate=0.9
    )
    print(f"✓ 에이전트 메트릭 업데이트: {metric_result['metric_id']}")

    # 시스템 메트릭 로깅
    print("\n[9단계] 시스템 메트릭 로깅")
    print("-" * 80)

    sys_metric_result = persistence.log_system_metrics(
        total_workflows=5,
        completed_workflows=4,
        total_tasks=20,
        completed_tasks=18,
        avg_workflow_duration_ms=500.0,
        cpu_usage_percent=35.5,
        memory_usage_percent=45.2,
        disk_usage_percent=60.1
    )
    print(f"✓ 시스템 메트릭 로깅: {sys_metric_result['system_metric_id']}")

    # 워크플로우 작업 조회
    print("\n[10단계] 워크플로우 작업 조회")
    print("-" * 80)

    tasks = persistence.get_workflow_tasks(workflow_id)
    print(f"워크플로우 작업: {len(tasks)} 개")
    for task in tasks:
        print(f"  • {task['description']}: {task['status']} ({task['duration_ms']}ms)")

    # 데이터베이스 연결 종료
    print("\n[11단계] 데이터베이스 연결 종료")
    print("-" * 80)

    persistence.close()
    print("✓ 연결 종료 완료")

    print("\n" + "=" * 80)
    print("영속성 통합 데모 완료!")
    print("=" * 80)


if __name__ == "__main__":
    demo_persistence_integration()
