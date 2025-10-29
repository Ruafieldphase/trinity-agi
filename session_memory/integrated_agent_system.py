#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integrated Agent System - 모든 에이전트를 통합하는 완전한 오케스트레이션 시스템

이 모듈은 다음을 통합합니다:
1. Agent Interface: 모든 에이전트의 기본 인터페이스
2. Message Router: 메시지 라우팅 및 작업 상태 관리
3. All Agents: Sena, Lubit, GitCode, RUNE
4. Full Workflow: 완전한 에이전트 협력 워크플로우
"""

import sys
import io
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from agent_interface import AgentConfig, AgentRole, TaskContext

# UTF-8 인코딩 강제 설정 (Windows 호환)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 에이전트 import
try:
    from agent_sena import SenaAgent
    from agent_lubit import LubitAgent
    from agent_gitcode import GitCodeAgent
    from agent_rune import RUNEAgent
    print("[System] 모든 에이전트 임포트 성공")
except ImportError as e:
    print(f"[Error] 에이전트 임포트 실패: {e}")
    sys.exit(1)


class IntegratedAgentSystem:
    """모든 에이전트를 통합하는 시스템"""

    def __init__(self):
        """시스템 초기화"""
        self.agents: Dict[str, Any] = {}
        self.task_history: List[Dict[str, Any]] = []
        self.message_log: List[Dict[str, Any]] = []

    def initialize_agents(self) -> bool:
        """모든 에이전트 초기화"""
        print("\n" + "=" * 80)
        print("[1] 에이전트 초기화")
        print("=" * 80)

        agent_configs = [
            (AgentRole.SENA, "Sena", "분석가 - 문제를 분석하고 도구를 선택"),
            (AgentRole.LUBIT, "Lubit", "게이트키퍼 - 분석을 검증"),
            (AgentRole.GITCODE, "GitCode", "실행자 - 작업을 실행"),
            (AgentRole.RUNE, "RUNE", "윤리 검증자 - 윤리적 검증")
        ]

        agent_classes = {
            AgentRole.SENA: SenaAgent,
            AgentRole.LUBIT: LubitAgent,
            AgentRole.GITCODE: GitCodeAgent,
            AgentRole.RUNE: RUNEAgent
        }

        for role, name, description in agent_configs:
            config = AgentConfig(
                role=role,
                name=name,
                description=description
            )

            agent_class = agent_classes[role]
            agent = agent_class(config)

            if agent.initialize():
                self.agents[role.value] = agent
                print(f"✓ {name} 에이전트 초기화 완료")
            else:
                print(f"✗ {name} 에이전트 초기화 실패")
                return False

        return True

    def execute_workflow(self, problem: str) -> Dict[str, Any]:
        """전체 워크플로우 실행"""
        print("\n" + "=" * 80)
        print("[2] 에이전트 협력 워크플로우 실행")
        print("=" * 80)

        task_id = f"task_{int(time.time() * 1000)}"
        print(f"\n작업 ID: {task_id}")
        print(f"문제: {problem}\n")

        # Step 1: Sena 분석
        print("[단계 1] Sena (분석가) 실행")
        print("-" * 80)

        sena = self.agents[AgentRole.SENA.value]
        sena_task_context = TaskContext(
            task_id=task_id,
            task_type="analysis",
            description=problem
        )

        sena_result = sena.execute_task(sena_task_context)

        if not sena_result.success:
            print(f"✗ Sena 분석 실패: {sena_result.error}")
            return {
                "success": False,
                "error": "Sena 분석 실패"
            }

        sena_output = sena_result.output
        print(f"✓ 분석 완료")
        print(f"  신뢰도: {sena_output['confidence']:.2%}")
        print(f"  도구: {', '.join(sena_output['analysis']['tools'])}")
        print(f"  부분 작업: {len(sena_output['analysis']['sub_problems'])}개")

        self.log_agent_action(task_id, "sena", "analysis", sena_output)

        # Step 2: Lubit 검증
        print("\n[단계 2] Lubit (게이트키퍼) 검증")
        print("-" * 80)

        lubit = self.agents[AgentRole.LUBIT.value]

        # Lubit이 필요한 형식으로 분석 데이터 구성
        analysis_for_lubit = {
            "analysis": sena_output['analysis']['problem'],
            "selected_tools": sena_output['analysis']['tools'],
            "sub_problems": sena_output['analysis']['sub_problems'],
            "confidence": sena_output['confidence'],
            "approach": sena_output['analysis']['approach']
        }

        lubit_validation = lubit.validate_analysis(analysis_for_lubit)
        lubit_decision = lubit.make_decision(lubit_validation)

        print(f"✓ 검증 완료")
        print(f"  검증 점수: {lubit_validation['score']:.2%}")
        print(f"  판정: {lubit_decision}")

        if lubit_decision == "rejected":
            print(f"✗ 분석이 거부되었습니다")
            return {
                "success": False,
                "error": "분석 거부",
                "reason": lubit_validation['risks']
            }

        self.log_agent_action(task_id, "lubit", "validation", {
            "validation_score": lubit_validation['score'],
            "decision": lubit_decision
        })

        # Step 3: GitCode 실행
        print("\n[단계 3] GitCode (실행자) 실행")
        print("-" * 80)

        gitcode = self.agents[AgentRole.GITCODE.value]

        sub_problems = sena_output['analysis']['sub_problems']
        print(f"부분 작업 실행 ({len(sub_problems)}개):")

        execution_results = []
        for sub_problem in sub_problems:
            result = gitcode.execute_subtask(sub_problem)
            execution_results.append(result)

        successful = sum(1 for r in execution_results if r['success'])
        print(f"\n✓ 실행 완료")
        print(f"  성공: {successful}/{len(execution_results)}")

        self.log_agent_action(task_id, "gitcode", "execution", {
            "total_tasks": len(execution_results),
            "successful_tasks": successful,
            "failed_tasks": len(execution_results) - successful
        })

        # Step 4: RUNE 윤리 검증
        print("\n[단계 4] RUNE (윤리 검증자) 최종 검증")
        print("-" * 80)

        rune = self.agents[AgentRole.RUNE.value]

        execution_data = {
            "sub_tasks": execution_results,
            "total_tasks": len(execution_results),
            "successful_tasks": successful,
            "failed_tasks": len(execution_results) - successful,
            "execution_status": "completed"
        }

        verification_results = {
            "transparency": rune.verify_transparency(execution_data),
            "collaboration": rune.verify_collaboration(execution_data),
            "autonomy": rune.verify_autonomy(execution_data),
            "fairness": rune.verify_fairness(execution_data)
        }

        ethical_score = rune.calculate_ethical_score(verification_results)

        if ethical_score >= 0.85:
            final_verdict = "final_approved"
        elif ethical_score >= 0.70:
            final_verdict = "review_needed"
        else:
            final_verdict = "rejected"

        print(f"✓ 윤리 검증 완료")
        print(f"  윤리 점수: {ethical_score:.2%}")
        print(f"  최종 판정: {final_verdict}")

        self.log_agent_action(task_id, "rune", "ethics_verification", {
            "ethical_score": ethical_score,
            "verdict": final_verdict
        })

        # 최종 결과 구성
        result = {
            "success": final_verdict == "final_approved",
            "task_id": task_id,
            "final_verdict": final_verdict,
            "stages": {
                "sena": {
                    "confidence": sena_output['confidence'],
                    "tools": sena_output['analysis']['tools'],
                    "sub_problems": len(sena_output['analysis']['sub_problems'])
                },
                "lubit": {
                    "validation_score": lubit_validation['score'],
                    "decision": lubit_decision
                },
                "gitcode": {
                    "total_tasks": len(execution_results),
                    "successful_tasks": successful,
                    "failed_tasks": len(execution_results) - successful
                },
                "rune": {
                    "ethical_score": ethical_score,
                    "verdict": final_verdict
                }
            }
        }

        self.task_history.append(result)
        return result

    def log_agent_action(self, task_id: str, agent: str, action: str, data: Dict[str, Any]):
        """에이전트 액션 로깅"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "agent": agent,
            "action": action,
            "data": data
        }
        self.message_log.append(log_entry)

    def print_system_summary(self):
        """시스템 요약 출력"""
        print("\n" + "=" * 80)
        print("[3] 시스템 요약")
        print("=" * 80)

        print("\n[에이전트 상태]")
        for role_value, agent in self.agents.items():
            status = agent.get_status()
            print(f"\n{agent.name} ({role_value})")
            print(f"  ID: {status['agent_id']}")
            print(f"   상태: {'초기화됨' if status['is_initialized'] else '미초기화'}")
            print(f"   처리한 메시지: {status['message_count']}")
            print(f"   처리한 작업: {status['task_count']}")

        print("\n[작업 이력]")
        if self.task_history:
            for task in self.task_history:
                print(f"\n작업: {task['task_id']}")
                print(f"  최종 판정: {task['final_verdict']}")
                print(f"  성공: {'✓' if task['success'] else '✗'}")
        else:
            print("처리된 작업이 없습니다.")

        print("\n[통계]")
        total_tasks = len(self.task_history)
        successful_tasks = sum(1 for t in self.task_history if t['success'])
        success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0

        print(f"  총 작업: {total_tasks}")
        print(f"  성공: {successful_tasks}")
        print(f"  성공률: {success_rate:.1f}%")


