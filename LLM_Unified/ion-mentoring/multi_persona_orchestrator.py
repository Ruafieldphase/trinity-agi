"""
Multi-Persona Orchestrator

복합 쿼리를 분석하여 여러 Persona를 조합 실행하고 결과를 병합합니다.

작성자: GitHub Copilot
날짜: 2025-10-21

주요 기능:
1. QueryAnalyzer: 복합 쿼리 분석 (단일 vs 다중 Persona)
2. PersonaChainStrategy: Persona 조합 전략 (순차/병렬)
3. ResultMerger: 여러 Persona 결과 병합
4. Memory 통합: 과거 Multi-Persona 실행 이력 활용
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class QueryComplexity(Enum):
    """쿼리 복잡도"""

    SIMPLE = "simple"  # 단일 Persona로 충분
    MODERATE = "moderate"  # 2개 Persona 조합
    COMPLEX = "complex"  # 3개 이상 Persona 조합


class ExecutionMode(Enum):
    """실행 모드"""

    SEQUENTIAL = "sequential"  # 순차 실행 (A → B → C)
    PARALLEL = "parallel"  # 병렬 실행 (A + B + C)
    HYBRID = "hybrid"  # 혼합 (A → (B+C))


class MergeStrategy(Enum):
    """결과 병합 전략"""

    CONCATENATE = "concatenate"  # 단순 연결
    WEIGHTED = "weighted"  # 가중 평균
    VOTING = "voting"  # 투표 방식
    HIERARCHICAL = "hierarchical"  # 계층적 병합


@dataclass
class QueryAspect:
    """쿼리의 한 측면"""

    aspect_type: str  # 'technical', 'emotional', 'data', 'coordination'
    keywords: List[str]  # 관련 키워드
    weight: float  # 중요도 (0.0~1.0)
    recommended_persona: str  # 추천 Persona


@dataclass
class PersonaChain:
    """Persona 실행 체인"""

    personas: List[str]  # Persona 목록 ['Elro', 'Nana']
    execution_mode: ExecutionMode  # 실행 모드
    merge_strategy: MergeStrategy  # 병합 전략
    reasoning: str  # 선택 이유


@dataclass
class MultiPersonaResult:
    """Multi-Persona 실행 결과"""

    query: str
    individual_results: Dict[str, Any]  # Persona별 결과
    merged_result: Any  # 병합된 최종 결과
    persona_chain: PersonaChain  # 사용된 체인
    execution_time: float  # 실행 시간 (초)


class QueryAnalyzer:
    """
    복합 쿼리 분석기

    쿼리를 여러 측면(aspect)으로 분해하고 필요한 Persona를 식별합니다.
    """

    def __init__(self):
        # 각 Persona의 전문 영역 키워드
        self.persona_keywords = {
            "Lua": [
                "감정",
                "공감",
                "힘들",
                "스트레스",
                "불안",
                "걱정",
                "기분",
                "마음",
                "위로",
                "지지",
                "고민",
                "상담",
            ],
            "Elro": [
                "설계",
                "구조",
                "아키텍처",
                "모델",
                "API",
                "엔드포인트",
                "클래스",
                "함수",
                "모듈",
                "컴포넌트",
                "패턴",
                "리팩토링",
                "구현",
                "코드",
                "기술",
            ],
            "Riri": [
                "성능",
                "메트릭",
                "지표",
                "데이터",
                "분석",
                "통계",
                "측정",
                "모니터링",
                "로그",
                "에러율",
                "처리량",
                "응답시간",
                "최적화",
                "병목",
                "벤치마크",
            ],
            "Nana": [
                "팀",
                "협업",
                "조율",
                "커뮤니케이션",
                "회의",
                "의견",
                "합의",
                "우선순위",
                "역할",
                "책임",
                "프로세스",
                "조직",
                "일정",
                "마일스톤",
                "조정",
            ],
        }

    def analyze_query(self, query: str) -> Tuple[QueryComplexity, List[QueryAspect]]:
        """
        쿼리를 분석하여 복잡도와 측면들을 반환

        Args:
            query: 사용자 쿼리

        Returns:
            (복잡도, 측면 리스트)

        Examples:
            >>> analyzer = QueryAnalyzer()
            >>> complexity, aspects = analyzer.analyze_query(
            ...     "프로젝트 API 구조를 설계하고 팀원들과 조율이 필요해요"
            ... )
            >>> complexity
            <QueryComplexity.MODERATE: 'moderate'>
            >>> len(aspects)
            2
        """
        aspects = []
        query_lower = query.lower()

        # 각 Persona의 키워드 매칭 점수 계산
        persona_scores = {}
        for persona, keywords in self.persona_keywords.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                persona_scores[persona] = score

        # 점수가 높은 Persona들을 aspects로 변환
        if not persona_scores:
            # 키워드 매칭 실패 시 기본 단일 Persona
            aspects.append(
                QueryAspect(
                    aspect_type="general",
                    keywords=[],
                    weight=1.0,
                    recommended_persona="Elro",  # 기본값
                )
            )
            complexity = QueryComplexity.SIMPLE
        else:
            # 점수 기준 정렬
            sorted_personas = sorted(persona_scores.items(), key=lambda x: x[1], reverse=True)

            # 상위 Persona들을 aspects로 추가
            total_score = sum(persona_scores.values())
            for persona, score in sorted_personas:
                if score >= 2:  # 최소 2개 이상 키워드 매칭
                    aspect_type = self._get_aspect_type(persona)
                    matched_keywords = [
                        kw for kw in self.persona_keywords[persona] if kw in query_lower
                    ]
                    aspects.append(
                        QueryAspect(
                            aspect_type=aspect_type,
                            keywords=matched_keywords,
                            weight=score / total_score,
                            recommended_persona=persona,
                        )
                    )

            # 복잡도 판단
            if len(aspects) == 1:
                complexity = QueryComplexity.SIMPLE
            elif len(aspects) == 2:
                complexity = QueryComplexity.MODERATE
            else:
                complexity = QueryComplexity.COMPLEX

        return complexity, aspects

    def _get_aspect_type(self, persona: str) -> str:
        """Persona에서 측면 타입 추출"""
        mapping = {"Lua": "emotional", "Elro": "technical", "Riri": "data", "Nana": "coordination"}
        return mapping.get(persona, "general")


class PersonaChainPlanner:
    """
    Persona 실행 체인 계획자

    분석된 쿼리 측면을 바탕으로 최적의 Persona 조합과 실행 전략을 수립합니다.
    """

    def __init__(self):
        # Persona 간 의존성 정의 (A가 B를 필요로 하는 경우)
        self.dependencies = {
            "Nana": ["Elro", "Riri"],  # 조율은 기술/데이터 분석 이후
        }

        # 자주 사용되는 Persona 조합 패턴
        self.common_chains = {
            ("Elro", "Riri"): {
                "mode": ExecutionMode.SEQUENTIAL,
                "merge": MergeStrategy.HIERARCHICAL,
                "reason": "구조 설계 후 성능 분석 순차 실행",
            },
            ("Lua", "Elro"): {
                "mode": ExecutionMode.SEQUENTIAL,
                "merge": MergeStrategy.CONCATENATE,
                "reason": "감정 이해 후 기술적 해결책 제시",
            },
            ("Elro", "Nana"): {
                "mode": ExecutionMode.SEQUENTIAL,
                "merge": MergeStrategy.HIERARCHICAL,
                "reason": "기술 설계 후 팀 조율",
            },
            ("Riri", "Nana"): {
                "mode": ExecutionMode.SEQUENTIAL,
                "merge": MergeStrategy.HIERARCHICAL,
                "reason": "데이터 분석 후 팀 액션 조율",
            },
            ("Lua", "Riri"): {
                "mode": ExecutionMode.PARALLEL,
                "merge": MergeStrategy.WEIGHTED,
                "reason": "감정 지원과 데이터 분석 병렬 실행",
            },
        }

    def plan_chain(self, complexity: QueryComplexity, aspects: List[QueryAspect]) -> PersonaChain:
        """
        실행 체인 계획 수립

        Args:
            complexity: 쿼리 복잡도
            aspects: 쿼리 측면 리스트

        Returns:
            PersonaChain: 실행 체인

        Examples:
            >>> planner = PersonaChainPlanner()
            >>> aspects = [
            ...     QueryAspect('technical', ['API', '설계'], 0.6, 'Elro'),
            ...     QueryAspect('coordination', ['팀', '조율'], 0.4, 'Nana')
            ... ]
            >>> chain = planner.plan_chain(QueryComplexity.MODERATE, aspects)
            >>> chain.personas
            ['Elro', 'Nana']
            >>> chain.execution_mode
            <ExecutionMode.SEQUENTIAL: 'sequential'>
        """
        if complexity == QueryComplexity.SIMPLE:
            # 단일 Persona
            persona = aspects[0].recommended_persona
            return PersonaChain(
                personas=[persona],
                execution_mode=ExecutionMode.SEQUENTIAL,
                merge_strategy=MergeStrategy.CONCATENATE,
                reasoning=f"단일 Persona {persona} 충분",
            )

        # 다중 Persona - 가중치 순 정렬
        sorted_aspects = sorted(aspects, key=lambda x: x.weight, reverse=True)
        personas = [asp.recommended_persona for asp in sorted_aspects]

        # 중복 제거 (순서 유지)
        unique_personas = []
        for p in personas:
            if p not in unique_personas:
                unique_personas.append(p)

        personas = unique_personas[:3]  # 최대 3개

        # 사전 정의된 체인 패턴 확인
        chain_key = tuple(personas[:2])  # 상위 2개로 패턴 검색
        if chain_key in self.common_chains:
            pattern = self.common_chains[chain_key]
            return PersonaChain(
                personas=personas,
                execution_mode=pattern["mode"],
                merge_strategy=pattern["merge"],
                reasoning=pattern["reason"],
            )

        # 의존성 기반 실행 모드 결정
        has_dependency = any(
            dep in personas for persona in personas for dep in self.dependencies.get(persona, [])
        )

        if has_dependency:
            # 의존성 있으면 순차 실행
            mode = ExecutionMode.SEQUENTIAL
            merge = MergeStrategy.HIERARCHICAL
            reason = "Persona 간 의존성으로 순차 실행"
        else:
            # 독립적이면 병렬 실행
            mode = ExecutionMode.PARALLEL
            merge = MergeStrategy.WEIGHTED
            reason = "독립적 Persona로 병렬 실행"

        return PersonaChain(
            personas=personas, execution_mode=mode, merge_strategy=merge, reasoning=reason
        )


class ResultMerger:
    """
    Multi-Persona 결과 병합기

    여러 Persona의 응답을 하나의 일관된 결과로 병합합니다.
    """

    def merge_results(
        self,
        individual_results: Dict[str, Any],
        merge_strategy: MergeStrategy,
        persona_chain: PersonaChain,
    ) -> str:
        """
        결과 병합

        Args:
            individual_results: Persona별 개별 결과
            merge_strategy: 병합 전략
            persona_chain: 사용된 체인

        Returns:
            병합된 최종 결과 (문자열)

        Examples:
            >>> merger = ResultMerger()
            >>> results = {
            ...     'Elro': 'API 구조는 RESTful로 설계하세요.',
            ...     'Nana': '팀원들과 API 명세를 공유하고 리뷰 받으세요.'
            ... }
            >>> chain = PersonaChain(
            ...     personas=['Elro', 'Nana'],
            ...     execution_mode=ExecutionMode.SEQUENTIAL,
            ...     merge_strategy=MergeStrategy.HIERARCHICAL,
            ...     reasoning='기술 설계 후 팀 조율'
            ... )
            >>> merged = merger.merge_results(results, MergeStrategy.HIERARCHICAL, chain)
            >>> 'Elro' in merged and 'Nana' in merged
            True
        """
        if merge_strategy == MergeStrategy.CONCATENATE:
            return self._merge_concatenate(individual_results, persona_chain)
        elif merge_strategy == MergeStrategy.WEIGHTED:
            return self._merge_weighted(individual_results, persona_chain)
        elif merge_strategy == MergeStrategy.VOTING:
            return self._merge_voting(individual_results, persona_chain)
        elif merge_strategy == MergeStrategy.HIERARCHICAL:
            return self._merge_hierarchical(individual_results, persona_chain)
        else:
            # 기본값: 단순 연결
            return self._merge_concatenate(individual_results, persona_chain)

    def _merge_concatenate(self, results: Dict[str, Any], chain: PersonaChain) -> str:
        """단순 연결 병합"""
        merged = "=== Multi-Persona 통합 응답 ===\n\n"
        for persona in chain.personas:
            if persona in results:
                merged += f"[{persona}의 관점]\n{results[persona]}\n\n"
        return merged.strip()

    def _merge_weighted(self, results: Dict[str, Any], chain: PersonaChain) -> str:
        """가중 병합 (중요도 순)"""
        merged = "=== Multi-Persona 종합 분석 ===\n\n"
        # 첫 번째 Persona를 메인으로
        if chain.personas and chain.personas[0] in results:
            main_persona = chain.personas[0]
            merged += f"[핵심 분석 - {main_persona}]\n{results[main_persona]}\n\n"

        # 나머지는 보조
        for persona in chain.personas[1:]:
            if persona in results:
                merged += f"[보조 의견 - {persona}]\n{results[persona]}\n\n"
        return merged.strip()

    def _merge_voting(self, results: Dict[str, Any], chain: PersonaChain) -> str:
        """투표 방식 병합 (합의점 찾기)"""
        merged = "=== Multi-Persona 합의 결과 ===\n\n"
        merged += "각 Persona의 의견을 종합한 결과:\n\n"
        for persona in chain.personas:
            if persona in results:
                merged += f"• {persona}: {results[persona]}\n"
        merged += "\n종합: 위 의견들의 공통점을 고려하여 진행하세요."
        return merged

    def _merge_hierarchical(self, results: Dict[str, Any], chain: PersonaChain) -> str:
        """계층적 병합 (순서 중요)"""
        merged = "=== Multi-Persona 단계별 가이드 ===\n\n"
        for i, persona in enumerate(chain.personas, 1):
            if persona in results:
                merged += f"단계 {i} - {persona}의 조언:\n{results[persona]}\n\n"
        merged += "위 단계를 순서대로 따라 진행하세요."
        return merged


class MultiPersonaOrchestrator:
    """
    Multi-Persona 오케스트레이터

    전체 Multi-Persona 실행을 조율합니다.
    """

    def __init__(self, enable_memory: bool = False):
        self.analyzer = QueryAnalyzer()
        self.planner = PersonaChainPlanner()
        self.merger = ResultMerger()
        self.enable_memory = enable_memory

    def analyze_and_plan(self, query: str) -> Tuple[QueryComplexity, PersonaChain]:
        """
        쿼리 분석 및 실행 계획 수립

        Args:
            query: 사용자 쿼리

        Returns:
            (복잡도, 실행 체인)
        """
        complexity, aspects = self.analyzer.analyze_query(query)
        chain = self.planner.plan_chain(complexity, aspects)

        logger.info(
            f"Query complexity: {complexity.value}, "
            f"Personas: {chain.personas}, "
            f"Mode: {chain.execution_mode.value}"
        )

        return complexity, chain

    def merge_persona_results(
        self, individual_results: Dict[str, Any], persona_chain: PersonaChain
    ) -> str:
        """
        Persona별 결과 병합

        Args:
            individual_results: Persona별 개별 결과
            persona_chain: 사용된 체인

        Returns:
            병합된 최종 결과
        """
        return self.merger.merge_results(
            individual_results, persona_chain.merge_strategy, persona_chain
        )


# 독립 실행 테스트
if __name__ == "__main__":
    print("=== Multi-Persona Orchestrator 테스트 ===\n")

    orchestrator = MultiPersonaOrchestrator()

    # 테스트 쿼리들
    test_queries = [
        "프로젝트 API 구조를 설계하고 팀원들과 조율이 필요해요",
        "코드 성능을 측정하고 최적화 방법을 알려주세요",
        "팀 회의가 비효율적이고 스트레스받아요",
        "새로운 기능 구현이 필요한데 어떻게 시작하죠?",
    ]

    for query in test_queries:
        print(f"쿼리: {query}")
        complexity, chain = orchestrator.analyze_and_plan(query)
        print(f"  복잡도: {complexity.value}")
        print(f"  Personas: {chain.personas}")
        print(f"  실행 모드: {chain.execution_mode.value}")
        print(f"  병합 전략: {chain.merge_strategy.value}")
        print(f"  이유: {chain.reasoning}")
        print()

    # 결과 병합 테스트
    print("=== 결과 병합 테스트 ===\n")
    mock_results = {
        "Elro": "API 구조는 RESTful 방식으로 설계하세요. 엔드포인트는 /api/v1/resources 형태로 구성합니다.",
        "Nana": "팀원들에게 API 명세서를 공유하고, 다음 주 회의에서 피드백을 받으세요.",
    }
    mock_chain = PersonaChain(
        personas=["Elro", "Nana"],
        execution_mode=ExecutionMode.SEQUENTIAL,
        merge_strategy=MergeStrategy.HIERARCHICAL,
        reasoning="기술 설계 후 팀 조율",
    )

    merged = orchestrator.merge_persona_results(mock_results, mock_chain)
    print("병합된 결과:")
    print(merged)
    print("\n✅ Multi-Persona Orchestrator 테스트 완료!")
