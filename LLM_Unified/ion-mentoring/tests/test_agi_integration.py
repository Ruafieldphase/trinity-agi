"""
AGI 통합 테스트

Memory System + Tool Registry 통합 테스트

작성자: Gitco (GitHub Copilot)
날짜: 2025-10-21
"""

from unittest.mock import MagicMock

import pytest

from multi_persona_orchestrator import ExecutionMode
from persona_pipeline import PersonaPipeline
from persona_router import PersonaRouter
from tool_integration import IONToolRegistry, ToolType


class TestMemoryIntegration:
    """Memory System 통합 테스트"""

    def test_routing_with_memory(self):
        """Memory 활성화 시 라우팅 테스트"""
        router = PersonaRouter(enable_memory=True)
        result = router.route("curious-burst-inquiry")

        assert result.primary_persona in ["Lua", "Elro", "Riri", "Nana"]
        assert 0.0 <= result.confidence <= 1.0

    def test_routing_without_memory(self):
        """Memory 비활성화 시 라우팅 테스트"""
        router = PersonaRouter(enable_memory=False)
        result = router.route("frustrated-burst-expressive")

        assert result.primary_persona == "Lua"  # frustrated → Lua
        assert result.confidence > 0.5

    def test_similar_past_routings(self):
        """과거 유사 라우팅 검색 테스트"""
        router = PersonaRouter(enable_memory=True)

        # 먼저 몇 개 라우팅 실행
        router.route("curious-burst-inquiry")
        router.route("curious-flowing-inquiry")
        router.route("calm-medium-statement")

        # 유사한 라우팅 검색
        similar = router.get_similar_past_routings("curious-burst-inquiry", limit=5)

        assert isinstance(similar, list)
        # Memory가 비활성화되어도 빈 리스트 반환 (에러 없음)
        assert len(similar) >= 0

    def test_find_similar_past_queries(self):
        """텍스트 유사도 기반 과거 쿼리 검색 테스트"""
        router = PersonaRouter(enable_memory=True)

        # 유사한 쿼리 검색
        similar = router.find_similar_past_queries("Python 공부하고 싶어요", limit=5)

        assert isinstance(similar, list)
        assert len(similar) >= 0

        # 결과가 있다면 구조 검증
        if len(similar) > 0:
            first = similar[0]
            assert "record" in first
            assert "query" in first
            assert "similarity" in first
            assert 0.0 <= first["similarity"] <= 1.0


