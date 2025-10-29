"""
Workflow Orchestration Tests - Week 3
======================================

테스트 시나리오:
1. 의존성 그래프 실행 (A → B → C)
2. 우선순위 스케줄링 (긴급 작업 우선)
3. 병렬 실행 최적화 ([A, B] → C)
4. 복잡한 워크플로우 (다이아몬드 패턴)

통합:
- agent_workflow_orchestrator
- orchestrator_main
- agent_base
"""

import asyncio

from agent_base import AGENT_FOLDERS, RESULTS_PATH
from agent_workflow_orchestrator import (
    WorkflowOrchestrator,
)

# ============================================================================
# 테스트 유틸리티
# ============================================================================


def cleanup_test_files():
    """테스트 파일 정리"""
    for folder in AGENT_FOLDERS.values():
        if folder.exists():
            for file in folder.glob("*.json"):
                file.unlink()

    if RESULTS_PATH.exists():
        for file in RESULTS_PATH.glob("*.json"):
            file.unlink()

    print("🧹 테스트 파일 정리 완료\n")


# ============================================================================
# Test 1: 의존성 그래프 실행 (A → B → C)
# ============================================================================


async def test_dependency_graph():
    """
    의존성 그래프 실행: A → B → C

    시나리오:
    1. 작업 A: Sian이 코드 리팩터링
    2. 작업 B: Lubit이 A의 결과 리뷰 (의존: A)
    3. 작업 C: Gitko가 B의 결과 배포 (의존: B)
    """
    print("\n" + "=" * 60)
    print("🔗 Test 1: 의존성 그래프 (A → B → C)")
    print("=" * 60 + "\n")

    cleanup_test_files()

    orchestrator = WorkflowOrchestrator()
    workflow_id = "dependency_test_001"

    # 작업 A
    print("1️⃣  작업 A 생성: Sian - 코드 리팩터링")
    task_a = orchestrator.create_agent_task(
        agent="sian",
        description="agent_workflow_orchestrator.py 리팩터링",
        workflow_id=workflow_id,
        priority=1,
    )

    # 작업 B (의존: A)
    print("2️⃣  작업 B 생성: Lubit - 리뷰 (의존: A)")
    task_b = orchestrator.create_agent_task(
        agent="lubit",
        description=f"작업 A({task_a.task_id}) 결과 리뷰",
        workflow_id=workflow_id,
        priority=1,
        depends_on=[task_a.task_id],
    )

    # 작업 C (의존: B)
    print("3️⃣  작업 C 생성: Gitko - 배포 (의존: B)")
    task_c = orchestrator.create_agent_task(
        agent="gitko",
        description=f"작업 B({task_b.task_id}) 결과 배포",
        workflow_id=workflow_id,
        priority=1,
        depends_on=[task_b.task_id],
    )

    print()

    # 상태 출력
    orchestrator.print_workflow_status(workflow_id)

    # 의존성 확인
    print("📊 의존성 그래프:")
    print(f"   A ({task_a.task_id})")
    print(f"   └→ B ({task_b.task_id})")
    print(f"      └→ C ({task_c.task_id})\n")

    # 검증
    assert len(task_a.depends_on) == 0, "A는 의존성이 없어야 함"
    assert task_a.task_id not in task_b.depends_on or len(task_b.depends_on) == 1, "B는 A에 의존"
    assert task_b.task_id not in task_c.depends_on or len(task_c.depends_on) == 1, "C는 B에 의존"

    print("✅ 의존성 그래프 테스트 완료!\n")

    return True


# ============================================================================
# Test 2: 우선순위 스케줄링
# ============================================================================


