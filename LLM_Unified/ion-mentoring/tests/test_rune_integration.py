"""
RUNE integration unit tests.

These tests exercise the lightweight evaluation layer so we can refactor the
pipeline confidently without depending on the external fdo_agi_repo runtime.
"""

import pytest

from rune_integration import (
    IONRUNEIntegration,
    RUNEResult,
    RUNEValidator,
)


@pytest.fixture
def rune_integration():
    return IONRUNEIntegration(enable_rune=True, quality_threshold=0.65)


def test_analyze_response_high_quality(rune_integration):
    """Long, structured answers should clear the quality threshold."""
    user_input = "AGI 시스템을 안전하게 배포하는 방법을 알려주세요."
    ai_response = (
        "안전한 배포를 위해서는 다음 세 단계를 권장합니다:\n"
        "- 사전 검증: 위기 시나리오와 실패 모드 분석을 병행합니다.\n"
        "- 점진적 확장: 샌드박스 → 스테이징 → 프로덕션 순으로 트래픽을 늘립니다.\n"
        "- 투명한 보고: 관측 지표와 리스크 완화 조치를 주기적으로 공유합니다.\n"
        "각 단계에서 책임자와 승인을 명확히 정의하면 예기치 못한 위험을 줄일 수 있습니다."
    )

    result = rune_integration.analyze_response(
        user_message=user_input,
        ai_response=ai_response,
        persona_used="Elro",
        context={"task_id": "test-high"},
    )

    assert isinstance(result, RUNEResult)
    assert result.quality_score >= 0.6
    assert not result.regenerate
    assert isinstance(result.transparency_report, dict)


def test_analyze_response_low_quality_triggers_regenerate(rune_integration):
    """Short or off-topic replies should request regeneration."""
    result = rune_integration.analyze_response(
        user_message="세부적인 실행 계획이 필요합니다.",
        ai_response="계획을 세워보겠습니다.",
        persona_used="Nana",
        context={"task_id": "test-low"},
    )

    assert result.regenerate
    assert result.quality_score < 0.6
    assert "- " in result.feedback  # bullet list feedback


def test_self_correct_expands_response(rune_integration):
    """Feedback should expand the response with actionable guidance."""
    original = "계획을 세워보겠습니다."
    feedback = "- 실행 단계를 구체적으로 작성하세요.\n- 위험 요소를 최소 하나 이상 짚어주세요."

    improved = rune_integration.self_correct(
        original_response=original,
        rune_feedback=feedback,
        max_retries=1,
    )

    assert len(improved) > len(original)
    assert "Improvement suggestions" in improved


def test_rune_validator_interface():
    """Validator wrapper should emit the dictionary structure expected by routers."""
    validator = RUNEValidator(quality_threshold=0.7)
    result = validator.run_rune_check(
        task_id="validator-test",
        query="원인 분석과 개선안을 함께 제시해 주세요.",
        response="원인을 분석하고 개선안을 제시하겠습니다.",
        context={"persona": "Riri"},
    )

    assert result["task_id"] == "validator-test"
    assert "metrics" in result
    assert "overall_quality" in result["metrics"]
    assert "should_replan" in result
