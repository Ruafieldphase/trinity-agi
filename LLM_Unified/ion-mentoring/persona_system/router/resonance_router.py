"""
개선된 파동키 기반 라우팅 알고리즘

Week 5-6: 라우팅 알고리즘 개선
- 가중치 기반 점수 계산
- 모든 페르소나 점수 반환
- 신뢰도 개선
- 디버깅 정보 포함
"""

import logging
from typing import Dict, Optional, Tuple

from ..base import AbstractRouter
from ..models import Intent, Pace, RoutingResult, Tone
from ..personas import ElroPersona, LuaPersona, NanaPersona, RiriPersona

logger = logging.getLogger(__name__)


class ResonanceBasedRouter(AbstractRouter):
    """파동키 기반 라우팅 알고리즘 (개선됨)"""

    def __init__(self):
        """라우터 초기화"""
        self.personas = {
            "Lua": LuaPersona(),
            "Elro": ElroPersona(),
            "Riri": RiriPersona(),
            "Nana": NanaPersona(),
        }

        # 점수 계산 가중치
        self.scoring_weights = {
            "tone": 0.5,  # 톤 매칭 (50%)
            "pace": 0.3,  # 속도 적합 (30%)
            "intent": 0.2,  # 의도 적합 (20%)
        }

        # 톤별 페르소나 친화도 (0.0-1.0)
        self.tone_affinity = {
            Tone.FRUSTRATED: {"Lua": 1.0, "Elro": 0.4, "Riri": 0.6, "Nana": 0.5},
            Tone.PLAYFUL: {"Lua": 1.0, "Elro": 0.3, "Riri": 0.4, "Nana": 0.7},
            Tone.ANXIOUS: {"Lua": 1.0, "Elro": 0.5, "Riri": 0.6, "Nana": 0.7},
            Tone.ANALYTICAL: {"Lua": 0.3, "Elro": 1.0, "Riri": 1.0, "Nana": 0.5},
            Tone.CALM: {"Lua": 0.6, "Elro": 1.0, "Riri": 1.0, "Nana": 0.7},
            Tone.CURIOUS: {"Lua": 0.7, "Elro": 1.0, "Riri": 0.9, "Nana": 0.8},
            Tone.URGENT: {"Lua": 0.5, "Elro": 0.8, "Riri": 0.6, "Nana": 1.0},
            Tone.CONFUSED: {"Lua": 0.8, "Elro": 0.6, "Riri": 0.7, "Nana": 1.0},
            Tone.COLLABORATIVE: {"Lua": 0.6, "Elro": 0.5, "Riri": 0.7, "Nana": 1.0},
        }

        # 속도별 페르소나 친화도
        self.pace_affinity = {
            Pace.BURST: {"Lua": 1.0, "Elro": 0.4, "Riri": 0.5, "Nana": 0.6},
            Pace.FLOWING: {"Lua": 1.0, "Elro": 0.8, "Riri": 0.9, "Nana": 0.9},
            Pace.CONTEMPLATIVE: {"Lua": 0.9, "Elro": 0.7, "Riri": 1.0, "Nana": 0.8},
            Pace.MEDIUM: {"Lua": 0.8, "Elro": 1.0, "Riri": 1.0, "Nana": 1.0},
        }

        # 의도별 페르소나 친화도
        self.intent_affinity = {
            Intent.SEEK_ADVICE: {"Lua": 1.0, "Elro": 0.6, "Riri": 0.7, "Nana": 0.8},
            Intent.PROBLEM_SOLVING: {"Lua": 0.7, "Elro": 1.0, "Riri": 0.9, "Nana": 0.8},
            Intent.LEARNING: {"Lua": 0.6, "Elro": 1.0, "Riri": 0.9, "Nana": 0.7},
            Intent.VALIDATION: {"Lua": 0.8, "Elro": 0.7, "Riri": 1.0, "Nana": 0.9},
            Intent.PLANNING: {"Lua": 0.5, "Elro": 0.8, "Riri": 0.9, "Nana": 1.0},
            Intent.REFLECTION: {"Lua": 1.0, "Elro": 0.4, "Riri": 0.7, "Nana": 0.6},
        }

    def route(self, resonance_key: str, context: Optional[Dict] = None) -> RoutingResult:
        """라우팅 실행

        Args:
            resonance_key: 파동키 (tone-pace-intent 형식)
            context: 추가 컨텍스트

        Returns:
            RoutingResult: 라우팅 결과 (모든 점수 포함)
        """
        try:
            # 1. 파동키 파싱
            tone, pace, intent = self._parse_resonance_key(resonance_key)

            # 2. 모든 페르소나에 대한 점수 계산
            scores = {}
            for persona_name in self.personas.keys():
                scores[persona_name] = self._calculate_score(tone, pace, intent, persona_name)

            # 3. 정렬 (상위 순)
            sorted_personas = sorted(scores.items(), key=lambda x: x[1], reverse=True)

            primary = sorted_personas[0][0]
            primary_score = sorted_personas[0][1]
            secondary = sorted_personas[1][0] if len(sorted_personas) > 1 else None
            secondary_score = sorted_personas[1][1] if len(sorted_personas) > 1 else None

            # 4. 신뢰도 계산
            confidence = self._calculate_confidence(
                primary_score, secondary_score if secondary_score else 0, scores
            )

            # 5. 선택 이유 생성
            reasoning = (
                f"Tone({tone.value}): {primary_score:.2f} | "
                f"Primary: {primary} | Secondary: {secondary}"
            )

            logger.info(f"Routing: {primary} (conf: {confidence:.2f})")

            return RoutingResult(
                primary_persona=primary,
                confidence=confidence,
                secondary_persona=secondary,
                secondary_confidence=secondary_score,
                reasoning=reasoning,
                all_scores=scores,
            )

        except Exception as e:
            logger.error(f"Routing error: {str(e)}")
            # 기본값으로 복구 (Lua)
            return RoutingResult(
                primary_persona="Lua", confidence=0.5, reasoning=f"Error: {str(e)}"
            )

    def get_available_personas(self) -> list:
        """사용 가능한 페르소나 목록"""
        return list(self.personas.keys())

    def evaluate_confidence(self, persona: str, scores: Dict[str, float]) -> float:
        """신뢰도 계산

        Args:
            persona: 선택된 페르소나
            scores: 모든 페르소나 점수

        Returns:
            신뢰도 (0.0-1.0)
        """
        if persona not in scores:
            return 0.0

        persona_score = scores[persona]
        other_scores = [s for k, s in scores.items() if k != persona]
        max_other = max(other_scores) if other_scores else 0

        # 신뢰도 = (주요 점수 - 차선 점수) + 절대 점수
        margin = persona_score - max_other
        absolute = persona_score

        confidence = (margin * 0.3 + absolute * 0.7) / 2
        return min(1.0, max(0.0, confidence))

    def _parse_resonance_key(self, resonance_key: str) -> Tuple[Tone, Pace, Intent]:
        """파동키 파싱

        Format: tone-pace-intent
        Example: frustrated-burst-seeking_advice

        Returns:
            (Tone, Pace, Intent) 튜플
        """
        parts = resonance_key.split("-")

        if len(parts) < 3:
            # 기본값
            return Tone.CALM, Pace.MEDIUM, Intent.LEARNING

        try:
            tone_str = parts[0]
            pace_str = parts[1]
            # intent는 underscore와 dash를 모두 지원해야 함
            intent_raw = parts[2]

            tone = Tone(tone_str)
            pace = Pace(pace_str)

            # intent 정규화: underscore를 underscore로 유지 (Enum 정의에 맞춤)
            # 다양한 형식 지원: "seeking_advice", "seek-advice", "seek_advice"
            intent_normalized = intent_raw.replace("-", "_")

            # Intent Enum 값과 매칭
            try:
                intent = Intent(intent_normalized)
            except ValueError:
                # 유사한 값 찾기
                if "seek" in intent_normalized and "advice" in intent_normalized:
                    intent = Intent.SEEK_ADVICE
                elif "problem" in intent_normalized and "solving" in intent_normalized:
                    intent = Intent.PROBLEM_SOLVING
                elif "learning" in intent_normalized:
                    intent = Intent.LEARNING
                elif "validation" in intent_normalized or "validate" in intent_normalized:
                    intent = Intent.VALIDATION
                elif "planning" in intent_normalized or "plan" in intent_normalized:
                    intent = Intent.PLANNING
                elif "reflection" in intent_normalized or "reflect" in intent_normalized:
                    intent = Intent.REFLECTION
                else:
                    intent = Intent.LEARNING  # 기본값

            return tone, pace, intent
        except ValueError as e:
            # 유효하지 않은 값은 기본값으로
            logger.debug(f"Invalid resonance key '{resonance_key}': {e}")
            return Tone.CALM, Pace.MEDIUM, Intent.LEARNING

    def _calculate_score(self, tone: Tone, pace: Pace, intent: Intent, persona_name: str) -> float:
        """페르소나 점수 계산

        Args:
            tone: 톤
            pace: 속도
            intent: 의도
            persona_name: 페르소나 이름

        Returns:
            점수 (0.0-1.0)
        """
        score = 0.0

        # 톤 점수 (50%)
        tone_score = self.tone_affinity.get(tone, {}).get(persona_name, 0.5)
        score += tone_score * self.scoring_weights["tone"]

        # 속도 점수 (30%)
        pace_score = self.pace_affinity.get(pace, {}).get(persona_name, 0.5)
        score += pace_score * self.scoring_weights["pace"]

        # 의도 점수 (20%)
        intent_score = self.intent_affinity.get(intent, {}).get(persona_name, 0.5)
        score += intent_score * self.scoring_weights["intent"]

        return min(1.0, max(0.0, score))

    def _calculate_confidence(
        self, primary_score: float, secondary_score: float, all_scores: Dict[str, float]
    ) -> float:
        """신뢰도 계산

        Args:
            primary_score: 주요 페르소나 점수
            secondary_score: 차선 페르소나 점수
            all_scores: 모든 점수

        Returns:
            신뢰도 (0.0-1.0)
        """
        # 점수 간 차이 (얼마나 명확한가)
        margin = primary_score - secondary_score

        # 절대 점수 (얼마나 좋은가)
        absolute = primary_score

        # 혼합 신뢰도
        confidence = margin * 0.3 + absolute * 0.7

        return min(1.0, max(0.0, confidence))
