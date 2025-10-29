"""
내다AI 파동키 기반 페르소나 라우팅 데모

이 스크립트는 ResonanceConverter와 PersonaRouter를 통합하여
사용자 입력 → 파동키 분석 → 페르소나 선택 흐름을 보여줍니다.

Week 2 Day 4 완료 후 통합 테스트용.
"""

import sys
from pathlib import Path

# 상위 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from persona_router import PersonaRouter
from resonance_converter import ResonanceConverter


def demo_routing_flow():
    """통합 라우팅 흐름 시연"""

    print("=" * 70)
    print("🌊 내다AI 통합 파동키 라우팅 데모")
    print("=" * 70)
    print()

    # 컴포넌트 초기화
    converter = ResonanceConverter()
    router = PersonaRouter()

    # 테스트 시나리오
    test_cases = [
        {"user_input": "이 문제를 빨리 해결해야 해요! 답답해요!", "description": "급한 감정 표현"},
        {
            "user_input": "이 현상이 왜 발생하는지 논리적으로 분석해주세요.",
            "description": "논리적 분석 요청",
        },
        {
            "user_input": "데이터를 보니까 패턴이 보이는데, 좀 더 자세히 알려주세요.",
            "description": "분석적 탐구",
        },
        {
            "user_input": "마음이 불편해요... 어떻게 해야 할지 모르겠어요.",
            "description": "감정적 고민",
        },
        {"user_input": "여러 관점을 종합해서 설명해주시겠어요?", "description": "종합적 조정 요청"},
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n{'─'*70}")
        print(f"📝 시나리오 {i}: {case['description']}")
        print(f"{'─'*70}")
        print(f"사용자 입력: \"{case['user_input']}\"")
        print()

        # Step 1: 리듬 분석
        rhythm = converter.analyze_rhythm(case["user_input"])
        print("🎵 리듬 분석:")
        print(f"   - 평균 문장 길이: {rhythm.avg_sentence_length:.1f}")
        print(f"   - 속도: {rhythm.pace}")
        print(f"   - 문장부호 밀도: {rhythm.punctuation_density:.2f}")
        print()

        # Step 2: 감정 톤 분석
        tone = converter.detect_emotion_tone(case["user_input"])
        print("💭 감정 톤 분석:")
        print(f"   - 주요 감정: {tone.primary}")
        print(f"   - 신뢰도: {tone.confidence:.2f}")
        if tone.secondary:
            print(f"   - 보조 감정: {tone.secondary}")
        print()

        # Step 3: 파동키 생성
        resonance_key = converter.generate_resonance_key(rhythm, tone)
        print(f"🔑 생성된 파동키: {resonance_key}")
        print()

        # Step 4: 페르소나 라우팅
        routing_result = router.route(resonance_key)
        print("🎯 페르소나 라우팅 결과:")
        print(
            f"   - 1순위: {routing_result.primary_persona} (신뢰도: {routing_result.confidence:.2f})"
        )
        if routing_result.secondary_persona:
            print(f"   - 2순위: {routing_result.secondary_persona}")
        print(f"   - 선택 이유: {routing_result.reasoning}")
        print()

        # 선택된 페르소나 정보
        selected_persona = router.get_persona_config(routing_result.primary_persona)
        if selected_persona:
            print(f"👤 선택된 페르소나 '{selected_persona.name}' 특성:")
            print(f"   - 주요 강점: {', '.join(selected_persona.strengths[:3])}")
            print(f"   - 선호하는 톤: {', '.join(selected_persona.preferred_tones[:3])}")
            print(f"   - 프롬프트 스타일: {selected_persona.prompt_style[:60]}...")

        print()

    print("=" * 70)
    print("✅ 데모 완료!")
    print("=" * 70)
    print()
    print("💡 학습 포인트:")
    print("   1. 사용자 입력 → 리듬/톤 분석 → 파동키 생성 → 페르소나 선택 흐름 확인")
    print("   2. 각 시나리오마다 다른 페르소나가 선택되는 것을 관찰")
    print("   3. 파동키 형식: [감정]-[속도]-[의도]")
    print("   4. 라우팅 시스템이 컨텍스트에 맞는 페르소나를 자동 선택")
    print()


def interactive_mode():
    """대화형 모드: 사용자가 직접 입력"""

    converter = ResonanceConverter()
    router = PersonaRouter()

    print("=" * 70)
    print("🌊 내다AI 대화형 라우팅 데모")
    print("=" * 70)
    print("사용자 입력을 받아 실시간으로 페르소나를 선택합니다.")
    print("종료하려면 'quit' 또는 'exit'를 입력하세요.")
    print("=" * 70)
    print()

    while True:
        user_input = input("📝 입력하세요: ").strip()

        if user_input.lower() in ["quit", "exit", "종료"]:
            print("\n👋 데모를 종료합니다.")
            break

        if not user_input:
            continue

        print()

        # 파동키 분석 및 라우팅
        rhythm = converter.analyze_rhythm(user_input)
        tone = converter.detect_emotion_tone(user_input)
        resonance_key = converter.generate_resonance_key(rhythm, tone)
        routing_result = router.route(resonance_key)

        print(f"🔑 파동키: {resonance_key}")
        print(
            f"🎯 선택된 페르소나: {routing_result.primary_persona} (신뢰도: {routing_result.confidence:.2f})"
        )
        print(f"💬 선택 이유: {routing_result.reasoning}")

        selected_persona = router.get_persona_config(routing_result.primary_persona)
        if selected_persona:
            print(f"✨ 응답 스타일: {selected_persona.prompt_style[:80]}...")

        print()
        print("─" * 70)
        print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="내다AI 파동키 라우팅 데모")
    parser.add_argument("--interactive", "-i", action="store_true", help="대화형 모드로 실행")

    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
    else:
        demo_routing_flow()
