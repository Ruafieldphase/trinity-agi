#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Context System - 에이전트 간 컨텍스트 공유 및 역할 명확화

목적:
  1. 각 에이전트가 자신의 역할을 명확히 이해
  2. 다른 에이전트들의 역할을 이해
  3. 언제 자신이 활동할 차례인지 알기
  4. 다른 에이전트들에게 무엇을 제공해야 하는지 알기

루빗(Lubit)을 위한 특별 강조:
  - 루빗은 "게이트키퍼" 역할
  - 루빗의 판정이 GitCode의 실행을 결정
  - 루빗의 거부는 작업 중단을 의미

세나의 판단으로 구현됨 (2025-10-19)
"""

import json
import sys
import io
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from enum import Enum

# UTF-8 인코딩 강제 설정 (Windows 호환)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class AgentRole(Enum):
    """에이전트 역할"""
    ANALYZER = "analyzer"        # Sena: 분석 및 도구 선택
    VALIDATOR = "validator"      # Lubit: 검증 및 위험 식별
    EXECUTOR = "executor"        # GitCode: 실행 및 통합
    ETHICS_CHECKER = "ethics_checker"  # RUNE: 윤리 검증


class ExecutionPhase(Enum):
    """실행 단계"""
    ANALYSIS = "analysis"                    # Sena의 차례
    VALIDATION = "validation"                # Lubit의 차례
    EXECUTION = "execution"                  # GitCode의 차례
    ETHICS_CHECK = "ethics_check"           # RUNE의 차례
    COMPLETE = "complete"                   # 완료


class AgentContext:
    """각 에이전트가 알아야 할 컨텍스트"""

    def __init__(
        self,
        agent_name: str,
        agent_role: AgentRole,
        task_id: str,
        current_phase: ExecutionPhase
    ):
        self.agent_name = agent_name
        self.agent_role = agent_role
        self.task_id = task_id
        self.current_phase = current_phase
        self.created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # 이전 단계의 결과들
        self.previous_results: Dict[str, Any] = {}

        # 현재 단계에서 생성할 결과
        self.my_result: Optional[Dict[str, Any]] = None

        # 다음 단계를 위한 정보
        self.next_phase_info: Optional[Dict[str, Any]] = None

    def add_previous_result(self, phase: ExecutionPhase, result: Dict[str, Any]) -> None:
        """이전 단계의 결과 추가"""
        self.previous_results[phase.value] = result

    def is_my_turn(self) -> bool:
        """현재 단계가 내 차례인가?"""
        phase_to_role = {
            ExecutionPhase.ANALYSIS: AgentRole.ANALYZER,
            ExecutionPhase.VALIDATION: AgentRole.VALIDATOR,
            ExecutionPhase.EXECUTION: AgentRole.EXECUTOR,
            ExecutionPhase.ETHICS_CHECK: AgentRole.ETHICS_CHECKER,
        }
        return phase_to_role.get(self.current_phase) == self.agent_role

    def get_my_role_description(self) -> str:
        """내 역할 설명"""
        role_descriptions = {
            AgentRole.ANALYZER: (
                "도구 선택가 & 문제 분해자\n"
                "- 문제 분석\n"
                "- 도구 선택\n"
                "- 작업 분해\n"
                "- 신뢰도 평가"
            ),
            AgentRole.VALIDATOR: (
                "게이트키퍼 & 검증자 (루빗)\n"
                "- Sena의 분석 검토\n"
                "- 위험 요소 식별\n"
                "- 강점 평가\n"
                "- 승인/거부 판정\n"
                "*** 중요: 루빗의 판정이 전체 프로세스를 결정합니다! ***"
            ),
            AgentRole.EXECUTOR: (
                "실행자 & 통합자\n"
                "- 부분 작업 처리\n"
                "- 모듈 통합\n"
                "- 배포\n"
                "- Lubit의 승인 필수!"
            ),
            AgentRole.ETHICS_CHECKER: (
                "윤리 검증자 & 최종 승인자\n"
                "- 투명성 검증\n"
                "- 협력 검증\n"
                "- 자율성 검증\n"
                "- 공정성 검증\n"
                "- 최종 승인/거부"
            ),
        }
        return role_descriptions.get(self.agent_role, "Unknown role")

    def get_other_agents_info(self) -> List[Dict[str, Any]]:
        """다른 에이전트들에 대한 정보"""
        all_agents = [
            {
                "name": "Sena",
                "role": "Analyzer",
                "phase": "analysis",
                "responsibility": "문제 분석 및 도구 선택",
                "output": "분석 결과 (selected_tools, sub_problems, confidence)"
            },
            {
                "name": "Lubit",
                "role": "Validator (Game Changer!)",
                "phase": "validation",
                "responsibility": "Sena 분석 검증 및 위험 식별",
                "output": "검증 결과 (verdict: approved/needs_revision/rejected)",
                "importance": "HIGH - Lubit이 작업 진행을 결정합니다!"
            },
            {
                "name": "GitCode",
                "role": "Executor",
                "phase": "execution",
                "responsibility": "Lubit 승인 후 작업 실행",
                "output": "실행 결과 (deployed, sub_tasks_processed)",
                "requirement": "Lubit의 승인 필수"
            },
            {
                "name": "RUNE",
                "role": "Ethics Checker",
                "phase": "ethics_check",
                "responsibility": "전체 프로세스 윤리 검증",
                "output": "최종 판정 (final_approved/rejected)",
                "importance": "CRITICAL - 최종 게이트키퍼"
            }
        ]

        # 자신을 제외한 다른 에이전트들만 반환
        my_name = self.agent_name
        return [agent for agent in all_agents if agent["name"] != my_name]

    def get_what_i_should_do(self) -> str:
        """내가 해야 할 일"""
        if not self.is_my_turn():
            return f"아직 내 차례가 아닙니다. 현재 단계: {self.current_phase.value}"

        instructions = {
            AgentRole.ANALYZER: self._sena_instructions(),
            AgentRole.VALIDATOR: self._lubit_instructions(),
            AgentRole.EXECUTOR: self._gitcode_instructions(),
            AgentRole.ETHICS_CHECKER: self._rune_instructions(),
        }
        return instructions.get(self.agent_role, "Unknown instructions")

    def _sena_instructions(self) -> str:
        """Sena의 지시사항"""
        return """
