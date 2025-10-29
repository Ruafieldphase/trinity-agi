"""RUNE + PersonaRouter 통합 테스트"""

from persona_router import PersonaRouter

print("=" * 60)
print("RUNE + PersonaRouter 통합 테스트")
print("=" * 60)

router = PersonaRouter(enable_rune=True)

# 테스트 1: 고품질 응답
print("\n[TEST 1] 고품질 응답 검증")
result1 = router.validate_response_with_rune(
    task_id="test-001",
    query="머신러닝이란?",
    response="머신러닝은 데이터로부터 학습하는 기술입니다. 예를 들어 이미지 분류 모델은 수천 개의 이미지를 학습합니다.",
    persona_used="Elro",
    context={"tools": ["rag"]},
)

print(f"품질: {result1['metrics']['overall_quality']:.2f}")
print(f"재계획: {result1['should_replan']}")
print(f"위험: {result1['risks']}")

# 테스트 2: 저품질 응답
print("\n[TEST 2] 저품질 응답 검증 (재계획 트리거)")
result2 = router.validate_response_with_rune(
    task_id="test-002",
    query="딥러닝과 머신러닝의 차이는?",
    response="아마도 다를 것 같아요.",
    persona_used="Lua",
    context={},
)

print(f"품질: {result2['metrics']['overall_quality']:.2f}")
print(f"재계획: {result2['should_replan']}")
print(f"위험 개수: {len(result2['risks'])}")

print("\n✅ RUNE + PersonaRouter 통합 성공!")
