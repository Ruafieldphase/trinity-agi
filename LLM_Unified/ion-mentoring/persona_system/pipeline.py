"""
간소화된 PersonaPipeline - 모든 컴포넌트 통합

Week 5-6: 통합 파이프라인
- 라우터, 페르소나, 프롬프트 빌더 통합
- 단순화된 인터페이스
- 성능 최적화
"""

import logging
import time
from typing import Any, Dict, Optional

from .models import ChatContext, PersonaResponse
from .personas import ElroPersona, LuaPersona, NanaPersona, RiriPersona
from .prompts import PromptBuilderFactory
from .router import ResonanceBasedRouter

logger = logging.getLogger(__name__)


class PersonaPipeline:
    """통합된 페르소나 파이프라인

    이 클래스는 라우팅, 프롬프트 생성, 페르소나 선택을 통합합니다.
    """

    def __init__(self):
        """파이프라인 초기화"""
        self.router = ResonanceBasedRouter()
        self.personas = {
            "Lua": LuaPersona(),
            "Elro": ElroPersona(),
            "Riri": RiriPersona(),
            "Nana": NanaPersona(),
        }
        self.prompt_factory = PromptBuilderFactory()
        logger.info("PersonaPipeline initialized")

    def process(
        self,
        user_input: str,
        resonance_key: str,
        context: Optional[ChatContext] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PersonaResponse:
        """전체 파이프라인 처리

        Args:
            user_input: 사용자 입력
            resonance_key: 파동키 (tone-pace-intent)
            context: 대화 컨텍스트
            metadata: 추가 메타데이터

        Returns:
            PersonaResponse: 처리 결과
        """
        start_time = time.time()

        try:
            # Step 1: 라우팅 - 최적의 페르소나 선택
            routing_result = self.router.route(resonance_key, context)

            # Step 2: 페르소나 선택
            selected_persona = self.personas[routing_result.primary_persona]

            # Step 3: 프롬프트 생성
            prompt_builder = self.prompt_factory.create(routing_result.primary_persona)
            selected_persona.generate_system_prompt()
            user_prompt = selected_persona.build_user_prompt(
                user_input=user_input, resonance_key=resonance_key, context=context
            )

            # Step 4: 프롬프트 빌더를 사용한 최종 프롬프트 구성
            prompt_builder.build(user_input, resonance_key, context)

            # Step 5: 응답 후처리 (페르소나 특화)
            # 실제 LLM 호출은 별도로 수행됨 (여기서는 파이프라인 구조만 제시)
            response_content = user_prompt  # 실제로는 LLM 응답

            execution_time_ms = (time.time() - start_time) * 1000

            # Step 6: 결과 구성
            result = PersonaResponse(
                content=response_content,
                persona_used=routing_result.primary_persona,
                resonance_key=resonance_key,
                confidence=routing_result.confidence,
                metadata={
                    "routing_result": {
                        "secondary_persona": routing_result.secondary_persona,
                        "all_scores": routing_result.all_scores,
                        "reasoning": routing_result.reasoning,
                    },
                    "tone_analysis": (
                        routing_result.tone_analysis
                        if hasattr(routing_result, "tone_analysis")
                        else None
                    ),
                    "rhythm_analysis": (
                        routing_result.rhythm_analysis
                        if hasattr(routing_result, "rhythm_analysis")
                        else None
                    ),
                    "user_provided_metadata": metadata or {},
                },
                execution_time_ms=execution_time_ms,
            )

            logger.info(
                f"Pipeline processed: persona={routing_result.primary_persona}, "
                f"confidence={routing_result.confidence:.2f}, "
                f"time={execution_time_ms:.0f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}", exc_info=True)
            # 기본값으로 복구
            execution_time_ms = (time.time() - start_time) * 1000
            return PersonaResponse(
                content=f"Error processing request: {str(e)}",
                persona_used="Lua",
                resonance_key=resonance_key,
                confidence=0.0,
                metadata={"error": str(e)},
                execution_time_ms=execution_time_ms,
            )

    def get_persona_capabilities(self, persona_name: str) -> Dict[str, Any]:
        """페르소나의 능력 정보 반환

        Args:
            persona_name: 페르소나 이름

        Returns:
            페르소나 정보 딕셔너리
        """
        if persona_name not in self.personas:
            raise ValueError(f"Unknown persona: {persona_name}")

        persona = self.personas[persona_name]
        config = persona.config

        return {
            "name": persona_name,
            "traits": config.traits,
            "strengths": config.strengths,
            "best_for_tones": self._get_best_tones_for_persona(persona_name),
            "best_for_paces": self._get_best_paces_for_persona(persona_name),
            "best_for_intents": self._get_best_intents_for_persona(persona_name),
        }

    def get_all_personas_info(self) -> Dict[str, Dict[str, Any]]:
        """모든 페르소나의 정보 반환

        Returns:
            모든 페르소나 정보 딕셔너리
        """
        return {
            persona_name: self.get_persona_capabilities(persona_name)
            for persona_name in self.personas.keys()
        }

    def recommend_persona(
        self, scenario: str, context: Optional[ChatContext] = None
    ) -> Dict[str, Any]:
        """시나리오에 최적의 페르소나 추천

        Args:
            scenario: 사용 시나리오 설명
            context: 추가 컨텍스트

        Returns:
            추천 정보
        """
        # 간단한 키워드 기반 분석 (실제로는 더 정교할 수 있음)
        scenario_lower = scenario.lower()

        keyword_mapping = {
            "Lua": ["감정", "emotion", "창의", "creative", "공감", "empathy"],
            "Elro": ["기술", "technical", "논리", "logic", "구조", "structure"],
            "Riri": ["분석", "analysis", "데이터", "data", "객관", "objective"],
            "Nana": ["협력", "collaboration", "팀", "team", "조정", "coordination"],
        }

        scores = {}
        for persona, keywords in keyword_mapping.items():
            score = sum(1 for keyword in keywords if keyword in scenario_lower)
            scores[persona] = score

        best_persona = max(scores, key=scores.get)

        return {
            "recommended_persona": best_persona,
            "scores": scores,
            "capabilities": self.get_persona_capabilities(best_persona),
        }

    def validate_resonance_key(self, resonance_key: str) -> bool:
        """파동키 유효성 검증

        Args:
            resonance_key: 파동키

        Returns:
            유효 여부
        """
        parts = resonance_key.split("-")
        if len(parts) < 3:
            return False

        from .models import Intent, Pace, Tone

        try:
            Tone(parts[0])
            Pace(parts[1])

            # Intent는 underscore와 dash를 모두 지원
            intent_normalized = parts[2].replace("_", "-")
            # 유효한 intent인지 확인 (또는 유사값 매칭)
            valid_intents = [intent.value for intent in Intent]
            if intent_normalized not in valid_intents:
                # 부분 매칭 확인
                if not any(
                    keyword in intent_normalized
                    for keyword in [
                        "seek",
                        "problem",
                        "learning",
                        "validation",
                        "planning",
                        "reflection",
                    ]
                ):
                    return False

            return True
        except ValueError:
            return False

    def _parse_tone(self, resonance_key: str) -> str:
        """파동키에서 톤 추출"""
        parts = resonance_key.split("-")
        return parts[0] if len(parts) > 0 else "calm"

    def _parse_pace(self, resonance_key: str) -> str:
        """파동키에서 속도 추출"""
        parts = resonance_key.split("-")
        return parts[1] if len(parts) > 1 else "medium"

    def _parse_intent(self, resonance_key: str) -> str:
        """파동키에서 의도 추출"""
        parts = resonance_key.split("-")
        return parts[2] if len(parts) > 2 else "learning"

    def _get_best_tones_for_persona(self, persona_name: str) -> list:
        """페르소나의 최고 성능 톤들"""
        from .models import Tone

        affinity = self.router.tone_affinity
        best_tones = []

        for tone in Tone:
            if affinity.get(tone, {}).get(persona_name, 0) >= 0.8:
                best_tones.append(tone.value)

        return best_tones

    def _get_best_paces_for_persona(self, persona_name: str) -> list:
        """페르소나의 최고 성능 속도들"""
        from .models import Pace

        affinity = self.router.pace_affinity
        best_paces = []

        for pace in Pace:
            if affinity.get(pace, {}).get(persona_name, 0) >= 0.8:
                best_paces.append(pace.value)

        return best_paces

    def _get_best_intents_for_persona(self, persona_name: str) -> list:
        """페르소나의 최고 성능 의도들"""
        from .models import Intent

        affinity = self.router.intent_affinity
        best_intents = []

        for intent in Intent:
            if affinity.get(intent, {}).get(persona_name, 0) >= 0.8:
                best_intents.append(intent.value)

        return best_intents


# 싱글톤 인스턴스
_pipeline_instance: Optional[PersonaPipeline] = None


def get_pipeline() -> PersonaPipeline:
    """파이프라인 싱글톤 인스턴스 반환"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = PersonaPipeline()
    return _pipeline_instance


def reset_pipeline() -> None:
    """파이프라인 리셋 (테스트용)"""
    global _pipeline_instance
    _pipeline_instance = None