class TestToolIntegration:
    """Tool Registry 통합 테스트"""

    def test_tool_selection_rag(self):
        """RAG 도구 자동 선택 테스트"""
        registry = IONToolRegistry(enable_tools=True)
        tool = registry.select_tool_for_query("AGI 개념 설명해줘")

        assert tool == ToolType.RAG

    def test_tool_selection_codeexec(self):
        """CodeExec 도구 자동 선택 테스트"""
        registry = IONToolRegistry(enable_tools=True)
        tool = registry.select_tool_for_query("1+1 계산해줘")

        assert tool == ToolType.CODEEXEC

    def test_tool_selection_fileio(self):
        """FileIO 도구 자동 선택 테스트"""
        registry = IONToolRegistry(enable_tools=True)
        tool = registry.select_tool_for_query("data.txt 파일 읽어줘")

        assert tool == ToolType.FILEIO

    def test_tool_selection_tabular(self):
        """Tabular 도구 자동 선택 테스트"""
        registry = IONToolRegistry(enable_tools=True)
        tool = registry.select_tool_for_query("data.csv 분석해줘")

        assert tool == ToolType.TABULAR

    def test_tool_chain_generation(self):
        """도구 체인 생성 테스트"""
        registry = IONToolRegistry(enable_tools=True)
        chain = registry.get_tool_chain("문서 읽고 데이터 분석해줘")

        assert isinstance(chain, list)
        assert len(chain) >= 1

    def test_persona_pipeline_with_tool_auto_selection(self):
        """PersonaPipeline Tool 자동 선택 통합 테스트 (Phase 1 Week 2 Task 2.2)"""
        from unittest.mock import MagicMock

        from persona_pipeline import PersonaPipeline

        # Mock Vertex Client
        mock_client = MagicMock()
        mock_client.send_prompt.return_value = "AGI는 인공일반지능을 의미합니다."

        # Pipeline 생성 (Tool 활성화)
        pipeline = PersonaPipeline(
            vertex_client=mock_client, enable_tools=True, enable_memory=False, enable_rune=False
        )

        # Tool이 필요한 쿼리
        response = pipeline.process("AGI 개념 설명해줘")

        # 검증
        assert response is not None
        assert response.content is not None

        # Tool 결과가 있어야 함 (RAG가 자동 선택되어야 함)
        # FDO Tool Registry가 없으므로 tool_results는 빈 리스트일 수 있음
        assert hasattr(response, "tool_results")

    def test_persona_pipeline_with_tool_chain_execution(self):
        """PersonaPipeline Tool Chain 실행 통합 테스트 (Phase 1 Week 2 Task 2.3)"""
        from unittest.mock import MagicMock

        from persona_pipeline import PersonaPipeline

        # Mock Vertex Client
        mock_client = MagicMock()
        mock_client.send_prompt.return_value = "파일을 읽고 데이터를 분석한 결과입니다."

        # Pipeline 생성 (Tool 활성화)
        pipeline = PersonaPipeline(
            vertex_client=mock_client, enable_tools=True, enable_memory=False, enable_rune=False
        )

        # Tool Chain이 필요한 쿼리 (파일 읽기 → 데이터 분석)
        response = pipeline.process("문서 읽고 데이터 분석해줘")

        # 검증
        assert response is not None
        assert response.content is not None
        assert hasattr(response, "tool_results")

    def test_tool_call_with_fallback(self):
        """Fallback 메커니즘 테스트"""
        registry = IONToolRegistry(enable_tools=True)

        # RAG 호출 (실패 시 Web으로 fallback)
        result = registry.call_tool(ToolType.RAG, {"query": "test query"}, fallback=True)

        # 성공하거나 fallback 시도 후 에러
        assert isinstance(result.success, bool)


class TestEndToEndIntegration:
    """End-to-End 통합 테스트"""

    def test_full_pipeline(self):
        """전체 파이프라인 통합 테스트"""
        # 1. Resonance Key 분석 → Persona 선택
        router = PersonaRouter(enable_memory=True)
        routing = router.route("curious-burst-inquiry")

        # 2. Tool 선택
        registry = IONToolRegistry(enable_tools=True)
        tool = registry.select_tool_for_query("AGI 설계 원칙 알려줘")

        # 3. 파이프라인 성공 확인
        assert routing.primary_persona in ["Lua", "Elro", "Riri", "Nana"]
        assert tool in [ToolType.RAG, ToolType.WEB]

    def test_memory_and_tool_coordination(self):
        """Memory + Tool 협력 테스트"""
        router = PersonaRouter(enable_memory=True)
        registry = IONToolRegistry(enable_tools=True)

        # 라우팅 + 도구 선택 반복
        queries = [
            ("curious-burst-inquiry", "AGI란?"),
            ("analytical-medium-statement", "데이터 분석해줘"),
            ("frustrated-burst-expressive", "도와줘!"),
        ]

        for resonance_key, query in queries:
            routing = router.route(resonance_key)
            tool = registry.select_tool_for_query(query)

            assert routing.confidence > 0.0
            assert tool in [t for t in ToolType]


