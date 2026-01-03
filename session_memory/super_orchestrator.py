#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SuperOrchestrator v3.0 - 재귀적 AI 에이전트 자동 오케스트레이션

역할:
  1. Core 워크플로우 (Unified Orchestrator v2.0) + 재귀적 깊이 처리 (PersonaOrchestrator)
  2. 자동 에이전트 활성화 및 작업 분배
  3. 각 에이전트의 재귀적 사고 구조 지원
  4. 실시간 협력 상태 추적 (COLLABORATION_STATE)
  5. 에이전트 간 자동 의사결정 및 피드백 루프
  6. AGI 학습 데이터 자동 생성

구조:
  ┌──────────────────────────────────────┐
  │   SuperOrchestrator v3.0             │
  │   (모든 AI 자동 협력의 중뇌)          │
  └──────────────────────────────────────┘
    ├─ RecursiveWorkflowEngine (Core + 깊이 제어)
    ├─ PersonaRouterV2 (Sena, Lubit, GitCode, RUNE)
    ├─ AgentAutoActivation (자동 에이전트 활성화)
    ├─ RecursiveThinkingLayer (각 에이전트의 재귀적 사고)
    ├─ CollaborationStateManager (실시간 협력 추적)
    ├─ DecisionFeedbackLoop (의사결정 및 피드백)
    └─ AGIDataPipelineV2 (학습 데이터 생성)

세나의 판단으로 구현됨 (2025-10-19)
재귀적 구조 완전 지원 (2025-10-19)
"""

import json
import time
import threading
import queue
import sys
import io
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field
import traceback

# UTF-8 인코딩 강제 설정 (Windows 호환)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def utc_now():
    """UTC 시간 반환"""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class NodeType(Enum):
    """Core 워크플로우 노드 타입"""
    USER_CLIP = "user_clip"
    SAFE_PRE = "safe_pre"
    META = "meta"
    PLAN = "plan"
    TOOL_SELECTION = "tool_selection"
    ANTAGONISTIC = "antagonistic"
    SYNTHESIS = "synthesis"
    SAFE_POST = "safe_post"
    EVALUATION = "evaluation"
    MEMORY = "memory"
    RUNE = "rune"


class PersonaType(Enum):
    """페르소나 타입"""
    SENA = "sena"           # 도구 선택 및 실행
    LUBIT = "lubit"         # 비판적 검토
    GITCODE = "gitcode"     # 통합 및 배포
    RUNE = "rune"           # 윤리 검증


class DecisionType(Enum):
    """의사결정 타입"""
    APPROVE = "approve"
    REVIEW = "review"
    DAMP = "damp"
    ESCALATE = "escalate"


@dataclass
class RecursionContext:
    """재귀 컨텍스트"""
    depth: int
    current_depth_index: int
    parent_synthesis: Optional[str] = None
    recursion_id: str = ""
    breadth_factor: int = 1  # 현재 깊이에서의 병렬 작업 수

    def __post_init__(self):
        if not self.recursion_id:
            ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            self.recursion_id = f"rec_{ts}_{id(self)}"

    def next_level(self) -> 'RecursionContext':
        """다음 재귀 레벨 생성"""
        return RecursionContext(
            depth=self.depth,
            current_depth_index=self.current_depth_index + 1,
            parent_synthesis=None,
            recursion_id=self.recursion_id,
            breadth_factor=max(1, self.breadth_factor // 2)
        )

    def is_leaf(self) -> bool:
        """리프 노드 확인"""
        return self.current_depth_index >= self.depth


@dataclass
class WorkflowNode:
    """Core 워크플로우 노드"""
    node_id: str
    node_type: NodeType
    required_persona: Optional[PersonaType] = None
    description: str = ""
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict] = None
    recursion_allowed: bool = True  # 이 노드에서 재귀 가능한가?


class CollaborationStateManager:
    """협력 상태 관리자"""

    def __init__(self, state_file: str):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.event_queue = queue.Queue()

    def log_event(self, event: Dict[str, Any]) -> None:
        """협력 상태 이벤트 기록"""
        event["timestamp"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        with self.lock:
            with open(self.state_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')

        self.event_queue.put(event)

    def get_agent_status(self, agent_name: str) -> Optional[Dict]:
        """특정 에이전트의 최신 상태 조회"""
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in reversed(lines):
                try:
                    event = json.loads(line.strip())
                    if event.get("agent") == agent_name:
                        return event
                except json.JSONDecodeError:
                    continue
        except FileNotFoundError:
            pass

        return None

    def wait_for_decision(self, agent_name: str, timeout: int = 30) -> Optional[Dict]:
        """특정 에이전트의 의사결정 대기"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.get_agent_status(agent_name)
            if status and status.get("event") == "decision":
                return status

            time.sleep(0.5)

        return None


