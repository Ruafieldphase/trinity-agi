#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
단위 테스트: Agent Interface

이 모듈은 Agent Interface의 기본 기능을 테스트합니다.
"""

import sys
import io
import unittest
from agent_interface import (
    BaseAgent, AnalysisAgent, ValidationAgent, ExecutionAgent, EthicsAgent,
    AgentConfig, AgentRole, TaskContext, ExecutionResult, MessageType
)

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================================
# 테스트용 구현 클래스
# ============================================================================

class MockAnalysisAgent(AnalysisAgent):
    """테스트용 분석 에이전트"""

    def initialize(self) -> bool:
        self.is_initialized = True
        return True

    def process_message(self, message: dict):
        return {"success": True}

    def execute_task(self, task_context: TaskContext) -> ExecutionResult:
        return ExecutionResult(success=True, output={"test": "data"})

    def validate_input(self, input_data):
        return True, None

    def generate_response(self, task_result: ExecutionResult):
        return {"success": task_result.success}

    def perform_analysis(self, problem: str):
        return {"analysis": problem}

    def identify_tools(self, problem: str):
        return ["tool1", "tool2"]

    def decompose_task(self, problem: str, tools: list):
        return [{"id": "sub_1"}, {"id": "sub_2"}]

    def evaluate_confidence(self, analysis: dict):
        return 0.85


class MockValidationAgent(ValidationAgent):
    """테스트용 검증 에이전트"""

    def initialize(self) -> bool:
        self.is_initialized = True
        return True

    def process_message(self, message: dict):
        return {"success": True}

    def execute_task(self, task_context: TaskContext) -> ExecutionResult:
        return ExecutionResult(success=True, output={"test": "data"})

    def validate_input(self, input_data):
        return True, None

    def generate_response(self, task_result: ExecutionResult):
        return {"success": task_result.success}

    def validate_analysis(self, analysis: dict):
        return {"score": 0.9, "strengths": [], "risks": []}

    def identify_risks(self, analysis: dict):
        return []

    def assess_strengths(self, analysis: dict):
        return ["strength1"]

    def make_decision(self, validation_result: dict):
        return "approved"


class MockExecutionAgent(ExecutionAgent):
    """테스트용 실행 에이전트"""

    def initialize(self) -> bool:
        self.is_initialized = True
        return True

    def process_message(self, message: dict):
        return {"success": True}

    def execute_task(self, task_context: TaskContext) -> ExecutionResult:
        return ExecutionResult(success=True, output={"test": "data"})

    def validate_input(self, input_data):
        return True, None

    def generate_response(self, task_result: ExecutionResult):
        return {"success": task_result.success}

    def execute_subtask(self, subtask: dict):
        return ExecutionResult(success=True, output={"subtask": "completed"})

    def handle_dependencies(self, subtasks: list):
        return True

    def monitor_execution(self, task_id: str):
        return {"status": "running"}

    def handle_failure(self, subtask: dict, error: str):
        return True


class MockEthicsAgent(EthicsAgent):
    """테스트용 윤리 에이전트"""

    def initialize(self) -> bool:
        self.is_initialized = True
        return True

    def process_message(self, message: dict):
        return {"success": True}

    def execute_task(self, task_context: TaskContext) -> ExecutionResult:
        return ExecutionResult(success=True, output={"test": "data"})

    def validate_input(self, input_data):
        return True, None

    def generate_response(self, task_result: ExecutionResult):
        return {"success": task_result.success}

    def verify_transparency(self, execution_data: dict):
        return {"score": 0.9}

    def verify_collaboration(self, execution_data: dict):
        return {"score": 0.88}

    def verify_autonomy(self, execution_data: dict):
        return {"score": 0.87}

    def verify_fairness(self, execution_data: dict):
        return {"score": 0.91}

    def calculate_ethical_score(self, verification_results: dict):
        scores = [v.get("score", 0.8) for v in verification_results.values()]
        return sum(scores) / len(scores) if scores else 0.8


# ============================================================================
# 테스트 케이스
# ============================================================================

class TestAgentConfig(unittest.TestCase):
    """AgentConfig 테스트"""

    def test_agent_config_creation(self):
        """에이전트 설정 생성 테스트"""
        config = AgentConfig(
            role=AgentRole.SENA,
            name="Sena",
            description="분석가"
        )
        self.assertEqual(config.role, AgentRole.SENA)
        self.assertEqual(config.name, "Sena")
        self.assertEqual(config.version, "1.0")

    def test_agent_config_to_dict(self):
        """에이전트 설정 딕셔너리 변환 테스트"""
        config = AgentConfig(
            role=AgentRole.SENA,
            name="Sena",
            description="분석가"
        )
        config_dict = config.to_dict()
        self.assertIn("role", config_dict)
        self.assertEqual(config_dict["role"], "sena")


class TestTaskContext(unittest.TestCase):
    """TaskContext 테스트"""

    def test_task_context_creation(self):
        """작업 컨텍스트 생성 테스트"""
        task = TaskContext(
            task_id="task_001",
            task_type="analysis",
            description="테스트 작업"
        )
        self.assertEqual(task.task_id, "task_001")
        self.assertEqual(task.task_type, "analysis")
        self.assertIsNotNone(task.created_at)

    def test_task_context_priority(self):
        """작업 우선순위 테스트"""
        task = TaskContext(
            task_id="task_001",
            task_type="analysis",
            description="테스트 작업",
            priority=10
        )
        self.assertEqual(task.priority, 10)


class TestExecutionResult(unittest.TestCase):
    """ExecutionResult 테스트"""

    def test_execution_result_success(self):
        """실행 결과 성공 테스트"""
        result = ExecutionResult(
            success=True,
            output={"data": "test"},
            execution_time_ms=100.5
        )
        self.assertTrue(result.success)
        self.assertEqual(result.output["data"], "test")

    def test_execution_result_failure(self):
        """실행 결과 실패 테스트"""
        result = ExecutionResult(
            success=False,
            output=None,
            error="테스트 에러"
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "테스트 에러")

    def test_execution_result_to_dict(self):
        """실행 결과 딕셔너리 변환 테스트"""
        result = ExecutionResult(
            success=True,
            output={"data": "test"}
        )
        result_dict = result.to_dict()
        self.assertIn("success", result_dict)
        self.assertTrue(result_dict["success"])


class TestAnalysisAgent(unittest.TestCase):
    """분석 에이전트 테스트"""

    def setUp(self):
        """테스트 설정"""
        config = AgentConfig(
            role=AgentRole.SENA,
            name="Sena",
            description="분석가"
        )
        self.agent = MockAnalysisAgent(config)

    def test_agent_initialization(self):
        """에이전트 초기화 테스트"""
        result = self.agent.initialize()
        self.assertTrue(result)
        self.assertTrue(self.agent.is_initialized)

    def test_perform_analysis(self):
        """분석 수행 테스트"""
        analysis = self.agent.perform_analysis("테스트 문제")
        self.assertIn("analysis", analysis)

    def test_identify_tools(self):
        """도구 식별 테스트"""
        tools = self.agent.identify_tools("테스트 문제")
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0)

    def test_decompose_task(self):
        """작업 분해 테스트"""
        sub_tasks = self.agent.decompose_task("테스트 문제", ["tool1", "tool2"])
        self.assertIsInstance(sub_tasks, list)
        self.assertGreater(len(sub_tasks), 0)

    def test_evaluate_confidence(self):
        """신뢰도 평가 테스트"""
        analysis = self.agent.perform_analysis("테스트 문제")
        confidence = self.agent.evaluate_confidence(analysis)
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)

    def test_get_status(self):
        """에이전트 상태 조회 테스트"""
        self.agent.initialize()
        status = self.agent.get_status()
        self.assertIn("agent_id", status)
        self.assertIn("role", status)
        self.assertTrue(status["is_initialized"])


class TestValidationAgent(unittest.TestCase):
    """검증 에이전트 테스트"""

    def setUp(self):
        """테스트 설정"""
        config = AgentConfig(
            role=AgentRole.LUBIT,
            name="Lubit",
            description="게이트키퍼"
        )
        self.agent = MockValidationAgent(config)

    def test_validate_analysis(self):
        """분석 검증 테스트"""
        analysis = {"analysis": "test", "confidence": 0.9}
        result = self.agent.validate_analysis(analysis)
        self.assertIn("score", result)
        self.assertGreaterEqual(result["score"], 0.0)

    def test_identify_risks(self):
        """위험 식별 테스트"""
        analysis = {"analysis": "test"}
        risks = self.agent.identify_risks(analysis)
        self.assertIsInstance(risks, list)

    def test_assess_strengths(self):
        """강점 평가 테스트"""
        analysis = {"analysis": "test", "confidence": 0.9}
        strengths = self.agent.assess_strengths(analysis)
        self.assertIsInstance(strengths, list)

    def test_make_decision(self):
        """최종 판정 테스트"""
        validation_result = {"score": 0.9, "risks": []}
        decision = self.agent.make_decision(validation_result)
        self.assertIn(decision, ["approved", "needs_revision", "rejected"])


class TestExecutionAgent(unittest.TestCase):
    """실행 에이전트 테스트"""

    def setUp(self):
        """테스트 설정"""
        config = AgentConfig(
            role=AgentRole.GITCODE,
            name="GitCode",
            description="실행자"
        )
        self.agent = MockExecutionAgent(config)

    def test_execute_subtask(self):
        """부분 작업 실행 테스트"""
        subtask = {"id": "sub_1", "description": "테스트"}
        result = self.agent.execute_subtask(subtask)
        self.assertTrue(result.success)

    def test_handle_dependencies(self):
        """의존성 처리 테스트"""
        subtasks = [
            {"id": "sub_1", "dependencies": []},
            {"id": "sub_2", "dependencies": ["sub_1"]}
        ]
        result = self.agent.handle_dependencies(subtasks)
        self.assertTrue(result)

    def test_monitor_execution(self):
        """실행 모니터링 테스트"""
        info = self.agent.monitor_execution("task_001")
        self.assertIn("status", info)

    def test_handle_failure(self):
        """실패 처리 테스트"""
        subtask = {"id": "sub_1"}
        result = self.agent.handle_failure(subtask, "테스트 에러")
        self.assertTrue(result)


class TestEthicsAgent(unittest.TestCase):
    """윤리 에이전트 테스트"""

    def setUp(self):
        """테스트 설정"""
        config = AgentConfig(
            role=AgentRole.RUNE,
            name="RUNE",
            description="윤리 검증자"
        )
        self.agent = MockEthicsAgent(config)

    def test_verify_transparency(self):
        """투명성 검증 테스트"""
        result = self.agent.verify_transparency({})
        self.assertIn("score", result)

    def test_verify_collaboration(self):
        """협력성 검증 테스트"""
        result = self.agent.verify_collaboration({})
        self.assertIn("score", result)

    def test_verify_autonomy(self):
        """자율성 검증 테스트"""
        result = self.agent.verify_autonomy({})
        self.assertIn("score", result)

    def test_verify_fairness(self):
        """공정성 검증 테스트"""
        result = self.agent.verify_fairness({})
        self.assertIn("score", result)

    def test_calculate_ethical_score(self):
        """윤리 점수 계산 테스트"""
        verification_results = {
            "transparency": {"score": 0.9},
            "collaboration": {"score": 0.88},
            "autonomy": {"score": 0.87},
            "fairness": {"score": 0.91}
        }
        score = self.agent.calculate_ethical_score(verification_results)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


class TestMessageTypes(unittest.TestCase):
    """메시지 타입 테스트"""

    def test_message_type_values(self):
        """메시지 타입 값 테스트"""
        self.assertEqual(MessageType.ANALYSIS_SUBMISSION.value, "analysis_submission")
        self.assertEqual(MessageType.VALIDATION_RESULT.value, "validation_result")
        self.assertEqual(MessageType.EXECUTION_RESULT.value, "execution_result")
        self.assertEqual(MessageType.FINAL_VERDICT.value, "final_verdict")


class TestAgentRoles(unittest.TestCase):
    """에이전트 역할 테스트"""

    def test_agent_role_values(self):
        """에이전트 역할 값 테스트"""
        self.assertEqual(AgentRole.SENA.value, "sena")
        self.assertEqual(AgentRole.LUBIT.value, "lubit")
        self.assertEqual(AgentRole.GITCODE.value, "gitcode")
        self.assertEqual(AgentRole.RUNE.value, "rune")


# ============================================================================
# 메인 실행
# ============================================================================

def run_tests():
    """테스트 실행"""
    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 모든 테스트 추가
    suite.addTests(loader.loadTestsFromTestCase(TestAgentConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskContext))
    suite.addTests(loader.loadTestsFromTestCase(TestExecutionResult))
    suite.addTests(loader.loadTestsFromTestCase(TestAnalysisAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestValidationAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestExecutionAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestEthicsAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestMessageTypes))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentRoles))

    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