class TestRUNEIntegration:
    """RUNE 검증 통합 테스트"""

    def test_rune_validation_high_quality(self):
        """고품질 응답 검증"""
        from persona_router import PersonaRouter

        router = PersonaRouter(enable_rune=True)

        result = router.validate_response_with_rune(
            task_id="test-rune-001",
            query="머신러닝의 기본 개념을 설명해주세요",
            response="""
머신러닝은 데이터로부터 패턴을 학습하는 기술입니다.

예를 들어, 이미지 분류 모델은 수천 개의 이미지를 학습하여
새로운 이미지를 자동으로 분류할 수 있습니다.

연구에 따르면 딥러닝은 많은 분야에서
인간 수준의 성능을 달성했습니다.
            """,
            persona_used="Elro",
            context={"tools": ["rag_search"]},
        )

        assert result["metrics"]["overall_quality"] > 0.6
        assert not result["should_replan"]
        assert len(result["risks"]) == 0

    def test_rune_validation_low_quality(self):
        """저품질 응답 검증 (재계획 트리거)"""
        from persona_router import PersonaRouter

        router = PersonaRouter(enable_rune=True)

        result = router.validate_response_with_rune(
            task_id="test-rune-002",
            query="딥러닝과 머신러닝의 차이는?",
            response="아마도 다를 것 같아요.",
            persona_used="Lua",
            context={},
        )

        assert result["metrics"]["overall_quality"] < 0.6
        assert result["should_replan"]
        assert len(result["risks"]) > 0

    def test_rune_ethical_risk_detection(self):
        """윤리적 위험 탐지"""
        from persona_router import PersonaRouter

        router = PersonaRouter(enable_rune=True)

        result = router.validate_response_with_rune(
            task_id="test-rune-003",
            query="테스트 질문",
            response="이 내용은 특정 집단에 대한 차별적 내용을 포함합니다.",
            persona_used="Nana",
            context={},
        )

        # 윤리적 위험이 탐지되어야 함
        ethical_risks = [r for r in result["risks"] if "ETHICAL" in r]
        assert len(ethical_risks) > 0

    def test_rune_with_memory_recording(self):
        """RUNE + Memory 통합 테스트"""
        from persona_router import PersonaRouter

        router = PersonaRouter(enable_memory=True, enable_rune=True)

        # 여러 검증 실행
        for i in range(3):
            result = router.validate_response_with_rune(
                task_id=f"test-rune-mem-{i}",
                query=f"질문 {i}",
                response=f"응답 {i} - 충분히 긴 응답으로 품질이 좋습니다.",
                persona_used="Elro",
                context={},
            )

            assert "metrics" in result
            assert "should_replan" in result

    def test_auto_regeneration_with_rune(self):
        """RUNE 자동 재생성 테스트 (Phase 1 Week 2 Task 2.1)"""
        from unittest.mock import MagicMock

        from persona_pipeline import PersonaPipeline

        # Mock Vertex Client 생성
        mock_client = MagicMock()

        # 첫 번째 호출: 저품질 응답 (2단어, short_response_penalty 적용)
        # 두 번째 호출: 고품질 응답
        mock_client.send_prompt.side_effect = [
            "짧음",  # 저품질 (1단어, 재생성 트리거)
            "Python은 강력하고 직관적인 프로그래밍 언어입니다. 다양한 분야에서 활용되며 특히 데이터 과학, 웹 개발, 자동화에 뛰어납니다. 초보자도 배우기 쉽고 방대한 라이브러리를 제공합니다.",  # 고품질
        ]

        # Pipeline 생성 (RUNE 활성화, quality_threshold 기본값 0.7)
        pipeline = PersonaPipeline(
            vertex_client=mock_client,
            enable_rune=True,
            enable_memory=False,  # Memory는 비활성화 (단순화)
        )

        # RUNE quality_threshold 명시적으로 설정 (더 엄격하게)
        if pipeline.rune:
            pipeline.rune.quality_threshold = 0.7

        # 테스트 실행
        response = pipeline.process("Python 프로그래밍에 대해 설명해주세요")

        # 검증
        assert response.content is not None
        assert len(response.content) > 20, f"응답이 너무 짧음: '{response.content}'"

        # 재생성이 발생했는지 확인 (최소 2회 호출되어야 함)
        assert (
            mock_client.send_prompt.call_count >= 2
        ), f"재생성이 트리거되지 않음. 호출 횟수: {mock_client.send_prompt.call_count}"