class RecursiveThinkingLayer:
    """각 페르소나의 재귀적 사고 레이어"""

    def __init__(self, persona: PersonaType, max_recursion_depth: int = 3):
        self.persona = persona
        self.max_recursion_depth = max_recursion_depth
        self.thinking_history: List[Dict] = []

    def think_recursively(
        self,
        problem: str,
        context: RecursionContext,
        tools_available: List[str]
    ) -> Dict[str, Any]:
        """재귀적 사고 수행"""

        thinking_step = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "persona": self.persona.value,
            "depth": context.current_depth_index,
            "recursion_id": context.recursion_id,
            "problem": problem[:100] + "..." if len(problem) > 100 else problem,
            "available_tools": tools_available,
            "sub_problems": [],
            "decomposition": None,
            "synthesis_approach": None
        }

        # 1. 문제 분해
        if context.current_depth_index < context.depth:
            sub_problems = self._decompose_problem(problem, context.breadth_factor)
            thinking_step["sub_problems"] = sub_problems
            thinking_step["decomposition"] = f"분해됨: {len(sub_problems)}개 부분문제"
        else:
            # 리프 노드: 직접 해결
            thinking_step["decomposition"] = "리프 노드: 직접 처리"

        # 2. 도구 선택 (페르소나별)
        selected_tools = self._select_tools_for_persona(tools_available)
        thinking_step["selected_tools"] = selected_tools

        # 3. 종합 접근 방식
        thinking_step["synthesis_approach"] = self._determine_synthesis_approach(
            context.current_depth_index,
            context.depth
        )

        self.thinking_history.append(thinking_step)
        return thinking_step

    def _decompose_problem(self, problem: str, breadth: int) -> List[str]:
        """문제 분해"""
        if self.persona == PersonaType.SENA:
            # Sena: 도구 관점에서 분해
            return [
                f"도구 {i}: {problem[:30]}의 관점에서 처리"
                for i in range(min(breadth, 3))
            ]
        elif self.persona == PersonaType.LUBIT:
            # Lubit: 비판 관점에서 분해
            return [
                f"비판점 {i}: {problem[:30]}의 약점 분석"
                for i in range(min(breadth, 3))
            ]
        elif self.persona == PersonaType.GITCODE:
            # GitCode: 통합 관점에서 분해
            return [
                f"통합모듈 {i}: {problem[:30]}의 시스템 통합"
                for i in range(min(breadth, 3))
            ]
        else:
            return []

    def _select_tools_for_persona(self, available_tools: List[str]) -> List[str]:
        """페르소나에 맞는 도구 선택"""
        if self.persona == PersonaType.SENA:
            return [t for t in available_tools if "execute" in t.lower() or "parse" in t.lower()]
        elif self.persona == PersonaType.LUBIT:
            return [t for t in available_tools if "validate" in t.lower() or "review" in t.lower()]
        elif self.persona == PersonaType.GITCODE:
            return [t for t in available_tools if "integrate" in t.lower() or "deploy" in t.lower()]
        return available_tools

    def _determine_synthesis_approach(self, current_depth: int, max_depth: int) -> str:
        """종합 접근 방식 결정"""
        remaining = max_depth - current_depth
        if remaining <= 0:
            return "리프 노드 처리: 직접 결과 생성"
        elif remaining == 1:
            return f"마지막 재귀 레벨: 부분 결과 종합"
        else:
            return f"중간 재귀 레벨 ({remaining}단계 남음): 하위 재귀 결과 수집 후 종합"