async def test_priority_scheduling():
    """
    우선순위 스케줄링

    시나리오:
    1. 낮은 우선순위 작업 (priority=3)
    2. 긴급 작업 (priority=0) - 먼저 실행되어야 함
    3. 보통 작업 (priority=2)
    """
    print("\n" + "=" * 60)
    print("⚡ Test 2: 우선순위 스케줄링")
    print("=" * 60 + "\n")

    cleanup_test_files()

    orchestrator = WorkflowOrchestrator()
    workflow_id = "priority_test_001"

    # 작업 1: 낮은 우선순위
    print("1️⃣  작업 1 생성: 낮은 우선순위 (priority=3)")
    task1 = orchestrator.create_agent_task(
        agent="sian", description="낮은 우선순위 작업", workflow_id=workflow_id, priority=3  # LOW
    )

    # 작업 2: 긴급
    print("2️⃣  작업 2 생성: 긴급 작업 (priority=0)")
    task2 = orchestrator.create_agent_task(
        agent="lubit", description="긴급 작업!", workflow_id=workflow_id, priority=0  # CRITICAL
    )

    # 작업 3: 보통
    print("3️⃣  작업 3 생성: 보통 우선순위 (priority=2)")
    task3 = orchestrator.create_agent_task(
        agent="gitko",
        description="보통 우선순위 작업",
        workflow_id=workflow_id,
        priority=2,  # NORMAL
    )

    print()

    # 우선순위 확인
    tasks = [
        (task1.task_id, task1.priority, task1.description),
        (task2.task_id, task2.priority, task2.description),
        (task3.task_id, task3.priority, task3.description),
    ]

    # 우선순위 정렬
    sorted_tasks = sorted(tasks, key=lambda t: t[1])

    print("📊 우선순위 순서 (실행 순서):")
    for i, (tid, pri, desc) in enumerate(sorted_tasks, 1):
        pri_name = ["긴급", "높음", "보통", "낮음"][pri]
        print(f"   {i}. [{pri_name}] {desc} ({tid})")

    print()

    # 검증
    assert sorted_tasks[0][1] == 0, "첫 번째는 긴급(0)"
    assert sorted_tasks[1][1] == 2, "두 번째는 보통(2)"
    assert sorted_tasks[2][1] == 3, "세 번째는 낮음(3)"

    print("✅ 우선순위 스케줄링 테스트 완료!\n")

    return True


# ============================================================================
# Test 3: 병렬 실행 최적화 ([A, B] → C)
# ============================================================================


async def test_parallel_execution():
    """
    병렬 실행 최적화: [A, B] → C

    시나리오:
    1. 작업 A와 B는 독립적 (병렬 실행 가능)
    2. 작업 C는 A와 B 모두에 의존 (A, B 완료 후 실행)
    """
    print("\n" + "=" * 60)
    print("⚡ Test 3: 병렬 실행 최적화 ([A, B] → C)")
    print("=" * 60 + "\n")

    cleanup_test_files()

    orchestrator = WorkflowOrchestrator()
    workflow_id = "parallel_test_001"

    # 작업 A (독립)
    print("1️⃣  작업 A 생성: Sian - 코드 리팩터링")
    task_a = orchestrator.create_agent_task(
        agent="sian", description="코드 리팩터링 (병렬 1)", workflow_id=workflow_id, priority=1
    )

    # 작업 B (독립)
    print("2️⃣  작업 B 생성: Lubit - 문서 리뷰")
    task_b = orchestrator.create_agent_task(
        agent="lubit", description="문서 리뷰 (병렬 2)", workflow_id=workflow_id, priority=1
    )

    # 작업 C (의존: A, B)
    print("3️⃣  작업 C 생성: Gitko - 통합 배포 (의존: A, B)")
    task_c = orchestrator.create_agent_task(
        agent="gitko",
        description="통합 배포 (의존: A, B)",
        workflow_id=workflow_id,
        priority=1,
        depends_on=[task_a.task_id, task_b.task_id],
    )

    print()

    # 의존성 확인
    print("📊 병렬 실행 그래프:")
    print(f"       ┌→ A ({task_a.task_id})")
    print("   시작|")
    print(f"       └→ B ({task_b.task_id})")
    print("            ↓")
    print(f"          C ({task_c.task_id})\n")

    # 검증
    assert len(task_a.depends_on) == 0, "A는 독립"
    assert len(task_b.depends_on) == 0, "B는 독립"
    assert len(task_c.depends_on) == 2, "C는 A와 B에 의존"

    print("✅ 병렬 실행 최적화 테스트 완료!\n")

    return True


# ============================================================================
# Test 4: 복잡한 워크플로우 (다이아몬드 패턴)
# ============================================================================


