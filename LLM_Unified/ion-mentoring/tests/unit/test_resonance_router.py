"""
ResonanceBasedRouter 단위 테스트

Week 5-6: 라우팅 알고리즘 테스트
- 파동키 파싱
- 친화도 점수 계산
- 신뢰도 평가
- 라우팅 결과 검증
"""

import pytest

from persona_system.models import Intent, Pace, RoutingResult, Tone
from persona_system.router import ResonanceBasedRouter


class TestResonanceBasedRouter:
    """ResonanceBasedRouter 기본 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.router = ResonanceBasedRouter()

    def test_router_initialization(self):
        """라우터 초기화 테스트"""
        assert self.router is not None
        assert len(self.router.personas) == 4
        assert set(self.router.personas.keys()) == {"Lua", "Elro", "Riri", "Nana"}

    def test_scoring_weights_sum(self):
        """가중치 합계가 1.0인지 검증"""
        total_weight = sum(self.router.scoring_weights.values())
        assert abs(total_weight - 1.0) < 0.01

    def test_tone_affinity_coverage(self):
        """톤 친화도가 모든 톤과 페르소나를 포함하는지 검증"""
        for tone in Tone:
            assert tone in self.router.tone_affinity
            assert len(self.router.tone_affinity[tone]) == 4
            for persona in ["Lua", "Elro", "Riri", "Nana"]:
                assert persona in self.router.tone_affinity[tone]

    def test_pace_affinity_coverage(self):
        """속도 친화도가 모든 속도와 페르소나를 포함하는지 검증"""
        for pace in Pace:
            assert pace in self.router.pace_affinity
            assert len(self.router.pace_affinity[pace]) == 4

    def test_intent_affinity_coverage(self):
        """의도 친화도가 모든 의도와 페르소나를 포함하는지 검증"""
        for intent in Intent:
            assert intent in self.router.intent_affinity
            assert len(self.router.intent_affinity[intent]) == 4


class TestResonanceKeyParsing:
    """파동키 파싱 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.router = ResonanceBasedRouter()

    def test_valid_resonance_key_parsing(self):
        """유효한 파동키 파싱"""
        tone, pace, intent = self.router._parse_resonance_key("frustrated-burst-seeking_advice")
        assert tone == Tone.FRUSTRATED
        assert pace == Pace.BURST
        assert intent == Intent.SEEK_ADVICE

    def test_calm_medium_learning_default(self):
        """기본값 (calm-medium-learning)"""
        tone, pace, intent = self.router._parse_resonance_key("calm-medium-learning")
        assert tone == Tone.CALM
        assert pace == Pace.MEDIUM
        assert intent == Intent.LEARNING

    def test_incomplete_resonance_key_fallback(self):
        """불완전한 파동키는 기본값으로 복구"""
        tone, pace, intent = self.router._parse_resonance_key("calm-medium")
        assert tone == Tone.CALM
        assert pace == Pace.MEDIUM
        assert intent == Intent.LEARNING

    def test_invalid_resonance_key_fallback(self):
        """유효하지 않은 파동키는 기본값으로 복구"""
        tone, pace, intent = self.router._parse_resonance_key("invalid-values-here")
        assert tone == Tone.CALM
        assert pace == Pace.MEDIUM
        assert intent == Intent.LEARNING

    def test_empty_resonance_key_fallback(self):
        """빈 파동키는 기본값으로 복구"""
        tone, pace, intent = self.router._parse_resonance_key("")
        assert tone == Tone.CALM
        assert pace == Pace.MEDIUM
        assert intent == Intent.LEARNING


