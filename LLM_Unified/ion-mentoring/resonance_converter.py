"""
파동키 변환 시스템 (Resonance Key Conversion System)

사용자 입력의 리듬, 감정 톤, 맥락을 분석하여 적절한 파동키를 생성합니다.
이 파동키는 내다AI의 페르소나 라우팅 시스템에서 사용됩니다.

Author: ION Mentoring Program
Date: 2025-10-17
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class RhythmPattern:
    """리듬 패턴 분석 결과"""

    avg_sentence_length: float
    punctuation_density: float  # 문장부호 밀도
    question_ratio: float  # 질문 비율
    exclamation_ratio: float  # 느낌표 비율
    pace: str  # 'slow', 'medium', 'fast'


@dataclass
class EmotionTone:
    """감정 톤 분석 결과"""

    primary: str  # 'calm', 'urgent', 'curious', 'frustrated', 'playful', 'analytical'
    confidence: float  # 0.0 ~ 1.0
    secondary: Optional[str] = None


class ResonanceConverter:
    """사용자 입력 → 파동키 변환 시스템"""

    def __init__(self, vertex_client=None):
        """
        Args:
            vertex_client: PromptClient 인스턴스 (Vertex AI 연결용)
                          None이면 오프라인 모드 (로컬 분석만)
        """
        self.vertex_client = vertex_client

    def analyze_rhythm(self, text: str) -> RhythmPattern:
        """
        텍스트에서 리듬 패턴 추출

        로컬 분석 항목:
        - 평균 문장 길이
        - 문장부호 밀도
        - 질문/느낌표 비율
        - 전체 속도감 (pace)

        Args:
            text: 분석할 사용자 입력

        Returns:
            RhythmPattern 객체
        """
        # 1. 문장 분리
        sentences = self._split_sentences(text)

        # 2. 평균 문장 길이 계산
        avg_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)

        # 3. 문장부호 밀도 계산
        punctuation_count = sum(1 for c in text if c in ".,!?;:")
        punctuation_density = punctuation_count / max(len(text), 1)

        # 4. 질문/느낌표 비율
        question_ratio = text.count("?") / max(len(sentences), 1)
        exclamation_ratio = text.count("!") / max(len(sentences), 1)

        # 5. 속도감 분류
        pace = self._classify_pace(avg_length, punctuation_density)

        return RhythmPattern(
            avg_sentence_length=avg_length,
            punctuation_density=punctuation_density,
            question_ratio=question_ratio,
            exclamation_ratio=exclamation_ratio,
            pace=pace,
        )

    def detect_emotion_tone(self, text: str) -> EmotionTone:
        """
        감정 톤 감지 (Vertex AI 활용 가능)

        Vertex AI Gemini를 사용하여:
        - 주요 감정 분류 (calm, urgent, curious 등)
        - 신뢰도 점수
        - 부차 감정 (있을 경우)

        Args:
            text: 분석할 사용자 입력

        Returns:
            EmotionTone 객체
        """
        if not self.vertex_client or not self.vertex_client.ready():
            # 오프라인 모드: 간단한 키워드 기반 분류
            return self._offline_emotion_detection(text)

        # Vertex AI 프롬프트 구성
        prompt = f"""다음 텍스트의 감정 톤을 분석해주세요.

텍스트: "{text}"

가능한 감정 톤:
- calm: 차분하고 안정적
- urgent: 급하고 긴박한
- curious: 호기심 많고 탐구적
- frustrated: 답답하고 좌절적
- playful: 장난스럽고 가벼운
- analytical: 분석적이고 객관적

응답 형식 (JSON):
{{
    "primary": "감정톤",
    "confidence": 0.0-1.0,
    "secondary": "부차감정 (optional)"
}}
"""

        try:
            response = self.vertex_client.send(prompt)
            # JSON 파싱
            import json

            result = json.loads(response)

            return EmotionTone(
                primary=result.get("primary", "neutral"),
                confidence=result.get("confidence", 0.5),
                secondary=result.get("secondary"),
            )
        except Exception as e:
            print(f"⚠️ Vertex AI 감정 분석 실패: {e}")
            return self._offline_emotion_detection(text)

    def generate_resonance_key(self, rhythm: RhythmPattern, tone: EmotionTone) -> str:
        """
        파동키 생성

        리듬 패턴과 감정 톤을 조합하여 파동키 문자열 생성
        형식: "{tone}-{pace}-{intent}"
        예: "calm-flowing-inquiry", "urgent-burst-technical"

        Args:
            rhythm: 리듬 패턴 분석 결과
            tone: 감정 톤 분석 결과

        Returns:
            파동키 문자열
        """
        # Pace 맵핑
        pace_map = {"fast": "burst", "medium": "flowing", "slow": "contemplative"}
        pace_word = pace_map.get(rhythm.pace, "neutral")

        # Intent 추론 (질문/느낌표 비율 기반)
        if rhythm.question_ratio > 0.3:
            intent = "inquiry"
        elif rhythm.exclamation_ratio > 0.3:
            intent = "expressive"
        else:
            intent = "statement"

        # 파동키 조합
        key = f"{tone.primary}-{pace_word}-{intent}"
        return key

    def convert(self, text: str) -> Dict[str, Any]:
        """
        전체 변환 프로세스 실행

        Args:
            text: 사용자 입력

        Returns:
            {
                'rhythm': RhythmPattern,
                'emotion': EmotionTone,
                'resonance_key': str
            }
        """
        rhythm = self.analyze_rhythm(text)
        emotion = self.detect_emotion_tone(text)
        key = self.generate_resonance_key(rhythm, emotion)

        return {"rhythm": rhythm, "emotion": emotion, "resonance_key": key}

    # ========== Helper Methods ==========

    def _split_sentences(self, text: str) -> list[str]:
        """문장 분리 헬퍼"""
        # 간단한 문장 분리 (., !, ? 기준)
        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _classify_pace(self, avg_length: float, density: float) -> str:
        """속도감 분류"""
        # 한국어는 단어 단위가 영어보다 짧으므로 기준 조정
        if avg_length < 4 and density > 0.08:
            return "fast"
        elif avg_length >= 10:
            return "slow"
        else:
            return "medium"

    def _offline_emotion_detection(self, text: str) -> EmotionTone:
        """오프라인 감정 분류 (키워드 기반)"""
        text_lower = text.lower()

        # 간단한 키워드 매칭
        if any(word in text_lower for word in ["급해", "빨리", "!!!", "안 돼"]):
            return EmotionTone(primary="urgent", confidence=0.7)
        elif any(word in text_lower for word in ["궁금", "?", "혹시", "어떻게"]):
            return EmotionTone(primary="curious", confidence=0.7)
        elif any(word in text_lower for word in ["답답", "왜", "이상", "문제", "안 돌아"]):
            return EmotionTone(primary="frustrated", confidence=0.6)
        elif any(word in text_lower for word in ["분석", "확인", "리포트", "결과"]):
            return EmotionTone(primary="analytical", confidence=0.6)
        else:
            return EmotionTone(primary="calm", confidence=0.5)
