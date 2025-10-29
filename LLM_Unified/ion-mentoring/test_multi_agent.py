"""
Multi-Agent System 테스트
==========================

테스트 시나리오:
1. 기본 INBOX 통신 테스트
2. Agent 간 Handoff 테스트
3. 워크플로우 컨텍스트 공유 테스트
"""

import asyncio
import uuid

from agent_base import (
    RESULTS_PATH,
    create_task,
    wait_for_result_async,
)
from agent_implementations import GitkoAgent, LubitAgent, SianAgent


async def test_basic_inbox_communication():
    """
    테스트 1: 기본 INBOX 통신

    Gitko → Sian: 작업 전달
    Sian: 작업 처리
    Gitko: 결과 확인
    """
    print("\n" + "=" * 60)
    print("테스트 1: 기본 INBOX 통신")
    print("=" * 60)

    # 에이전트 생성
    gitko = GitkoAgent()
    sian = SianAgent()

    # Gitko가 Sian에게 작업 전달
    task = create_task(
        agent="sian", description="함수 리팩터링: calculate_total() 개선", created_by="gitko"
    )

    print("\n1️⃣  Gitko → Sian 작업 전달")
    gitko.dispatch_to_agent("sian", task)

    # Sian이 작업 처리
    print("\n2️⃣  Sian 작업 처리")
    result = await sian.process_inbox_once()
    print(f"   처리된 작업 개수: {result}")

    # Gitko가 결과 확인
    print("\n3️⃣  Gitko 결과 확인")
    task_result = await wait_for_result_async(task.task_id, timeout_seconds=10)

    if task_result:
        print("   ✅ 작업 완료!")
        print(f"   상태: {task_result.status.value}")
        print(f"   결과: {task_result.output}")
    else:
        print("   ❌ 타임아웃")

    return task_result is not None


async def test_handoff_workflow():
    """
    테스트 2: Agent 간 Handoff

    Gitko → Sian: "코드 개선 후 리뷰 요청"
    Sian → Lubit: "개선된 코드 리뷰해주세요" (자동 Handoff)
    Lubit: 리뷰 완료
    Gitko: 전체 워크플로우 결과 확인
    """
    print("\n" + "=" * 60)
    print("테스트 2: Agent 간 Handoff 워크플로우")
    print("=" * 60)

    # 에이전트 생성
    gitko = GitkoAgent()
    sian = SianAgent()
    lubit = LubitAgent()

    workflow_id = str(uuid.uuid4())

    # Gitko가 Sian에게 작업 전달 (review 키워드 포함 → Handoff 트리거)
    task = create_task(
        agent="sian",
        description="코드 개선 후 review 요청",
        workflow_id=workflow_id,
        created_by="gitko",
    )

    print(f"\n1️⃣  Gitko → Sian 작업 전달 (workflow_id: {workflow_id[:8]}...)")
    gitko.dispatch_to_agent("sian", task)

    # Sian 작업 처리 (자동으로 Lubit에게 Handoff)
    print("\n2️⃣  Sian 작업 처리 (Lubit으로 자동 Handoff 예정)")
    await sian.process_inbox_once()

    # Sian 결과 확인
    sian_result = await wait_for_result_async(task.task_id, timeout_seconds=5)
    if sian_result:
        print(f"   ✅ Sian 완료: {sian_result.output}")
        if sian_result.next_agent:
            print(f"   ➡️  다음 에이전트: {sian_result.next_agent}")

    # Lubit 작업 처리
    print("\n3️⃣  Lubit 작업 처리")
    await asyncio.sleep(0.5)  # Handoff 파일 생성 대기
    await lubit.process_inbox_once()

    # 모든 결과 확인
    print("\n4️⃣  전체 결과 확인")
    all_results = list(RESULTS_PATH.glob("*_result.json"))
    print(f"   생성된 결과 파일: {len(all_results)}개")
    for result_file in all_results:
        print(f"   - {result_file.name}")

    return len(all_results) >= 2


async def test_context_sharing():
    """
    테스트 3: 워크플로우 컨텍스트 공유

    Sian: Context에 데이터 저장
    Lubit: Context에서 데이터 읽기
    Gitko: 전체 Context 확인
    """
    print("\n" + "=" * 60)
    print("테스트 3: 워크플로우 컨텍스트 공유")
    print("=" * 60)

    # 에이전트 생성
    sian = SianAgent()
    lubit = LubitAgent()
    gitko = GitkoAgent()

    workflow_id = str(uuid.uuid4())

    # Sian이 Context에 데이터 저장
    print("\n1️⃣  Sian: Context에 데이터 저장")
    sian.save_to_context(
        workflow_id,
        {
            "sian_refactoring": {
                "functions_extracted": 3,
                "lines_reduced": 45,
                "type_hints_added": True,
            }
        },
    )
    print("   ✅ 저장 완료")

    # Lubit이 Context에 데이터 추가
    print("\n2️⃣  Lubit: Context에 데이터 추가")
    lubit.save_to_context(workflow_id, {"lubit_review": {"status": "approved", "issues_found": 0}})
    print("   ✅ 저장 완료")

    # Gitko가 전체 Context 읽기
    print("\n3️⃣  Gitko: 전체 Context 읽기")
    context = gitko.load_from_context(workflow_id)

    print("   워크플로우 컨텍스트:")
    for key, value in context.items():
        print(f"   - {key}: {value}")

    has_both = "sian_refactoring" in context and "lubit_review" in context
    print(f"\n   {'✅' if has_both else '❌'} 양측 데이터 확인")

    return has_both


async def test_all():
    """모든 테스트 실행"""
    print("\n🚀 Multi-Agent System 통합 테스트 시작\n")

    results = {
        "기본 INBOX 통신": await test_basic_inbox_communication(),
        "Handoff 워크플로우": await test_handoff_workflow(),
        "컨텍스트 공유": await test_context_sharing(),
    }

    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 모든 테스트 통과!")
    else:
        print("⚠️  일부 테스트 실패")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    # 테스트 실행
    asyncio.run(test_all())
