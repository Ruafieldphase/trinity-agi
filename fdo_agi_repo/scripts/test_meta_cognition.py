"""
Meta-Cognition 시스템 테스트
"""
import sys
import os

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from orchestrator.meta_cognition import (
    MetaCognitionSystem,
    select_best_persona_for_task,
    infer_task_domain,
    check_tools_availability
)


def test_domain_inference():
    """도메인 추론 테스트"""
    print("=== Domain Inference Test ===")
    
    test_cases = [
        ("Python 리스트 컴프리헨션 설명", "python"),
        ("머신러닝과 딥러닝의 차이", "ml"),
        ("데이터 분석 방법론", "data"),
        ("AGI 자기교정 루프 설명", "general"),
    ]
    
    for goal, expected in test_cases:
        result = infer_task_domain(goal)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{goal[:30]}...' → {result} (expected: {expected})")
    print()


def test_tools_availability():
    """도구 가용성 테스트"""
    print("=== Tools Availability Test ===")
    
    available_tools = ["rag", "fileio", "codeexec"]
    
    test_cases = [
        ("문서에서 정보 검색", 1.0),  # rag 필요, 있음
        ("웹에서 최신 뉴스 찾기", 0.0),  # websearch 필요, 없음
        ("Python 코드 실행", 1.0),  # codeexec 필요, 있음
        ("AGI 설명", 1.0),  # 특정 도구 불필요
    ]
    
    for goal, expected in test_cases:
        result = check_tools_availability(goal, available_tools)
        status = "✅" if abs(result - expected) < 0.1 else "❌"
        print(f"{status} '{goal}' → {result:.2f} (expected: {expected:.2f})")
    print()


def test_self_capability_evaluation():
    """자기 능력 평가 테스트"""
    print("=== Self Capability Evaluation Test ===")
    
    system = MetaCognitionSystem()
    available_tools = ["rag", "fileio", "codeexec", "tabular"]
    
    test_cases = [
        ("Python 리스트 컴프리헨션 설명", "thesis"),
        ("머신러닝 모델 평가", "antithesis"),
        ("프로젝트 요약 작성", "synthesis"),
    ]
    
    for goal, persona in test_cases:
        result = system.evaluate_self_capability(
            task_goal=goal,
            persona=persona,
            available_tools=available_tools
        )
        
        print(f"\n작업: {goal}")
        print(f"Persona: {persona}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Past Performance: {result['past_performance']:.2f}")
        print(f"  Tools Availability: {result['tools_availability']:.2f}")
        print(f"  Domain: {result['domain']}")
        print(f"  Should Delegate: {result['should_delegate']}")
        print(f"  Reason: {result['reason']}")
    print()


def test_best_persona_selection():
    """최적 Persona 선택 테스트"""
    print("=== Best Persona Selection Test ===")
    
    available_tools = ["rag", "fileio", "codeexec"]
    task_goal = "AGI 자기개선 메커니즘을 3단계로 설명"
    
    best_persona, evaluations = select_best_persona_for_task(
        task_goal=task_goal,
        available_tools=available_tools
    )
    
    print(f"작업: {task_goal}")
    print(f"\n최적 Persona: {best_persona} ⭐")
    print("\n모든 Persona 평가:")
    
    for persona, eval_result in sorted(
        evaluations.items(),
        key=lambda x: x[1]["confidence"],
        reverse=True
    ):
        marker = "⭐" if persona == best_persona else "  "
        print(f"{marker} {persona}: confidence={eval_result['confidence']:.2f}")
    print()


def main():
    """전체 테스트 실행"""
    print("\n" + "="*60)
    print("  Meta-Cognition System Test Suite")
    print("  AGI Phase 4: Self-Capability Evaluation")
    print("="*60 + "\n")
    
    try:
        test_domain_inference()
        test_tools_availability()
        test_self_capability_evaluation()
        test_best_persona_selection()
        
        print("="*60)
        print("✅ All tests completed!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
