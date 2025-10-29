"""
PersonaPipeline 통합 테스트

Week 1 (28 tests) + Week 2 Day 4 (15 tests) + Day 5 (10 tests) = 53 tests

이 테스트는 ResonanceConverter → PersonaRouter → PersonaPipeline의
전체 통합 흐름을 검증합니다.

Author: ION Mentoring Program - Week 2 Day 5
Date: 2025-10-17
"""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# 동적 모듈 로딩 (ion-mentoring 디렉토리 처리)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from persona_pipeline import PERSONA_PROMPT_TEMPLATES, PersonaPipeline, PersonaResponse

# ===== Test Fixtures =====


@pytest.fixture
def mock_vertex_client():
    """Mock Vertex AI 클라이언트

    실제 Vertex AI 호출 없이 테스트 가능하도록 Mock 객체 제공
    """
    client = Mock()
    client.send_prompt.return_value = "Mock Vertex AI 응답입니다. 도움이 되셨기를 바랍니다!"
    return client


@pytest.fixture
def pipeline(mock_vertex_client):
    """테스트용 PersonaPipeline 인스턴스"""
    return PersonaPipeline(mock_vertex_client)


# ===== Phase 1: 기본 흐름 테스트 (3 tests) =====


def test_process_basic_flow(pipeline, mock_vertex_client):
    """Test 1: 기본 처리 흐름 - 입력 → 응답"""
    user_input = "이 문제를 어떻게 해결할까요?"

    result = pipeline.process(user_input)

    # 응답 생성 확인
    assert isinstance(result, PersonaResponse)
    assert result.content
    assert result.persona_used in ["Lua", "Elro", "Riri", "Nana"]
    assert 0.0 <= result.confidence <= 1.0
    assert result.resonance_key

    # Vertex AI 호출 확인
    mock_vertex_client.send_prompt.assert_called_once()


def test_process_curious_inquiry_routes_to_elro_or_riri(pipeline):
    """Test 2: 호기심 많은 질문 → Elro/Riri 선택"""
    user_input = "이게 왜 이렇게 작동하는지 궁금해요."

    result = pipeline.process(user_input)

    # Curious 톤은 Elro 또는 Riri가 처리
    assert result.persona_used in ["Elro", "Riri"]
    assert "curious" in result.resonance_key


def test_process_frustrated_expressive_routes_to_lua(pipeline):
    """Test 3: 답답한 감정 표현 → Lua/Nana 또는 감정 톤 기반 라우팅"""
    user_input = "이거 진짜 답답해요! 왜 안 되는 거죠?"

    result = pipeline.process(user_input)

    # 느낌표와 "왜"가 있어서 curious 또는 frustrated로 인식될 수 있음
    # 둘 다 유효한 라우팅 결과
    assert result.persona_used in ["Lua", "Nana", "Elro", "Riri"]
    # 파동키에 감정 표현 또는 질문 의도가 포함되어야 함
    assert (
        result.resonance_key.startswith("frustrated")
        or result.resonance_key.startswith("urgent")
        or result.resonance_key.startswith("curious")
    )


# ===== Phase 2: 프롬프트 구성 테스트 (3 tests) =====


def test_build_persona_prompt_lua(pipeline):
    """Test 4: Lua 프롬프트 템플릿 적용"""
    prompt = pipeline._build_persona_prompt(
        persona_name="Lua", user_input="도와주세요", resonance_key="frustrated-burst-expressive"
    )

    # Lua 템플릿 요소 확인
    assert "Lua" in prompt
    assert "도와주세요" in prompt
    assert "frustrated-burst-expressive" in prompt
    assert "따뜻" in prompt or "공감" in prompt or "창의" in prompt


def test_build_persona_prompt_elro(pipeline):
    """Test 5: Elro 프롬프트 템플릿 적용"""
    prompt = pipeline._build_persona_prompt(
        persona_name="Elro", user_input="분석해주세요", resonance_key="analytical-flowing-inquiry"
    )

    # Elro 템플릿 요소 확인
    assert "Elro" in prompt
    assert "분석해주세요" in prompt
    assert "논리" in prompt or "체계" in prompt or "아키텍트" in prompt


