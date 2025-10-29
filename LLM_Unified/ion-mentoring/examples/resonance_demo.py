"""
파동키 변환 시스템 데모

이 스크립트는 ResonanceConverter의 실제 작동을 시연합니다.
- 오프라인 모드: 로컬 키워드 기반 분석
- 온라인 모드: Vertex AI를 활용한 고급 감정 분석

Author: ION Mentoring Program
Date: 2025-10-17
"""

import importlib.util
import os
import types


def load_module(module_name: str, file_path: str) -> types.ModuleType:
    """동적으로 모듈 로드"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec and spec.loader, f"Failed to load {module_name}"
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def setup_paths():
    """필요한 모듈 경로 설정"""
    here = os.path.dirname(__file__)
    parent_dir = os.path.abspath(os.path.join(here, ".."))

    # ResonanceConverter 모듈 로드
    rc_path = os.path.join(parent_dir, "resonance_converter.py")
    rc = load_module("resonance_converter", rc_path)

    # PromptClient 모듈 로드
    pc_path = os.path.join(parent_dir, "prompt_client.py")
    pc = load_module("prompt_client", pc_path)

    return rc, pc


def run_offline_demo(ResonanceConverter):
    """오프라인 모드 데모"""
    print("\n" + "=" * 60)
    print("🔧 오프라인 모드 (로컬 키워드 기반 분석)")
    print("=" * 60)

    converter = ResonanceConverter()

    test_inputs = [
        "이 코드가 왜 안 돌아가는 거야?! 답답해!",
        "혹시 이 부분을 개선할 방법이 있을까요?",
        "데이터 분석 결과를 확인해주세요.",
        "와! 이거 정말 멋진데요! 어떻게 만든 거예요?",
        "빨리 해결해야 해요. 급합니다!",
    ]

    for i, text in enumerate(test_inputs, 1):
        print(f'\n[{i}] 입력: "{text}"')

        result = converter.convert(text)

        print(f"   📏 리듬: {result['rhythm'].pace}")
        print(f"      - 평균 문장 길이: {result['rhythm'].avg_sentence_length:.1f} 단어")
        print(f"      - 문장부호 밀도: {result['rhythm'].punctuation_density:.2%}")
        print(f"      - 질문 비율: {result['rhythm'].question_ratio:.1f}")
        print(f"      - 느낌표 비율: {result['rhythm'].exclamation_ratio:.1f}")

        print(f"   🎭 감정: {result['emotion'].primary}")
        print(f"      - 신뢰도: {result['emotion'].confidence:.2%}")
        if result["emotion"].secondary:
            print(f"      - 부차 감정: {result['emotion'].secondary}")

        print(f"   🎯 파동키: {result['resonance_key']}")


def run_online_demo(ResonanceConverter, create_default_vertex_prompt_client):
    """온라인 모드 데모 (Vertex AI)"""
    print("\n" + "=" * 60)
    print("☁️ 온라인 모드 (Vertex AI 통합)")
    print("=" * 60)

    # 환경 변수 체크
    if not os.getenv("GOOGLE_CLOUD_PROJECT") and not os.getenv("GCP_PROJECT"):
        print("\n⚠️ 환경 변수가 설정되지 않았습니다.")
        print("온라인 모드를 사용하려면 다음을 설정하세요:")
        print("  - GOOGLE_CLOUD_PROJECT 또는 GCP_PROJECT")
        print("  - GOOGLE_APPLICATION_CREDENTIALS")
        print("\n오프라인 모드로 계속합니다...\n")
        return None

    try:
        # Vertex AI 클라이언트 생성
        vertex_client = create_default_vertex_prompt_client()
        vertex_client.initialize().load()

        print("\n✅ Vertex AI 연결 성공!")
        print(f"   {vertex_client.info()}\n")

        # ResonanceConverter 생성 (Vertex AI 통합)
        converter = ResonanceConverter(vertex_client=vertex_client)

        test_inputs = [
            "데이터 분석 결과를 확인해주세요.",
            "이 시스템의 아키텍처를 천천히 살펴보면 흥미롭습니다.",
        ]

        for i, text in enumerate(test_inputs, 1):
            print(f'[{i}] 입력: "{text}"')

            result = converter.convert(text)

            print(
                f"   📏 리듬: {result['rhythm'].pace} ({result['rhythm'].avg_sentence_length:.1f} 단어)"
            )
            print(
                f"   🎭 감정: {result['emotion'].primary} (신뢰도: {result['emotion'].confidence:.2%})"
            )
            print(f"   🎯 파동키: {result['resonance_key']}\n")

        return converter

    except Exception as e:
        print(f"\n⚠️ Vertex AI 연결 실패: {e}")
        print("오프라인 모드로 폴백합니다...\n")
        return None


def interactive_mode(converter):
    """대화형 모드"""
    print("\n" + "=" * 60)
    print("💬 대화형 모드 (직접 입력해보세요)")
    print("=" * 60)
    print("종료하려면 'quit' 또는 'exit'를 입력하세요.\n")

    while True:
        try:
            user_input = input("입력 > ").strip()

            if user_input.lower() in ["quit", "exit", "종료", ""]:
                print("👋 데모를 종료합니다.")
                break

            result = converter.convert(user_input)

            print(f"  📏 리듬: {result['rhythm'].pace}")
            print(f"  🎭 감정: {result['emotion'].primary} ({result['emotion'].confidence:.2%})")
            print(f"  🎯 파동키: {result['resonance_key']}\n")

        except KeyboardInterrupt:
            print("\n\n👋 데모를 종료합니다.")
            break
        except Exception as e:
            print(f"  ⚠️ 오류: {e}\n")


def main():
    """메인 함수"""
    print("\n" + "=" * 60)
    print("🎵 파동키 변환 시스템 데모")
    print("   ResonanceConverter - ION Mentoring Day 3")
    print("=" * 60)

    # 모듈 로드
    rc, pc = setup_paths()
    ResonanceConverter = rc.ResonanceConverter
    create_default_vertex_prompt_client = pc.create_default_vertex_prompt_client

    # 오프라인 데모 실행
    run_offline_demo(ResonanceConverter)

    # 온라인 데모 시도
    online_converter = run_online_demo(ResonanceConverter, create_default_vertex_prompt_client)

    # 대화형 모드
    converter = online_converter if online_converter else ResonanceConverter()

    try:
        interactive_mode(converter)
    except Exception as e:
        print(f"\n⚠️ 대화형 모드 오류: {e}")

    print("\n✨ 데모 완료!")


if __name__ == "__main__":
    main()
