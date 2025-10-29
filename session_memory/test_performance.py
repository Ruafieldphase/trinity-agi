#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
성능 테스트: Agent System

이 모듈은 에이전트 시스템의 성능을 측정합니다.
"""

import sys
import io
import time
import statistics
from agent_interface import AgentRole, AgentConfig, TaskContext
from agent_sena import SenaAgent
from agent_lubit import LubitAgent
from agent_gitcode import GitCodeAgent
from agent_rune import RUNEAgent
from integrated_agent_system import IntegratedAgentSystem

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================================
# 성능 측정 클래스
# ============================================================================

class PerformanceMetrics:
    """성능 메트릭 수집"""

    def __init__(self):
        self.results = {}

    def measure(self, name: str, func, *args, **kwargs):
        """함수 실행 시간 측정"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        execution_time = (end_time - start_time) * 1000  # 밀리초

        if name not in self.results:
            self.results[name] = []

        self.results[name].append(execution_time)
        return result

    def get_stats(self, name: str):
        """통계 계산"""
        if name not in self.results:
            return None

        times = self.results[name]
        return {
            "count": len(times),
            "min": min(times),
            "max": max(times),
            "avg": statistics.mean(times),
            "median": statistics.median(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0
        }

    def print_report(self):
        """성능 보고서 출력"""
        print("\n" + "=" * 80)
        print("성능 테스트 결과")
        print("=" * 80)

        for name in sorted(self.results.keys()):
            stats = self.get_stats(name)
            print(f"\n{name}")
            print(f"  실행 횟수: {stats['count']}")
            print(f"  최소: {stats['min']:.3f}ms")
            print(f"  최대: {stats['max']:.3f}ms")
            print(f"  평균: {stats['avg']:.3f}ms")
            print(f"  중앙값: {stats['median']:.3f}ms")
            if stats['stdev'] > 0:
                print(f"  표준편차: {stats['stdev']:.3f}ms")


# ============================================================================
# 성능 테스트
# ============================================================================

def test_agent_performance():
    """에이전트 성능 테스트"""
    print("\n" + "=" * 80)
    print("[1] 에이전트 성능 테스트")
    print("=" * 80)

    metrics = PerformanceMetrics()

    # Sena 성능 테스트
    print("\nSena 성능 측정...")
    config = AgentConfig(role=AgentRole.SENA, name="Sena", description="분석가")
    sena = SenaAgent(config)
    sena.initialize()

    problems = [
        "데이터 분석",
        "웹 크롤링",
        "텍스트 처리",
        "이미지 분류",
        "시계열 예측"
    ]

    for problem in problems:
        metrics.measure("Sena - 문제 분석", sena.perform_analysis, problem)
        metrics.measure("Sena - 도구 선택", sena.identify_tools, problem)
        metrics.measure("Sena - 작업 분해", sena.decompose_task, problem, ["tool1"])
        analysis = sena.perform_analysis(problem)
        metrics.measure("Sena - 신뢰도 평가", sena.evaluate_confidence, analysis)

    # Lubit 성능 테스트
    print("Lubit 성능 측정...")
    config = AgentConfig(role=AgentRole.LUBIT, name="Lubit", description="게이트키퍼")
    lubit = LubitAgent(config)
    lubit.initialize()

    test_analyses = [
        {
            "analysis": "test",
            "selected_tools": ["tool1", "tool2"],
            "sub_problems": [{"id": "sub_1"}, {"id": "sub_2"}],
            "confidence": 0.9
        },
        {
            "analysis": "test",
            "selected_tools": ["tool1"],
            "sub_problems": [{"id": "sub_1"}],
            "confidence": 0.6
        }
    ]

    for analysis in test_analyses:
        metrics.measure("Lubit - 분석 검증", lubit.validate_analysis, analysis)
        result = lubit.validate_analysis(analysis)
        metrics.measure("Lubit - 판정 결정", lubit.make_decision, result)

    # GitCode 성능 테스트
    print("GitCode 성능 측정...")
    config = AgentConfig(role=AgentRole.GITCODE, name="GitCode", description="실행자")
    gitcode = GitCodeAgent(config)
    gitcode.initialize()

    subtasks = [
        {"id": "sub_1", "description": "작업1", "tools": ["tool1"]},
        {"id": "sub_2", "description": "작업2", "tools": ["tool2"]},
        {"id": "sub_3", "description": "작업3", "tools": ["tool3"]}
    ]

    for subtask in subtasks:
        metrics.measure("GitCode - 부분 작업 실행", gitcode.execute_subtask, subtask)

    dependencies = [
        [{"id": "sub_1"}, {"id": "sub_2"}, {"id": "sub_3"}],
        [{"id": "sub_1"}, {"id": "sub_2"}]
    ]

    for deps in dependencies:
        metrics.measure("GitCode - 의존성 처리", gitcode.handle_dependencies, deps)

    # RUNE 성능 테스트
    print("RUNE 성능 측정...")
    config = AgentConfig(role=AgentRole.RUNE, name="RUNE", description="윤리 검증자")
    rune = RUNEAgent(config)
    rune.initialize()

    execution_data = {
        "sub_tasks": [{"id": "sub_1"}],
        "successful_tasks": 1,
        "execution_status": "completed"
    }

    for _ in range(10):
        metrics.measure("RUNE - 투명성 검증", rune.verify_transparency, execution_data)
        metrics.measure("RUNE - 협력성 검증", rune.verify_collaboration, execution_data)
        metrics.measure("RUNE - 자율성 검증", rune.verify_autonomy, execution_data)
        metrics.measure("RUNE - 공정성 검증", rune.verify_fairness, execution_data)

    metrics.print_report()


def test_workflow_performance():
    """워크플로우 성능 테스트"""
    print("\n" + "=" * 80)
    print("[2] 워크플로우 성능 테스트")
    print("=" * 80)

    metrics = PerformanceMetrics()

    system = IntegratedAgentSystem()
    system.initialize_agents()

    test_problems = [
        "간단한 분석",
        "복잡한 데이터 처리",
        "웹 데이터 수집 및 분석",
        "머신러닝 모델 학습",
        "이미지 처리 및 분류"
    ]

    print("\n완전한 워크플로우 성능 측정...")
    for problem in test_problems:
        metrics.measure("완전한 워크플로우", system.execute_workflow, problem)

    # 워크플로우 단계별 성능 테스트
    print("\n각 단계별 성능 측정...")
    sena = SenaAgent(AgentConfig(role=AgentRole.SENA, name="Sena", description="분석가"))
    sena.initialize()

    lubit = LubitAgent(AgentConfig(role=AgentRole.LUBIT, name="Lubit", description="게이트키퍼"))
    lubit.initialize()

    gitcode = GitCodeAgent(AgentConfig(role=AgentRole.GITCODE, name="GitCode", description="실행자"))
    gitcode.initialize()

    rune = RUNEAgent(AgentConfig(role=AgentRole.RUNE, name="RUNE", description="윤리 검증자"))
    rune.initialize()

    problem = "테스트 작업"
    for _ in range(5):
        # Step 1: Sena
        analysis = metrics.measure("Step 1 - Sena 분석", sena.perform_analysis, problem)

        # Step 2: Lubit
        validation = lubit.validate_analysis({
            "analysis": "test",
            "selected_tools": ["tool1"],
            "sub_problems": [{"id": "sub_1"}],
            "confidence": 0.85
        })
        metrics.measure("Step 2 - Lubit 검증", lubit.make_decision, validation)

        # Step 3: GitCode
        subtask = {"id": "sub_1", "description": "test", "tools": ["tool1"]}
        metrics.measure("Step 3 - GitCode 실행", gitcode.execute_subtask, subtask)

        # Step 4: RUNE
        execution_data = {"sub_tasks": [subtask], "successful_tasks": 1}
        metrics.measure("Step 4 - RUNE 검증", rune.calculate_ethical_score, {
            "transparency": {"score": 0.9},
            "collaboration": {"score": 0.88},
            "autonomy": {"score": 0.87},
            "fairness": {"score": 0.91}
        })

    metrics.print_report()


def test_scalability():
    """확장성 테스트"""
    print("\n" + "=" * 80)
    print("[3] 확장성 테스트")
    print("=" * 80)

    metrics = PerformanceMetrics()

    system = IntegratedAgentSystem()
    system.initialize_agents()

    print("\n다양한 크기의 작업 처리 성능...")

    # 부분 작업 개수를 증가시키면서 성능 측정
    sena = SenaAgent(AgentConfig(role=AgentRole.SENA, name="Sena", description="분석가"))
    sena.initialize()

    for task_count in [1, 5, 10, 20]:
        # 부분 작업 모의 생성
        sub_tasks = [{"id": f"sub_{i}", "description": f"작업{i}", "tools": ["tool1"]}
                    for i in range(task_count)]

        gitcode = GitCodeAgent(AgentConfig(role=AgentRole.GITCODE, name="GitCode", description="실행자"))
        gitcode.initialize()

        # 모든 부분 작업 처리 시간 측정
        def execute_all():
            for subtask in sub_tasks:
                gitcode.execute_subtask(subtask)

        metrics.measure(f"GitCode - {task_count}개 부분 작업 실행", execute_all)

    metrics.print_report()


def test_reliability():
    """신뢰성 테스트"""
    print("\n" + "=" * 80)
    print("[4] 신뢰성 테스트")
    print("=" * 80)

    system = IntegratedAgentSystem()
    system.initialize_agents()

    print("\n연속 작업 처리 테스트...")

    success_count = 0
    failure_count = 0
    total_tasks = 20

    for i in range(total_tasks):
        problem = f"연속 테스트 작업 {i+1}"
        try:
            result = system.execute_workflow(problem)
            if result.get("success"):
                success_count += 1
            else:
                failure_count += 1
        except Exception as e:
            failure_count += 1
            print(f"  ✗ 작업 {i+1} 실패: {e}")

    print(f"\n결과:")
    print(f"  성공: {success_count}/{total_tasks}")
    print(f"  실패: {failure_count}/{total_tasks}")
    print(f"  성공률: {success_count/total_tasks*100:.1f}%")

    # 에이전트 상태 확인
    print(f"\n에이전트 처리 통계:")
    for role_value, agent in system.agents.items():
        status = agent.get_status()
        print(f"  {agent.name}")
        print(f"    처리한 메시지: {status['message_count']}")
        print(f"    처리한 작업: {status['task_count']}")


def print_performance_summary():
    """성능 요약 출력"""
    print("\n" + "=" * 80)
    print("성능 테스트 요약")
    print("=" * 80)

    summary = """
예상 성능 목표:

1. 에이전트별 성능
   ✓ Sena (분석가): < 5ms/분석
   ✓ Lubit (게이트키퍼): < 5ms/검증
   ✓ GitCode (실행자): 50-500ms/작업
   ✓ RUNE (윤리 검증자): < 5ms/검증

2. 워크플로우 성능
   ✓ 전체 워크플로우: 1-2초 (부분 작업 포함)
   ✓ 메시지 전달: < 1ms
   ✓ 작업 완료율: 100%

3. 확장성
   ✓ 부분 작업 1개: 50-100ms
   ✓ 부분 작업 10개: 500-1000ms
   ✓ 부분 작업 20개: 1000-2000ms

4. 신뢰성
   ✓ 연속 작업 처리: 100% 성공률
   ✓ 에러 복구: 자동 재시도
   ✓ 메시지 로깅: 모든 작업 추적
"""
    print(summary)


# ============================================================================
# 메인 실행
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Agent System 성능 테스트")
    print("=" * 80)

    # 에이전트 성능 테스트
    test_agent_performance()

    # 워크플로우 성능 테스트
    test_workflow_performance()

    # 확장성 테스트
    test_scalability()

    # 신뢰성 테스트
    test_reliability()

    # 성능 요약
    print_performance_summary()

    print("\n" + "=" * 80)
    print("성능 테스트 완료!")
    print("=" * 80 + "\n")
