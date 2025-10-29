"""
페르소나 라우팅 시스템

파동키를 분석하여 최적의 내다AI 페르소나를 선택합니다.

작성자: Ion (이온)
날짜: 2025-10-17

통합 업데이트:
- 2025-10-21: Memory System 통합 (fdo_agi_repo)
- 2025-10-21: RUNE 검증 시스템 통합
- Few-shot 예제 자동 선택 기능 추가
"""

import logging
import os
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# fdo_agi_repo Memory System 통합
FDO_AGI_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "fdo_agi_repo")
if os.path.exists(FDO_AGI_PATH):
    sys.path.insert(0, FDO_AGI_PATH)
    from orchestrator.memory_bus import append_coordinate, snapshot_memory, tail_ledger
else:
    # Fallback: Memory 기능 없이 동작
    def append_coordinate(record):
        pass

    def tail_ledger(n=20):
        return []

    def snapshot_memory():
        return {}


# Multi-Persona Orchestrator 통합
from multi_persona_orchestrator import PersonaChain

# RUNE 통합
try:
    from rune_integration import ResponseQualityMetrics, RUNEValidator

    RUNE_AVAILABLE = True
except ImportError:
    RUNE_AVAILABLE = False
    logging.warning("RUNE integration not available. Response validation disabled.")

# Persona Phase Registry 통합
try:
    from persona_phase_registry import PersonaPhaseRegistry

    PHASE_REGISTRY_AVAILABLE = True
except ImportError:
    PHASE_REGISTRY_AVAILABLE = False
    logging.warning("Persona Phase Registry not available.")

# Multi-Persona Orchestrator 통합
try:
    from multi_persona_orchestrator import MultiPersonaOrchestrator, PersonaChain, QueryComplexity

    MULTI_PERSONA_AVAILABLE = True
except ImportError:
    MULTI_PERSONA_AVAILABLE = False
    logging.warning("Multi-Persona Orchestrator not available.")

logger = logging.getLogger(__name__)


class Tone(Enum):
    """감정 톤 (Emotion Tone)"""

    FRUSTRATED = "frustrated"
    CALM = "calm"
    CURIOUS = "curious"
    ANALYTICAL = "analytical"
    PLAYFUL = "playful"
    ANXIOUS = "anxious"
    URGENT = "urgent"
    CONFUSED = "confused"
    COLLABORATIVE = "collaborative"


class Pace(Enum):
    """리듬 속도 (Rhythm Pace)"""

    BURST = "burst"
    FLOWING = "flowing"
    MEDIUM = "medium"


class Intent(Enum):
    """의도 (Intent)"""

    INQUIRY = "inquiry"
    STATEMENT = "statement"
    EXPRESSIVE = "expressive"
    SEEK_ADVICE = "seek-advice"
    SEEKING_ADVICE = "seeking_advice"
    LEARNING = "learning"


@dataclass
class PersonaConfig:
    """페르소나 설정"""

    name: str  # 페르소나 이름 ('Lua', 'Elro', 'Riri', 'Nana')
    traits: List[str]  # 특성 (['empathetic', 'creative', 'flexible'])
    strengths: List[str]  # 강점 (['emotion_understanding', 'creative_problem_solving'])
    prompt_style: str  # 프롬프트 스타일 ('warm_and_encouraging')
    preferred_tones: List[str]  # 선호 감정 톤 (['frustrated', 'playful', 'anxious'])


@dataclass
class RoutingResult:
    """라우팅 결과"""

    primary_persona: str  # 1순위 페르소나
    confidence: float  # 매칭 점수 (0.0 ~ 1.0)
    secondary_persona: Optional[str] = None  # 2순위 페르소나
    reasoning: str = ""  # 선택 이유