class TestScoreCalculation:
    """점수 계산 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.router = ResonanceBasedRouter()

    def test_score_in_valid_range(self):
        """점수가 0.0-1.0 범위에 있는지 검증"""
        for tone in [Tone.FRUSTRATED, Tone.CALM, Tone.CURIOUS]:
            for pace in [Pace.BURST, Pace.MEDIUM, Pace.CONTEMPLATIVE]:
                for intent in [Intent.LEARNING, Intent.PROBLEM_SOLVING, Intent.VALIDATION]:
                    for persona in ["Lua", "Elro", "Riri", "Nana"]:
                        score = self.router._calculate_score(tone, pace, intent, persona)
                        assert 0.0 <= score <= 1.0, f"Score out of range for {persona}: {score}"

    def test_lua_highest_for_frustrated_burst(self):
        """Lua는 frustrated-burst에서 가장 높은 점수"""
        scores = {}
        for persona in ["Lua", "Elro", "Riri", "Nana"]:
            scores[persona] = self.router._calculate_score(
                Tone.FRUSTRATED, Pace.BURST, Intent.SEEK_ADVICE, persona
            )
        assert scores["Lua"] == max(scores.values())

    def test_elro_highest_for_analytical_medium(self):
        """Elro는 analytical-medium-learning에서 높은 점수"""
        scores = {}
        for persona in ["Lua", "Elro", "Riri", "Nana"]:
            scores[persona] = self.router._calculate_score(
                Tone.ANALYTICAL, Pace.MEDIUM, Intent.LEARNING, persona
            )
        assert scores["Elro"] >= 0.8

    def test_riri_highest_for_analytical_contemplative(self):
        """Riri는 analytical-contemplative-validation에서 높은 점수"""
        scores = {}
        for persona in ["Lua", "Elro", "Riri", "Nana"]:
            scores[persona] = self.router._calculate_score(
                Tone.ANALYTICAL, Pace.CONTEMPLATIVE, Intent.VALIDATION, persona
            )
        assert scores["Riri"] >= 0.8

    def test_nana_highest_for_collaborative_planning(self):
        """Nana는 collaborative-medium-planning에서 높은 점수"""
        scores = {}
        for persona in ["Lua", "Elro", "Riri", "Nana"]:
            scores[persona] = self.router._calculate_score(
                Tone.COLLABORATIVE, Pace.MEDIUM, Intent.PLANNING, persona
            )
        assert scores["Nana"] >= 0.8


class TestConfidenceCalculation:
    """신뢰도 계산 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.router = ResonanceBasedRouter()

    def test_confidence_in_valid_range(self):
        """신뢰도가 0.0-1.0 범위에 있는지 검증"""
        confidence = self.router._calculate_confidence(0.9, 0.7, {"Lua": 0.9, "Elro": 0.7})
        assert 0.0 <= confidence <= 1.0

    def test_confidence_high_margin(self):
        """큰 점수 차이는 높은 신뢰도를 생성"""
        high_margin = self.router._calculate_confidence(0.95, 0.5, {"A": 0.95, "B": 0.5})
        low_margin = self.router._calculate_confidence(0.75, 0.70, {"A": 0.75, "B": 0.70})
        assert high_margin > low_margin

    def test_confidence_high_absolute_score(self):
        """높은 절대 점수는 높은 신뢰도를 생성"""
        high_absolute = self.router._calculate_confidence(0.9, 0.85, {"A": 0.9, "B": 0.85})
        low_absolute = self.router._calculate_confidence(0.55, 0.50, {"A": 0.55, "B": 0.50})
        assert high_absolute > low_absolute

    def test_confidence_formula_weighting(self):
        """신뢰도 = margin * 0.3 + absolute * 0.7"""
        primary = 0.8
        secondary = 0.6
        expected = 0.2 * 0.3 + 0.8 * 0.7  # margin=0.2, absolute=0.8
        actual = self.router._calculate_confidence(
            primary, secondary, {"A": primary, "B": secondary}
        )
        assert abs(actual - expected) < 0.01


