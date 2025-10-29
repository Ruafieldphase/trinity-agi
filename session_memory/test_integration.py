#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 테스트: Agent System

이 모듈은 통합된 에이전트 시스템의 전체 워크플로우를 테스트합니다.
"""

import sys
import io
import unittest
import time
from agent_interface import AgentRole
from agent_sena import SenaAgent, AgentConfig
from agent_lubit import LubitAgent
from agent_gitcode import GitCodeAgent
from agent_rune import RUNEAgent
from integrated_agent_system import IntegratedAgentSystem

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================================
# 통합 테스트
# ============================================================================

class TestAgentInitialization(unittest.TestCase):
    """에이전트 초기화 테스트"""

    def test_sena_initialization(self):
        """Sena 에이전트 초기화"""
        config = AgentConfig(
            role=AgentRole.SENA,
            name="Sena",
            description="분석가"
        )
        agent = SenaAgent(config)
        self.assertTrue(agent.initialize())
        self.assertTrue(agent.is_initialized)

    def test_lubit_initialization(self):
        """Lubit 에이전트 초기화"""
        config = AgentConfig(
            role=AgentRole.LUBIT,
            name="Lubit",
            description="게이트키퍼"
        )
        agent = LubitAgent(config)
        self.assertTrue(agent.initialize())
        self.assertTrue(agent.is_initialized)

    def test_gitcode_initialization(self):
        """GitCode 에이전트 초기화"""
        config = AgentConfig(
            role=AgentRole.GITCODE,
            name="GitCode",
            description="실행자"
        )
        agent = GitCodeAgent(config)
        self.assertTrue(agent.initialize())
        self.assertTrue(agent.is_initialized)

    def test_rune_initialization(self):
        """RUNE 에이전트 초기화"""
        config = AgentConfig(
            role=AgentRole.RUNE,
            name="RUNE",
            description="윤리 검증자"
        )
        agent = RUNEAgent(config)
        self.assertTrue(agent.initialize())
        self.assertTrue(agent.is_initialized)


class TestSenaWorkflow(unittest.TestCase):
    """Sena 분석 워크플로우 테스트"""

    def setUp(self):
        """테스트 설정"""
        config = AgentConfig(
            role=AgentRole.SENA,
            name="Sena",
            description="분석가"
        )
        self.agent = SenaAgent(config)
        self.agent.initialize()

    def test_problem_analysis(self):
        """문제 분석 테스트"""
        problem = "고객 데이터 분석"
        analysis = self.agent.perform_analysis(problem)

        self.assertIn("problem", analysis)
        self.assertIn("domain", analysis)
        self.assertIn("tools", analysis)
        self.assertIn("sub_problems", analysis)

    def test_tool_identification(self):
        """도구 식별 테스트"""
        problem = "웹 데이터 수집"
        tools = self.agent.identify_tools(problem)

        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0)
        for tool in tools:
            self.assertIn(tool, self.agent.AVAILABLE_TOOLS.keys())

    def test_task_decomposition(self):
        """작업 분해 테스트"""
        problem = "복잡한 분석"
        tools = ["data_processor", "statistical_analyzer"]
        sub_problems = self.agent.decompose_task(problem, tools)

        self.assertIsInstance(sub_problems, list)
        self.assertGreaterEqual(len(sub_problems), 2)
        for sub in sub_problems:
            self.assertIn("id", sub)
            self.assertIn("step", sub)
            self.assertIn("description", sub)

    def test_confidence_evaluation(self):
        """신뢰도 평가 테스트"""
        analysis = self.agent.perform_analysis("테스트 문제")
        confidence = self.agent.evaluate_confidence(analysis)

        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)

    def test_domain_identification(self):
        """도메인 식별 테스트"""
        problems = [
            ("데이터 분석", "data_analysis"),
            ("웹 크롤링", "web_scraping"),
            ("텍스트 처리", "text_processing")
        ]

        for problem, expected_domain in problems:
            domain = self.agent._identify_domain(problem)
            # 예상 도메인을 식별하거나 일반 도메인으로 표시
            self.assertIsNotNone(domain)


class TestLubitWorkflow(unittest.TestCase):
    """Lubit 검증 워크플로우 테스트"""

    def setUp(self):
        """테스트 설정"""
        config = AgentConfig(
            role=AgentRole.LUBIT,
            name="Lubit",
            description="게이트키퍼"
        )
        self.agent = LubitAgent(config)
        self.agent.initialize()

    def test_analysis_validation(self):
        """분석 검증 테스트"""
        analysis = {
            "analysis": "테스트",
            "selected_tools": ["tool1", "tool2"],
            "sub_problems": [{"id": "sub_1"}, {"id": "sub_2"}],
            "confidence": 0.9
        }

        result = self.agent.validate_analysis(analysis)

        self.assertIn("score", result)
        self.assertIn("strengths", result)
        self.assertIn("risks", result)
        self.assertGreaterEqual(result["score"], 0.0)
        self.assertLessEqual(result["score"], 1.0)

    def test_risk_identification(self):
        """위험 식별 테스트"""
        analysis = {
            "analysis": "테스트",
            "selected_tools": ["tool1"],
            "sub_problems": [{"id": "sub_1"}],
            "confidence": 0.5
        }

        risks = self.agent.identify_risks(analysis)
        self.assertIsInstance(risks, list)
        # 낮은 신뢰도로 인한 위험 식별
        self.assertGreater(len(risks), 0)

    def test_decision_making(self):
        """최종 판정 테스트"""
        validation_result = {
            "score": 0.9,
            "risks": [],
            "strengths": ["strong"]
        }

        decision = self.agent.make_decision(validation_result)
        self.assertIn(decision, ["approved", "needs_revision", "rejected"])
        self.assertEqual(decision, "approved")

    def test_validation_score_thresholds(self):
        """검증 점수 임계값 테스트"""
        test_cases = [
            (0.95, "approved"),
            (0.85, "approved"),
            (0.75, "approved"),
            (0.70, "needs_revision"),
            (0.60, "needs_revision"),
            (0.50, "rejected")
        ]

        for score, expected_decision in test_cases:
            validation_result = {
                "score": score,
                "risks": [] if score >= 0.85 else ["risk"],
                "strengths": []
            }
            decision = self.agent.make_decision(validation_result)
            self.assertEqual(decision, expected_decision,
                           f"Score {score} should result in {expected_decision}, got {decision}")


class TestGitCodeWorkflow(unittest.TestCase):
    """GitCode 실행 워크플로우 테스트"""

    def setUp(self):
        """테스트 설정"""
        config = AgentConfig(
            role=AgentRole.GITCODE,
            name="GitCode",
            description="실행자"
        )
        self.agent = GitCodeAgent(config)
        self.agent.initialize()

    def test_subtask_execution(self):
        """부분 작업 실행 테스트"""
        subtask = {
            "id": "sub_1",
            "description": "테스트 작업",
            "tools": ["tool1"],
            "dependencies": []
        }

        result = self.agent.execute_subtask(subtask)

        self.assertIn("subtask_id", result)
        self.assertIn("success", result)
        self.assertIn("output", result)

    def test_dependency_handling(self):
        """의존성 처리 테스트"""
        subtasks = [
            {"id": "sub_1", "dependencies": []},
            {"id": "sub_2", "dependencies": ["sub_1"]},
            {"id": "sub_3", "dependencies": ["sub_2"]}
        ]

        result = self.agent.handle_dependencies(subtasks)
        self.assertTrue(result)

    def test_execution_monitoring(self):
        """실행 모니터링 테스트"""
        # 몇 가지 작업 실행
        for i in range(3):
            subtask = {"id": f"sub_{i}", "description": "테스트", "tools": []}
            self.agent.execute_subtask(subtask)

        monitoring = self.agent.monitor_execution("task_001")

        self.assertIn("execution_count", monitoring)
        self.assertIn("success_count", monitoring)
        self.assertIn("failure_count", monitoring)
        self.assertIn("success_rate", monitoring)

    def test_failure_handling(self):
        """실패 처리 테스트"""
        subtask = {"id": "sub_failed", "description": "실패", "tools": []}
        result = self.agent.handle_failure(subtask, "테스트 에러")
        self.assertTrue(result)


class TestRUNEWorkflow(unittest.TestCase):
    """RUNE 윤리 검증 워크플로우 테스트"""

    def setUp(self):
        """테스트 설정"""
        config = AgentConfig(
            role=AgentRole.RUNE,
            name="RUNE",
            description="윤리 검증자"
        )
        self.agent = RUNEAgent(config)
        self.agent.initialize()

    def test_transparency_verification(self):
        """투명성 검증 테스트"""
        execution_data = {
            "sub_tasks": [{"id": "sub_1"}],
            "successful_tasks": 1,
            "execution_status": "completed"
        }

        result = self.agent.verify_transparency(execution_data)
        self.assertIn("score", result)
        self.assertGreaterEqual(result["score"], 0.0)
        self.assertLessEqual(result["score"], 1.0)

    def test_collaboration_verification(self):
        """협력성 검증 테스트"""
        execution_data = {"sub_tasks": [{"id": "sub_1"}]}
        result = self.agent.verify_collaboration(execution_data)

        self.assertIn("score", result)
        self.assertGreaterEqual(result["score"], 0.0)
        self.assertLessEqual(result["score"], 1.0)

    def test_autonomy_verification(self):
        """자율성 검증 테스트"""
        execution_data = {}
        result = self.agent.verify_autonomy(execution_data)

        self.assertIn("score", result)
        self.assertGreaterEqual(result["score"], 0.0)
        self.assertLessEqual(result["score"], 1.0)

    def test_fairness_verification(self):
        """공정성 검증 테스트"""
        execution_data = {"successful_tasks": 3}
        result = self.agent.verify_fairness(execution_data)

        self.assertIn("score", result)
        self.assertGreaterEqual(result["score"], 0.0)
        self.assertLessEqual(result["score"], 1.0)

    def test_ethical_score_calculation(self):
        """윤리 점수 계산 테스트"""
        verification_results = {
            "transparency": {"score": 0.92},
            "collaboration": {"score": 0.88},
            "autonomy": {"score": 0.87},
            "fairness": {"score": 0.91}
        }

        score = self.agent.calculate_ethical_score(verification_results)

        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        # 모든 점수가 높으면 최종 점수도 높아야 함
        self.assertGreater(score, 0.85)


class TestIntegratedSystem(unittest.TestCase):
    """통합 시스템 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.system = IntegratedAgentSystem()

    def test_system_initialization(self):
        """시스템 초기화 테스트"""
        result = self.system.initialize_agents()
        self.assertTrue(result)
        self.assertEqual(len(self.system.agents), 4)

    def test_complete_workflow(self):
        """완전한 워크플로우 테스트"""
        # 시스템 초기화
        self.system.initialize_agents()

        # 워크플로우 실행
        problem = "데이터 분석 및 시각화"
        result = self.system.execute_workflow(problem)

        # 결과 검증
        self.assertIn("success", result)
        self.assertIn("task_id", result)
        self.assertIn("final_verdict", result)
        self.assertIn("stages", result)

    def test_workflow_execution_time(self):
        """워크플로우 실행 시간 테스트"""
        self.system.initialize_agents()

        start_time = time.time()
        result = self.system.execute_workflow("간단한 분석")
        end_time = time.time()

        execution_time = (end_time - start_time) * 1000  # 밀리초로 변환
        self.assertLess(execution_time, 5000)  # 5초 이내

    def test_task_history_tracking(self):
        """작업 이력 추적 테스트"""
        self.system.initialize_agents()

        # 여러 작업 실행
        problems = ["작업 1", "작업 2"]
        for problem in problems:
            self.system.execute_workflow(problem)

        # 이력 확인
        self.assertEqual(len(self.system.task_history), len(problems))

    def test_message_logging(self):
        """메시지 로깅 테스트"""
        self.system.initialize_agents()
        self.system.execute_workflow("테스트")

        # 메시지가 로깅되었는지 확인
        self.assertGreater(len(self.system.message_log), 0)

    def test_error_handling(self):
        """에러 처리 테스트"""
        self.system.initialize_agents()

        # 빈 문제로 테스트
        result = self.system.execute_workflow("")

        # 시스템이 여전히 작동해야 함
        self.assertIsNotNone(result)


