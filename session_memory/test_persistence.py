#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터 영속성 테스트 - Agent System 데이터 저장 및 조회

이 모듈은 데이터베이스 모델, 마이그레이션, 영속성 통합 레이어를 테스트합니다.
"""

import sys
import io
import unittest
from datetime import datetime

from database_models import (
    DatabaseManager, Agent, Task, Message, HealthRecord, AgentMetrics,
    SystemMetrics, Workflow, AgentRole, TaskStatus, MessageType,
    AgentRepository, TaskRepository, MessageRepository
)
from database_migration import MigrationManager, MigrationVersion
from persistence_integration import PersistenceService

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================================
# 데이터베이스 모델 테스트
# ============================================================================

class TestDatabaseModels(unittest.TestCase):
    """데이터베이스 모델 테스트"""

    def setUp(self):
        """테스트 초기화"""
        self.db = DatabaseManager()
        self.db.initialize()
        self.session = self.db.get_session()

    def tearDown(self):
        """테스트 정리"""
        self.session.close()
        self.db.close()

    def test_agent_creation(self):
        """에이전트 생성 테스트"""
        agent_repo = AgentRepository(self.session)
        agent = agent_repo.create_agent("agent_test", "Test Agent", AgentRole.SENA, "테스트")

        self.assertIsNotNone(agent)
        self.assertEqual(agent.agent_id, "agent_test")
        self.assertEqual(agent.name, "Test Agent")
        self.assertEqual(agent.role, AgentRole.SENA)

    def test_task_creation(self):
        """작업 생성 테스트"""
        task_repo = TaskRepository(self.session)
        task = task_repo.create_task(
            task_id="task_test",
            workflow_id="wf_test",
            agent_id="agent_test",
            description="테스트 작업",
            priority=5,
            input_data={"key": "value"}
        )

        self.assertIsNotNone(task)
        self.assertEqual(task.task_id, "task_test")
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.priority, 5)

    def test_task_status_update(self):
        """작업 상태 업데이트 테스트"""
        task_repo = TaskRepository(self.session)
        task_repo.create_task(
            task_id="task_update",
            workflow_id="wf_test",
            agent_id="agent_test",
            description="테스트"
        )

        task_repo.update_task_status(
            task_id="task_update",
            status=TaskStatus.COMPLETED,
            output_data={"result": "success"},
            duration_ms=100.5
        )

        task = task_repo.get_task("task_update")
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertEqual(task.duration_ms, 100.5)

    def test_message_creation(self):
        """메시지 생성 테스트"""
        message_repo = MessageRepository(self.session)

        # 먼저 에이전트 생성
        agent_repo = AgentRepository(self.session)
        agent_repo.create_agent("agent_from", "From", AgentRole.SENA)
        agent_repo.create_agent("agent_to", "To", AgentRole.LUBIT)

        # 메시지 생성
        message = message_repo.create_message(
            message_id="msg_test",
            from_agent_id="agent_from",
            to_agent_id="agent_to",
            message_type=MessageType.TASK_REQUEST,
            content={"task": "test"},
            task_id="task_1"
        )

        self.assertIsNotNone(message)
        self.assertEqual(message.from_agent_id, "agent_from")
        self.assertEqual(message.message_type, MessageType.TASK_REQUEST)

    def test_health_record_creation(self):
        """헬스 체크 기록 생성 테스트"""
        health = HealthRecord(
            health_id="health_test",
            component="agent_sena",
            status="healthy",
            message="테스트 건강도",
            response_time_ms=2.5
        )
        self.session.add(health)
        self.session.commit()

        retrieved = self.session.query(HealthRecord).filter_by(health_id="health_test").first()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.status, "healthy")

    def test_agent_metrics_creation(self):
        """에이전트 메트릭 생성 테스트"""
        metrics = AgentMetrics(
            metric_id="metric_test",
            agent_id="agent_sena",
            total_tasks=10,
            completed_tasks=9,
            failed_tasks=1,
            success_rate=0.9
        )
        self.session.add(metrics)
        self.session.commit()

        retrieved = self.session.query(AgentMetrics).filter_by(metric_id="metric_test").first()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.success_rate, 0.9)


# ============================================================================
# 마이그레이션 테스트
# ============================================================================

class TestMigration(unittest.TestCase):
    """마이그레이션 테스트"""

    def setUp(self):
        """테스트 초기화"""
        self.manager = MigrationManager("sqlite:///:memory:")

    def test_initial_migration(self):
        """초기 마이그레이션 테스트"""
        success = self.manager.migrate_up(target_version=1)
        self.assertTrue(success)

        versions = self.manager.get_applied_versions()
        self.assertIn(1, versions)

    def test_upgrade_migration(self):
        """마이그레이션 업그레이드 테스트"""
        success = self.manager.migrate_up(target_version=3)
        self.assertTrue(success)

        versions = self.manager.get_applied_versions()
        self.assertEqual(len(versions), 3)
        self.assertEqual(self.manager.get_latest_version(), 3)

    def test_downgrade_migration(self):
        """마이그레이션 다운그레이드 테스트"""
        # 먼저 업그레이드
        self.manager.migrate_up(target_version=3)

        # 다운그레이드
        success = self.manager.migrate_down(target_version=1)
        self.assertTrue(success)

        versions = self.manager.get_applied_versions()
        self.assertEqual(self.manager.get_latest_version(), 1)


# ============================================================================
# 영속성 통합 테스트
# ============================================================================

class TestPersistenceIntegration(unittest.TestCase):
    """영속성 통합 테스트"""

    def setUp(self):
        """테스트 초기화"""
        self.persistence = PersistenceService()

    def tearDown(self):
        """테스트 정리"""
        self.persistence.close()

    def test_agent_registration(self):
        """에이전트 등록 테스트"""
        result = self.persistence.register_agent(
            "agent_test",
            "Test Agent",
            "sena",
            "테스트 에이전트"
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["agent_id"], "agent_test")

    def test_get_agent_info(self):
        """에이전트 정보 조회 테스트"""
        # 에이전트 등록
        self.persistence.register_agent("agent_test", "Test", "sena")

        # 정보 조회
        agent_info = self.persistence.get_agent_info("agent_test")
        self.assertIsNotNone(agent_info)
        self.assertEqual(agent_info["name"], "Test")
        self.assertEqual(agent_info["role"], "sena")

    def test_create_workflow(self):
        """워크플로우 생성 테스트"""
        result = self.persistence.create_workflow(
            description="테스트 워크플로우",
            input_data={"test": "data"}
        )

        self.assertTrue(result["success"])
        self.assertIn("workflow_id", result)

    def test_create_task(self):
        """작업 생성 테스트"""
        # 워크플로우 생성
        wf_result = self.persistence.create_workflow()
        workflow_id = wf_result["workflow_id"]

        # 작업 생성
        result = self.persistence.create_task(
            workflow_id=workflow_id,
            agent_id="agent_test",
            description="테스트 작업",
            priority=10
        )

        self.assertTrue(result["success"])
        self.assertIn("task_id", result)

    def test_update_task_status(self):
        """작업 상태 업데이트 테스트"""
        # 워크플로우 및 작업 생성
        wf_result = self.persistence.create_workflow()
        task_result = self.persistence.create_task(
            workflow_id=wf_result["workflow_id"],
            agent_id="agent_test",
            description="테스트"
        )
        task_id = task_result["task_id"]

        # 상태 업데이트
        result = self.persistence.update_task_status(
            task_id=task_id,
            status="completed",
            output_data={"result": "success"},
            duration_ms=100.0
        )

        self.assertTrue(result["success"])

    def test_log_message(self):
        """메시지 로깅 테스트"""
        # 에이전트 등록
        self.persistence.register_agent("agent_from", "From", "sena")
        self.persistence.register_agent("agent_to", "To", "lubit")

        # 메시지 로깅
        result = self.persistence.log_message(
            from_agent_id="agent_from",
            to_agent_id="agent_to",
            message_type="task_request",
            content={"task": "test"}
        )

        self.assertTrue(result["success"])
        self.assertIn("message_id", result)

    def test_health_check_logging(self):
        """헬스 체크 로깅 테스트"""
        result = self.persistence.log_health_check(
            component="agent_sena",
            status="healthy",
            message="정상 작동",
            response_time_ms=2.5
        )

        self.assertTrue(result["success"])
        self.assertIn("health_id", result)

    def test_agent_metrics_update(self):
        """에이전트 메트릭 업데이트 테스트"""
        result = self.persistence.update_agent_metrics(
            agent_id="agent_sena",
            total_tasks=10,
            completed_tasks=9,
            failed_tasks=1,
            success_rate=0.9
        )

        self.assertTrue(result["success"])
        self.assertIn("metric_id", result)

    def test_system_metrics_logging(self):
        """시스템 메트릭 로깅 테스트"""
        result = self.persistence.log_system_metrics(
            total_workflows=5,
            completed_workflows=4,
            total_tasks=20,
            completed_tasks=18,
            cpu_usage_percent=35.5
        )

        self.assertTrue(result["success"])
        self.assertIn("system_metric_id", result)

    def test_get_all_agents(self):
        """모든 에이전트 조회 테스트"""
        # 여러 에이전트 등록
        self.persistence.register_agent("agent_1", "Agent 1", "sena")
        self.persistence.register_agent("agent_2", "Agent 2", "lubit")

        # 조회
        agents = self.persistence.get_all_agents()
        self.assertGreaterEqual(len(agents), 2)

    def test_get_workflow_tasks(self):
        """워크플로우 작업 조회 테스트"""
        # 워크플로우 및 작업 생성
        wf_result = self.persistence.create_workflow()
        workflow_id = wf_result["workflow_id"]

        task1 = self.persistence.create_task(
            workflow_id=workflow_id,
            agent_id="agent_1",
            description="작업1"
        )
        task2 = self.persistence.create_task(
            workflow_id=workflow_id,
            agent_id="agent_2",
            description="작업2"
        )

        # 조회
        tasks = self.persistence.get_workflow_tasks(workflow_id)
        self.assertEqual(len(tasks), 2)


# ============================================================================
# 종합 테스트
# ============================================================================

class TestIntegration(unittest.TestCase):
    """종합 통합 테스트"""

    def setUp(self):
        """테스트 초기화"""
        self.persistence = PersistenceService()

    def tearDown(self):
        """테스트 정리"""
        self.persistence.close()

    def test_complete_workflow(self):
        """완전한 워크플로우 테스트"""
        # 1. 에이전트 등록
        self.persistence.register_agent("agent_sena", "Sena", "sena")
        self.persistence.register_agent("agent_lubit", "Lubit", "lubit")

        # 2. 워크플로우 생성
        wf_result = self.persistence.create_workflow(
            description="데이터 분석",
            input_data={"problem": "분석 요청"}
        )
        workflow_id = wf_result["workflow_id"]

        # 3. 작업 생성
        task_result = self.persistence.create_task(
            workflow_id=workflow_id,
            agent_id="agent_sena",
            description="분석 수행",
            priority=10
        )
        task_id = task_result["task_id"]

        # 4. 작업 상태 업데이트
        self.persistence.update_task_status(
            task_id=task_id,
            status="completed",
            output_data={"result": "분석 완료"},
            duration_ms=150.5
        )

        # 5. 메시지 로깅
        self.persistence.log_message(
            from_agent_id="agent_sena",
            to_agent_id="agent_lubit",
            message_type="task_response",
            content={"status": "완료"},
            task_id=task_id
        )

        # 6. 헬스 체크 로깅
        self.persistence.log_health_check(
            component="agent_sena",
            status="healthy",
            response_time_ms=2.5,
            agent_id="agent_sena"
        )

        # 7. 메트릭 업데이트
        self.persistence.update_agent_metrics(
            agent_id="agent_sena",
            total_tasks=10,
            completed_tasks=9,
            success_rate=0.9
        )

        # 8. 데이터 검증
        workflow_tasks = self.persistence.get_workflow_tasks(workflow_id)
        self.assertEqual(len(workflow_tasks), 1)
        self.assertEqual(workflow_tasks[0]["status"], "completed")

        agents = self.persistence.get_all_agents()
        self.assertGreaterEqual(len(agents), 2)


# ============================================================================
# 성능 테스트
# ============================================================================

class TestPerformance(unittest.TestCase):
    """성능 테스트"""

    def setUp(self):
        """테스트 초기화"""
        self.persistence = PersistenceService()

    def tearDown(self):
        """테스트 정리"""
        self.persistence.close()

    def test_bulk_agent_creation(self):
        """대량 에이전트 생성 테스트"""
        import time

        start_time = time.time()

        for i in range(100):
            self.persistence.register_agent(
                f"agent_{i}",
                f"Agent {i}",
                "sena" if i % 4 == 0 else "lubit" if i % 4 == 1 else "gitcode"
            )

        duration_ms = (time.time() - start_time) * 1000

        agents = self.persistence.get_all_agents()
        self.assertGreaterEqual(len(agents), 100)
        print(f"✓ 100개 에이전트 생성: {duration_ms:.1f}ms")

    def test_bulk_task_creation(self):
        """대량 작업 생성 테스트"""
        import time

        wf_result = self.persistence.create_workflow()
        workflow_id = wf_result["workflow_id"]

        start_time = time.time()

        for i in range(50):
            self.persistence.create_task(
                workflow_id=workflow_id,
                agent_id="agent_sena",
                description=f"작업 {i}",
                priority=i % 10
            )

        duration_ms = (time.time() - start_time) * 1000

        tasks = self.persistence.get_workflow_tasks(workflow_id)
        self.assertEqual(len(tasks), 50)
        print(f"✓ 50개 작업 생성: {duration_ms:.1f}ms")


# ============================================================================
# 테스트 실행
# ============================================================================

def run_tests():
    """테스트 실행"""
    print("=" * 80)
    print("데이터 영속성 테스트")
    print("=" * 80)

    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 테스트 추가
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseModels))
    suite.addTests(loader.loadTestsFromTestCase(TestMigration))
    suite.addTests(loader.loadTestsFromTestCase(TestPersistenceIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))

    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 결과 요약
    print("\n" + "=" * 80)
    print("테스트 결과 요약")
    print("=" * 80)
    print(f"실행: {result.testsRun}")
    print(f"성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"실패: {len(result.failures)}")
    print(f"오류: {len(result.errors)}")
    print(f"성공률: {(result.testsRun - len(result.failures) - len(result.errors))/result.testsRun*100:.1f}%")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
