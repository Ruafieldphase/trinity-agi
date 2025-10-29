#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lubit - 게이트키퍼/검증자 에이전트

Lubit은 다음 역할을 수행합니다:
1. 분석 검증: Sena의 분석이 충분한지 검증
2. 위험 식별: 분석에 숨어있는 위험 식별
3. 강점 평가: 분석의 강점 평가
4. 최종 판정: 분석 수용/거부/수정 판정

메시지 라우터를 통해 Sena에게 피드백 또는 GitCode에게 승인 전달
"""

import sys
import io
import json
import time
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from agent_interface import (
    ValidationAgent, AgentConfig, AgentRole, TaskContext, ExecutionResult, MessageType
)

# UTF-8 인코딩 강제 설정 (Windows 호환)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class LubitAgent(ValidationAgent):
    """
    Lubit - 게이트키퍼/검증자 에이전트 구현

    역할: Sena의 분석을 검증하고 최종 판정을 내림
    """

    # 검증 규칙
    VALIDATION_RULES = {
        "min_confidence": 0.7,  # 최소 신뢰도
        "min_tools": 1,  # 최소 도구 개수
        "max_tools": 8,  # 최대 도구 개수
        "min_sub_problems": 2,  # 최소 부분 작업 개수
        "max_sub_problems": 10,  # 최대 부분 작업 개수
        "required_fields": ["analysis", "selected_tools", "sub_problems", "confidence"]
    }

    # 위험 식별 규칙
    RISK_PATTERNS = {
        "low_confidence": {
            "threshold": 0.7,
            "message": "신뢰도가 낮음 (70% 미만)"
        },
        "insufficient_tools": {
            "count": 1,
            "message": "도구가 너무 적음 (최소 2개 필요)"
        },
        "excessive_tools": {
            "count": 8,
            "message": "도구가 너무 많음 (최대 8개)"
        },
        "imbalanced_decomposition": {
            "min": 2,
            "max": 10,
            "message": "부분 작업이 불균형함"
        }
    }

    # 강점 평가 기준
    STRENGTH_CRITERIA = {
        "high_confidence": {
            "threshold": 0.85,
            "message": "높은 신뢰도"
        },
        "appropriate_tools": {
            "min": 2,
            "max": 5,
            "message": "적절한 도구 선택"
        },
        "good_decomposition": {
            "min": 3,
            "max": 7,
            "message": "잘 구성된 작업 분해"
        },
        "clear_approach": {
            "message": "명확한 접근 방식"
        }
    }

    def __init__(self, config: AgentConfig):
        """Lubit 에이전트 초기화"""
        super().__init__(config)
        self.validation_rules = self.VALIDATION_RULES
        self.approved_analyses: List[str] = []
        self.rejected_analyses: List[str] = []

    def initialize(self) -> bool:
        """에이전트 초기화"""
        self.is_initialized = True
        self.log_message({
            "from": self.role.value,
            "message_type": "system",
            "content": "Lubit 에이전트 초기화 완료"
        }, direction="system")
        return True

    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """메시지 처리"""
        self.log_message(message, direction="received")

        message_type = message.get("message_type")

        if message_type == "analysis_submission":
            return self._handle_analysis_submission(message)
        else:
            return {
                "success": False,
                "error": f"알 수 없는 메시지 타입: {message_type}"
            }

    def _handle_analysis_submission(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """분석 제출 처리"""
        task_id = message.get("task_id")
        content = message.get("content", {})

        # 분석 검증
        validation_result = self.validate_analysis(content)
        decision = self.make_decision(validation_result)

        response = {
            "message_type": MessageType.VALIDATION_RESULT.value,
            "from_agent": self.role.value,
            "to_agent": "gitcode" if decision == "approved" else "sena",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "content": {
                "verdict": decision,
                "validation_score": validation_result["score"],
                "strengths": validation_result["strengths"],
                "risks": validation_result["risks"],
                "reasoning": validation_result["reasoning"]
            },
            "metadata": {
                "version": "1.0",
                "status": "validation_complete"
            }
        }

        if decision == "approved":
            self.approved_analyses.append(task_id)
            print(f"\n[Lubit] ✓ 분석 승인: {task_id}")
        elif decision == "needs_revision":
            print(f"\n[Lubit] ~ 수정 필요: {task_id}")
            response["content"]["feedback"] = self._generate_feedback(validation_result)
        else:  # rejected
            self.rejected_analyses.append(task_id)
            print(f"\n[Lubit] ✗ 분석 거부: {task_id}")

        self.log_message(response, direction="sent")
        self.log_task(task_id, f"validation_{decision}", response)

        return response

    def execute_task(self, task_context: TaskContext) -> ExecutionResult:
        """작업 실행"""
        try:
            start_time = time.time()

            # 더미 분석 검증
            analysis = {
                "analysis": "test",
                "selected_tools": ["tool1", "tool2"],
                "sub_problems": [{"id": "sub_1"}, {"id": "sub_2"}],
                "confidence": 0.85
            }

            validation_result = self.validate_analysis(analysis)

            execution_time_ms = (time.time() - start_time) * 1000

            return ExecutionResult(
                success=True,
                output={
                    "validation_score": validation_result["score"],
                    "decision": self.make_decision(validation_result)
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

        for field in self.VALIDATION_RULES["required_fields"]:
            if field not in input_data:
                return False, f"{field} 필드가 필요합니다"

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
            "validation_score": output["validation_score"],
            "decision": output["decision"],
            "execution_time_ms": task_result.execution_time_ms
        }

    def validate_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """분석 검증"""
        score = 0.0
        strengths = []
        risks = []

        # 1. 필수 필드 검증
        missing_fields = []
        for field in self.VALIDATION_RULES["required_fields"]:
            if field not in analysis:
                missing_fields.append(field)

        if missing_fields:
            risks.append(f"필수 필드 누락: {', '.join(missing_fields)}")

        # 2. 신뢰도 검증
        confidence = analysis.get("confidence", 0)
        if confidence < self.VALIDATION_RULES["min_confidence"]:
            risks.append(f"신뢰도 낮음: {confidence:.2%} (최소: {self.VALIDATION_RULES['min_confidence']:.2%})")
            score += confidence * 0.3
        else:
            if confidence > self.STRENGTH_CRITERIA["high_confidence"]["threshold"]:
                strengths.append(f"높은 신뢰도: {confidence:.2%}")
                score += 0.95 * 0.3
            else:
                score += confidence * 0.3

        # 3. 도구 개수 검증
        tools = analysis.get("selected_tools", [])
        tool_count = len(tools)

        if tool_count < self.VALIDATION_RULES["min_tools"]:
            risks.append(f"도구 부족: {tool_count}개 (최소: {self.VALIDATION_RULES['min_tools']}개)")
        elif tool_count > self.VALIDATION_RULES["max_tools"]:
            risks.append(f"도구 과다: {tool_count}개 (최대: {self.VALIDATION_RULES['max_tools']}개)")
        else:
            if self.STRENGTH_CRITERIA["appropriate_tools"]["min"] <= tool_count <= self.STRENGTH_CRITERIA["appropriate_tools"]["max"]:
                strengths.append(self.STRENGTH_CRITERIA["appropriate_tools"]["message"])
            score += 0.9 * 0.3

        # 4. 부분 작업 검증
        sub_problems = analysis.get("sub_problems", [])
        sub_count = len(sub_problems)

        if sub_count < self.VALIDATION_RULES["min_sub_problems"]:
            risks.append(f"부분 작업 부족: {sub_count}개 (최소: {self.VALIDATION_RULES['min_sub_problems']}개)")
        elif sub_count > self.VALIDATION_RULES["max_sub_problems"]:
            risks.append(f"부분 작업 과다: {sub_count}개 (최대: {self.VALIDATION_RULES['max_sub_problems']}개)")
        else:
            if self.STRENGTH_CRITERIA["good_decomposition"]["min"] <= sub_count <= self.STRENGTH_CRITERIA["good_decomposition"]["max"]:
                strengths.append(self.STRENGTH_CRITERIA["good_decomposition"]["message"])
            score += 0.9 * 0.4

        return {
            "score": min(1.0, score),
            "strengths": strengths,
            "risks": risks,
            "reasoning": self._generate_reasoning(analysis, strengths, risks)
        }

    def identify_risks(self, analysis: Dict[str, Any]) -> List[str]:
        """위험 식별"""
        risks = []

        confidence = analysis.get("confidence", 0)
        if confidence < self.RISK_PATTERNS["low_confidence"]["threshold"]:
            risks.append(self.RISK_PATTERNS["low_confidence"]["message"])

        tool_count = len(analysis.get("selected_tools", []))
        if tool_count < self.RISK_PATTERNS["insufficient_tools"]["count"]:
            risks.append(self.RISK_PATTERNS["insufficient_tools"]["message"])
        elif tool_count > self.RISK_PATTERNS["excessive_tools"]["count"]:
            risks.append(self.RISK_PATTERNS["excessive_tools"]["message"])

        sub_count = len(analysis.get("sub_problems", []))
        if not (self.RISK_PATTERNS["imbalanced_decomposition"]["min"] <= sub_count <= self.RISK_PATTERNS["imbalanced_decomposition"]["max"]):
            risks.append(self.RISK_PATTERNS["imbalanced_decomposition"]["message"])

        return risks

    def assess_strengths(self, analysis: Dict[str, Any]) -> List[str]:
        """강점 평가"""
        strengths = []

        confidence = analysis.get("confidence", 0)
        if confidence > self.STRENGTH_CRITERIA["high_confidence"]["threshold"]:
            strengths.append(self.STRENGTH_CRITERIA["high_confidence"]["message"])

        tool_count = len(analysis.get("selected_tools", []))
        if self.STRENGTH_CRITERIA["appropriate_tools"]["min"] <= tool_count <= self.STRENGTH_CRITERIA["appropriate_tools"]["max"]:
            strengths.append(self.STRENGTH_CRITERIA["appropriate_tools"]["message"])

        sub_count = len(analysis.get("sub_problems", []))
        if self.STRENGTH_CRITERIA["good_decomposition"]["min"] <= sub_count <= self.STRENGTH_CRITERIA["good_decomposition"]["max"]:
            strengths.append(self.STRENGTH_CRITERIA["good_decomposition"]["message"])

        if "approach" in analysis and len(analysis["approach"]) > 0:
            strengths.append(self.STRENGTH_CRITERIA["clear_approach"]["message"])

        return strengths

    def make_decision(self, validation_result: Dict[str, Any]) -> str:
        """최종 판정"""
        score = validation_result["score"]
        risks = validation_result["risks"]

        # 판정 기준
        if score >= 0.9 and len(risks) == 0:
            return "approved"
        elif score >= 0.75 and len(risks) <= 1:
            return "approved"
        elif score >= 0.6:
            return "needs_revision"
        else:
            return "rejected"

    def _generate_reasoning(self, analysis: Dict[str, Any], strengths: List[str], risks: List[str]) -> str:
        """판정 근거 생성"""
        reasoning = "검증 평가:\n"

        if strengths:
            reasoning += f"\n강점:\n" + "\n".join(f"  • {s}" for s in strengths)

        if risks:
            reasoning += f"\n위험:\n" + "\n".join(f"  • {r}" for r in risks)

        return reasoning.strip()

    def _generate_feedback(self, validation_result: Dict[str, Any]) -> str:
        """개선 피드백 생성"""
        feedback = "수정이 필요합니다:\n"

        if validation_result["risks"]:
            feedback += "\n해결할 문제:\n"
            for risk in validation_result["risks"]:
                feedback += f"  • {risk}\n"

        feedback += "\n권장사항:\n"
        feedback += "  • 신뢰도를 높여주세요\n"
        feedback += "  • 도구 선택을 재검토해주세요\n"
        feedback += "  • 부분 작업을 재조정해주세요\n"

        return feedback.strip()


# ============================================================================
# 데모: Lubit 에이전트
# ============================================================================

def demo_lubit_agent():
    """Lubit 에이전트 데모"""
    print("=" * 80)
    print("Lubit (게이트키퍼) 에이전트 데모")
    print("=" * 80)

    # 1. Lubit 에이전트 생성
    print("\n[1단계] Lubit 에이전트 생성")
    print("-" * 80)

    config = AgentConfig(
        role=AgentRole.LUBIT,
        name="Lubit",
        description="게이트키퍼 - 분석을 검증하는 에이전트"
    )

    lubit = LubitAgent(config)
    lubit.initialize()
    print(f"Lubit 에이전트 생성 완료: {lubit.agent_id}")

    # 2. 분석 검증 테스트
    print("\n[2단계] 분석 검증 테스트")
    print("-" * 80)

    test_analyses = [
        {
            "name": "좋은 분석",
            "data": {
                "analysis": "데이터 분석",
                "selected_tools": ["data_processor", "statistical_analyzer"],
                "sub_problems": [
                    {"id": "sub_1", "description": "수집"},
                    {"id": "sub_2", "description": "정제"},
                    {"id": "sub_3", "description": "분석"}
                ],
                "confidence": 0.92,
                "approach": "데이터 수집 → 정제 → 분석"
            }
        },
        {
            "name": "불충분한 분석",
            "data": {
                "analysis": "분석",
                "selected_tools": ["tool1"],
                "sub_problems": [
                    {"id": "sub_1"}
                ],
                "confidence": 0.65,
                "approach": ""
            }
        },
        {
            "name": "도구 과다 분석",
            "data": {
                "analysis": "분석",
                "selected_tools": ["tool1", "tool2", "tool3", "tool4", "tool5", "tool6", "tool7", "tool8", "tool9"],
                "sub_problems": [
                    {"id": f"sub_{i}"} for i in range(1, 4)
                ],
                "confidence": 0.88,
                "approach": "복잡한 분석"
            }
        }
    ]

    for test in test_analyses:
        print(f"\n{test['name']}:")
        validation_result = lubit.validate_analysis(test['data'])
        decision = lubit.make_decision(validation_result)

        print(f"  검증 점수: {validation_result['score']:.2%}")
        print(f"  판정: {decision}")
        print(f"  강점:")
        for strength in validation_result['strengths']:
            print(f"    • {strength}")
        print(f"  위험:")
        for risk in validation_result['risks']:
            print(f"    • {risk}")

    # 3. 위험 식별 테스트
    print("\n[3단계] 위험 식별 테스트")
    print("-" * 80)

    risky_analysis = {
        "analysis": "분석",
        "selected_tools": ["tool1"],
        "sub_problems": [{"id": "sub_1"}],
        "confidence": 0.6
    }

    print("\n분석:")
    print(f"  신뢰도: {risky_analysis['confidence']:.2%}")
    print(f"  도구: {len(risky_analysis['selected_tools'])}개")
    print(f"  부분 작업: {len(risky_analysis['sub_problems'])}개")

    risks = lubit.identify_risks(risky_analysis)
    print(f"\n식별된 위험:")
    for risk in risks:
        print(f"  • {risk}")

    # 4. 메시지 처리 테스트
    print("\n[4단계] 메시지 처리 테스트")
    print("-" * 80)

    message = {
        "message_type": "analysis_submission",
        "task_id": "task_001",
        "from": "sena",
        "to": "lubit",
        "content": {
            "analysis": "데이터 분석",
            "selected_tools": ["data_processor", "statistical_analyzer"],
            "sub_problems": [
                {"id": "sub_1"},
                {"id": "sub_2"},
                {"id": "sub_3"}
            ],
            "confidence": 0.92
        }
    }

    print(f"\n분석 수신: {message['content']['analysis']}")
    response = lubit.process_message(message)

    print(f"판정: {response['content']['verdict']}")
    print(f"검증 점수: {response['content']['validation_score']:.2%}")
    print(f"다음 에이전트: {response['to_agent']}")

    # 5. 에이전트 상태 조회
    print("\n[5단계] 에이전트 상태 조회")
    print("-" * 80)

    status = lubit.get_status()
    print(f"\n에이전트 상태:")
    print(f"  - ID: {status['agent_id']}")
    print(f"  - 역할: {status['role']}")
    print(f"  - 이름: {status['name']}")
    print(f"  - 초기화: {status['is_initialized']}")
    print(f"  - 처리한 메시지: {status['message_count']}")
    print(f"  - 처리한 작업: {status['task_count']}")

    print("\n" + "=" * 80)
    print("Lubit 에이전트 데모 완료!")
    print("=" * 80)


if __name__ == "__main__":
    demo_lubit_agent()