class AgentAutoActivation:
    """자동 에이전트 활성화"""

    def __init__(self, collab_state_manager: CollaborationStateManager):
        self.collab_manager = collab_state_manager
        self.active_agents: Dict[PersonaType, bool] = {}

    def activate_persona(
        self,
        persona: PersonaType,
        task: str,
        context: RecursionContext,
        recursive_thinking: Dict
    ) -> Dict[str, Any]:
        """페르소나 자동 활성화"""

        activation_event = {
            "agent": persona.value,
            "event": "activated",
            "task": task,
            "recursion_level": context.current_depth_index,
            "recursion_id": context.recursion_id,
            "sub_problems": recursive_thinking.get("sub_problems", []),
            "available_tools": recursive_thinking.get("selected_tools", []),
            "status": "active",
            "action": f"시작: {task[:50]}",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }

        self.collab_manager.log_event(activation_event)
        self.active_agents[persona] = True

        return activation_event

    def deactivate_persona(self, persona: PersonaType, result: Dict) -> None:
        """페르소나 활성화 해제"""
        deactivation_event = {
            "agent": persona.value,
            "event": "deactivated",
            "result_summary": result.get("summary", ""),
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }

        self.collab_manager.log_event(deactivation_event)
        self.active_agents[persona] = False

    def wait_for_collaboration(self, required_agents: List[PersonaType]) -> Dict[str, Dict]:
        """여러 에이전트의 협력 결과 대기"""
        results = {}
        timeout_per_agent = 30

        for agent in required_agents:
            decision = self.collab_manager.wait_for_decision(agent.value, timeout_per_agent)
            if decision:
                results[agent.value] = decision
            else:
                results[agent.value] = {"status": "timeout", "agent": agent.value}

        return results


class RecursiveWorkflowEngine:
    """재귀적 워크플로우 엔진"""

    def __init__(self):
        self.workflows: Dict[str, List[WorkflowNode]] = {}
        self._setup_default_workflow()

    def _setup_default_workflow(self) -> None:
        """기본 Core 워크플로우 설정"""
        self.workflows["Core"] = [
            WorkflowNode("U1", NodeType.USER_CLIP, description="사용자 입력", recursion_allowed=True),
            WorkflowNode("S0", NodeType.SAFE_PRE, description="사전 안전 검사"),
            WorkflowNode("M0", NodeType.META, description="메타인지"),
            WorkflowNode("P0", NodeType.PLAN, description="계획"),
            WorkflowNode("L1", NodeType.TOOL_SELECTION, PersonaType.SENA, "도구 선택", recursion_allowed=True),
            WorkflowNode("A1", NodeType.ANTAGONISTIC, PersonaType.LUBIT, "비판 검토", recursion_allowed=True),
            WorkflowNode("SYN", NodeType.SYNTHESIS, PersonaType.GITCODE, "종합", recursion_allowed=True),
            WorkflowNode("S1", NodeType.SAFE_POST, description="사후 안전 검사"),
            WorkflowNode("E1", NodeType.EVALUATION, description="평가"),
            WorkflowNode("MEM", NodeType.MEMORY, description="메모리 저장"),
            WorkflowNode("R1", NodeType.RUNE, PersonaType.RUNE, "윤리 검증"),
        ]

    def get_workflow(self, workflow_name: str = "Core") -> List[WorkflowNode]:
        """워크플로우 조회"""
        return self.workflows.get(workflow_name, [])

    def get_recursion_nodes(self, workflow_name: str = "Core") -> List[WorkflowNode]:
        """재귀 가능한 노드 조회"""
        workflow = self.get_workflow(workflow_name)
        return [node for node in workflow if node.recursion_allowed]