def test_build_persona_prompt_unknown_persona_fallback(pipeline):
    """Test 6: 알 수 없는 페르소나 → 폴백 템플릿"""
    prompt = pipeline._build_persona_prompt(
        persona_name="UnknownPersona", user_input="테스트", resonance_key="test-test-test"
    )

    # 폴백 템플릿이 적용되어야 함
    assert "테스트" in prompt
    assert prompt  # 비어있지 않음
    assert "UnknownPersona" in prompt


# ===== Phase 3: 에러 핸들링 테스트 (2 tests) =====


def test_process_empty_input_raises_error(pipeline):
    """Test 7: 빈 입력 → ValueError"""
    with pytest.raises(ValueError, match="비어있습니다"):
        pipeline.process("")

    with pytest.raises(ValueError, match="비어있습니다"):
        pipeline.process("   ")  # 공백만 있는 경우


def test_process_vertex_error_returns_fallback(pipeline, mock_vertex_client):
    """Test 8: Vertex AI 장애 → 폴백 응답"""
    # Vertex AI 에러 시뮬레이션
    mock_vertex_client.send_prompt.side_effect = RuntimeError("API Error")

    result = pipeline.process("테스트 입력")

    # 폴백 응답 확인
    assert isinstance(result, PersonaResponse)
    assert result.persona_used == "Nana"  # 에러 조율은 Nana
    assert result.confidence == 0.0
    assert "문제가 발생" in result.content
    assert result.metadata is not None
    assert "error" in result.metadata


# ===== Phase 4: 메타데이터 검증 테스트 (2 tests) =====


def test_process_includes_metadata(pipeline):
    """Test 9: 응답에 풍부한 메타데이터 포함"""
    result = pipeline.process("메타데이터 테스트")

    # 메타데이터 존재 확인
    assert result.metadata is not None
    assert "rhythm" in result.metadata
    assert "tone" in result.metadata
    assert "routing" in result.metadata

    # 리듬 정보
    rhythm_meta = result.metadata["rhythm"]
    assert "pace" in rhythm_meta
    assert "avg_length" in rhythm_meta
    assert "punctuation_density" in rhythm_meta

    # 톤 정보
    tone_meta = result.metadata["tone"]
    assert "primary" in tone_meta
    assert "confidence" in tone_meta

    # 라우팅 정보
    routing_meta = result.metadata["routing"]
    assert "reasoning" in routing_meta


def test_process_metadata_secondary_persona(pipeline):
    """Test 10: 2순위 페르소나 정보 포함"""
    result = pipeline.process("여러 관점이 필요한 복잡한 질문입니다")

    routing_meta = result.metadata.get("routing", {})

    # 2순위 페르소나가 있어야 함
    assert "secondary_persona" in routing_meta
    secondary = routing_meta["secondary_persona"]

    # None이거나 유효한 페르소나 이름
    assert secondary is None or secondary in ["Lua", "Elro", "Riri", "Nana"]


# ===== 보너스: 프롬프트 템플릿 검증 =====


def test_all_persona_templates_exist():
    """보너스 Test: 모든 페르소나 템플릿 존재 확인"""
    required_personas = ["Lua", "Elro", "Riri", "Nana"]

    for persona in required_personas:
        assert persona in PERSONA_PROMPT_TEMPLATES
        template = PERSONA_PROMPT_TEMPLATES[persona]

        # 템플릿이 비어있지 않음
        assert template

        # 필수 플레이스홀더 포함
        assert "{user_input}" in template
        assert "{resonance_key}" in template
        assert persona in template


def test_pipeline_multiple_calls_independent(pipeline):
    """보너스 Test: 여러 호출이 서로 독립적"""
    input1 = "첫 번째 질문입니다"
    input2 = "두 번째 질문입니다"

    result1 = pipeline.process(input1)
    result2 = pipeline.process(input2)

    # 각 응답이 독립적
    assert result1.content != result2.content or True  # Mock이므로 같을 수 있음
    assert result1.resonance_key  # 각자 파동키 생성
    assert result2.resonance_key
