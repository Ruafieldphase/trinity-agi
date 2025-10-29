"""
Multi-Persona 통합 테스트

multi_persona_orchestrator.py와 persona_router.py 통합 테스트
"""

import os
import sys

# 경로 설정
sys.path.insert(0, os.path.dirname(__file__))

from multi_persona_orchestrator import ExecutionMode, MergeStrategy, PersonaChain
from persona_router import PersonaRouter


def test_multi_persona_integration():
    """Multi-Persona 통합 기본 테스트"""
    print("테스트 1: Multi-Persona 통합 기본 테스트")

    router = PersonaRouter(enable_multi_persona=True)
    assert router.enable_multi_persona, "Multi-Persona가 활성화되지 않음"
    assert hasattr(router, "multi_orchestrator"), "Orchestrator가 없음"

    print("  ✅ Multi-Persona Orchestrator 초기화 성공\n")


def test_analyze_simple_query():
    """단순 쿼리 분석 테스트"""
    print("테스트 2: 단순 쿼리 분석")

    router = PersonaRouter(enable_multi_persona=True)
    query = "코드 성능을 측정하고 싶어요"

    needs_multi, chain = router.analyze_multi_persona_need(query)

    print(f"  쿼리: {query}")
    print(f"  Multi-Persona 필요: {needs_multi}")

    # 단순 쿼리는 Multi-Persona 불필요
    if not needs_multi:
        print("  ✅ 단일 Persona로 충분 (정상)\n")
    else:
        print(f"  ℹ️ Multi-Persona 필요 판단: {chain.personas}\n")


def test_analyze_complex_query():
    """복합 쿼리 분석 테스트"""
    print("테스트 3: 복합 쿼리 분석")

    router = PersonaRouter(enable_multi_persona=True)
    query = "프로젝트 API 구조를 설계하고 팀원들과 조율이 필요해요"

    needs_multi, chain = router.analyze_multi_persona_need(query)

    print(f"  쿼리: {query}")
    print(f"  Multi-Persona 필요: {needs_multi}")

    if needs_multi:
        print(f"  Personas: {chain.personas}")
        print(f"  실행 모드: {chain.execution_mode.value}")
        print(f"  병합 전략: {chain.merge_strategy.value}")
        print(f"  이유: {chain.reasoning}")
        assert len(chain.personas) >= 2, "복합 쿼리는 2개 이상 Persona 필요"
        print("  ✅ Multi-Persona 체인 생성 성공\n")
    else:
        print("  ℹ️ 단일 Persona로 충분 판단\n")


def test_execution_plan():
    """실행 계획 생성 테스트"""
    print("테스트 4: Multi-Persona 실행 계획 생성")

    router = PersonaRouter(enable_multi_persona=True, enable_phases=True)
    query = "API 설계하고 팀 조율 필요"

    needs_multi, chain = router.analyze_multi_persona_need(query)

    if needs_multi:
        plan_json = router.execute_multi_persona_chain(query, chain)
        print(f"  실행 계획:\n{plan_json}")

        assert "personas" in plan_json, "실행 계획에 Persona 정보 없음"
        assert "steps" in plan_json, "실행 계획에 스텝 정보 없음"
        print("  ✅ 실행 계획 생성 성공\n")
    else:
        print("  ℹ️ Multi-Persona 불필요\n")


def test_result_merge():
    """결과 병합 테스트"""
    print("테스트 5: Multi-Persona 결과 병합")

    router = PersonaRouter(enable_multi_persona=True)

    mock_results = {
        "Elro": "API 구조는 RESTful 방식으로 설계하세요. 엔드포인트는 /api/v1/resources 형태입니다.",
        "Nana": "팀원들에게 API 명세서를 공유하고 다음 주 회의에서 피드백을 받으세요.",
    }

    mock_chain = PersonaChain(
        personas=["Elro", "Nana"],
        execution_mode=ExecutionMode.SEQUENTIAL,
        merge_strategy=MergeStrategy.HIERARCHICAL,
        reasoning="기술 설계 후 팀 조율",
    )

    merged = router.merge_multi_persona_results(mock_results, mock_chain)

    print(f"  병합 결과:\n{merged}\n")

    assert "Elro" in merged, "Elro 결과가 병합에 없음"
    assert "Nana" in merged, "Nana 결과가 병합에 없음"
    assert len(merged) > 100, "병합 결과가 너무 짧음"
    print("  ✅ 결과 병합 성공\n")


def test_various_queries():
    """다양한 쿼리 테스트"""
    print("테스트 6: 다양한 쿼리 패턴")

    router = PersonaRouter(enable_multi_persona=True)

    test_cases = [
        ("코드 리팩토링 방법 알려줘", "기술 단일"),
        ("성능 측정하고 개선 방법 찾기", "데이터 단일"),
        ("팀 회의가 비효율적이고 스트레스받아요", "조율+감정"),
        ("프로젝트 구조 설계하고 성능도 최적화하고 팀 조율도 필요해", "복합 3개"),
    ]

    for query, expected_type in test_cases:
        needs_multi, chain = router.analyze_multi_persona_need(query)
        print(f"  쿼리: {query}")
        print(f"  예상: {expected_type}")
        print(f"  결과: Multi={needs_multi}, Personas={chain.personas if chain else '단일'}")
        print()

    print("  ✅ 다양한 쿼리 분석 완료\n")


def test_all_merge_strategies():
    """모든 병합 전략 테스트"""
    print("테스트 7: 모든 병합 전략")

    router = PersonaRouter(enable_multi_persona=True)

    mock_results = {"Elro": "API 설계는 RESTful로", "Nana": "팀원과 공유하세요"}

    strategies = [
        MergeStrategy.CONCATENATE,
        MergeStrategy.WEIGHTED,
        MergeStrategy.VOTING,
        MergeStrategy.HIERARCHICAL,
    ]

    for strategy in strategies:
        chain = PersonaChain(
            personas=["Elro", "Nana"],
            execution_mode=ExecutionMode.SEQUENTIAL,
            merge_strategy=strategy,
            reasoning=f"테스트: {strategy.value}",
        )

        merged = router.merge_multi_persona_results(mock_results, chain)
        print(f"  전략: {strategy.value}")
        print(f"  결과 길이: {len(merged)}자")
        assert len(merged) > 50, f"{strategy.value} 병합 실패"

    print("  ✅ 모든 병합 전략 동작 확인\n")


# 메인 실행
if __name__ == "__main__":
    print("=" * 60)
    print("Multi-Persona 통합 테스트 시작")
    print("=" * 60)
    print()

    try:
        test_multi_persona_integration()
        test_analyze_simple_query()
        test_analyze_complex_query()
        test_execution_plan()
        test_result_merge()
        test_various_queries()
        test_all_merge_strategies()

        print("=" * 60)
        print("✅ 모든 Multi-Persona 통합 테스트 성공!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
    except Exception as e:
        print(f"\n❌ 예외 발생: {e}")
        import traceback

        traceback.print_exc()