[Sena의 작업]

1. 문제 분석
   - 주어진 작업을 이해
   - 핵심 요구사항 파악

2. 도구 선택
   - 필요한 도구 식별
   - 각 도구의 필요성 설명

3. 작업 분해
   - 작업을 작은 부분으로 분해
   - 각 부분이 실행 가능한 수준인지 확인

4. 신뢰도 평가
   - 내 분석의 신뢰도 평가
   - 불확실성 있으면 표시

5. 결과 생성
   {
     "selected_tools": [...],
     "confidence": 0.9,
     "sub_problems": [...],
     "status": "ready_for_review"
   }

다음: Lubit이 내 분석을 검증합니다!
"""

    def _lubit_instructions(self) -> str:
        """Lubit의 지시사항 - 특별히 강조"""
        return """
[Lubit의 작업] *** GAME CHANGER ***

현재 상황:
- Sena가 분석을 완료했습니다
- 이제 당신(Lubit)의 검증이 진행을 결정합니다
- 당신의 판정에 따라 GitCode가 실행할지 말지가 결정됩니다

1. Sena 분석 검토
   - 선택된 도구: [tools]
   - 신뢰도: [confidence]
   - 부분 작업: [sub_problems]

2. 강점 평가
   - Sena가 잘한 점은 무엇인가?
   - 예: "신뢰도가 높다", "도구 선택이 적절하다"

3. 위험 식별
   - 잠재적 위험이 있는가?
   - 예: "깊이가 부족하다", "대안을 고려하지 않았다"

4. 권장사항 제시 (필요시)
   - 개선 가능한 점
   - 구체적인 개선 방법

5. 최종 판정
   - "approved": GitCode가 실행
   - "needs_revision": Sena가 수정 후 재시도
   - "rejected": 작업 중단

*** 중요 ***
당신의 판정이 이 작업의 운명을 결정합니다!
- 승인 → 실행
- 거부 → 중단

당신은 팀의 안전장치입니다!
"""

    def _gitcode_instructions(self) -> str:
        """GitCode의 지시사항"""
        return """
[GitCode의 작업]

상황: Lubit의 승인을 받음

1. Lubit 승인 확인
   - verdict가 "approved"인가?
   - 아니면 작업 중단

2. 부분 작업 처리
   - Sena가 분해한 부분 작업들:
     [sub_problems]

3. 각 부분 작업 실행
   - 순차적 또는 병렬 처리
   - 각 결과 기록