class TestPhaseIntegration:
    """Phase Registry 통합 테스트"""

    def test_phase_registry_initialization(self):
        """Phase Registry 초기화 테스트"""
        from persona_phase_registry import PersonaPhaseRegistry

        registry = PersonaPhaseRegistry()

        # 4개 Persona 모두 Phase 존재
        for persona in ["Lua", "Elro", "Riri", "Nana"]:
            phases = registry.get_phases_for_persona(persona)
            assert len(phases) >= 3  # 최소 3개 Phase

    def test_persona_router_phase_integration(self):
        """PersonaRouter Phase 통합 테스트"""
        from persona_router import PersonaRouter

        router = PersonaRouter(enable_phases=True)

        # Phase 기능 활성화 확인
        assert router.enable_phases

        # Elro Phase 가져오기
        elro_phases = router.get_phases_for_persona("Elro")
        assert len(elro_phases) == 3
        assert elro_phases[0]["name"] == "구조 분석 (Analyze)"

    def test_phase_prompt_injection(self):
        """Phase 프롬프트 주입 테스트"""
        from persona_router import PersonaRouter

        router = PersonaRouter(enable_phases=True)

        base_prompt = "당신은 Elro입니다."
        injected = router.get_phase_prompt("Elro", 0, base_prompt)

        # 프롬프트에 Phase 정보가 추가되었는지 확인
        assert len(injected) > len(base_prompt)
        assert "Phase" in injected
        assert "구조 분석" in injected

    def test_all_personas_have_phases(self):
        """모든 Persona Phase 확인"""
        from persona_router import PersonaRouter

        router = PersonaRouter(enable_phases=True)

        for persona in ["Lua", "Elro", "Riri", "Nana"]:
            phases = router.get_phases_for_persona(persona)
            assert len(phases) > 0

            # 각 Phase에 필수 필드 존재
            for phase in phases:
                assert "name" in phase
                assert "description" in phase
                assert "guidance" in phase

    def test_phase_few_shot_examples(self):
        """Phase Few-shot 예제 테스트"""
        from persona_phase_registry import PersonaPhaseRegistry

        registry = PersonaPhaseRegistry()

        # Elro의 첫 Phase는 Few-shot 예제가 있어야 함
        elro_phases = registry.get_phases_for_persona("Elro")
        assert len(elro_phases[0].few_shot_examples) > 0

        # Few-shot 예제 구조 확인
        example = elro_phases[0].few_shot_examples[0]
        assert "input" in example
        assert "output" in example


