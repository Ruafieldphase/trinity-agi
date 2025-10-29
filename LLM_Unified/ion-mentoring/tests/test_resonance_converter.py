"""
Tests for ResonanceConverter (파동키 변환 시스템)

Author: ION Mentoring Program
Date: 2025-10-17
"""

import importlib.util
import os
import types


def load_resonance_module() -> types.ModuleType:
    """Dynamically load resonance_converter.py as a module for testing."""
    here = os.path.dirname(__file__)
    target = os.path.abspath(os.path.join(here, "..", "resonance_converter.py"))
    spec = importlib.util.spec_from_file_location("resonance_converter", target)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec and spec.loader, "Failed to load spec"
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


# Load module for all tests
rc = load_resonance_module()
ResonanceConverter = rc.ResonanceConverter
RhythmPattern = rc.RhythmPattern
EmotionTone = rc.EmotionTone


# ========== Rhythm Analysis Tests ==========


def test_analyze_rhythm_fast_pace():
    """빠른 리듬 감지 테스트"""
    converter = ResonanceConverter()
    text = "뭐야! 안 돼! 왜?!"

    rhythm = converter.analyze_rhythm(text)

    assert rhythm.pace == "fast"
    assert rhythm.exclamation_ratio > 0
    assert rhythm.avg_sentence_length < 5


def test_analyze_rhythm_slow_pace():
    """느린 리듬 감지 테스트"""
    converter = ResonanceConverter()
    text = "이 시스템의 아키텍처를 천천히 살펴보면, 여러 흥미로운 패턴들을 발견할 수 있습니다."

    rhythm = converter.analyze_rhythm(text)

    assert rhythm.pace == "slow"
    assert rhythm.avg_sentence_length > 10


def test_analyze_rhythm_medium_pace():
    """중간 속도 리듬 감지 테스트"""
    converter = ResonanceConverter()
    text = "이 코드를 리팩토링하면 좋을 것 같아요. 의견이 어떠신가요?"

    rhythm = converter.analyze_rhythm(text)

    assert rhythm.pace == "medium"
    # Medium pace는 fast나 slow가 아님
    assert rhythm.avg_sentence_length >= 4


def test_analyze_rhythm_question_pattern():
    """질문 패턴 감지 테스트"""
    converter = ResonanceConverter()
    text = "이게 맞나요? 혹시 다른 방법은 없을까요?"

    rhythm = converter.analyze_rhythm(text)

    assert rhythm.question_ratio > 0
    assert text.count("?") == 2


def test_analyze_rhythm_punctuation_density():
    """문장부호 밀도 계산 테스트"""
    converter = ResonanceConverter()
    text = "정말! 이건 대단해요, 너무 좋아요."

    rhythm = converter.analyze_rhythm(text)

    assert rhythm.punctuation_density > 0
    # 문장부호: !, , , .  = 4개
    # 문장부호 수만 확인
    assert rhythm.punctuation_density > 0.1  # 밀도가 0보다 충분히 큼


# ========== Emotion Detection Tests ==========


def test_detect_emotion_urgent_offline():
    """긴급 감정 감지 테스트 (오프라인)"""
    converter = ResonanceConverter()  # 오프라인 모드
    text = "빨리 해결해야 해요! 급합니다!"

    emotion = converter.detect_emotion_tone(text)

    assert emotion.primary == "urgent"
    assert emotion.confidence > 0.5


def test_detect_emotion_curious_offline():
    """호기심 감정 감지 테스트 (오프라인)"""
    converter = ResonanceConverter()
    text = "이 기능은 어떻게 동작하나요? 궁금합니다."

    emotion = converter.detect_emotion_tone(text)

    assert emotion.primary == "curious"
    assert emotion.confidence > 0.5


def test_detect_emotion_frustrated_offline():
    """좌절 감정 감지 테스트 (오프라인)"""
    converter = ResonanceConverter()
    text = "왜 이게 안 되는지 모르겠어요. 답답해요."

    emotion = converter.detect_emotion_tone(text)

    assert emotion.primary == "frustrated"
    assert emotion.confidence > 0.5


def test_detect_emotion_calm_offline():
    """차분한 감정 감지 테스트 (오프라인)"""
    converter = ResonanceConverter()
    text = "코드 리뷰를 진행하겠습니다."

    emotion = converter.detect_emotion_tone(text)

    assert emotion.primary == "calm"