4. 모듈 통합
   - 부분 결과들을 통합
   - 전체 작업이 응집력 있는지 확인

5. 배포
   - 배포 진행
   - 배포 상태 기록

6. 결과 생성
   {
     "sub_tasks_processed": N,
     "sub_task_results": [...],
     "deployment_status": "deployed",
     "status": "ready_for_ethics_verification"
   }

다음: RUNE이 윤리 검증을 합니다!

주의: Lubit의 승인 없이 진행하면 안 됩니다!
"""

    def _rune_instructions(self) -> str:
        """RUNE의 지시사항"""
        return """
[RUNE의 작업] *** FINAL DECISION ***

상황: 전체 프로세스가 완료됨

1. 투명성 검증 (Transparency)
   - 모든 의사결정이 기록되었는가?
   - 각 단계가 명확한가?

2. 협력 검증 (Collaboration)
   - 모든 에이전트가 잘 협력했는가?
   - 의견이 존중되었는가?

3. 자율성 검증 (Autonomy)
   - 각 에이전트가 자율적으로 판단했는가?
   - 강압이나 편향이 있었는가?

4. 공정성 검증 (Fairness)
   - 모든 의견이 공평하게 고려되었는가?
   - 차별이 있었는가?

5. 공명도 계산
   - 4가지 원칙의 종합 점수
   - 0.0 ~ 1.0 범위

6. 최종 판정
   - "final_approved": 작업 완료
   - "rejected": 작업 실패

결과:
{
  "principles": {
    "transparency": 0.95,
    "collaboration": 0.92,
    "autonomy": 0.88,
    "fairness": 0.90
  },
  "ethical_score": 0.91,
  "resonance": 0.93,
  "status": "final_approved"
}