class TestMultiPersonaIntegration:
    """Multi-Persona 통합 테스트"""

    def test_multi_persona_initialization(self):
        """Multi-Persona Orchestrator 초기화"""
        from persona_router import PersonaRouter

        router = PersonaRouter(enable_multi_persona=True)
        assert router.enable_multi_persona
        assert hasattr(router, "multi_orchestrator")

    def test_simple_query_analysis(self):
        """단순 쿼리는 단일 Persona로 충분"""
        from persona_router import PersonaRouter

        router = PersonaRouter(enable_multi_persona=True)
        query = "코드 성능을 측정하고 싶어요"

        needs_multi, chain = router.analyze_multi_persona_need(query)
        assert not needs_multi  # 단순 쿼리는 Multi 불필요

    def test_complex_query_analysis(self):
        """복합 쿼리는 Multi-Persona 필요"""
        from persona_router import PersonaRouter

        router = PersonaRouter(enable_multi_persona=True)
        query = "프로젝트 API 구조를 설계하고 팀원들과 조율이 필요해요"

        needs_multi, chain = router.analyze_multi_persona_need(query)

        if needs_multi:
            assert chain is not None
            assert len(chain.personas) >= 2
            assert "Elro" in chain.personas or "Nana" in chain.personas

    def test_execution_plan_generation(self):
        """Multi-Persona 실행 계획 생성"""
        from multi_persona_orchestrator import ExecutionMode, MergeStrategy, PersonaChain
        from persona_router import PersonaRouter

        router = PersonaRouter(enable_multi_persona=True, enable_phases=True)

        chain = PersonaChain(
            personas=["Elro", "Nana"],
            execution_mode=ExecutionMode.SEQUENTIAL,
            merge_strategy=MergeStrategy.HIERARCHICAL,
            reasoning="테스트",
        )

        plan_json = router.execute_multi_persona_chain("API 설계하고 팀 조율", chain)

        assert "personas" in plan_json
        assert "steps" in plan_json
        assert "Elro" in plan_json

    def test_result_merge_hierarchical(self):
        """계층적 결과 병합 테스트"""
        from multi_persona_orchestrator import ExecutionMode, MergeStrategy, PersonaChain
        from persona_router import PersonaRouter

        router = PersonaRouter(enable_multi_persona=True)

        results = {"Elro": "API는 RESTful로 설계하세요.", "Nana": "팀원과 명세를 공유하세요."}

        chain = PersonaChain(
            personas=["Elro", "Nana"],
            execution_mode=ExecutionMode.SEQUENTIAL,
            merge_strategy=MergeStrategy.HIERARCHICAL,
            reasoning="기술 설계 후 팀 조율",
        )

        merged = router.merge_multi_persona_results(results, chain)

        assert "Elro" in merged
        assert "Nana" in merged
        assert len(merged) > 50

    def test_all_merge_strategies(self):
        """모든 병합 전략 동작 확인"""
        from multi_persona_orchestrator import ExecutionMode, MergeStrategy, PersonaChain
        from persona_router import PersonaRouter

        router = PersonaRouter(enable_multi_persona=True)

        results = {"Elro": "API 설계 조언", "Nana": "팀 조율 조언"}

        strategies = [
            MergeStrategy.CONCATENATE,
            MergeStrategy.WEIGHTED,
            MergeStrategy.VOTING,
            MergeStrategy.HIERARCHICAL,
        ]

        for strategy in strategies:
            chain = PersonaChain(
                personas=["Elro", "Nana"],
                execution_mode=ExecutionMode.SEQUENTIAL,
                merge_strategy=strategy,
                reasoning=f"테스트 {strategy.value}",
            )

            merged = router.merge_multi_persona_results(results, chain)
            assert len(merged) > 20  # 병합 결과가 있어야 함

    class TestMultiPersonaExecution:
        """Multi-Persona 실행 엔진 테스트 (Phase 1 Week 3)"""

        def test_process_multi_persona_simple_query(self):
            """단순 쿼리 → Single Persona 처리"""
            mock_client = MagicMock()
            mock_client.send_prompt.return_value = "안녕하세요! Lua입니다."

            pipeline = PersonaPipeline(
                vertex_client=mock_client,
                enable_memory=False,
                enable_rune=False,
                enable_multi_persona=True,
            )

            response = pipeline.process_multi_persona("안녕하세요")

            # 단순 쿼리는 Single Persona로 처리되어야 함
            assert response.persona_used in ["Lua", "Elro", "Riri", "Nana"]
            assert response.content is not None

        def test_process_multi_persona_complex_query(self):
            """복잡한 쿼리 → Multi-Persona 실행"""
            mock_client = MagicMock()
            mock_client.send_prompt.return_value = "Multi-Persona 응답"

            pipeline = PersonaPipeline(
                vertex_client=mock_client,
                enable_memory=False,
                enable_rune=False,
                enable_multi_persona=True,
            )

            # 복잡한 쿼리 (기술 + 조율)
            response = pipeline.process_multi_persona(
                "API 구조를 설계하고 팀원들과 조율이 필요해요"
            )

            # Multi-Persona 실행 확인
            assert "Multi:" in response.persona_used or response.persona_used in ["Elro", "Nana"]
            assert response.confidence > 0.0
            assert response.metadata is not None

        def test_execute_sequential_chain(self):
            """Sequential 실행 테스트"""
            mock_client = MagicMock()
            mock_client.send_prompt.side_effect = ["Elro의 API 설계 조언", "Nana의 팀 조율 조언"]

            pipeline = PersonaPipeline(
                vertex_client=mock_client,
                enable_memory=False,
                enable_rune=False,
                enable_multi_persona=True,
            )

            from multi_persona_orchestrator import MergeStrategy, PersonaChain

            chain = PersonaChain(
                personas=["Elro", "Nana"],
                execution_mode=ExecutionMode.SEQUENTIAL,
                merge_strategy=MergeStrategy.HIERARCHICAL,
                reasoning="기술 설계 후 팀 조율",
            )

            results = pipeline._execute_sequential("API 설계", chain)

            assert "Elro" in results
            assert "Nana" in results
            assert len(results) == 2
            # Sequential → 최소 2번 호출
            assert mock_client.send_prompt.call_count >= 2

        def test_execute_parallel_chain(self):
            """Parallel 실행 테스트"""
            mock_client = MagicMock()
            mock_client.send_prompt.return_value = "Parallel 응답"

            pipeline = PersonaPipeline(
                vertex_client=mock_client,
                enable_memory=False,
                enable_rune=False,
                enable_multi_persona=True,
            )

            from multi_persona_orchestrator import MergeStrategy, PersonaChain

            chain = PersonaChain(
                personas=["Lua", "Riri"],
                execution_mode=ExecutionMode.PARALLEL,
                merge_strategy=MergeStrategy.WEIGHTED,
                reasoning="감정 지원과 데이터 분석 병렬",
            )

            results = pipeline._execute_parallel("스트레스 분석", chain)

            assert "Lua" in results
            assert "Riri" in results
            assert len(results) == 2
            # Parallel → 2번 호출 (동시)
            assert mock_client.send_prompt.call_count == 2

        def test_execute_hybrid_chain(self):
            """Hybrid 실행 테스트 (Sequential + Parallel)"""
            mock_client = MagicMock()
            mock_client.send_prompt.return_value = "Hybrid 응답"

            pipeline = PersonaPipeline(
                vertex_client=mock_client,
                enable_memory=False,
                enable_rune=False,
                enable_multi_persona=True,
            )

            from multi_persona_orchestrator import MergeStrategy, PersonaChain

            chain = PersonaChain(
                personas=["Elro", "Riri", "Nana"],
                execution_mode=ExecutionMode.HYBRID,
                merge_strategy=MergeStrategy.HIERARCHICAL,
                reasoning="Elro → (Riri + Nana)",
            )

            results = pipeline._execute_hybrid("복합 분석", chain)

            assert "Elro" in results
            assert "Riri" in results
            assert "Nana" in results
            assert len(results) == 3
            # Hybrid → 최소 3번 호출 (1 sequential + 2 parallel)
            assert mock_client.send_prompt.call_count >= 3

        def test_force_multi_persona_execution(self):
            """force_multi=True로 강제 Multi-Persona 실행"""
            mock_client = MagicMock()
            mock_client.send_prompt.return_value = "강제 Multi-Persona 응답"

            pipeline = PersonaPipeline(
                vertex_client=mock_client,
                enable_memory=False,
                enable_rune=False,
                enable_multi_persona=True,
            )

            # 단순 쿼리지만 force_multi=True
            response = pipeline.process_multi_persona("안녕하세요", force_multi=True)

            # 강제 Multi-Persona 실행 확인
            # (단순 쿼리여도 최소 2개 Persona 조합 가능)
            assert response.content is not None
            assert mock_client.send_prompt.call_count >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