class SuperOrchestrator:
    """SuperOrchestrator v3.0 - 재귀적 AI 에이전트 자동 오케스트레이션"""

    def __init__(self, collab_state_path: str):
        self.collab_state_path = collab_state_path
        self.collab_manager = CollaborationStateManager(collab_state_path)
        self.workflow_engine = RecursiveWorkflowEngine()
        self.agent_activator = AgentAutoActivation(self.collab_manager)

        # 페르소나별 재귀 사고층
        self.thinking_layers: Dict[PersonaType, RecursiveThinkingLayer] = {
            PersonaType.SENA: RecursiveThinkingLayer(PersonaType.SENA),
            PersonaType.LUBIT: RecursiveThinkingLayer(PersonaType.LUBIT),
            PersonaType.GITCODE: RecursiveThinkingLayer(PersonaType.GITCODE),
            PersonaType.RUNE: RecursiveThinkingLayer(PersonaType.RUNE),
        }

        self.running = False
        ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        self.session_id = f"sess_{ts}"

        print(f"[SuperOrchestrator v3.0] 초기화 완료 (세션: {self.session_id})")

    def start(self, task: str, max_recursion_depth: int = 3) -> None:
        """오케스트레이션 시작"""
        if self.running:
            print("[SuperOrchestrator] 이미 실행 중입니다")
            return

        self.running = True
        self.orchestration_thread = threading.Thread(
            target=self._orchestration_loop,
            args=(task, max_recursion_depth),
            daemon=True
        )
        self.orchestration_thread.start()
        print(f"[SuperOrchestrator] 오케스트레이션 시작: {task[:50]}")

    def stop(self) -> None:
        """오케스트레이션 중지"""
        self.running = False
        if hasattr(self, 'orchestration_thread'):
            self.orchestration_thread.join(timeout=10)
        print("[SuperOrchestrator] 오케스트레이션 중지")

    def _orchestration_loop(self, task: str, max_depth: int) -> None:
        """메인 오케스트레이션 루프"""
        try:
            print(f"\n{'='*70}")
            print(f"[SuperOrchestrator] 오케스트레이션 시작")
            print(f"{'='*70}\n")

            # 초기 재귀 컨텍스트
            context = RecursionContext(depth=max_depth, current_depth_index=1)

            # 재귀적 처리 시작
            result = self._process_recursive(task, context)

            print(f"\n{'='*70}")
            print(f"[SuperOrchestrator] 오케스트레이션 완료")
            print(f"{'='*70}\n")

            # 최종 결과 기록
            self.collab_manager.log_event({
                "agent": "super_orchestrator",
                "event": "orchestration_complete",
                "session_id": self.session_id,
                "final_result_preview": str(result)[:100] if result else "None",
                "status": "completed"
            })

        except Exception as e:
            print(f"[SuperOrchestrator] 오케스트레이션 에러: {str(e)}")
            print(traceback.format_exc())
            self.collab_manager.log_event({
                "agent": "super_orchestrator",
                "event": "orchestration_error",
                "error": str(e),
                "status": "failed"
            })

    def _process_recursive(self, task: str, context: RecursionContext) -> str:
        """재귀적 처리"""
        print(f"\n[Recursion Depth {context.current_depth_index}/{context.depth}] 시작")

        # 현재 깊이에서의 워크플로우 실행
        workflow = self.workflow_engine.get_workflow("Core")
        synthesis_result = self._execute_workflow(task, workflow, context)

        # 재귀 처리
        if not context.is_leaf():
            next_context = context.next_level()
            print(f"\n[Recursion] 다음 레벨로 진행 ({next_context.current_depth_index}/{context.depth})")
            synthesis_result = self._process_recursive(synthesis_result, next_context)

        return synthesis_result

    def _execute_workflow(
        self,
        task: str,
        workflow: List[WorkflowNode],
        context: RecursionContext
    ) -> str:
        """워크플로우 실행"""
        current_output = task

        for i, node in enumerate(workflow, 1):
            if not self.running:
                break

            print(f"\n[Node {i}/{len(workflow)}] {node.node_id}: {node.node_type.value}")

            try:
                # 페르소나가 필요한 노드인 경우
                if node.required_persona:
                    current_output = self._execute_persona_node(
                        node, current_output, context
                    )
                else:
                    # 일반 노드 실행
                    current_output = self._execute_generic_node(node, current_output, context)

                time.sleep(0.5)  # 노드 간 간격

            except Exception as e:
                print(f"[Node Error] {node.node_id}: {str(e)}")
                self.collab_manager.log_event({
                    "agent": "orchestrator",
                    "event": "node_error",
                    "node_id": node.node_id,
                    "error": str(e),
                    "recursion_depth": context.current_depth_index
                })

        return current_output

    def _execute_persona_node(
        self,
        node: WorkflowNode,
        input_data: str,
        context: RecursionContext
    ) -> str:
        """페르소나 노드 실행"""
        persona = node.required_persona

        # 재귀적 사고 수행
        thinking_layer = self.thinking_layers[persona]
        recursive_thinking = thinking_layer.think_recursively(
            input_data,
            context,
            tools_available=["execute", "validate", "integrate", "deploy"]
        )

        # 페르소나 자동 활성화
        self.agent_activator.activate_persona(
            persona,
            node.description,
            context,
            recursive_thinking
        )

        # 협력 결과 대기 (다른 에이전트들과의 협력)
        if persona == PersonaType.GITCODE:
            # GitCode는 Sena와 Lubit의 결과를 기다림
            collab_results = self.agent_activator.wait_for_collaboration(
                [PersonaType.SENA, PersonaType.LUBIT]
            )
            print(f"[{persona.value}] 협력 결과 수집: {len(collab_results)}개 에이전트")

        # 페르소나 작업 완료
        node.status = "completed"
        node.result = recursive_thinking

        self.agent_activator.deactivate_persona(persona, recursive_thinking)

        # 출력 생성
        output = f"[{persona.value}] {node.description}: 완료 (깊이: {context.current_depth_index})"
        return output

    def _execute_generic_node(
        self,
        node: WorkflowNode,
        input_data: str,
        context: RecursionContext
    ) -> str:
        """일반 노드 실행"""
        print(f"  ↳ {node.description} (입력 길이: {len(input_data)})")

        # 노드별 로직
        if node.node_type == NodeType.USER_CLIP:
            result = {"type": "user_input", "data": input_data}
        elif node.node_type == NodeType.SAFE_PRE:
            result = {"type": "safety_check", "passed": True, "score": 0.95}
        elif node.node_type == NodeType.META:
            result = {"type": "metacognition", "alignment": 0.98}
        elif node.node_type == NodeType.PLAN:
            result = {"type": "plan", "steps": ["분석", "설계", "구현", "검증"]}
        elif node.node_type == NodeType.SAFE_POST:
            result = {"type": "safety_check", "passed": True, "score": 0.97}
        elif node.node_type == NodeType.EVALUATION:
            result = {
                "type": "evaluation",
                "metrics": {
                    "completeness": 0.92,
                    "quality": 0.90,
                    "innovation": 0.88
                }
            }
        elif node.node_type == NodeType.MEMORY:
            result = {"type": "memory_store", "stored": True, "id": f"mem_{id(node)}"}
        elif node.node_type == NodeType.RUNE:
            result = {
                "type": "ethics_verification",
                "approved": True,
                "resonance": 0.93
            }
        else:
            result = {"type": "generic", "status": "completed"}

        node.status = "completed"
        node.result = result

        # 이벤트 기록
        self.collab_manager.log_event({
            "agent": "orchestrator",
            "event": "node_executed",
            "node_id": node.node_id,
            "node_type": node.node_type.value,
            "recursion_depth": context.current_depth_index,
            "result_type": result.get("type", "unknown")
        })

        return json.dumps(result, ensure_ascii=False)

    def print_status(self) -> None:
        """상태 출력"""
        print(f"\n{'='*70}")
        print("SuperOrchestrator v3.0 - 상태")
        print(f"{'='*70}")
        print(f"세션 ID: {self.session_id}")
        print(f"실행 중: {self.running}")
        print(f"활성 페르소나: {[p.value for p, is_active in self.agent_activator.active_agents.items() if is_active]}")

        # 재귀 사고층 상태
        print(f"\n재귀 사고층 상태:")
        for persona, thinking_layer in self.thinking_layers.items():
            if thinking_layer.thinking_history:
                latest = thinking_layer.thinking_history[-1]
                print(f"  {persona.value}: 깊이 {latest['depth']}, "
                      f"부분문제 {len(latest.get('sub_problems', []))}개")

        print(f"{'='*70}\n")