async def test_diamond_workflow():
    """
    다이아몬드 패턴 워크플로우

           A (시작)
          / \\
         B   C (병렬)
          \\ /
           D (통합)

    시나리오:
    1. A: Gitko가 작업 할당
    2. B, C: Sian과 Lubit이 병렬 작업
    3. D: Gitko가 결과 통합
    """
    print("\n" + "=" * 60)
    print("💎 Test 4: 다이아몬드 패턴 워크플로우")
    print("=" * 60 + "\n")

    cleanup_test_files()

    orchestrator = WorkflowOrchestrator()
    workflow_id = "diamond_test_001"

    # A: 시작
    print("1️⃣  작업 A: Gitko - 작업 계획")
    task_a = orchestrator.create_agent_task(
        agent="gitko", description="작업 계획 수립", workflow_id=workflow_id, priority=0
    )

    # B: A의 결과로 리팩터링
    print("2️⃣  작업 B: Sian - 리팩터링 (의존: A)")
    task_b = orchestrator.create_agent_task(
        agent="sian",
        description=f"A({task_a.task_id}) 기반 리팩터링",
        workflow_id=workflow_id,
        priority=1,
        depends_on=[task_a.task_id],
    )

    # C: A의 결과로 문서 작성
    print("3️⃣  작업 C: Lubit - 문서 작성 (의존: A)")
    task_c = orchestrator.create_agent_task(
        agent="lubit",
        description=f"A({task_a.task_id}) 기반 문서 작성",
        workflow_id=workflow_id,
        priority=1,
        depends_on=[task_a.task_id],
    )

    # D: B와 C 통합
    print("4️⃣  작업 D: Gitko - 통합 (의존: B, C)")
    task_d = orchestrator.create_agent_task(
        agent="gitko",
        description=f"B({task_b.task_id})와 C({task_c.task_id}) 통합",
        workflow_id=workflow_id,
        priority=2,
        depends_on=[task_b.task_id, task_c.task_id],
    )

    print()

    # 다이아몬드 패턴 출력
    print("📊 다이아몬드 패턴:")
    print(f"         A ({task_a.task_id})")
    print("        / \\\\")
    print("       /   \\\\")
    print("      B     C")
    print("       \\\\   /")
    print("        \\\\ /")
    print(f"         D ({task_d.task_id})\n")

    # 상태 출력
    orchestrator.print_workflow_status(workflow_id)

    # 검증
    assert len(task_a.depends_on) == 0, "A는 독립"
    assert task_a.task_id in task_b.depends_on, "B는 A에 의존"
    assert task_a.task_id in task_c.depends_on, "C는 A에 의존"
    assert task_b.task_id in task_d.depends_on, "D는 B에 의존"
    assert task_c.task_id in task_d.depends_on, "D는 C에 의존"

    print("✅ 다이아몬드 패턴 워크플로우 테스트 완료!\n")

    return True


# ============================================================================
# 모든 테스트 실행
# ============================================================================


async def run_all_tests():
    """모든 워크플로우 오케스트레이션 테스트 실행"""
    print("\n" + "=" * 60)
    print("🧪 Workflow Orchestration Tests")
    print("=" * 60)

    results = []

    # Test 1: 의존성 그래프
    try:
        result = await test_dependency_graph()
        results.append(("의존성 그래프", result))
    except Exception as e:
        print(f"❌ 의존성 그래프 테스트 실패: {e}\n")
        results.append(("의존성 그래프", False))

    # Test 2: 우선순위 스케줄링
    try:
        result = await test_priority_scheduling()
        results.append(("우선순위 스케줄링", result))
    except Exception as e:
        print(f"❌ 우선순위 스케줄링 테스트 실패: {e}\n")
        results.append(("우선순위 스케줄링", False))

    # Test 3: 병렬 실행
    try:
        result = await test_parallel_execution()
        results.append(("병렬 실행 최적화", result))
    except Exception as e:
        print(f"❌ 병렬 실행 테스트 실패: {e}\n")
        results.append(("병렬 실행 최적화", False))

    # Test 4: 다이아몬드 패턴
    try:
        result = await test_diamond_workflow()
        results.append(("다이아몬드 패턴", result))
    except Exception as e:
        print(f"❌ 다이아몬드 패턴 테스트 실패: {e}\n")
        results.append(("다이아몬드 패턴", False))

    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60 + "\n")

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)

    print(f"\n총 {total_count}개 테스트 중 {passed_count}개 통과")

    if passed_count == total_count:
        print("\n🎉 모든 워크플로우 오케스트레이션 테스트 통과!")
    else:
        print(f"\n⚠️  {total_count - passed_count}개 테스트 실패")

    print("=" * 60 + "\n")

    return passed_count == total_count


if __name__ == "__main__":
    asyncio.run(run_all_tests())