class TestRouting:
    """라우팅 실행 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.router = ResonanceBasedRouter()

    def test_routing_result_structure(self):
        """라우팅 결과 구조 검증"""
        result = self.router.route("frustrated-burst-seeking_advice")
        assert isinstance(result, RoutingResult)
        assert result.primary_persona is not None
        assert result.confidence is not None
        assert result.secondary_persona is not None
        assert result.all_scores is not None

    def test_routing_returns_valid_persona(self):
        """라우팅 결과는 유효한 페르소나를 반환"""
        result = self.router.route("calm-medium-learning")
        assert result.primary_persona in ["Lua", "Elro", "Riri", "Nana"]

    def test_routing_primary_higher_than_secondary(self):
        """1순위 점수가 2순위 점수보다 높음"""
        result = self.router.route("frustrated-burst-seeking_advice")
        assert (
            result.all_scores[result.primary_persona] >= result.all_scores[result.secondary_persona]
        )

    def test_routing_all_personas_scored(self):
        """라우팅 결과는 모든 페르소나의 점수를 포함"""
        result = self.router.route("calm-medium-learning")
        assert len(result.all_scores) == 4
        assert set(result.all_scores.keys()) == {"Lua", "Elro", "Riri", "Nana"}

    def test_routing_confidence_accuracy(self):
        """라우팅 신뢰도가 계산된 값과 일치"""
        result = self.router.route("analytical-medium-learning")
        primary_score = result.all_scores[result.primary_persona]
        secondary_score = result.all_scores[result.secondary_persona]
        expected_confidence = self.router._calculate_confidence(
            primary_score, secondary_score, result.all_scores
        )
        assert abs(result.confidence - expected_confidence) < 0.01

    def test_routing_with_invalid_key_fallback(self):
        """유효하지 않은 파동키는 기본 라우팅으로 복구"""
        result = self.router.route("invalid-invalid-invalid")
        assert result.primary_persona is not None
        assert result.confidence >= 0.0


class TestRoutingConsistency:
    """라우팅 일관성 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.router = ResonanceBasedRouter()

    def test_same_resonance_key_same_result(self):
        """동일한 파동키는 동일한 결과를 반환"""
        key = "frustrated-burst-seeking_advice"
        result1 = self.router.route(key)
        result2 = self.router.route(key)
        assert result1.primary_persona == result2.primary_persona
        assert result1.confidence == result2.confidence

    def test_get_available_personas(self):
        """사용 가능한 페르소나 목록 반환"""
        personas = self.router.get_available_personas()
        assert len(personas) == 4
        assert set(personas) == {"Lua", "Elro", "Riri", "Nana"}


class TestEdgeCases:
    """엣지 케이스 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.router = ResonanceBasedRouter()

    def test_routing_with_context(self):
        """컨텍스트 포함 라우팅"""
        context = {"user_id": "test_user", "session_id": "test_session"}
        result = self.router.route("calm-medium-learning", context)
        assert result.primary_persona is not None

    def test_routing_without_context(self):
        """컨텍스트 없이 라우팅"""
        result = self.router.route("calm-medium-learning", None)
        assert result.primary_persona is not None

    def test_all_tone_pace_intent_combinations(self):
        """모든 Tone × Pace × Intent 조합에서 라우팅 성공"""
        test_count = 0
        for tone in Tone:
            for pace in Pace:
                for intent in Intent:
                    key = f"{tone.value}-{pace.value}-{intent.value}"
                    result = self.router.route(key)
                    assert result.primary_persona is not None
                    assert 0.0 <= result.confidence <= 1.0
                    test_count += 1

        # Tone: 9, Pace: 4, Intent: 6 = 216 combinations
        assert test_count == 9 * 4 * 6

    def test_routing_reasoning_text(self):
        """라우팅 이유 텍스트 생성"""
        result = self.router.route("calm-medium-learning")
        assert result.reasoning is not None
        assert isinstance(result.reasoning, str)
        assert len(result.reasoning) > 0
        assert result.primary_persona in result.reasoning


class TestAffinityScores:
    """친화도 점수 세부 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.router = ResonanceBasedRouter()

    def test_tone_affinity_range(self):
        """모든 톤 친화도 점수가 0.0-1.0 범위"""
        for tone, affinities in self.router.tone_affinity.items():
            for persona, score in affinities.items():
                assert 0.0 <= score <= 1.0, f"{tone} → {persona}: {score}"

    def test_pace_affinity_range(self):
        """모든 속도 친화도 점수가 0.0-1.0 범위"""
        for pace, affinities in self.router.pace_affinity.items():
            for persona, score in affinities.items():
                assert 0.0 <= score <= 1.0, f"{pace} → {persona}: {score}"

    def test_intent_affinity_range(self):
        """모든 의도 친화도 점수가 0.0-1.0 범위"""
        for intent, affinities in self.router.intent_affinity.items():
            for persona, score in affinities.items():
                assert 0.0 <= score <= 1.0, f"{intent} → {persona}: {score}"

    def test_lua_high_for_emotional_tones(self):
        """Lua는 감정적 톤에서 높은 친화도"""
        emotional_tones = [Tone.FRUSTRATED, Tone.PLAYFUL, Tone.ANXIOUS, Tone.CURIOUS]
        for tone in emotional_tones:
            lua_affinity = self.router.tone_affinity[tone]["Lua"]
            assert lua_affinity >= 0.6


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