# ============================================================================
# 데모: 통합 에이전트 시스템
# ============================================================================

def demo_integrated_system():
    """통합 에이전트 시스템 데모"""
    print("=" * 80)
    print("통합 에이전트 시스템 데모")
    print("=" * 80)

    # 시스템 생성
    system = IntegratedAgentSystem()

    # 에이전트 초기화
    if not system.initialize_agents():
        print("에이전트 초기화 실패")
        return

    # 테스트 작업들
    test_problems = [
        "고객 행동 데이터 분석 및 세분화",
        "웹에서 시장 동향 검색 및 요약",
        "제품 리뷰 감정 분석"
    ]

    # 각 문제에 대해 워크플로우 실행
    for i, problem in enumerate(test_problems, 1):
        print("\n" + "=" * 80)
        print(f"작업 {i}/{len(test_problems)}")
        print("=" * 80)

        result = system.execute_workflow(problem)

        if result['success']:
            print(f"\n✓ 작업 완료 성공")
        else:
            print(f"\n✗ 작업 완료 실패")
            if 'reason' in result:
                print(f"  이유: {result['reason']}")

    # 시스템 요약 출력
    system.print_system_summary()

    print("\n" + "=" * 80)
    print("통합 에이전트 시스템 데모 완료!")
    print("=" * 80)


if __name__ == "__main__":
    demo_integrated_system()
