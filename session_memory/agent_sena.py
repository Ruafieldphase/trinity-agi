#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sena - 분석가 에이전트

Sena는 다음 역할을 수행합니다:
1. 문제 분석: 주어진 문제를 깊이 있게 분석
2. 도구 선택: 최적의 도구 식별
3. 작업 분해: 큰 작업을 작은 부분으로 분해
4. 신뢰도 평가: 분석의 신뢰도 평가

메시지 라우터를 통해 Lubit으로 분석 결과 전달
"""

import sys
import io
import json
import time
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from agent_interface import (
    AnalysisAgent, AgentConfig, AgentRole, TaskContext, ExecutionResult, MessageType
)

# UTF-8 인코딩 강제 설정 (Windows 호환)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class SenaAgent(AnalysisAgent):
    """
    Sena - 분석가 에이전트 구현

    역할: 문제를 분석하고 최적의 도구를 선택하며 작업을 분해
    """

    # 사용 가능한 도구 데이터베이스
    AVAILABLE_TOOLS = {
        "information_theory": {
            "name": "정보 이론",
            "description": "정보 이론 메트릭 계산",
            "domain": "analysis",
            "cost": 2
        },
        "parser": {
            "name": "파서",
            "description": "데이터 구조 분석",
            "domain": "parsing",
            "cost": 1
        },
        "classifier": {
            "name": "분류기",
            "description": "데이터 분류",
            "domain": "classification",
            "cost": 3
        },
        "data_processor": {
            "name": "데이터 처리",
            "description": "데이터 전처리 및 정제",
            "domain": "data_preparation",
            "cost": 2
        },
        "statistical_analyzer": {
            "name": "통계 분석기",
            "description": "통계 분석",
            "domain": "analysis",
            "cost": 3
        },
        "web_crawler": {
            "name": "웹 크롤러",
            "description": "웹 페이지 검색",
            "domain": "data_collection",
            "cost": 2
        },
        "text_processor": {
            "name": "텍스트 처리",
            "description": "텍스트 정제",
            "domain": "text_preparation",
            "cost": 1
        },
        "summarizer": {
            "name": "요약기",
            "description": "요약 생성",
            "domain": "text_analysis",
            "cost": 2
        }
    }

    # 도메인별 문제 패턴
    PROBLEM_PATTERNS = {
        "data_analysis": ["분석", "데이터", "통계", "인사이트"],
        "web_scraping": ["웹", "검색", "크롤", "수집"],
        "text_processing": ["텍스트", "처리", "정제", "요약"],
        "classification": ["분류", "카테고리", "타입"]
    }

    def __init__(self, config: AgentConfig):
        """Sena 에이전트 초기화"""
        super().__init__(config)
        self.analysis_templates = self._initialize_templates()

    def _initialize_templates(self) -> Dict[str, Any]:
        """분석 템플릿 초기화"""
        return {
            "data_analysis": {
                "tools": ["data_processor", "statistical_analyzer"],
                "steps": ["수집", "정제", "분석", "시각화"]
            },
            "web_scraping": {
                "tools": ["web_crawler", "text_processor"],
                "steps": ["검색", "정제", "추출"]
            },
            "text_processing": {
                "tools": ["text_processor", "summarizer"],
                "steps": ["정제", "분석", "요약"]
            },
            "classification": {
                "tools": ["parser", "classifier"],
                "steps": ["파싱", "특성추출", "분류"]
            }
        }

    def initialize(self) -> bool:
        """에이전트 초기화"""
        self.is_initialized = True
        self.log_message({
            "from": self.role.value,
            "message_type": "system",
            "content": "Sena 에이전트 초기화 완료"
        }, direction="system")
        return True

    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """메시지 처리"""
        self.log_message(message, direction="received")

        message_type = message.get("message_type")

        if message_type == "task_request":
            return self._handle_task_request(message)
        elif message_type == "revision_request":
            return self._handle_revision_request(message)
        else:
            return {
                "success": False,
                "error": f"알 수 없는 메시지 타입: {message_type}"
            }

    def _handle_task_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """작업 요청 처리"""
        task_id = message.get("task_id")
        problem = message.get("content", {}).get("problem")

        if not problem:
            return {"success": False, "error": "문제 설명이 없습니다"}

        # 분석 수행
        analysis = self.perform_analysis(problem)

        # 신뢰도 평가
        confidence = self.evaluate_confidence(analysis)

        # 응답 생성
        response = {
            "message_type": MessageType.ANALYSIS_SUBMISSION.value,
            "from_agent": self.role.value,
            "to_agent": "lubit",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "content": {
                "analysis": analysis,
                "selected_tools": analysis["tools"],
                "sub_problems": analysis["sub_problems"],
                "confidence": confidence,
                "approach": analysis["approach"]
            },
            "metadata": {
                "version": "1.0",
                "status": "analysis_complete"
            }
        }

        self.log_message(response, direction="sent")
        self.log_task(task_id, "analysis_complete", response)

        return response

    def _handle_revision_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """수정 요청 처리 (Lubit에서 거부됨)"""
        task_id = message.get("task_id")
        problem = message.get("content", {}).get("problem")
        feedback = message.get("content", {}).get("feedback")

        print(f"\n[Sena] 수정 요청 받음. 피드백: {feedback}")

        # 피드백을 고려하여 재분석
        analysis = self.perform_analysis(problem, feedback=feedback)
        confidence = self.evaluate_confidence(analysis)

        response = {
            "message_type": MessageType.ANALYSIS_SUBMISSION.value,
            "from_agent": self.role.value,
            "to_agent": "lubit",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "content": {
                "analysis": analysis,
                "selected_tools": analysis["tools"],
                "sub_problems": analysis["sub_problems"],
                "confidence": confidence,
                "approach": analysis["approach"],
                "feedback_incorporated": True
            },
            "metadata": {
                "version": "1.0",
                "status": "analysis_revised"
            }
        }

        self.log_message(response, direction="sent")
        self.log_task(task_id, "analysis_revised", response)

        return response

    def execute_task(self, task_context: TaskContext) -> ExecutionResult:
        """작업 실행"""
        try:
            start_time = time.time()

            # 문제 분석
            analysis = self.perform_analysis(task_context.description)

            # 신뢰도 평가
            confidence = self.evaluate_confidence(analysis)

            execution_time_ms = (time.time() - start_time) * 1000

            return ExecutionResult(
                success=True,
                output={
                    "analysis": analysis,
                    "confidence": confidence
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

        if "problem" not in input_data:
            return False, "problem 필드가 필요합니다"

        problem = input_data.get("problem")
        if not isinstance(problem, str) or len(problem) == 0:
            return False, "problem은 공백이 아닌 문자열이어야 합니다"

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
            "analysis": output["analysis"],
            "confidence": output["confidence"],
            "execution_time_ms": task_result.execution_time_ms
        }

    def perform_analysis(self, problem: str, feedback: str = None) -> Dict[str, Any]:
        """문제 분석 수행"""
        # 문제 도메인 식별
        domain = self._identify_domain(problem)

        # 필요한 도구 식별
        tools = self.identify_tools(problem)

        # 작업 분해
        sub_problems = self.decompose_task(problem, tools)

        # 분석 결과 구성
        analysis = {
            "problem": problem,
            "domain": domain,
            "tools": tools,
            "sub_problems": sub_problems,
            "approach": self._create_approach_description(domain, tools, sub_problems)
        }

        return analysis

    def _identify_domain(self, problem: str) -> str:
        """문제 도메인 식별"""
        problem_lower = problem.lower()

        for domain, keywords in self.PROBLEM_PATTERNS.items():
            if any(keyword in problem_lower for keyword in keywords):
                return domain

        return "general"

    def identify_tools(self, problem: str) -> List[str]:
        """필요한 도구 식별"""
        domain = self._identify_domain(problem)

        # 도메인 기반 도구 선택
        if domain in self.analysis_templates:
            base_tools = self.analysis_templates[domain]["tools"]
        else:
            base_tools = ["data_processor", "text_processor"]

        # 문제 내용 분석하여 추가 도구 결정
        problem_lower = problem.lower()

        additional_tools = []
        if "통계" in problem or "분석" in problem:
            additional_tools.append("statistical_analyzer")
        if "분류" in problem or "카테고리" in problem:
            additional_tools.append("classifier")
        if "요약" in problem:
            additional_tools.append("summarizer")

        # 중복 제거 및 반환
        all_tools = list(set(base_tools + additional_tools))
        return sorted(all_tools)

    def decompose_task(self, problem: str, tools: List[str]) -> List[Dict[str, Any]]:
        """작업 분해"""
        domain = self._identify_domain(problem)

        # 템플릿 기반 단계 가져오기
        if domain in self.analysis_templates:
            steps = self.analysis_templates[domain]["steps"]
        else:
            steps = ["준비", "처리", "분석", "결과"]

        # 부분 작업 생성
        sub_problems = []
        for i, step in enumerate(steps, 1):
            sub_problems.append({
                "id": f"sub_{i}",
                "step": i,
                "description": step,
                "tools": [tools[i % len(tools)]],  # 단계별로 도구 할당
                "estimated_time": 5 + (i * 2)  # 예상 소요 시간
            })

        return sub_problems

    def evaluate_confidence(self, analysis: Dict[str, Any]) -> float:
        """신뢰도 평가"""
        score = 0.0

        # 도구 검증 (각 도구가 실제 존재하는지)
        valid_tools = sum(1 for tool in analysis["tools"] if tool in self.AVAILABLE_TOOLS)
        tool_score = (valid_tools / len(analysis["tools"])) if analysis["tools"] else 0
        score += tool_score * 0.3

        # 분해 품질 (부분 작업이 적절한 개수인지)
        sub_problem_count = len(analysis["sub_problems"])
        if 2 <= sub_problem_count <= 5:
            decomposition_score = 1.0
        elif 1 <= sub_problem_count <= 7:
            decomposition_score = 0.8
        else:
            decomposition_score = 0.6
        score += decomposition_score * 0.4

        # 도메인 명확성
        domain = analysis.get("domain", "general")
        domain_score = 1.0 if domain != "general" else 0.7
        score += domain_score * 0.3

        return min(1.0, score)

    def _create_approach_description(self, domain: str, tools: List[str], sub_problems: List[Dict]) -> str:
        """접근 방식 설명 생성"""
        tool_names = [self.AVAILABLE_TOOLS.get(tool, {}).get("name", tool) for tool in tools]
        step_descriptions = [sp["description"] for sp in sub_problems]

        description = f"""