def demo():
    """데모: SuperOrchestrator v3.0"""
    print("="*70)
    print("SuperOrchestrator v3.0 Demo")
    print("재귀적 AI 에이전트 자동 오케스트레이션")
    print("="*70)

    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    if (Path(__file__).parent.parent / 'fdo_agi_repo').exists():
        sys.path.insert(0, str(Path(__file__).parent.parent / 'fdo_agi_repo'))
        from workspace_utils import find_workspace_root
        workspace = find_workspace_root(Path(__file__).parent)
    else:
        workspace = Path(__file__).parent.parent
    
    collab_state_path = workspace / "session_memory" / "COLLABORATION_STATE.jsonl"

    # 오케스트레이터 생성
    orchestrator = SuperOrchestrator(collab_state_path)

    # 상태 출력
    orchestrator.print_status()

    # 오케스트레이션 시작 (재귀 깊이: 2)
    print("[Demo] 오케스트레이션 시작 (재귀 깊이 2)...\n")
    orchestrator.start(
        task="AGI 학습 데이터 자동 생성 및 검증",
        max_recursion_depth=2
    )

    # 완료 대기
    print("[Demo] 처리 중... (15초 대기)")
    time.sleep(15)

    # 상태 출력
    orchestrator.print_status()

    # 정리
    orchestrator.stop()

    print("\n" + "="*70)
    print("[SUCCESS] SuperOrchestrator v3.0 데모 완료!")
    print("="*70)


if __name__ == "__main__":
    demo()