def test_detect_emotion_with_vertex_ai():
    """Vertex AI 통합 감정 분석 테스트"""

    class MockVertexClient:
        def ready(self):
            return True

        def send(self, prompt):
            return '{"primary": "analytical", "confidence": 0.85, "secondary": "curious"}'

    converter = ResonanceConverter(vertex_client=MockVertexClient())
    text = "데이터 분석 결과를 확인해주세요."

    emotion = converter.detect_emotion_tone(text)

    assert emotion.primary == "analytical"
    assert emotion.confidence == 0.85
    assert emotion.secondary == "curious"


def test_detect_emotion_vertex_ai_fallback():
    """Vertex AI 실패 시 오프라인 폴백 테스트"""

    class FailingVertexClient:
        def ready(self):
            return True

        def send(self, prompt):
            raise Exception("Network error")

    converter = ResonanceConverter(vertex_client=FailingVertexClient())
    text = "궁금한 게 있어요."

    emotion = converter.detect_emotion_tone(text)

    # 폴백으로 오프라인 감정 감지
    assert emotion.primary in ["curious", "calm"]
    assert emotion.confidence > 0


# ========== Resonance Key Generation Tests ==========


def test_generate_resonance_key_urgent_burst():
    """긴급-빠른 파동키 생성 테스트"""
    rhythm = RhythmPattern(
        avg_sentence_length=3.0,
        punctuation_density=0.1,
        question_ratio=0.0,
        exclamation_ratio=1.0,
        pace="fast",
    )
    emotion = EmotionTone(primary="urgent", confidence=0.8)

    converter = ResonanceConverter()
    key = converter.generate_resonance_key(rhythm, emotion)

    assert key == "urgent-burst-expressive"


def test_generate_resonance_key_curious_inquiry():
    """호기심-질문 파동키 생성 테스트"""
    rhythm = RhythmPattern(
        avg_sentence_length=8.0,
        punctuation_density=0.03,
        question_ratio=0.5,
        exclamation_ratio=0.0,
        pace="medium",
    )
    emotion = EmotionTone(primary="curious", confidence=0.75)

    converter = ResonanceConverter()
    key = converter.generate_resonance_key(rhythm, emotion)

    assert key == "curious-flowing-inquiry"


def test_generate_resonance_key_calm_statement():
    """차분-서술 파동키 생성 테스트"""
    rhythm = RhythmPattern(
        avg_sentence_length=18.0,
        punctuation_density=0.02,
        question_ratio=0.0,
        exclamation_ratio=0.0,
        pace="slow",
    )
    emotion = EmotionTone(primary="calm", confidence=0.9)

    converter = ResonanceConverter()
    key = converter.generate_resonance_key(rhythm, emotion)

    assert key == "calm-contemplative-statement"


# ========== Full Pipeline Tests ==========


def test_convert_full_pipeline_urgent():
    """전체 변환 파이프라인 테스트 - 긴급"""
    converter = ResonanceConverter()
    text = "이 코드가 왜 안 돌아가는 거야?! 답답해!"

    result = converter.convert(text)

    assert "rhythm" in result
    assert "emotion" in result
    assert "resonance_key" in result

    # 예상: "frustrated-burst-inquiry" 또는 유사
    key = result["resonance_key"]
    # 좌절/긴급 감정 또는 질문 의도 확인
    assert "frustrated" in key or "inquiry" in key


def test_convert_full_pipeline_calm_inquiry():
    """전체 변환 파이프라인 테스트 - 차분한 질문"""
    converter = ResonanceConverter()
    text = "혹시 이 부분을 개선할 수 있는 방법이 있을까요?"

    result = converter.convert(text)
    key = result["resonance_key"]

    assert any(word in key for word in ["curious", "calm"])
    assert "inquiry" in key


def test_convert_full_pipeline_analytical():
    """전체 변환 파이프라인 테스트 - 분석적"""
    converter = ResonanceConverter()
    text = "데이터 분석 결과를 확인해주세요. 리포트가 준비되었습니다."

    result = converter.convert(text)

    # 분석적/차분한 감정이어야 함
    assert result["emotion"].primary in ["calm", "analytical"]


def test_convert_empty_text():
    """빈 텍스트 처리 테스트"""
    converter = ResonanceConverter()
    text = ""

    result = converter.convert(text)

    # 빈 텍스트도 처리 가능해야 함
    assert "resonance_key" in result
    assert result["resonance_key"] != ""


def test_convert_single_word():
    """단일 단어 처리 테스트"""
    converter = ResonanceConverter()
    text = "안녕하세요"

    result = converter.convert(text)

    assert result["rhythm"].avg_sentence_length > 0
    assert result["emotion"].primary in [
        "calm",
        "curious",
        "frustrated",
        "urgent",
        "playful",
        "analytical",
    ]
