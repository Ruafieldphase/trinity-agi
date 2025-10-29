"""
PersonaOrchestrator 데이터 모델

리팩토링 Week 1-2: 데이터 모델 분리
- 기존 PersonaResponse 개선
- 새로운 모델 추가 (RhythmAnalysis, ToneAnalysis)
- 타입 안정성 강화
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Pace(str, Enum):
    """리듬 속도"""

    BURST = "burst"  # 빠르고 격정적
    FLOWING = "flowing"  # 자연스럽고 매끄로움
    CONTEMPLATIVE = "contemplative"  # 느리고 사려 깊음
    MEDIUM = "medium"  # 중간 속도


class Tone(str, Enum):
    """감정 톤"""

    FRUSTRATED = "frustrated"  # 답답함
    PLAYFUL = "playful"  # 장난스러움
    ANXIOUS = "anxious"  # 불안함
    ANALYTICAL = "analytical"  # 분석적
    CALM = "calm"  # 차분함
    CURIOUS = "curious"  # 호기심
    URGENT = "urgent"  # 긴급
    CONFUSED = "confused"  # 혼란스러움
    COLLABORATIVE = "collaborative"  # 협력적


class Intent(str, Enum):
    """의도"""

    SEEK_ADVICE = "seek_advice"  # 조언 구하기
    PROBLEM_SOLVING = "problem_solving"  # 문제 해결
    LEARNING = "learning"  # 학습
    VALIDATION = "validation"  # 검증
    PLANNING = "planning"  # 계획
    REFLECTION = "reflection"  # 성찰


@dataclass
class RhythmAnalysis:
    """리듬 분석 결과"""

    pace: Pace  # 속도
    avg_sentence_length: float  # 평균 문장 길이
    punctuation_density: float  # 문장부호 밀도 (0.0-1.0)
    energy_level: float  # 에너지 수준 (0.0-1.0)

    def __post_init__(self):
        """검증"""
        if not 0.0 <= self.punctuation_density <= 1.0:
            raise ValueError("punctuation_density must be between 0.0 and 1.0")
        if not 0.0 <= self.energy_level <= 1.0:
            raise ValueError("energy_level must be between 0.0 and 1.0")


@dataclass
class ToneAnalysis:
    """톤 분석 결과"""

    primary: Tone  # 주요 톤
    confidence: float  # 신뢰도 (0.0-1.0)
    secondary: Optional[Tone] = None  # 보조 톤
    secondary_confidence: Optional[float] = None  # 보조 신뢰도

    def __post_init__(self):
        """검증"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if self.secondary_confidence is not None:
            if not 0.0 <= self.secondary_confidence <= 1.0:
                raise ValueError("secondary_confidence must be between 0.0 and 1.0")


@dataclass
class PersonaConfig:
    """페르소나 설정 (불변)"""

    name: str  # 페르소나 이름
    traits: List[str]  # 특성
    strengths: List[str]  # 강점
    prompt_style: str  # 프롬프트 스타일
    preferred_tones: List[Tone]  # 선호 톤
    description: str  # 설명
    examples: List[Dict[str, str]] = field(default_factory=list)  # 예제
    version: str = "1.0"  # 버전

    def __post_init__(self):
        """검증"""
        if not self.name:
            raise ValueError("name cannot be empty")
        if not self.traits:
            raise ValueError("traits cannot be empty")
        if not self.strengths:
            raise ValueError("strengths cannot be empty")


@dataclass
class RoutingResult:
    """라우팅 결과"""

    primary_persona: str  # 1순위 페르소나
    confidence: float  # 신뢰도 (0.0-1.0)
    secondary_persona: Optional[str] = None  # 2순위 페르소나
    secondary_confidence: Optional[float] = None  # 2순위 신뢰도
    reasoning: str = ""  # 선택 이유
    all_scores: Dict[str, float] = field(default_factory=dict)  # 모든 점수
    tone_analysis: Optional[ToneAnalysis] = None  # 톤 분석
    rhythm_analysis: Optional[RhythmAnalysis] = None  # 리듬 분석

    def __post_init__(self):
        """검증"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if self.secondary_confidence is not None:
            if not 0.0 <= self.secondary_confidence <= 1.0:
                raise ValueError("secondary_confidence must be between 0.0 and 1.0")


@dataclass
class PersonaResponse:
    """페르소나 응답 (최상위 데이터 모델)

    Attributes:
        content: 생성된 응답 텍스트
        persona_used: 사용된 페르소나 ('Lua', 'Elro', 'Riri', 'Nana')
        resonance_key: 입력 파동키
        confidence: 라우팅 신뢰도 (0.0~1.0)
        metadata: 추가 정보 (리듬, 톤, 라우팅 상세)
        execution_time_ms: 실행 시간 (ms)
    """

    content: str  # 생성된 응답
    persona_used: str  # 사용된 페르소나
    resonance_key: str  # 입력 파동키
    confidence: float  # 라우팅 신뢰도
    metadata: Dict[str, Any] = field(default_factory=dict)  # 메타데이터
    execution_time_ms: float = 0.0  # 실행 시간

    def __str__(self):
        """문자열 표현"""
        return f"[{self.persona_used}] {self.content[:50]}... (confidence: {self.confidence:.2f})"

    def __post_init__(self):
        """검증"""
        if not self.content:
            raise ValueError("content cannot be empty")
        if not self.persona_used:
            raise ValueError("persona_used cannot be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if self.execution_time_ms < 0:
            raise ValueError("execution_time_ms cannot be negative")


@dataclass
class ChatContext:
    """대화 컨텍스트"""

    user_id: str  # 사용자 ID
    session_id: str  # 세션 ID
    message_history: List[Dict[str, str]] = field(default_factory=list)  # 메시지 이력
    persona_preference: Optional[str] = None  # 선호 페르소나
    custom_context: Dict[str, Any] = field(default_factory=dict)  # 커스텀 컨텍스트

    def add_message(self, role: str, content: str):
        """메시지 추가"""
        self.message_history.append({"role": role, "content": content})

    def get_recent_messages(self, limit: int = 5) -> List[Dict[str, str]]:
        """최근 메시지 반환"""
        return self.message_history[-limit:]


# 캐시 타입 힌트
ResponseCache = Dict[str, PersonaResponse]
