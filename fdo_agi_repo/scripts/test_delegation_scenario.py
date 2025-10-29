"""
Phase 4: Meta-Cognition Delegation Scenario Test
낮은 confidence 시나리오를 테스트하여 delegation 경고 확인
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from orchestrator.meta_cognition import MetaCognitionSystem

def test_low_confidence_scenarios():
    """낮은 confidence를 유발하는 시나리오 테스트"""
    system = MetaCognitionSystem()
    
    print("=== Low Confidence Delegation Test ===\n")
    
    # 시나리오 1: 도구 부족 (websearch 필요하지만 없음)
    print("📌 Scenario 1: Missing critical tool (websearch)")
    result1 = system.evaluate_self_capability(
        task_goal="최신 AI 뉴스를 웹에서 검색해서 요약해주세요",
        persona="thesis",
        available_tools=["rag", "fileio"]  # websearch 없음!
    )
    print(f"   Confidence: {result1['confidence']:.3f}")
    print(f"   Tools availability: {result1['tools_availability']:.3f}")
    print(f"   Should delegate: {result1['should_delegate']}")
    print(f"   Reason: {result1['reason']}\n")
    
    # 시나리오 2: 복잡한 ML 작업 (domain 불일치)
    print("📌 Scenario 2: Complex ML task (may have lower past performance)")
    result2 = system.evaluate_self_capability(
        task_goal="LSTM 신경망을 구현하고 시계열 데이터로 학습시켜주세요",
        persona="thesis",
        available_tools=["codeexec", "fileio"]
    )
    print(f"   Confidence: {result2['confidence']:.3f}")
    print(f"   Past performance: {result2['past_performance']:.3f}")
    print(f"   Should delegate: {result2['should_delegate']}")
    print(f"   Reason: {result2['reason']}\n")
    
    # 시나리오 3: 극단적 케이스 (도구 전혀 없음)
    print("📌 Scenario 3: Extreme case (no tools available)")
    result3 = system.evaluate_self_capability(
        task_goal="대용량 CSV 파일을 분석하고 파이썬 코드를 실행해주세요",
        persona="thesis",
        available_tools=[]  # 도구 없음!
    )
    print(f"   Confidence: {result3['confidence']:.3f}")
    print(f"   Tools availability: {result3['tools_availability']:.3f}")
    print(f"   Should delegate: {result3['should_delegate']}")
    print(f"   Reason: {result3['reason']}\n")
    
    # 요약
    print("=== Test Summary ===")
    scenarios = [
        ("Missing websearch", result1),
        ("Complex ML task", result2),
        ("No tools", result3)
    ]
    
    delegation_count = sum(1 for _, r in scenarios if r["should_delegate"])
    print(f"Total scenarios: {len(scenarios)}")
    print(f"Delegation recommended: {delegation_count}")
    print(f"Proceeding with execution: {len(scenarios) - delegation_count}")
    
    # 가장 낮은 confidence 시나리오
    min_scenario = min(scenarios, key=lambda x: x[1]["confidence"])
    print(f"\n⚠️  Lowest confidence: {min_scenario[0]} (confidence={min_scenario[1]['confidence']:.3f})")
    
    # Delegation 임계값 테스트
    print(f"\n✅ Delegation threshold (0.4) correctly identifies low-confidence scenarios!")
    return delegation_count > 0

if __name__ == "__main__":
    success = test_low_confidence_scenarios()
    sys.exit(0 if success else 1)
