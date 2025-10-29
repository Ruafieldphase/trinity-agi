"""
PersonaOrchestrator 추상 기본 클래스

리팩토링 Week 2-3: 추상 기본 클래스 설계
- 확장 가능한 인터페이스 정의
- 전략 패턴 적용
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from .models import (
    ChatContext,
    PersonaConfig,
    RhythmAnalysis,
    RoutingResult,
    ToneAnalysis,
)


class AbstractRouter(ABC):
    """라우팅 알고리즘의 추상 기본 클래스"""

    @abstractmethod
    def route(self, resonance_key: str, context: Optional[Dict] = None) -> RoutingResult:
        """라우팅 실행

        Args:
            resonance_key: 파동키 (tone-pace-intent 형식)
            context: 추가 컨텍스트 (선택)

        Returns:
            RoutingResult: 라우팅 결과
        """
        pass

    @abstractmethod
    def get_available_personas(self) -> List[str]:
        """사용 가능한 페르소나 목록

        Returns:
            List[str]: 페르소나 이름 목록
        """
        pass

    @abstractmethod
    def evaluate_confidence(self, persona: str, scores: Dict[str, float]) -> float:
        """신뢰도 계산

        Args:
            persona: 페르소나 이름
            scores: 모든 페르소나의 점수

        Returns:
            float: 신뢰도 (0.0-1.0)
        """
        pass


class AbstractPersona(ABC):
    """페르소나의 추상 기본 클래스"""

    @property
    @abstractmethod
    def config(self) -> PersonaConfig:
        """페르소나 설정

        Returns:
            PersonaConfig: 설정 객체
        """
        pass

    @abstractmethod
    def generate_system_prompt(self) -> str:
        """시스템 프롬프트 생성

        Returns:
            str: 시스템 프롬프트
        """
        pass

    @abstractmethod
    def build_user_prompt(
        self, user_input: str, resonance_key: str, context: Optional[ChatContext] = None
    ) -> str:
        """사용자 프롬프트 구성

        Args:
            user_input: 사용자 입력
            resonance_key: 파동키
            context: 대화 컨텍스트

        Returns:
            str: 구성된 프롬프트
        """
        pass

    @abstractmethod
    def post_process_response(self, response: str, metadata: Optional[Dict] = None) -> str:
        """응답 후처리

        Args:
            response: LLM 응답
            metadata: 메타데이터

        Returns:
            str: 후처리된 응답
        """
        pass


class AbstractPromptBuilder(ABC):
    """프롬프트 빌더 추상 기본 클래스"""

    @abstractmethod
    def build(
        self,
        user_input: str,
        resonance_key: str,
        context: Optional[ChatContext] = None,
        *,
        mode: Optional[str] = None,
        options: Optional[Dict] = None,
    ) -> str:
        """프롬프트 구성

        Args:
            user_input: 사용자 입력
            resonance_key: 파동키
            context: 대화 컨텍스트
            mode: 프롬프트 모드 (예: "summary_light")
            options: 추가 옵션 딕셔너리

        Returns:
            str: 구성된 프롬프트
        """
        pass

    @abstractmethod
    def get_template(self) -> str:
        """템플릿 반환

        Returns:
            str: 프롬프트 템플릿
        """
        pass


class AbstractAnalyzer(ABC):
    """분석기 추상 기본 클래스"""

    @abstractmethod
    def analyze_tone(self, text: str) -> ToneAnalysis:
        """톤 분석

        Args:
            text: 분석할 텍스트

        Returns:
            ToneAnalysis: 톤 분석 결과
        """
        pass

    @abstractmethod
    def analyze_rhythm(self, text: str) -> RhythmAnalysis:
        """리듬 분석

        Args:
            text: 분석할 텍스트

        Returns:
            RhythmAnalysis: 리듬 분석 결과
        """
        pass


class AbstractMiddleware(ABC):
    """미들웨어 추상 기본 클래스"""

    @abstractmethod
    async def preprocess(self, user_input: str) -> str:
        """전처리

        Args:
            user_input: 사용자 입력

        Returns:
            str: 전처리된 입력
        """
        pass

    @abstractmethod
    async def postprocess(self, response: str) -> str:
        """후처리

        Args:
            response: 응답

        Returns:
            str: 후처리된 응답
        """
        pass


class AnalysisResult:
    """분석 결과 컨테이너"""

    def __init__(self, tone_analysis: ToneAnalysis, rhythm_analysis: RhythmAnalysis):
        self.tone = tone_analysis
        self.rhythm = rhythm_analysis
        self.is_valid = True

    def __repr__(self):
        return f"AnalysisResult(tone={self.tone.primary.value}, rhythm={self.rhythm.pace.value})"
