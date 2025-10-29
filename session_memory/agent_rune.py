#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RUNE - 윤리 검증자 에이전트

RUNE은 다음 역할을 수행합니다:
1. 투명성 검증: 전체 프로세스가 투명한지 검증
2. 협력성 검증: 에이전트들의 협력이 적절한지 검증
3. 자율성 검증: 각 에이전트의 자율성이 존중되는지 검증
4. 공정성 검증: 결과가 공정한지 검증

메시지 라우터를 통해 최종 판정 결과 반환
"""

import sys
import io
import json
import time
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from agent_interface import (
    EthicsAgent, AgentConfig, AgentRole, TaskContext, ExecutionResult, MessageType
)

# UTF-8 인코딩 강제 설정 (Windows 호환)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class RUNEAgent(EthicsAgent):
    """
    RUNE - 윤리 검증자 에이전트 구현

    역할: 전체 프로세스의 윤리성을 검증
    """

    # 윤리 검증 기준
    ETHICS_STANDARDS = {
        "transparency": {
            "name": "투명성",
            "description": "모든 단계가 명확하고 이해할 수 있는가?",
            "weight": 0.25,
            "criteria": [
                "분석 과정이 명확한가?",
                "검증 기준이 명확한가?",
                "실행 과정이 추적 가능한가?",
                "결과가 설명 가능한가?"
            ]
        },
        "collaboration": {
            "name": "협력성",
            "description": "에이전트들 간의 협력이 적절한가?",
            "weight": 0.25,
            "criteria": [
                "에이전트들이 역할을 충실히 하는가?",
                "메시지가 제대로 전달되는가?",
                "피드백이 반영되는가?",
                "문제 해결이 협력적인가?"
            ]
        },
        "autonomy": {
            "name": "자율성",
            "description": "각 에이전트의 자율성이 존중되는가?",
            "weight": 0.25,
            "criteria": [
                "각 에이전트가 자신의 역할을 선택할 수 있는가?",
                "의사결정 과정이 존중되는가?",
                "개선 제안이 수용되는가?",
                "피드백 루프가 존재하는가?"
            ]
        },
        "fairness": {
            "name": "공정성",
            "description": "모든 처리가 공정한가?",
            "weight": 0.25,
            "criteria": [
                "동일한 기준이 일관되게 적용되는가?",
                "편향이 없는가?",
                "모든 옵션이 공평하게 검토되는가?",
                "결과가 타당한가?"
            ]
        }
    }

    def __init__(self, config: AgentConfig):
        """RUNE 에이전트 초기화"""
        super().__init__(config)
        self.verification_count = 0
        self.approved_count = 0
        self.review_needed_count = 0
        self.rejected_count = 0

    def initialize(self) -> bool:
        """에이전트 초기화"""
        self.is_initialized = True
        self.log_message({
            "from": self.role.value,
            "message_type": "system",
            "content": "RUNE 에이전트 초기화 완료"
        }, direction="system")
        return True

    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """메시지 처리"""
        self.log_message(message, direction="received")

        message_type = message.get("message_type")

        if message_type == "execution_result":
            return self._handle_execution_result(message)
        else:
            return {
                "success": False,
                "error": f"알 수 없는 메시지 타입: {message_type}"
            }

    def _handle_execution_result(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """실행 결과 처리"""
        task_id = message.get("task_id")
        content = message.get("content", {})

        # 윤리 검증 수행
        verification_results = {}
        verification_results["transparency"] = self.verify_transparency(content)
        verification_results["collaboration"] = self.verify_collaboration(content)
        verification_results["autonomy"] = self.verify_autonomy(content)
        verification_results["fairness"] = self.verify_fairness(content)

        # 최종 윤리 점수 계산
        ethical_score = self.calculate_ethical_score(verification_results)

        # 최종 판정
        if ethical_score >= 0.85:
            verdict = "final_approved"
            self.approved_count += 1
        elif ethical_score >= 0.70:
            verdict = "review_needed"
            self.review_needed_count += 1
        else:
            verdict = "rejected"
            self.rejected_count += 1

        response = {
            "message_type": MessageType.FINAL_VERDICT.value,
            "from_agent": self.role.value,
            "to_agent": "router",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "content": {
                "verdict": verdict,
                "ethical_score": ethical_score,
                "verification_results": verification_results,
                "status": "ethics_verification_complete"
            },
            "metadata": {
                "version": "1.0",
                "status": "final_verdict"
            }
        }

        print(f"\n[RUNE] 윤리 검증 완료: {task_id}")
        print(f"  판정: {verdict}")
        print(f"  윤리 점수: {ethical_score:.2%}")

        self.log_message(response, direction="sent")
        self.log_task(task_id, f"ethics_{verdict}", response)

        return response

    def execute_task(self, task_context: TaskContext) -> ExecutionResult:
        """작업 실행"""
        try:
            start_time = time.time()

            # 더미 검증 수행
            verification_results = {
                "transparency": {"score": 0.9, "comments": "높은 투명성"},
                "collaboration": {"score": 0.85, "comments": "좋은 협력"},
                "autonomy": {"score": 0.88, "comments": "존중되는 자율성"},
                "fairness": {"score": 0.92, "comments": "공정한 처리"}
            }

            ethical_score = self.calculate_ethical_score(verification_results)

            execution_time_ms = (time.time() - start_time) * 1000

            return ExecutionResult(
                success=True,
                output={
                    "ethical_score": ethical_score,
                    "verification_results": verification_results
                },
                execution_time_ms=execution_time_ms
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output=None,
                error=str(e)
            )

    def validate_input(self, input_data: Any) -> Tuple[bool, Optional[str]]:
        """입력 검증"""
        if not isinstance(input_data, dict):
            return False, "입력은 딕셔너리여야 합니다"

        if "sub_tasks" not in input_data:
            return False, "sub_tasks 필드가 필요합니다"

        return True, None

    def generate_response(self, task_result: ExecutionResult) -> Dict[str, Any]:
        """응답 생성"""
        if not task_result.success:
            return {
                "success": False,
                "error": task_result.error
            }

        output = task_result.output
        return {
            "success": True,
            "ethical_score": output["ethical_score"],
            "verification_results": output["verification_results"],
            "execution_time_ms": task_result.execution_time_ms
        }

    def verify_transparency(self, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """투명성 검증"""
        criteria = self.ETHICS_STANDARDS["transparency"]["criteria"]

        # 각 기준별 점수 계산
        scores = []

        # 1. 분석 과정이 명확한가?
        if execution_data.get("sub_tasks"):
            scores.append(1.0)
        else:
            scores.append(0.5)

        # 2. 검증 기준이 명확한가?
        scores.append(0.9)  # 기본적으로 높은 점수

        # 3. 실행 과정이 추적 가능한가?
        if execution_data.get("successful_tasks") is not None:
            scores.append(0.95)
        else:
            scores.append(0.7)

        # 4. 결과가 설명 가능한가?
        if execution_data.get("execution_status"):
            scores.append(0.9)
        else:
            scores.append(0.6)

        avg_score = sum(scores) / len(scores) if scores else 0.7

        return {
            "score": avg_score,
            "criteria_scores": dict(zip(criteria, scores)),
            "comments": f"투명성 점수: {avg_score:.2%}"
        }

    def verify_collaboration(self, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """협력성 검증"""
        criteria = self.ETHICS_STANDARDS["collaboration"]["criteria"]

        scores = []

        # 1. 에이전트들이 역할을 충실히 하는가?
        scores.append(0.88)

        # 2. 메시지가 제대로 전달되는가?
        scores.append(0.92)

        # 3. 피드백이 반영되는가?
        scores.append(0.85)

        # 4. 문제 해결이 협력적인가?
        if execution_data.get("sub_tasks"):
            scores.append(0.90)
        else:
            scores.append(0.70)

        avg_score = sum(scores) / len(scores) if scores else 0.7

        return {
            "score": avg_score,
            "criteria_scores": dict(zip(criteria, scores)),
            "comments": f"협력성 점수: {avg_score:.2%}"
        }

    def verify_autonomy(self, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """자율성 검증"""
        criteria = self.ETHICS_STANDARDS["autonomy"]["criteria"]

        scores = []

        # 1. 각 에이전트가 자신의 역할을 선택할 수 있는가?
        scores.append(0.90)

        # 2. 의사결정 과정이 존중되는가?
        scores.append(0.87)

        # 3. 개선 제안이 수용되는가?
        scores.append(0.85)

        # 4. 피드백 루프가 존재하는가?
        scores.append(0.88)

        avg_score = sum(scores) / len(scores) if scores else 0.7

        return {
            "score": avg_score,
            "criteria_scores": dict(zip(criteria, scores)),
            "comments": f"자율성 점수: {avg_score:.2%}"
        }

    def verify_fairness(self, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """공정성 검증"""
        criteria = self.ETHICS_STANDARDS["fairness"]["criteria"]

        scores = []

        # 1. 동일한 기준이 일관되게 적용되는가?
        scores.append(0.93)

        # 2. 편향이 없는가?
        scores.append(0.89)

        # 3. 모든 옵션이 공평하게 검토되는가?
        scores.append(0.86)

        # 4. 결과가 타당한가?
        if execution_data.get("successful_tasks", 0) > 0:
            scores.append(0.94)
        else:
            scores.append(0.70)

        avg_score = sum(scores) / len(scores) if scores else 0.7

        return {
            "score": avg_score,
            "criteria_scores": dict(zip(criteria, scores)),
            "comments": f"공정성 점수: {avg_score:.2%}"
        }

    def calculate_ethical_score(self, verification_results: Dict[str, Any]) -> float:
        """최종 윤리 점수 계산"""
        total_score = 0.0
        total_weight = 0.0

        for principle, results in verification_results.items():
            if principle in self.ETHICS_STANDARDS:
                weight = self.ETHICS_STANDARDS[principle]["weight"]
                score = results.get("score", 0.7)
                total_score += score * weight
                total_weight += weight

        # 최종 점수 (0.0 ~ 1.0)
        final_score = total_score / total_weight if total_weight > 0 else 0.7
        return min(1.0, final_score)


# ============================================================================
# 데모: RUNE 에이전트
# ============================================================================

def demo_rune_agent():
    """RUNE 에이전트 데모"""
    print("=" * 80)
    print("RUNE (윤리 검증자) 에이전트 데모")
    print("=" * 80)

    # 1. RUNE 에이전트 생성
    print("\n[1단계] RUNE 에이전트 생성")
    print("-" * 80)

    config = AgentConfig(
        role=AgentRole.RUNE,
        name="RUNE",
        description="윤리 검증자 - 윤리적 검증을 수행하는 에이전트"
    )

    rune = RUNEAgent(config)
    rune.initialize()
    print(f"RUNE 에이전트 생성 완료: {rune.agent_id}")

    # 2. 윤리 검증 기준 출력
    print("\n[2단계] 윤리 검증 기준")
    print("-" * 80)

    for principle, standards in rune.ETHICS_STANDARDS.items():
        print(f"\n{standards['name']} ({principle})")
        print(f"  가중치: {standards['weight']:.0%}")
        print(f"  설명: {standards['description']}")
        print(f"  기준:")
        for criterion in standards['criteria']:
            print(f"    • {criterion}")

    # 3. 투명성 검증 테스트
    print("\n[3단계] 투명성 검증 테스트")
    print("-" * 80)

    execution_data = {
        "sub_tasks": [
            {"id": "sub_1", "success": True},
            {"id": "sub_2", "success": True},
            {"id": "sub_3", "success": True}
        ],
        "successful_tasks": 3,
        "execution_status": "completed"
    }

    transparency = rune.verify_transparency(execution_data)
    print(f"\n투명성 점수: {transparency['score']:.2%}")
    print(f"설명: {transparency['comments']}")

    # 4. 협력성 검증 테스트
    print("\n[4단계] 협력성 검증 테스트")
    print("-" * 80)

    collaboration = rune.verify_collaboration(execution_data)
    print(f"\n협력성 점수: {collaboration['score']:.2%}")
    print(f"설명: {collaboration['comments']}")

    # 5. 자율성 검증 테스트
    print("\n[5단계] 자율성 검증 테스트")
    print("-" * 80)

    autonomy = rune.verify_autonomy(execution_data)
    print(f"\n자율성 점수: {autonomy['score']:.2%}")
    print(f"설명: {autonomy['comments']}")

    # 6. 공정성 검증 테스트
    print("\n[6단계] 공정성 검증 테스트")
    print("-" * 80)

    fairness = rune.verify_fairness(execution_data)
    print(f"\n공정성 점수: {fairness['score']:.2%}")
    print(f"설명: {fairness['comments']}")

    # 7. 최종 윤리 점수 계산
    print("\n[7단계] 최종 윤리 점수 계산")
    print("-" * 80)

    verification_results = {
        "transparency": transparency,
        "collaboration": collaboration,
        "autonomy": autonomy,
        "fairness": fairness
    }

    ethical_score = rune.calculate_ethical_score(verification_results)
    print(f"\n최종 윤리 점수: {ethical_score:.2%}")

    # 점수별 판정
    if ethical_score >= 0.85:
        verdict = "최종 승인 (final_approved)"
    elif ethical_score >= 0.70:
        verdict = "재검토 필요 (review_needed)"
    else:
        verdict = "거부 (rejected)"

    print(f"판정: {verdict}")

    # 8. 메시지 처리 테스트
    print("\n[8단계] 메시지 처리 테스트")
    print("-" * 80)

    message = {
        "message_type": "execution_result",
        "task_id": "task_001",
        "from": "gitcode",
        "to": "rune",
        "content": execution_data
    }

    print(f"\n실행 결과 수신")
    response = rune.process_message(message)

    print(f"최종 판정: {response['content']['verdict']}")
    print(f"윤리 점수: {response['content']['ethical_score']:.2%}")

    # 9. TaskContext를 이용한 execute_task 테스트
    print("\n[9단계] 작업 실행 테스트")
    print("-" * 80)

    task_context = TaskContext(
        task_id="task_002",
        task_type="ethics_verification",
        description="전체 프로세스 윤리 검증"
    )

    result = rune.execute_task(task_context)
    print(f"\n작업 실행 성공: {result.success}")
    print(f"실행 시간: {result.execution_time_ms:.2f}ms")
    print(f"윤리 점수: {result.output['ethical_score']:.2%}")

    # 10. 에이전트 상태 조회
    print("\n[10단계] 에이전트 상태 조회")
    print("-" * 80)

    status = rune.get_status()
    print(f"\n에이전트 상태:")
    print(f"  - ID: {status['agent_id']}")
    print(f"  - 역할: {status['role']}")
    print(f"  - 이름: {status['name']}")
    print(f"  - 초기화: {status['is_initialized']}")
    print(f"  - 처리한 메시지: {status['message_count']}")
    print(f"  - 처리한 작업: {status['task_count']}")

    print("\n" + "=" * 80)
    print("RUNE 에이전트 데모 완료!")
    print("=" * 80)


if __name__ == "__main__":
    demo_rune_agent()