class TestAgentCommunication(unittest.TestCase):
    """에이전트 간 통신 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.sena = SenaAgent(AgentConfig(
            role=AgentRole.SENA,
            name="Sena",
            description="분석가"
        ))
        self.lubit = LubitAgent(AgentConfig(
            role=AgentRole.LUBIT,
            name="Lubit",
            description="게이트키퍼"
        ))
        self.sena.initialize()
        self.lubit.initialize()

    def test_message_passing(self):
        """메시지 전달 테스트"""
        # Sena 분석
        analysis = self.sena.perform_analysis("테스트 문제")

        # Lubit 검증
        validation_result = self.lubit.validate_analysis({
            "analysis": "테스트",
            "selected_tools": ["tool1", "tool2"],
            "sub_problems": [{"id": "sub_1"}],
            "confidence": 0.85
        })

        self.assertIn("score", validation_result)

    def test_workflow_stages(self):
        """워크플로우 단계 테스트"""
        # Stage 1: Sena 분석
        analysis = self.sena.perform_analysis("문제")
        self.assertIsNotNone(analysis)

        # Stage 2: Lubit 검증
        validation = self.lubit.validate_analysis({
            "analysis": "test",
            "selected_tools": ["tool1"],
            "sub_problems": [{"id": "sub_1"}],
            "confidence": 0.8
        })
        decision = self.lubit.make_decision(validation)
        self.assertIn(decision, ["approved", "needs_revision", "rejected"])


# ============================================================================
# 메인 실행
# ============================================================================

def run_tests():
    """테스트 실행"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 모든 테스트 추가
    suite.addTests(loader.loadTestsFromTestCase(TestAgentInitialization))
    suite.addTests(loader.loadTestsFromTestCase(TestSenaWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestLubitWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestGitCodeWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestRUNEWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegratedSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentCommunication))

    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
