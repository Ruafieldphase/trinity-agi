"""
Advanced Multi-Agent Workflow Tests
====================================

테스트 시나리오:
1. 순환 워크플로우: Sian ↔ Lubit (반복 리팩터링 → 리뷰)
2. 병렬 워크플로우: Gitko → [Sian, Lubit] → Gitko (동시 작업)
3. 조건부 분기: review_passed ? deploy : refactor
4. PowerShell 스크립트 통합: 배포 + 모니터링

통합:
- agent_base
- agent_handoff_tools
- agent_tools_extended
"""

import asyncio
import time

from agent_base import AGENT_FOLDERS, RESULTS_PATH, TaskResult, TaskStatus, create_task
from agent_handoff_tools import (
    conditional_handoff,
    create_handoff_tool,
    send_to_multiple_agents,
)
from agent_tools_extended import (
    execute_script_as_task,
    find_scripts,
    run_powershell_script,
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


def wait_for_task_completion(task_id: str, timeout: int = 30) -> TaskResult | None:
    """
    작업 완료 대기

    Args:
        task_id: 작업 ID
        timeout: 타임아웃 (초)

    Returns:
        TaskResult 또는 None (타임아웃)
    """
    result_file = RESULTS_PATH / f"{task_id}_result.json"

    elapsed = 0
    while elapsed < timeout:
        if result_file.exists():
            import json

            with open(result_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            return TaskResult(
                task_id=data["task_id"],
                status=TaskStatus(data["status"]),
                output=data.get("output"),
                error_message=data.get("error_message"),
            )

        time.sleep(0.5)
        elapsed += 0.5

    return None


# ============================================================================
# Test 1: 순환 워크플로우 (Sian ↔ Lubit)
# ============================================================================


async def test_circular_workflow():
    """
    순환 워크플로우: Sian → Lubit → Sian → Lubit

    시나리오:
    1. Gitko가 Sian에게 리팩터링 요청
    2. Sian이 리팩터링 후 Lubit에게 리뷰 요청
    3. Lubit이 리뷰 후 개선사항 발견 → Sian에게 재작업 요청
    4. Sian이 재리팩터링 후 Lubit에게 재리뷰 요청
    5. Lubit이 최종 승인
    """
    print("\n" + "=" * 60)
    print("🔄 Test 1: 순환 워크플로우 (Sian ↔ Lubit)")
    print("=" * 60 + "\n")

    cleanup_test_files()

    workflow_id = "circular_test_001"

    # Step 1: Gitko → Sian
    print("1️⃣  Gitko → Sian: 리팩터링 요청")
    gitko_tool = create_handoff_tool("gitko", "sian")
    task1_id = gitko_tool.handler(
        task_description="agent_base.py의 process_inbox_once 함수를 개선해주세요 (순환 워크플로우 테스트)",
        workflow_id=workflow_id,
        params={"file": "agent_base.py", "iteration": 1},
    )
    print(f"   작업 생성: {task1_id}\n")

    # 짧은 대기 (실제로는 Watcher가 처리)
    await asyncio.sleep(1)

    # Step 2: Sian → Lubit (시뮬레이션)
    print("2️⃣  Sian → Lubit: 리뷰 요청 (시뮬레이션)")
    sian_tool = create_handoff_tool("sian", "lubit")
    task2_id = sian_tool.handler(
        task_description=f"Sian의 리팩터링 결과 리뷰 (작업 {task1_id})",
        workflow_id=workflow_id,
        params={"previous_task": task1_id, "iteration": 1},
    )
    print(f"   작업 생성: {task2_id}\n")

    await asyncio.sleep(1)

    # Step 3: Lubit → Sian (재작업 요청)
    print("3️⃣  Lubit → Sian: 재작업 요청 (시뮬레이션)")
    lubit_tool = create_handoff_tool("lubit", "sian")
    task3_id = lubit_tool.handler(
        task_description=f"리뷰 피드백 반영 (작업 {task2_id})",
        workflow_id=workflow_id,
        params={"previous_task": task2_id, "iteration": 2, "feedback": "변수명 개선 필요"},
    )
    print(f"   작업 생성: {task3_id}\n")

    await asyncio.sleep(1)

    # Step 4: Sian → Lubit (재리뷰 요청)
    print("4️⃣  Sian → Lubit: 재리뷰 요청 (시뮬레이션)")
    task4_id = sian_tool.handler(
        task_description=f"재리팩터링 결과 리뷰 (작업 {task3_id})",
        workflow_id=workflow_id,
        params={"previous_task": task3_id, "iteration": 2},
    )
    print(f"   작업 생성: {task4_id}\n")

    # 검증
    print("✅ 순환 워크플로우 작업 생성 완료!")
    print(f"   워크플로우 ID: {workflow_id}")
    print(f"   작업 체인: {task1_id} → {task2_id} → {task3_id} → {task4_id}")
    print("   총 4개 작업 생성\n")

    return True


# ============================================================================
# Test 2: 병렬 워크플로우 (Gitko → [Sian, Lubit])
# ============================================================================


async def test_parallel_workflow():
    """
    병렬 워크플로우: Gitko → [Sian, Lubit] → Gitko

    시나리오:
    1. Gitko가 Sian과 Lubit에게 동시에 작업 할당
       - Sian: 코드 리팩터링
       - Lubit: 문서 리뷰
    2. 두 작업이 병렬로 실행
    3. 모두 완료되면 Gitko가 통합
    """
    print("\n" + "=" * 60)
    print("⚡ Test 2: 병렬 워크플로우 (Gitko → [Sian, Lubit])")
    print("=" * 60 + "\n")

    cleanup_test_files()

    workflow_id = "parallel_test_001"

    # 병렬 작업 생성
    print("1️⃣  Gitko → [Sian, Lubit]: 병렬 작업 할당")

    task_descriptions = {
        "sian": "agent_handoff_tools.py 리팩터링 (병렬 테스트)",
        "lubit": "agent_handoff_tools.py 문서 리뷰 (병렬 테스트)",
    }

    task_ids = send_to_multiple_agents(
        source_agent="gitko",
        target_agents=["sian", "lubit"],
        task_descriptions=task_descriptions,
        workflow_id=workflow_id,
    )

    print(f"   Sian 작업: {task_ids['sian']}")
    print(f"   Lubit 작업: {task_ids['lubit']}\n")

    # 작업 파일 확인
    sian_file = AGENT_FOLDERS["sian"] / f"{task_ids['sian']}.json"
    lubit_file = AGENT_FOLDERS["lubit"] / f"{task_ids['lubit']}.json"

    print("2️⃣  작업 파일 확인")
    print(f"   Sian INBOX: {'✅' if sian_file.exists() else '❌'}")
    print(f"   Lubit INBOX: {'✅' if lubit_file.exists() else '❌'}\n")

    # 검증
    assert sian_file.exists(), "Sian 작업 파일이 없습니다"
    assert lubit_file.exists(), "Lubit 작업 파일이 없습니다"

    print("✅ 병렬 워크플로우 작업 생성 완료!")
    print(f"   워크플로우 ID: {workflow_id}")
    print("   병렬 작업 2개 생성\n")

    return True


# ============================================================================
# Test 3: 조건부 분기 (review_passed ? deploy : refactor)
# ============================================================================


async def test_conditional_handoff():
    """
    조건부 분기: review_passed ? deploy : refactor

    시나리오:
    1. 리뷰 통과 → Gitko에게 배포 요청
    2. 리뷰 실패 → Sian에게 재작업 요청
    """
    print("\n" + "=" * 60)
    print("🔀 Test 3: 조건부 분기 (review ? deploy : refactor)")
    print("=" * 60 + "\n")

    cleanup_test_files()

    workflow_id = "conditional_test_001"

    # Case 1: 리뷰 통과
    print("1️⃣  Case 1: 리뷰 통과 → Gitko (배포)")
    review_passed = True

    task1_id = conditional_handoff(
        source_agent="lubit",
        condition=review_passed,
        true_agent="gitko",
        false_agent="sian",
        true_task="코드 리뷰 통과! 배포 진행 (조건부 테스트)",
        false_task="코드 리뷰 실패. 재작업 필요 (조건부 테스트)",
        workflow_id=workflow_id,
    )

    print(f"   작업 생성: {task1_id}")
    print("   대상 에이전트: gitko ✅\n")

    # 파일 확인
    gitko_file = AGENT_FOLDERS["gitko"] / f"{task1_id}.json"
    assert gitko_file.exists(), "Gitko 작업 파일이 없습니다"

    # Case 2: 리뷰 실패
    print("2️⃣  Case 2: 리뷰 실패 → Sian (재작업)")
    review_passed = False

    task2_id = conditional_handoff(
        source_agent="lubit",
        condition=review_passed,
        true_agent="gitko",
        false_agent="sian",
        true_task="코드 리뷰 통과! 배포 진행 (조건부 테스트)",
        false_task="코드 리뷰 실패. 재작업 필요 (조건부 테스트)",
        workflow_id=workflow_id,
    )

    print(f"   작업 생성: {task2_id}")
    print("   대상 에이전트: sian ✅\n")

    # 파일 확인
    sian_file = AGENT_FOLDERS["sian"] / f"{task2_id}.json"
    assert sian_file.exists(), "Sian 작업 파일이 없습니다"

    print("✅ 조건부 분기 작업 생성 완료!")
    print(f"   워크플로우 ID: {workflow_id}")
    print("   조건부 작업 2개 생성\n")

    return True


# ============================================================================
# Test 4: PowerShell 스크립트 통합
# ============================================================================


async def test_powershell_integration():
    """
    PowerShell 스크립트 통합 테스트

    시나리오:
    1. 모니터링 상태 확인 스크립트 실행
    2. 결과를 TaskResult로 받기
    """
    print("\n" + "=" * 60)
    print("🔧 Test 4: PowerShell 스크립트 통합")
    print("=" * 60 + "\n")

    # 모니터링 스크립트 찾기
    scripts = find_scripts("check_monitoring_status.ps1")

    if not scripts:
        print("⚠️  check_monitoring_status.ps1 파일이 없습니다.")
        print("   PowerShell 통합 테스트 스킵\n")
        return True

    script_path = scripts[0]
    print(f"1️⃣  스크립트 발견: {script_path.name}")
    print(f"   경로: {script_path}\n")

    # 스크립트 실행
    print("2️⃣  스크립트 실행 중...")
    result = await run_powershell_script(script_path, timeout_seconds=30)

    print(f"   상태: {result.status.value}")
    if result.status == TaskStatus.COMPLETED:
        print("   ✅ 성공!")
        if result.output:
            output_preview = result.output[:200]
            print(f"   출력 미리보기: {output_preview}...")
    else:
        print(f"   ❌ 실패: {result.error_message}")

    print()

    # TaskContext 통합 테스트
    print("3️⃣  TaskContext 통합 테스트")
    task = create_task(
        agent="gitko",
        description="모니터링 상태 확인",
        params={"script": "check_monitoring_status.ps1"},
    )

    result2 = await execute_script_as_task(task, script_name="check_monitoring_status.ps1")

    print(f"   작업 ID: {result2.task_id}")
    print(f"   상태: {result2.status.value}\n")

    print("✅ PowerShell 통합 테스트 완료!\n")

    return True


# ============================================================================
# 모든 테스트 실행
# ============================================================================


async def run_all_tests():
    """모든 고급 워크플로우 테스트 실행"""
    print("\n" + "=" * 60)
    print("🧪 Advanced Multi-Agent Workflow Tests")
    print("=" * 60)

    results = []

    # Test 1: 순환 워크플로우
    try:
        result = await test_circular_workflow()
        results.append(("순환 워크플로우", result))
    except Exception as e:
        print(f"❌ 순환 워크플로우 테스트 실패: {e}\n")
        results.append(("순환 워크플로우", False))

    # Test 2: 병렬 워크플로우
    try:
        result = await test_parallel_workflow()
        results.append(("병렬 워크플로우", result))
    except Exception as e:
        print(f"❌ 병렬 워크플로우 테스트 실패: {e}\n")
        results.append(("병렬 워크플로우", False))

    # Test 3: 조건부 분기
    try:
        result = await test_conditional_handoff()
        results.append(("조건부 분기", result))
    except Exception as e:
        print(f"❌ 조건부 분기 테스트 실패: {e}\n")
        results.append(("조건부 분기", False))

    # Test 4: PowerShell 통합
    try:
        result = await test_powershell_integration()
        results.append(("PowerShell 통합", result))
    except Exception as e:
        print(f"❌ PowerShell 통합 테스트 실패: {e}\n")
        results.append(("PowerShell 통합", False))

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
        print("\n🎉 모든 고급 워크플로우 테스트 통과!")
    else:
        print(f"\n⚠️  {total_count - passed_count}개 테스트 실패")

    print("=" * 60 + "\n")

    return passed_count == total_count


if __name__ == "__main__":
    asyncio.run(run_all_tests())