문제 도메인: {domain}
필요 도구: {', '.join(tool_names)}
처리 단계:
{chr(10).join(f'  {i}. {step}' for i, step in enumerate(step_descriptions, 1))}
"""
        return description.strip()


# ============================================================================
# 데모: Sena 에이전트
# ============================================================================

def demo_sena_agent():
    """Sena 에이전트 데모"""
    print("=" * 80)
    print("Sena (분석가) 에이전트 데모")
    print("=" * 80)

    # 1. Sena 에이전트 생성
    print("\n[1단계] Sena 에이전트 생성")
    print("-" * 80)

    config = AgentConfig(
        role=AgentRole.SENA,
        name="Sena",
        description="분석가 - 문제를 분석하고 도구를 선택"
    )

    sena = SenaAgent(config)
    sena.initialize()
    print(f"Sena 에이전트 생성 완료: {sena.agent_id}")

    # 2. 문제 분석 테스트
    print("\n[2단계] 문제 분석 테스트")
    print("-" * 80)

    problems = [
        "복잡한 데이터 분석 및 시각화",
        "웹에서 뉴스 검색 및 요약",
        "텍스트 분류 및 감정 분석"
    ]

    for i, problem in enumerate(problems, 1):
        print(f"\n{i}. 문제: {problem}")
        analysis = sena.perform_analysis(problem)
        print(f"   도메인: {analysis['domain']}")
        print(f"   도구: {', '.join(analysis['tools'])}")
        print(f"   부분 작업:")
        for sub in analysis['sub_problems']:
            print(f"     - {sub['step']}: {sub['description']} (도구: {sub['tools'][0]})")

    # 3. 신뢰도 평가 테스트
    print("\n[3단계] 신뢰도 평가 테스트")
    print("-" * 80)

    for i, problem in enumerate(problems, 1):
        analysis = sena.perform_analysis(problem)
        confidence = sena.evaluate_confidence(analysis)
        print(f"\n{i}. '{problem}'")
        print(f"   신뢰도: {confidence:.2%}")

    # 4. 메시지 처리 테스트
    print("\n[4단계] 메시지 처리 테스트")
    print("-" * 80)

    message = {
        "message_type": "task_request",
        "task_id": "task_001",
        "from": "router",
        "to": "sena",
        "content": {
            "problem": "대규모 고객 데이터 분석 및 세분화"
        }
    }

    print(f"\n요청 메시지: {message['content']['problem']}")
    response = sena.process_message(message)

    print(f"\n응답 메시지 타입: {response['message_type']}")
    print(f"신뢰도: {response['content']['confidence']:.2%}")
    print(f"선택된 도구: {', '.join(response['content']['selected_tools'])}")
    print(f"부분 작업:")
    for sub in response['content']['sub_problems']:
        print(f"  - {sub['step']}: {sub['description']}")

    # 5. TaskContext를 이용한 execute_task 테스트
    print("\n[5단계] 작업 실행 테스트")
    print("-" * 80)

    task_context = TaskContext(
        task_id="task_002",
        task_type="analysis",
        description="시계열 데이터 분석 및 예측"
    )

    result = sena.execute_task(task_context)
    print(f"\n작업 실행 성공: {result.success}")
    print(f"실행 시간: {result.execution_time_ms:.2f}ms")
    print(f"신뢰도: {result.output['confidence']:.2%}")

    # 6. 에이전트 상태 조회
    print("\n[6단계] 에이전트 상태 조회")
    print("-" * 80)

    status = sena.get_status()
    print(f"\n에이전트 상태:")
    print(f"  - ID: {status['agent_id']}")
    print(f"  - 역할: {status['role']}")
    print(f"  - 이름: {status['name']}")
    print(f"  - 초기화: {status['is_initialized']}")
    print(f"  - 처리한 메시지: {status['message_count']}")
    print(f"  - 처리한 작업: {status['task_count']}")

    print("\n" + "=" * 80)
    print("Sena 에이전트 데모 완료!")
    print("=" * 80)


if __name__ == "__main__":
    demo_sena_agent()
