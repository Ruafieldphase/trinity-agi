#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
에이전트 간 협력 강화 - 협력 워크플로우 및 공유 메모리

이 모듈은 에이전트들 간의 더욱 효과적인 협력을 지원합니다.
"""

import sys
import io
import json
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================================
# 협력 메모리
# ============================================================================

class MemoryType(Enum):
    """메모리 타입"""
    SHARED = "shared"          # 모든 에이전트가 접근 가능
    AGENT_SPECIFIC = "agent_specific"  # 특정 에이전트만 접근
    READONLY = "readonly"      # 읽기만 가능


@dataclass
class MemoryEntry:
    """메모리 항목"""
    key: str
    value: Any
    memory_type: str = MemoryType.SHARED.value
    created_by: str = "system"
    created_at: str = None
    access_count: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class CollaborativeMemory:
    """협력 메모리"""

    def __init__(self):
        """초기화"""
        self.memory: Dict[str, MemoryEntry] = {}
        self.access_history: List[Dict[str, Any]] = []

    def write(self, key: str, value: Any, agent_id: str, memory_type: str = MemoryType.SHARED.value) -> bool:
        """메모리 쓰기"""
        entry = MemoryEntry(
            key=key,
            value=value,
            memory_type=memory_type,
            created_by=agent_id
        )
        self.memory[key] = entry

        self._log_access("write", key, agent_id, True)
        return True

    def read(self, key: str, agent_id: str) -> Optional[Any]:
        """메모리 읽기"""
        if key not in self.memory:
            self._log_access("read", key, agent_id, False)
            return None

        entry = self.memory[key]
        entry.access_count += 1
        self._log_access("read", key, agent_id, True)
        return entry.value

    def append(self, key: str, value: Any, agent_id: str) -> bool:
        """메모리에 항목 추가"""
        if key not in self.memory:
            self.memory[key] = MemoryEntry(key=key, value=[], created_by=agent_id)

        current = self.memory[key].value
        if isinstance(current, list):
            current.append(value)
            self._log_access("append", key, agent_id, True)
            return True

        return False

    def get_all(self, agent_id: str) -> Dict[str, Any]:
        """모든 메모리 조회"""
        self._log_access("get_all", "*", agent_id, True)
        return {k: v.value for k, v in self.memory.items()}

    def _log_access(self, operation: str, key: str, agent_id: str, success: bool):
        """접근 로깅"""
        self.access_history.append({
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "key": key,
            "agent_id": agent_id,
            "success": success
        })

    def get_statistics(self) -> Dict[str, Any]:
        """통계"""
        return {
            "total_entries": len(self.memory),
            "total_accesses": len(self.access_history),
            "memory_entries": {
                k: {
                    "type": v.memory_type,
                    "created_by": v.created_by,
                    "access_count": v.access_count
                } for k, v in self.memory.items()
            }
        }


# ============================================================================
# 협력 워크플로우
# ============================================================================

class CollaborationPhase(Enum):
    """협력 단계"""
    INITIATION = "initiation"
    NEGOTIATION = "negotiation"
    EXECUTION = "execution"
    VERIFICATION = "verification"
    COMPLETION = "completion"


@dataclass
class CollaborativeTask:
    """협력 작업"""
    task_id: str
    description: str
    required_agents: List[str]
    phase: str = CollaborationPhase.INITIATION.value
    context: Dict[str, Any] = None
    results: Dict[str, Any] = None
    created_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.context is None:
            self.context = {}
        if self.results is None:
            self.results = {}


class CollaborativeWorkflow:
    """협력 워크플로우"""

    def __init__(self, memory: CollaborativeMemory):
        """초기화"""
        self.memory = memory
        self.tasks: Dict[str, CollaborativeTask] = {}
        self.agent_callbacks: Dict[str, Callable] = {}

    def register_agent_callback(self, agent_id: str, callback: Callable):
        """에이전트 콜백 등록"""
        self.agent_callbacks[agent_id] = callback

    def create_task(self, task: CollaborativeTask) -> str:
        """협력 작업 생성"""
        self.tasks[task.task_id] = task
        self.memory.write(f"task_{task.task_id}", task, "system")
        return task.task_id

    def update_phase(self, task_id: str, phase: CollaborationPhase):
        """작업 단계 업데이트"""
        if task_id in self.tasks:
            self.tasks[task_id].phase = phase.value
            self.memory.write(f"task_{task_id}_phase", phase.value, "system")

    def add_result(self, task_id: str, agent_id: str, result: Any):
        """에이전트 결과 추가"""
        if task_id in self.tasks:
            self.tasks[task_id].results[agent_id] = result
            self.memory.append(f"task_{task_id}_results", {
                "agent": agent_id,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }, agent_id)

    def execute_collaboration(self, task_id: str) -> Dict[str, Any]:
        """협력 실행"""
        if task_id not in self.tasks:
            return {"success": False, "error": "Task not found"}

        task = self.tasks[task_id]

        print(f"\n협력 작업: {task.task_id}")
        print(f"필요 에이전트: {', '.join(task.required_agents)}")

        # Phase 1: Initiation
        print(f"\n[1단계] 초기화 - {CollaborationPhase.INITIATION.value}")
        self.update_phase(task_id, CollaborationPhase.INITIATION)
        time.sleep(0.2)

        # Phase 2: Negotiation
        print(f"[2단계] 협상 - {CollaborationPhase.NEGOTIATION.value}")
        self.update_phase(task_id, CollaborationPhase.NEGOTIATION)

        for agent_id in task.required_agents:
            if agent_id in self.agent_callbacks:
                callback = self.agent_callbacks[agent_id]
                result = callback(task)
                self.add_result(task_id, agent_id, result)
                print(f"  {agent_id}: 협상 완료")
            time.sleep(0.1)

        # Phase 3: Execution
        print(f"[3단계] 실행 - {CollaborationPhase.EXECUTION.value}")
        self.update_phase(task_id, CollaborationPhase.EXECUTION)
        time.sleep(0.2)

        # Phase 4: Verification
        print(f"[4단계] 검증 - {CollaborationPhase.VERIFICATION.value}")
        self.update_phase(task_id, CollaborationPhase.VERIFICATION)
        time.sleep(0.2)

        # Phase 5: Completion
        print(f"[5단계] 완료 - {CollaborationPhase.COMPLETION.value}")
        self.update_phase(task_id, CollaborationPhase.COMPLETION)

        return {
            "success": True,
            "task_id": task_id,
            "results": task.results,
            "phase": task.phase
        }


# ============================================================================
# 에이전트 협력 관리자
# ============================================================================

class AgentCollaborationManager:
    """에이전트 협력 관리자"""

    def __init__(self):
        """초기화"""
        self.memory = CollaborativeMemory()
        self.workflow = CollaborativeWorkflow(self.memory)
        self.agents: Dict[str, Dict[str, Any]] = {}

    def register_agent(self, agent_id: str, agent_name: str, agent_type: str):
        """에이전트 등록"""
        self.agents[agent_id] = {
            "name": agent_name,
            "type": agent_type,
            "registered_at": datetime.now().isoformat()
        }
        self.memory.write(f"agent_{agent_id}", self.agents[agent_id], "system")

    def establish_collaboration(self, task_id: str, required_agents: List[str]) -> Dict[str, Any]:
        """협력 수립"""
        print(f"\n협력 수립: {task_id}")
        print(f"참여 에이전트: {', '.join(required_agents)}")

        task = CollaborativeTask(
            task_id=task_id,
            description=f"Collaborative task: {task_id}",
            required_agents=required_agents
        )

        self.workflow.create_task(task)

        # 각 에이전트에 역할 할당
        for i, agent_id in enumerate(required_agents):
            role = ["분석가", "검증자", "실행자", "평가자"][i % 4]
            self.memory.write(f"agent_{agent_id}_role_{task_id}", role, "system")
            print(f"  {agent_id}: {role}")

        return {"success": True, "task_id": task_id}

    def share_information(self, agent_id: str, key: str, value: Any):
        """정보 공유"""
        self.memory.write(key, value, agent_id, MemoryType.SHARED.value)

    def get_shared_information(self, agent_id: str, key: str) -> Optional[Any]:
        """공유 정보 조회"""
        return self.memory.read(key, agent_id)

    def get_collaboration_summary(self) -> Dict[str, Any]:
        """협력 요약"""
        return {
            "registered_agents": len(self.agents),
            "agents": self.agents,
            "memory_statistics": self.memory.get_statistics(),
            "recent_accesses": self.memory.access_history[-10:]
        }


# ============================================================================
# 데모: 에이전트 협력
# ============================================================================

def demo_agent_collaboration():
    """에이전트 협력 데모"""
    print("=" * 80)
    print("에이전트 협력 시스템 데모")
    print("=" * 80)

    # 협력 관리자 생성
    print("\n[1단계] 협력 관리자 초기화")
    print("-" * 80)

    manager = AgentCollaborationManager()

    # 에이전트 등록
    print("\n[2단계] 에이전트 등록")
    print("-" * 80)

    agents = [
        ("sena", "Sena", "분석가"),
        ("lubit", "Lubit", "검증자"),
        ("gitcode", "GitCode", "실행자"),
        ("rune", "RUNE", "평가자")
    ]

    for agent_id, agent_name, agent_type in agents:
        manager.register_agent(agent_id, agent_name, agent_type)
        print(f"✓ {agent_name} ({agent_type}) 등록")

    # 협력 수립
    print("\n[3단계] 협력 수립")
    print("-" * 80)

    collaboration_result = manager.establish_collaboration(
        "collab_001",
        ["sena", "lubit", "gitcode", "rune"]
    )

    # 정보 공유
    print("\n[4단계] 정보 공유")
    print("-" * 80)

    manager.share_information("sena", "problem_statement", "고객 행동 분석")
    manager.share_information("lubit", "analysis_criteria", {"confidence": 0.85, "risks": []})
    manager.share_information("gitcode", "execution_plan", {"tasks": ["task1", "task2"]})
    manager.share_information("rune", "ethics_principles", ["transparency", "fairness"])

    print("✓ 정보 공유 완료")

    # 협력 실행
    print("\n[5단계] 협력 워크플로우 실행")
    print("-" * 80)

    def agent_callback(task):
        """에이전트 콜백"""
        return f"Result from {task.required_agents[0]}"

    for agent_id in ["sena", "lubit", "gitcode", "rune"]:
        manager.workflow.register_agent_callback(agent_id, agent_callback)

    execution_result = manager.workflow.execute_collaboration("collab_001")

    # 결과 출력
    print("\n[6단계] 협력 결과")
    print("-" * 80)

    print(f"\n실행 결과:")
    print(f"  성공: {execution_result['success']}")
    print(f"  작업 ID: {execution_result['task_id']}")
    print(f"  최종 단계: {execution_result['phase']}")

    # 협력 요약
    print("\n[7단계] 협력 요약")
    print("-" * 80)

    summary = manager.get_collaboration_summary()

    print(f"\n등록된 에이전트: {summary['registered_agents']}")
    print(f"공유된 정보:")
    for key in ["problem_statement", "analysis_criteria", "execution_plan", "ethics_principles"]:
        value = manager.get_shared_information("system", key)
        if value:
            print(f"  {key}: {value}")

    print(f"\n메모리 통계:")
    stats = summary['memory_statistics']
    print(f"  총 항목: {stats['total_entries']}")
    print(f"  총 접근: {stats['total_accesses']}")

    print("\n" + "=" * 80)
    print("에이전트 협력 시스템 데모 완료!")
    print("=" * 80)


if __name__ == "__main__":
    demo_agent_collaboration()