class PersonaRouter:
    """파동키 기반 페르소나 라우터 + Memory 통합 + RUNE 검증 + Phase Registry + Multi-Persona"""

    def __init__(
        self,
        enable_memory: bool = True,
        enable_rune: bool = True,
        enable_phases: bool = True,
        enable_multi_persona: bool = False,
    ):
        """
        라우터 초기화

        Args:
            enable_memory: Memory System 활성화 여부
            enable_rune: RUNE 검증 활성화 여부
            enable_phases: Phase Registry 활성화 여부
            enable_multi_persona: Multi-Persona Orchestrator 활성화 여부
        """
        self.personas: Dict[str, PersonaConfig] = {}
        self.enable_memory = enable_memory
        self.enable_rune = enable_rune and RUNE_AVAILABLE
        self.enable_phases = enable_phases and PHASE_REGISTRY_AVAILABLE
        self.enable_multi_persona = enable_multi_persona and MULTI_PERSONA_AVAILABLE

        # RUNE Validator 초기화
        if self.enable_rune:
            self.rune_validator = RUNEValidator(quality_threshold=0.6)
            logger.info("RUNE validation enabled")

        # Phase Registry 초기화
        if self.enable_phases:
            self.phase_registry = PersonaPhaseRegistry()
            logger.info("Persona Phase Registry enabled")

        # Multi-Persona Orchestrator 초기화
        if self.enable_multi_persona:
            self.multi_orchestrator = MultiPersonaOrchestrator(enable_memory=enable_memory)
            logger.info("Multi-Persona Orchestrator enabled")

        self._load_persona_configs()

    def _load_persona_configs(self):
        """
        페르소나 설정 로드

        내다AI 4개 페르소나:
        - Lua (루아): 감성 공감
        - Elro (엘로): 구조 설계
        - Riri (리리): 균형 관찰
        - Nana (나나): 팀 조율
        """
        self.personas = {
            "Lua": PersonaConfig(
                name="Lua",
                traits=["empathetic", "creative", "flexible"],
                strengths=["emotion_understanding", "creative_problem_solving", "motivation"],
                prompt_style="warm_and_encouraging",
                preferred_tones=["frustrated", "playful", "anxious"],
            ),
            "Elro": PersonaConfig(
                name="Elro",
                traits=["logical", "systematic", "clear"],
                strengths=["technical_architecture", "code_design", "pattern_application"],
                prompt_style="structured_and_precise",
                preferred_tones=["curious", "analytical", "calm"],
            ),
            "Riri": PersonaConfig(
                name="Riri",
                traits=["analytical", "balanced", "objective"],
                strengths=["metric_analysis", "quality_verification", "data_interpretation"],
                prompt_style="data_driven_measurable",
                preferred_tones=["analytical", "calm", "curious"],
            ),
            "Nana": PersonaConfig(
                name="Nana",
                traits=["coordinating", "integrative", "collaborative"],
                strengths=["cross_team_collaboration", "process_management", "documentation"],
                prompt_style="coordinating_and_comprehensive",
                preferred_tones=["urgent", "confused", "collaborative"],
            ),
        }

    def route(self, resonance_key: str, context: Optional[Dict[str, Any]] = None) -> RoutingResult:
        """
        파동키를 페르소나로 라우팅

        Args:
            resonance_key: 파동키 (예: "curious-burst-inquiry")
            context: 추가 컨텍스트 (선택사항)

        Returns:
            RoutingResult: 라우팅 결과

        Examples:
            >>> router = PersonaRouter()
            >>> result = router.route("curious-flowing-inquiry")
            >>> result.primary_persona in ['Elro', 'Riri']
            True
        """
        # Memory에 라우팅 기록
        if self.enable_memory:
            self._record_routing(resonance_key, context)

        # 과거 유사한 라우팅 패턴 조회 (Memory 활용)
        past_routings = []
        if self.enable_memory:
            past_routings = self.get_similar_past_routings(resonance_key, limit=10)

        # 모든 페르소나에 대한 매칭 점수 계산
        scores = {}
        for persona_name in self.personas.keys():
            base_score = self.calculate_match_score(resonance_key, persona_name)

            # 과거 성공 패턴 반영 (Memory Boost)
            memory_boost = 0.0
            if past_routings:
                # 과거 라우팅에서 이 Persona가 선택된 비율 계산
                selected_count = sum(
                    1
                    for r in past_routings
                    if r.get("context", {}).get("selected_persona") == persona_name
                )
                memory_boost = (selected_count / len(past_routings)) * 0.1  # 최대 10% 보너스

            scores[persona_name] = base_score + memory_boost

        # 점수 기준 정렬 (내림차순)
        sorted_personas = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # 1순위, 2순위 선택
        primary_persona, primary_score = sorted_personas[0]
        secondary_persona = sorted_personas[1][0] if len(sorted_personas) > 1 else None

        # 선택 이유 생성
        tone, pace, intent = self._parse_resonance_key(resonance_key)
        reasoning = (
            f"파동키 '{resonance_key}' 분석 결과: "
            f"감정 톤={tone.value}, 속도={pace.value}, 의도={intent.value}. "
            f"{primary_persona}가 가장 적합 (점수: {primary_score:.2f})"
        )

        return RoutingResult(
            primary_persona=primary_persona,
            confidence=primary_score,
            secondary_persona=secondary_persona,
            reasoning=reasoning,
        )

    def _record_routing(self, resonance_key: str, context: Optional[Dict[str, Any]]):
        """
        라우팅 기록을 Memory에 저장

        Args:
            resonance_key: 파동키
            context: 컨텍스트
        """
        try:
            record = {"type": "routing", "resonance_key": resonance_key, "context": context or {}}
            append_coordinate(record)
        except Exception:
            # Memory 저장 실패해도 라우팅은 계속 진행
            pass

    def get_similar_past_routings(self, resonance_key: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        과거 유사한 라우팅 기록 조회 (Few-shot 예제용)

        Args:
            resonance_key: 현재 파동키
            limit: 최대 반환 개수

        Returns:
            List[Dict[str, Any]]: 유사한 과거 라우팅 기록

        Examples:
            >>> router = PersonaRouter()
            >>> past_routings = router.get_similar_past_routings("curious-burst-inquiry")
            >>> isinstance(past_routings, list)
            True
        """
        if not self.enable_memory:
            return []

        try:
            recent_records = tail_ledger(100)  # 최근 100개 조회

            # 파동키 유사도 기반 필터링
            tone, pace, intent = self._parse_resonance_key(resonance_key)
            similar = []

            for record in recent_records:
                if record.get("type") != "routing":
                    continue

                past_key = record.get("resonance_key", "")
                past_tone, past_pace, past_intent = self._parse_resonance_key(past_key)

                # 유사도 계산 (tone 가중치 60%, pace 20%, intent 20%)
                similarity = 0.0
                if tone == past_tone:
                    similarity += 0.6
                if pace == past_pace:
                    similarity += 0.2
                if intent == past_intent:
                    similarity += 0.2

                if similarity >= 0.4:  # 40% 이상 유사
                    similar.append({"record": record, "similarity": similarity})

            # 유사도 내림차순 정렬 후 limit 개 반환
            similar.sort(key=lambda x: x["similarity"], reverse=True)
            return [item["record"] for item in similar[:limit]]

        except Exception:
            return []

    def find_similar_past_queries(
        self, query: str, limit: int = 5, min_similarity: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        텍스트 유사도 기반으로 과거 유사한 쿼리 조회

        Args:
            query: 현재 사용자 쿼리
            limit: 최대 반환 개수
            min_similarity: 최소 유사도 (0.0 ~ 1.0)

        Returns:
            List[Dict[str, Any]]: 유사한 과거 쿼리 및 라우팅 결과

        Examples:
            >>> router = PersonaRouter()
            >>> similar = router.find_similar_past_queries("Python 배우고 싶어요")
            >>> isinstance(similar, list)
            True
        """
        if not self.enable_memory:
            return []

        try:
            recent_records = tail_ledger(200)  # 최근 200개 조회

            # 쿼리가 포함된 라우팅 기록만 필터링
            query_records = []
            for record in recent_records:
                if record.get("type") != "routing":
                    continue

                # context에서 쿼리 추출 (있는 경우)
                context = record.get("context", {})
                past_query = context.get("query", "") or context.get("message", "")

                if past_query:
                    query_records.append({"record": record, "query": past_query})

            # 텍스트 유사도 계산 (단순 단어 기반)
            query_words = set(query.lower().split())
            similar = []

            for item in query_records:
                past_query = item["query"]
                past_words = set(past_query.lower().split())

                # Jaccard 유사도 계산
                if len(query_words | past_words) > 0:
                    similarity = len(query_words & past_words) / len(query_words | past_words)
                else:
                    similarity = 0.0

                if similarity >= min_similarity:
                    similar.append(
                        {"record": item["record"], "query": past_query, "similarity": similarity}
                    )

            # 유사도 내림차순 정렬 후 limit 개 반환
            similar.sort(key=lambda x: x["similarity"], reverse=True)
            return similar[:limit]

        except Exception as e:
            logger.warning(f"Error finding similar queries: {e}")
            return []

    def get_persona_config(self, persona_name: str) -> Optional[PersonaConfig]:
        """
        페르소나 설정 조회

        Args:
            persona_name: 페르소나 이름

        Returns:
            Optional[PersonaConfig]: 페르소나 설정 또는 None

        Examples:
            >>> router = PersonaRouter()
            >>> lua_config = router.get_persona_config('Lua')
            >>> lua_config.name
            'Lua'
        """
        return self.personas.get(persona_name)

    def calculate_match_score(self, resonance_key: str, persona_name: str) -> float:
        """
        파동키와 페르소나 간 매칭 점수 계산

        점수 계산 로직:
        - 감정 톤 매칭: 0.5점
        - 속도 적합성: 0.3점
        - 의도 적합성: 0.2점

        Args:
            resonance_key: 파동키
            persona_name: 페르소나 이름

        Returns:
            float: 매칭 점수 (0.0 ~ 1.0)

        Examples:
            >>> router = PersonaRouter()
            >>> score = router.calculate_match_score("frustrated-burst-expressive", "Lua")
            >>> score == 1.0
            True
        """
        persona = self.get_persona_config(persona_name)
        if not persona:
            return 0.0

        tone, pace, intent = self._parse_resonance_key(resonance_key)

        score = 0.0

        # 감정 톤 매칭 (50%)
        if tone.value in persona.preferred_tones:
            score += 0.5

        # 속도 적합성 (30%)
        pace_scores = {
            "Lua": {"burst": 0.3, "flowing": 0.3, "medium": 0.3},
            "Elro": {"burst": 0.1, "flowing": 0.3, "medium": 0.3},
            "Riri": {"burst": 0.1, "flowing": 0.3, "medium": 0.3},
            "Nana": {"burst": 0.3, "flowing": 0.2, "medium": 0.3},
        }
        score += pace_scores.get(persona_name, {}).get(pace.value, 0.0)

        # 의도 적합성 (20%)
        intent_scores = {
            "Lua": {"inquiry": 0.2, "statement": 0.1, "expressive": 0.2},
            "Elro": {"inquiry": 0.2, "statement": 0.2, "expressive": 0.1},
            "Riri": {"inquiry": 0.2, "statement": 0.2, "expressive": 0.1},
            "Nana": {"inquiry": 0.2, "statement": 0.2, "expressive": 0.2},
        }
        score += intent_scores.get(persona_name, {}).get(intent.value, 0.0)

        return score

    def _parse_resonance_key(self, resonance_key: str) -> Tuple[Tone, Pace, Intent]:
        """
        파동키 파싱

        Args:
            resonance_key: 파동키 (예: "curious-burst-inquiry")

        Returns:
            Tuple[Tone, Pace, Intent]: 감정 톤, 리듬 속도, 의도

        Examples:
            >>> router = PersonaRouter()
            >>> tone, pace, intent = router._parse_resonance_key("curious-burst-inquiry")
            >>> tone == Tone.CURIOUS
            True

            >>> tone, pace, intent = router._parse_resonance_key("calm-flowing-statement")
            >>> tone == Tone.CALM
            True
        """
        parts = resonance_key.split("-")

        # 기본 검증 및 기본값 반환
        if len(parts) != 3:
            return (Tone.CALM, Pace.MEDIUM, Intent.INQUIRY)

        tone_str, pace_str, intent_str = parts[0], parts[1], parts[2]

        # Tone 변환 (underscore를 지원하도록)
        try:
            tone = Tone(tone_str)
        except ValueError:
            tone = Tone.CALM

        # Pace 변환
        try:
            pace = Pace(pace_str)
        except ValueError:
            pace = Pace.MEDIUM

        # Intent 변환 (underscore/dash 모두 지원)
        intent_normalized = intent_str.replace("_", "-")
        try:
            # seeking_advice 또는 seek-advice 처리
            if intent_normalized == "seeking-advice":
                intent = Intent.SEEK_ADVICE
            else:
                intent = Intent(intent_normalized)
        except ValueError:
            intent = Intent.INQUIRY

        return (tone, pace, intent)

    def validate_response_with_rune(
        self,
        task_id: str,
        query: str,
        response: str,
        persona_used: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        RUNE을 사용하여 생성된 응답 품질 검증

        Args:
            task_id: 작업 ID
            query: 사용자 질문
            response: 생성된 응답
            persona_used: 사용된 페르소나
            context: 추가 컨텍스트 (도구 사용 정보 등)

        Returns:
            Dict: RUNE 검증 결과 (품질 메트릭, 재계획 필요 여부 등)
        """
        if not self.enable_rune:
            logger.warning("RUNE validation disabled. Skipping validation.")
            return {"validated": False, "reason": "RUNE not enabled"}

        # 컨텍스트에 페르소나 정보 추가
        full_context = context or {}
        full_context["persona"] = persona_used

        # RUNE 검증 실행
        result = self.rune_validator.run_rune_check(
            task_id=task_id, query=query, response=response, context=full_context
        )

        # Memory에 검증 결과 기록
        if self.enable_memory:
            self._record_validation(result)

        return result

    def _record_validation(self, validation_result: Dict[str, Any]):
        """
        RUNE 검증 결과를 Memory에 저장

        Args:
            validation_result: 검증 결과
        """
        try:
            record = {
                "type": "rune_validation",
                "task_id": validation_result.get("task_id"),
                "quality": validation_result.get("metrics", {}).get("overall_quality", 0.0),
                "replan": validation_result.get("should_replan", False),
                "risks": validation_result.get("risks", []),
            }
            append_coordinate(record)
        except Exception as e:
            logger.error(f"Failed to record validation: {e}")

    def get_phases_for_persona(self, persona: str) -> List[Dict]:
        """
        특정 Persona의 Phase 리스트 반환

        Args:
            persona: 페르소나 이름 (Lua, Elro, Riri, Nana)

        Returns:
            Phase 정보 리스트
        """
        if not self.enable_phases:
            logger.warning("Phase Registry not enabled")
            return []

        phases = self.phase_registry.get_phases_for_persona(persona)
        return [
            {
                "name": p.phase_name,
                "description": p.description,
                "guidance": p.guidance,
                "few_shot_count": len(p.few_shot_examples),
            }
            for p in phases
        ]

    def get_phase_prompt(self, persona: str, phase_index: int = 0, base_prompt: str = "") -> str:
        """
        Phase가 주입된 프롬프트 생성

        Args:
            persona: 페르소나 이름
            phase_index: Phase 인덱스 (0부터 시작)
            base_prompt: 기본 프롬프트

        Returns:
            Phase가 주입된 프롬프트
        """
        if not self.enable_phases:
            return base_prompt

        phase_section = self.phase_registry.get_phase_prompt(persona, phase_index)

        if not phase_section:
            return base_prompt

        return f"{base_prompt}\n\n## 현재 Phase\n{phase_section}"

    def analyze_multi_persona_need(self, query: str) -> Tuple[bool, Optional[PersonaChain]]:
        """
        쿼리가 Multi-Persona 처리가 필요한지 분석

        Args:
            query: 사용자 쿼리

        Returns:
            (Multi-Persona 필요 여부, PersonaChain 또는 None)

        Examples:
            >>> router = PersonaRouter(enable_multi_persona=True)
            >>> needs_multi, chain = router.analyze_multi_persona_need(
            ...     "API 설계하고 팀 조율도 필요해요"
            ... )
            >>> needs_multi
            True
            >>> chain.personas
            ['Elro', 'Nana']
        """
        if not self.enable_multi_persona:
            return False, None

        complexity, chain = self.multi_orchestrator.analyze_and_plan(query)

        # SIMPLE이면 단일 Persona로 충분
        if complexity == QueryComplexity.SIMPLE:
            return False, None

        # MODERATE, COMPLEX면 Multi-Persona 필요
        return True, chain

    def execute_multi_persona_chain(
        self, query: str, persona_chain: PersonaChain, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Multi-Persona 체인 실행 (실제 LLM 호출은 외부에서)

        이 메서드는 실행 계획만 수립하고, 실제 각 Persona의 LLM 호출은
        persona_pipeline.py에서 수행됩니다.

        Args:
            query: 사용자 쿼리
            persona_chain: 실행할 Persona 체인
            context: 추가 컨텍스트

        Returns:
            실행 계획 정보 (JSON 문자열)

        Examples:
            >>> router = PersonaRouter(enable_multi_persona=True)
            >>> chain = PersonaChain(
            ...     personas=['Elro', 'Nana'],
            ...     execution_mode=ExecutionMode.SEQUENTIAL,
            ...     merge_strategy=MergeStrategy.HIERARCHICAL,
            ...     reasoning='기술 설계 후 팀 조율'
            ... )
            >>> plan = router.execute_multi_persona_chain(
            ...     "API 설계하고 팀 조율",
            ...     chain
            ... )
            >>> 'Elro' in plan
            True
        """
        import json

        execution_plan = {
            "query": query,
            "personas": persona_chain.personas,
            "execution_mode": persona_chain.execution_mode.value,
            "merge_strategy": persona_chain.merge_strategy.value,
            "reasoning": persona_chain.reasoning,
            "steps": [],
        }

        # 각 Persona에 대한 실행 스텝 생성
        for i, persona in enumerate(persona_chain.personas):
            step = {
                "order": i + 1,
                "persona": persona,
                "prompt_base": f"당신은 {persona}입니다. 다음 질문에 답변해주세요: {query}",
            }

            # Phase 정보 추가 (enable_phases가 True인 경우)
            if self.enable_phases:
                phases = self.get_phases_for_persona(persona)
                step["phases"] = phases

            execution_plan["steps"].append(step)

        # Memory에 Multi-Persona 실행 계획 기록
        if self.enable_memory:
            append_coordinate(
                {
                    "type": "multi_persona_plan",
                    "query": query,
                    "personas": persona_chain.personas,
                    "execution_mode": persona_chain.execution_mode.value,
                }
            )

        return json.dumps(execution_plan, ensure_ascii=False, indent=2)

    def merge_multi_persona_results(
        self, individual_results: Dict[str, Any], persona_chain: PersonaChain
    ) -> str:
        """
        Multi-Persona 결과 병합

        Args:
            individual_results: Persona별 개별 결과
            persona_chain: 사용된 체인

        Returns:
            병합된 최종 결과

        Examples:
            >>> router = PersonaRouter(enable_multi_persona=True)
            >>> results = {
            ...     'Elro': 'API는 RESTful로 설계하세요.',
            ...     'Nana': '팀원들과 명세를 공유하세요.'
            ... }
            >>> chain = PersonaChain(
            ...     personas=['Elro', 'Nana'],
            ...     execution_mode=ExecutionMode.SEQUENTIAL,
            ...     merge_strategy=MergeStrategy.HIERARCHICAL,
            ...     reasoning='기술 설계 후 팀 조율'
            ... )
            >>> merged = router.merge_multi_persona_results(results, chain)
            >>> 'Elro' in merged and 'Nana' in merged
            True
        """
        if not self.enable_multi_persona:
            # Fallback: 단순 연결
            merged = "\n\n".join([f"[{p}] {r}" for p, r in individual_results.items()])
            return merged

        return self.multi_orchestrator.merge_persona_results(individual_results, persona_chain)


# 간단한 사용 예시
if __name__ == "__main__":
    router = PersonaRouter()

    # 테스트 파동키들
    test_keys = [
        "curious-burst-inquiry",
        "frustrated-burst-expressive",
        "calm-flowing-statement",
        "analytical-medium-statement",
    ]

    print("=== PersonaRouter 테스트 ===\n")
    for key in test_keys:
        result = router.route(key)
        print(f"파동키: {key}")
        print(f"  → 1순위: {result.primary_persona} (점수: {result.confidence:.2f})")
        if result.secondary_persona:
            print(f"  → 2순위: {result.secondary_persona}")
        print(f"  → 이유: {result.reasoning}\n")