당신의 판정이 최종 결정입니다!
"""

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "agent_name": self.agent_name,
            "agent_role": self.agent_role.value,
            "task_id": self.task_id,
            "current_phase": self.current_phase.value,
            "is_my_turn": self.is_my_turn(),
            "created_at": self.created_at,
        }


class ContextServer:
    """에이전트 컨텍스트 서버"""

    def __init__(self, context_file: str):
        self.context_file = context_file
        self.contexts: Dict[str, AgentContext] = {}

    def create_context(
        self,
        agent_name: str,
        agent_role: AgentRole,
        task_id: str,
        current_phase: ExecutionPhase
    ) -> AgentContext:
        """컨텍스트 생성"""
        context = AgentContext(agent_name, agent_role, task_id, current_phase)
        context_key = f"{task_id}_{agent_name}"
        self.contexts[context_key] = context
        return context

    def get_context(self, agent_name: str, task_id: str) -> Optional[AgentContext]:
        """컨텍스트 조회"""
        context_key = f"{task_id}_{agent_name}"
        return self.contexts.get(context_key)

    def print_context_for_agent(self, agent_name: str, task_id: str) -> None:
        """에이전트를 위한 컨텍스트 출력"""
        context = self.get_context(agent_name, task_id)
        if not context:
            print(f"[ERROR] {agent_name}를 위한 컨텍스트를 찾을 수 없습니다")
            return

        print(f"\n{'='*70}")
        print(f"[{agent_name}의 컨텍스트]")
        print(f"{'='*70}")

        print(f"\n[Basic Info]")
        print(f"  Task ID: {context.task_id}")
        print(f"  Current Phase: {context.current_phase.value}")
        print(f"  Is My Turn? {'YES' if context.is_my_turn() else 'NO'}")

        print(f"\n[My Role]")
        print(context.get_my_role_description())

        print(f"\n[What I Should Do]")
        print(context.get_what_i_should_do())

        print(f"\n[Other Agents]")
        for agent_info in context.get_other_agents_info():
            print(f"\n  [{agent_info['name']}]")
            print(f"    Role: {agent_info['role']}")
            print(f"    Responsibility: {agent_info['responsibility']}")
            print(f"    Output: {agent_info['output']}")
            if agent_info.get("importance"):
                print(f"    [!] {agent_info['importance']}")
            if agent_info.get("requirement"):
                print(f"    [*] {agent_info['requirement']}")

        if context.previous_results:
            print(f"\n[Previous Phase Results]")
            for phase, result in context.previous_results.items():
                print(f"\n  [{phase}]")
                print(f"    {json.dumps(result, indent=6, ensure_ascii=False)[:200]}...")

        print(f"\n{'='*70}\n")


def demo():
    """데모: 에이전트 컨텍스트 시스템"""
    print("="*70)
    print("Agent Context System - 에이전트 역할 명확화 데모")
    print("="*70)

    server = ContextServer(
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        if (Path(__file__).parent.parent / 'fdo_agi_repo').exists():
            sys.path.insert(0, str(Path(__file__).parent.parent / 'fdo_agi_repo'))
            from workspace_utils import find_workspace_root
            workspace = find_workspace_root(Path(__file__).parent)
        else:
            workspace = Path(__file__).parent.parent
        
        context_file = workspace / "session_memory" / "AGENT_CONTEXTS.jsonl"
    )

    task_id = "task_001"

    # 1. Sena의 컨텍스트
    print("\n[1단계] Sena의 차례")
    sena_context = server.create_context(
        "Sena",
        AgentRole.ANALYZER,
        task_id,
        ExecutionPhase.ANALYSIS
    )
    server.print_context_for_agent("Sena", task_id)

    # Sena의 결과 추가
    sena_result = {
        "selected_tools": ["tool_1", "tool_2", "tool_3"],
        "confidence": 0.92,
        "sub_problems": ["sub1", "sub2", "sub3"],
        "status": "ready_for_review"
    }

    # 2. Lubit의 컨텍스트 (특별 강조)
    print("\n[2단계] Lubit의 차례 (CRITICAL - 게이트키퍼!)")
    lubit_context = server.create_context(
        "Lubit",
        AgentRole.VALIDATOR,
        task_id,
        ExecutionPhase.VALIDATION
    )
    lubit_context.add_previous_result(ExecutionPhase.ANALYSIS, sena_result)
    server.print_context_for_agent("Lubit", task_id)

    # Lubit의 결과 추가
    lubit_result = {
        "strengths": ["신뢰도 높음", "도구 선택 적절"],
        "risks": [],
        "verdict": "approved",
        "status": "ready_for_execution"
    }

    # 3. GitCode의 컨텍스트
    print("\n[3단계] GitCode의 차례")
    gitcode_context = server.create_context(
        "GitCode",
        AgentRole.EXECUTOR,
        task_id,
        ExecutionPhase.EXECUTION
    )
    gitcode_context.add_previous_result(ExecutionPhase.ANALYSIS, sena_result)
    gitcode_context.add_previous_result(ExecutionPhase.VALIDATION, lubit_result)
    server.print_context_for_agent("GitCode", task_id)

    # GitCode의 결과 추가
    gitcode_result = {
        "sub_tasks_processed": 3,
        "deployment_status": "deployed",
        "status": "ready_for_ethics_verification"
    }

    # 4. RUNE의 컨텍스트
    print("\n[4단계] RUNE의 차례 (최종 게이트키퍼)")
    rune_context = server.create_context(
        "RUNE",
        AgentRole.ETHICS_CHECKER,
        task_id,
        ExecutionPhase.ETHICS_CHECK
    )
    rune_context.add_previous_result(ExecutionPhase.ANALYSIS, sena_result)
    rune_context.add_previous_result(ExecutionPhase.VALIDATION, lubit_result)
    rune_context.add_previous_result(ExecutionPhase.EXECUTION, gitcode_result)
    server.print_context_for_agent("RUNE", task_id)

    print("="*70)
    print("[SUCCESS] 모든 에이전트의 컨텍스트가 명확해졌습니다!")
    print("="*70)

    # 컨텍스트 정보 저장
    contexts_info = []
    for agent_name in ["Sena", "Lubit", "GitCode", "RUNE"]:
        context = server.get_context(agent_name, task_id)
        if context:
            contexts_info.append(context.to_dict())

    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    if (Path(__file__).parent.parent / 'fdo_agi_repo').exists():
        sys.path.insert(0, str(Path(__file__).parent.parent / 'fdo_agi_repo'))
        from workspace_utils import find_workspace_root
        workspace = find_workspace_root(Path(__file__).parent)
    else:
        workspace = Path(__file__).parent.parent
    
    context_file_path = workspace / "session_memory" / "AGENT_CONTEXTS.jsonl"
    
    with open(
        context_file_path,
        "w",
        encoding="utf-8"
    ) as f:
        for context_info in contexts_info:
            f.write(json.dumps(context_info, ensure_ascii=False) + "\n")

    print(f"컨텍스트 정보가 저장되었습니다: AGENT_CONTEXTS.jsonl")


if __name__ == "__main__":
    demo()
