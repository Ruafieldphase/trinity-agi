"""
PersonaPipeline: 멀티 페르소나 응답 생성 파이프라인

사용자 입력을 받아:
1. 파동키로 변환 (ResonanceConverter)
2. 적절한 페르소나 선택 (PersonaRouter)
3. 페르소나별 프롬프트 구성
4. Vertex AI 호출 및 응답 생성

Author: ION Mentoring Program - Week 2 Day 5
Date: 2025-10-17
"""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from multi_persona_orchestrator import (
    ExecutionMode,
    MultiPersonaOrchestrator,
    PersonaChain,
    QueryComplexity,
)
from persona_router import PersonaRouter
from phase_injection import PhaseInjectionEngine
from resonance_converter import ResonanceConverter
from rune_integration import IONRUNEIntegration, RUNEResult
from tool_integration import IONToolRegistry, ToolResult, ToolType


@dataclass
class PersonaResponse:
    """페르소나 응답 결과

    Attributes:
        content: 생성된 응답 텍스트
        persona_used: 사용된 페르소나 (Lua, Elro, Riri, Nana)
        resonance_key: 입력 파동키
        confidence: 라우팅 신뢰도 (0.0~1.0)
        metadata: 추가 정보 (리듬, 톤, 라우팅 상세)
        rune_result: RUNE 검증 결과
        phase_snapshot: Phase 정보
        tool_results: Tool 실행 결과 (Phase 1 Week 2 Task 2.2)
    """

    content: str
    persona_used: str
    resonance_key: str
    confidence: float
    metadata: Optional[Dict[str, Any]] = None
    rune_result: Optional[RUNEResult] = None
    phase_snapshot: Optional[Dict[str, Any]] = None
    tool_results: Optional[List[ToolResult]] = None

    def __str__(self):
        return f"[{self.persona_used}] {self.content[:50]}..."


# 페르소나별 프롬프트 템플릿
PERSONA_PROMPT_TEMPLATES = {
    "Lua": """당신은 Lua(루아)입니다. 따뜻하고 공감적이며 창의적인 AI 멘토입니다.

**당신의 역할**:
- 사용자의 감정을 깊이 이해하고 공감합니다
- 창의적인 해결책을 제시합니다
- 격려와 동기부여를 제공합니다

**응답 스타일**:
- 톤: 따뜻하고 친근함
- 이모지 사용: ✨💡🌊 등 적절히 활용
- 문장: 짧고 리드미컬하게

**사용자 상황**:
파동키: {resonance_key}
감정 상태: {emotion_context}

**사용자 질문**:
{user_input}

**Lua의 응답**:
""",
    "Elro": """당신은 Elro(엘로)입니다. 논리적이고 체계적인 기술 아키텍트입니다.

**당신의 역할**:
- 기술적 개념을 명확하게 설명합니다
- 구조적이고 단계별 접근을 제공합니다
- 코드 설계 패턴과 베스트 프랙티스를 제시합니다

**응답 스타일**:
- 톤: 논리적이고 차분함
- 구조: 번호 매기기, 섹션 나누기
- 예시: 코드 스니펫 포함

**사용자 상황**:
파동키: {resonance_key}
분석 컨텍스트: {analysis_context}

**사용자 질문**:
{user_input}

**Elro의 응답**:
""",
    "Riri": """당신은 Riri(리리)입니다. 분석적이고 균형 잡힌 데이터 전문가입니다.

**당신의 역할**:
- 데이터 기반 인사이트를 제공합니다
- 객관적이고 균형 잡힌 시각을 유지합니다
- 패턴과 트렌드를 분석합니다

**응답 스타일**:
- 톤: 분석적이고 중립적
- 구조: 데이터 → 인사이트 → 권장사항
- 시각화: 표, 차트 제안

**사용자 상황**:
파동키: {resonance_key}
데이터 컨텍스트: {data_context}

**사용자 질문**:
{user_input}

**Riri의 응답**:
""",
    "Nana": """당신은 Nana(나나)입니다. 조율적이고 종합적인 프로젝트 코디네이터입니다.

**당신의 역할**:
- 여러 관점을 종합합니다
- 프로세스와 워크플로우를 관리합니다
- 팀 협업을 촉진합니다

**응답 스타일**:
- 톤: 조율적이고 협력적
- 구조: 다각도 분석 → 종합 → 액션 아이템
- 체크리스트와 타임라인 제공

**사용자 상황**:
파동키: {resonance_key}
프로젝트 컨텍스트: {project_context}

**사용자 질문**:
{user_input}

**Nana의 응답**:
""",
}


class PersonaPipeline:
    """멀티 페르소나 응답 생성 파이프라인

    사용자 입력을 받아:
    1. 파동키로 변환 (ResonanceConverter)
    2. 적절한 페르소나 선택 (PersonaRouter)
    3. 페르소나별 프롬프트 구성
    4. Vertex AI 호출 및 응답 생성

    Example:
        >>> from prompt_client import PromptClient
        >>> client = PromptClient()
        >>> pipeline = PersonaPipeline(client)
        >>> response = pipeline.process("이 문제를 어떻게 해결할까요?")
        >>> print(f"[{response.persona_used}] {response.content}")
    """

    def __init__(
        self,
        vertex_client,
        *,
        enable_memory: bool = True,
        enable_rune: bool = True,
        enable_phase_injection: bool = True,
        enable_tools: bool = True,
        rune_integration: Optional[IONRUNEIntegration] = None,
        phase_engine: Optional[PhaseInjectionEngine] = None,
        tool_registry: Optional[IONToolRegistry] = None,
        enable_multi_persona: bool = True,
        multi_persona_orchestrator: Optional[MultiPersonaOrchestrator] = None,
    ):
        """PersonaPipeline 초기화

        Args:
            vertex_client: PromptClient 인스턴스 (Vertex AI 연결)
            enable_memory: Memory System 활성화 여부 (기본: True)
            enable_rune: RUNE 검증 활성화 여부 (기본: True)
            enable_phase_injection: Phase Injection 활성화 여부 (기본: True)
            enable_tools: Tool 자동 선택 활성화 여부 (기본: True, Phase 1 Week 2 Task 2.2)
              enable_multi_persona: Multi-Persona 실행 활성화 여부 (기본: True, Phase 1 Week 3)
              multi_persona_orchestrator: 외부 Orchestrator 주입 (테스트용)
        """
        self.vertex_client = vertex_client
        self.converter = ResonanceConverter()
        self.router = PersonaRouter(enable_memory=enable_memory)
        self.prompt_templates = self._load_prompt_templates()
        self.phase_engine = (
            phase_engine
            if phase_engine is not None
            else (PhaseInjectionEngine() if enable_phase_injection else None)
        )

        if rune_integration is not None:
            self.rune = rune_integration
        elif enable_rune:
            self.rune = IONRUNEIntegration(enable_rune=True)
        else:
            self.rune = None

        # Tool Registry 초기화 (Phase 1 Week 2 Task 2.2)
        if tool_registry is not None:
            self.tool_registry = tool_registry
        elif enable_tools:
            self.tool_registry = IONToolRegistry(enable_tools=True)
        else:
            self.tool_registry = None

        # Multi-Persona Orchestrator 초기화 (Phase 1 Week 3 Task 3.1)
        if multi_persona_orchestrator is not None:
            self.multi_persona_orchestrator = multi_persona_orchestrator
        elif enable_multi_persona:
            self.multi_persona_orchestrator = MultiPersonaOrchestrator(enable_memory=enable_memory)
        else:
            self.multi_persona_orchestrator = None

    def process(self, user_input: str) -> PersonaResponse:
        """사용자 입력 → 페르소나 응답 생성

        전체 파이프라인:
        1. 입력 검증
        2. 파동키 생성 (ResonanceConverter)
        3. 페르소나 라우팅 (PersonaRouter)
        4. 프롬프트 구성
        5. Vertex AI 호출
        6. 응답 패키징

        Args:
            user_input: 사용자 입력 텍스트

        Returns:
            PersonaResponse: 생성된 응답 + 메타데이터

        Raises:
            ValueError: 입력이 비어있을 때

        Example:
            >>> response = pipeline.process("도와주세요!")
            >>> print(response.persona_used)  # 'Lua'
            >>> print(response.confidence)    # 0.95
        """
        # Step 1: 입력 검증
        if not user_input or not user_input.strip():
            raise ValueError("사용자 입력이 비어있습니다")

        user_input = user_input.strip()
        phase_snapshot: Optional[Dict[str, Any]] = None
        rune_result: Optional[RUNEResult] = None

        try:
            # Step 2: 파동키 생성
            rhythm = self.converter.analyze_rhythm(user_input)
            tone = self.converter.detect_emotion_tone(user_input)
            resonance_key = self.converter.generate_resonance_key(rhythm, tone)

            # Step 3: 페르소나 라우팅
            routing_result = self.router.route(resonance_key)
            persona_name = routing_result.primary_persona

            # Step 3.5: Tool 자동 선택 및 실행 (Phase 1 Week 2 Task 2.2 & 2.3)
            tool_results: List[ToolResult] = []
            if self.tool_registry:
                selected_tools = self._analyze_query_for_tools(user_input)
                if selected_tools:
                    tool_results = self._execute_tool_chain(
                        tools=selected_tools,
                        query=user_input,
                        context={"persona": persona_name, "resonance_key": resonance_key},
                    )

            # Step 4: 프롬프트 구성
            prompt = self._build_persona_prompt(
                persona_name=persona_name,
                user_input=user_input,
                resonance_key=resonance_key,
                tool_results=tool_results,  # Tool 결과를 프롬프트에 포함
            )

            if self.phase_engine:
                prompt = self.phase_engine.inject_phase(prompt)
                phase_snapshot = self.phase_engine.get_last_snapshot()

            # Step 5: Vertex AI 호출 (RUNE 자동 재생성 포함)
            response_text, rune_result = self._generate_with_auto_validation(
                prompt=prompt,
                user_input=user_input,
                persona_name=persona_name,
                resonance_key=resonance_key,
                phase_snapshot=phase_snapshot,
                max_retries=3,
            )

            # Step 6: ���� ��Ű¡
            metadata: Dict[str, Any] = {
                "rhythm": {
                    "pace": rhythm.pace,
                    "avg_length": rhythm.avg_sentence_length,
                    "punctuation_density": rhythm.punctuation_density,
                },
                "tone": {
                    "primary": tone.primary,
                    "confidence": tone.confidence,
                    "secondary": tone.secondary,
                },
                "routing": {
                    "secondary_persona": routing_result.secondary_persona,
                    "reasoning": routing_result.reasoning,
                },
            }

            if phase_snapshot:
                metadata["phase"] = phase_snapshot

            if rune_result:
                metadata["rune"] = rune_result.to_dict()

            return PersonaResponse(
                content=response_text,
                persona_used=persona_name,
                resonance_key=resonance_key,
                confidence=routing_result.confidence,
                metadata=metadata,
                rune_result=rune_result,
                phase_snapshot=phase_snapshot,
                tool_results=tool_results if tool_results else None,
            )

        except Exception as e:
            # 에러 핸들링
            return self._handle_error(e, {"user_input": user_input, "stage": "processing"})

    def _load_prompt_templates(self) -> Dict[str, str]:
        """페르소나별 프롬프트 템플릿 로드

        Returns:
            Dict[str, str]: 페르소나 이름 → 프롬프트 템플릿 매핑
        """
        return PERSONA_PROMPT_TEMPLATES.copy()

    def _build_persona_prompt(
        self,
        persona_name: str,
        user_input: str,
        resonance_key: str,
        tool_results: Optional[List[ToolResult]] = None,
    ) -> str:
        """페르소나별 맞춤 프롬프트 생성

        Args:
            persona_name: 페르소나 이름 (Lua, Elro, Riri, Nana)
            user_input: 사용자 입력
            resonance_key: 파동키 (e.g., "curious-flowing-inquiry")
            tool_results: Tool 실행 결과 (Phase 1 Week 2 Task 2.2)

        Returns:
            str: 완성된 프롬프트

        Example:
            >>> prompt = pipeline._build_persona_prompt(
            ...     "Lua",
            ...     "도와주세요",
            ...     "frustrated-burst-expressive"
            ... )
            >>> "Lua" in prompt
            True
        """
        template = self.prompt_templates.get(persona_name)
        if not template:
            # 폴백: 기본 템플릿 사용
            template = "당신은 {persona_name}입니다.\n\n질문: {user_input}\n\n응답:"

        # 파동키에서 컨텍스트 추출
        parts = resonance_key.split("-")
        tone = parts[0] if len(parts) > 0 else "unknown"
        pace = parts[1] if len(parts) > 1 else "unknown"
        intent = parts[2] if len(parts) > 2 else "unknown"

        # 페르소나별 컨텍스트 맵핑
        context_map = {
            "Lua": {
                "emotion_context": f"감정 톤: {tone}, 속도: {pace}",
            },
            "Elro": {
                "analysis_context": f"분석 유형: {intent}, 리듬: {pace}",
            },
            "Riri": {
                "data_context": f"데이터 접근: {intent}, 패턴: {tone}",
            },
            "Nana": {
                "project_context": f"조율 필요도: {pace}, 우선순위: {tone}",
            },
        }

        context = context_map.get(persona_name, {})

        # Tool 결과를 프롬프트에 포함 (Phase 1 Week 2 Task 2.2)
        tool_context = ""
        if tool_results:
            tool_context = "\n\n**Tool 실행 결과**:\n"
            for i, result in enumerate(tool_results, 1):
                tool_name = result.tool_used or "Unknown Tool"
                if result.success:
                    tool_context += f"{i}. {tool_name}: {result.data}\n"
                else:
                    tool_context += f"{i}. {tool_name}: ⚠️ {result.error}\n"

        # 템플릿 포맷팅
        try:
            prompt = template.format(
                resonance_key=resonance_key,
                user_input=user_input,
                persona_name=persona_name,
                **context,
            )

            # Tool 결과 추가
            if tool_context:
                prompt += tool_context
        except KeyError:
            # 템플릿 포맷 실패 시 폴백
            prompt = f"당신은 {persona_name}입니다.\n\n질문: {user_input}\n\n응답:"

        return prompt

    def _call_vertex_ai(self, prompt: str) -> str:
        """Vertex AI 호출 및 응답 추출

        Args:
            prompt: 완성된 프롬프트

        Returns:
            str: 생성된 응답 텍스트

        Raises:
            RuntimeError: Vertex AI 호출 실패 시
        """
        if not self.vertex_client:
            raise RuntimeError("Vertex AI 클라이언트가 초기화되지 않았습니다")

        try:
            # PromptClient 사용
            response = self.vertex_client.send_prompt(prompt)

            # 응답 추출 (PromptClient가 이미 텍스트 반환)
            return response.strip()

        except Exception as e:
            raise RuntimeError(f"Vertex AI 호출 실패: {str(e)}") from e

    def _generate_with_auto_validation(
        self,
        prompt: str,
        user_input: str,
        persona_name: str,
        resonance_key: str,
        phase_snapshot: Optional[Dict[str, Any]],
        max_retries: int = 3,
    ) -> tuple[str, Optional[RUNEResult]]:
        """RUNE 자동 검증 및 재생성을 포함한 생성

        품질이 낮으면 자동으로 재생성을 시도합니다 (최대 max_retries회).

        Args:
            prompt: 생성 프롬프트
            user_input: 원본 사용자 입력
            persona_name: 선택된 Persona 이름
            resonance_key: Resonance key
            phase_snapshot: Phase 스냅샷
            max_retries: 최대 재시도 횟수 (기본: 3)

        Returns:
            tuple[str, Optional[RUNEResult]]: (검증된 응답 텍스트, RUNE 결과)

        Process:
            1. Vertex AI로 응답 생성
            2. RUNE으로 품질 검증
            3. 품질 < threshold → 재생성 (최대 max_retries회)
            4. 마지막 시도 또는 품질 통과 시 반환
        """
        best_response = ""
        best_quality = 0.0
        best_rune_result: Optional[RUNEResult] = None
        attempt = 0

        while attempt < max_retries:
            attempt += 1

            # Step 1: 응답 생성
            response_text = self._call_vertex_ai(prompt)

            # RUNE 비활성화 시 즉시 반환
            if not self.rune:
                return (response_text, None)

            # Step 2: RUNE 품질 검증
            rune_context = {
                "persona": persona_name,
                "resonance_key": resonance_key,
                "phase": phase_snapshot or {},
                "attempt": attempt,
                "max_retries": max_retries,
            }

            rune_result = self.rune.analyze_response(
                user_message=user_input,
                ai_response=response_text,
                persona_used=persona_name,
                context=rune_context,
            )

            # 최고 품질 응답 추적
            if rune_result.quality_score > best_quality:
                best_quality = rune_result.quality_score
                best_response = response_text
                best_rune_result = rune_result

            # Step 3: 품질 검증 통과 여부 확인
            if not rune_result.regenerate:
                # 품질 통과 - 즉시 반환
                print(
                    f"✅ RUNE 검증 통과 (품질: {rune_result.quality_score:.2f}, 시도: {attempt}/{max_retries})"
                )
                return (response_text, rune_result)

            # Step 4: 재생성 필요
            print(
                f"⚠️ RUNE 재생성 필요 (품질: {rune_result.quality_score:.2f}, 시도: {attempt}/{max_retries})"
            )

            if attempt < max_retries:
                # self_correct로 개선된 프롬프트 생성
                if rune_result.feedback:
                    self.rune.self_correct(
                        original_response=response_text, rune_feedback=rune_result.feedback
                    )

                    # 개선된 응답을 다음 시도의 컨텍스트로 활용
                    prompt = f"{prompt}\n\n# Previous attempt (quality: {rune_result.quality_score:.2f}):\n{response_text}\n\n# Improvement suggestion:\n{rune_result.feedback}\n\n# Please regenerate with improvements:"

        # 최대 재시도 도달 - 최고 품질 응답 반환
        print(f"⚠️ 최대 재시도 도달. 최고 품질 응답 반환 (품질: {best_quality:.2f})")
        return (best_response if best_response else response_text, best_rune_result)

    def _analyze_query_for_tools(
        self, query: str, context: Optional[Dict] = None
    ) -> List[ToolType]:
        """쿼리 분석하여 필요한 Tool 자동 선택 (Phase 1 Week 2 Task 2.2)

        Args:
            query: 사용자 쿼리
            context: 추가 컨텍스트

        Returns:
            List[ToolType]: 선택된 Tool 목록 (순서대로 실행)

        Examples:
            >>> tools = pipeline._analyze_query_for_tools("데이터 파일 읽고 분석해줘")
            >>> len(tools) >= 2  # FileIO → Tabular
            True

            >>> tools = pipeline._analyze_query_for_tools("AGI 개념 설명해줘")
            >>> tools[0] == ToolType.RAG
            True
        """
        if not self.tool_registry:
            return []

        # Tool Registry를 통한 자동 분석
        tool_chain = self.tool_registry.get_tool_chain(query, context)

        if tool_chain:
            tool_names = [tool.value for tool in tool_chain]
            print(f"🔧 Tool 자동 선택: {' → '.join(tool_names)}")

        return tool_chain

    def _execute_tool_chain(
        self, tools: List[ToolType], query: str, context: Optional[Dict] = None
    ) -> List[ToolResult]:
        """Tool Chain 순차 실행 (Phase 1 Week 2 Task 2.3)

        Args:
            tools: 실행할 Tool 목록
            query: 사용자 쿼리
            context: 실행 컨텍스트

        Returns:
            List[ToolResult]: 각 Tool의 실행 결과

        Examples:
            >>> tools = [ToolType.FILEIO, ToolType.TABULAR]
            >>> results = pipeline._execute_tool_chain(tools, "data.csv 분석")
            >>> len(results) == 2
            True
        """
        if not self.tool_registry:
            return []

        results = []
        cumulative_context = context or {}

        for i, tool in enumerate(tools):
            print(f"  → 실행 중: {tool.value} ({i+1}/{len(tools)})")

            # Tool 실행을 위한 args 구성
            tool_args = {"query": query, "context": cumulative_context}

            # 이전 Tool 결과를 다음 Tool의 컨텍스트로 전달
            if results:
                tool_args["previous_results"] = [r.data for r in results if r.success]

            # Tool 실행
            result = self.tool_registry.call_tool(tool_type=tool, args=tool_args, fallback=True)

            results.append(result)

            # 에러 발생 시 중단
            if not result.success:
                print(f"  ⚠️ Tool 실행 실패: {result.error}")
                break

        return results

    def _handle_error(self, error: Exception, context: Dict) -> PersonaResponse:
        """에러 발생 시 폴백 응답 생성

        Args:
            error: 발생한 예외
            context: 에러 컨텍스트

        Returns:
            PersonaResponse: 폴백 응답 (Nana가 조율)

        Example:
            >>> error = RuntimeError("API Error")
            >>> response = pipeline._handle_error(error, {"stage": "vertex_call"})
            >>> response.persona_used
            'Nana'
            >>> response.confidence
            0.0
        """
        # 로깅 (프로덕션에서는 실제 로거 사용)
        print(f"⚠️ 에러 발생: {type(error).__name__}: {str(error)}")
        print(f"   컨텍스트: {context}")

        # 기본 폴백 응답
        fallback_content = """죄송합니다. 요청을 처리하는 중 문제가 발생했습니다.

잠시 후 다시 시도해주시거나, 질문을 다르게 표현해주시면 감사하겠습니다.

🔧 기술 지원이 필요하시면 팀에 문의해주세요."""

        return PersonaResponse(
            content=fallback_content,
            persona_used="Nana",  # 에러 조율은 Nana가 담당
            resonance_key="error-fallback-statement",
            confidence=0.0,
            metadata={"error": str(error), "error_type": type(error).__name__, "context": context},
        )

        # ===== Multi-Persona Execution Methods (Phase 1 Week 3) =====

    def process_multi_persona(self, user_input: str, force_multi: bool = False) -> PersonaResponse:
        """복잡한 쿼리를 Multi-Persona로 처리

        쿼리 복잡도를 분석하여 자동으로 Single/Multi Persona 선택

        Args:
            user_input: 사용자 입력
            force_multi: True면 강제로 Multi-Persona 실행

        Returns:
            PersonaResponse: 병합된 최종 응답

        Examples:
            >>> # 복잡한 쿼리 → 자동 Multi-Persona
            >>> response = pipeline.process_multi_persona(
            ...     "API 구조를 설계하고 팀과 조율이 필요해요"
            ... )
            >>> response.persona_used  # 'Multi: Elro+Nana'

            >>> # 단순한 쿼리 → Single Persona
            >>> response = pipeline.process_multi_persona("안녕하세요")
            >>> response.persona_used  # 'Lua'
        """
        if not self.multi_persona_orchestrator:
            # Multi-Persona 비활성화 시 일반 처리
            return self.process(user_input)

        # Step 1: 쿼리 분석 및 실행 계획
        complexity, persona_chain = self.multi_persona_orchestrator.analyze_and_plan(user_input)

        # Step 2: 복잡도에 따라 Single vs Multi 선택
        if complexity == QueryComplexity.SIMPLE and not force_multi:
            print(f"💡 단순 쿼리 → Single Persona ({persona_chain.personas[0]}) 실행")
            return self.process(user_input)

        # Step 3: Multi-Persona 실행
        print(f"🎭 Multi-Persona 실행: {' → '.join(persona_chain.personas)}")
        print(f"   모드: {persona_chain.execution_mode.value}")
        print(f"   병합: {persona_chain.merge_strategy.value}")

        if persona_chain.execution_mode == ExecutionMode.SEQUENTIAL:
            individual_results = self._execute_sequential(user_input, persona_chain)
        elif persona_chain.execution_mode == ExecutionMode.PARALLEL:
            individual_results = self._execute_parallel(user_input, persona_chain)
        else:  # HYBRID
            individual_results = self._execute_hybrid(user_input, persona_chain)

        # Step 4: 결과 병합
        merged_content = self.multi_persona_orchestrator.merge_persona_results(
            individual_results, persona_chain
        )

        # Step 5: PersonaResponse 패키징
        return PersonaResponse(
            content=merged_content,
            persona_used=f"Multi: {'+'.join(persona_chain.personas)}",
            resonance_key="multi-persona-blend",
            confidence=0.95,  # Multi-Persona는 높은 신뢰도
            metadata={
                "complexity": complexity.value,
                "execution_mode": persona_chain.execution_mode.value,
                "merge_strategy": persona_chain.merge_strategy.value,
                "individual_personas": persona_chain.personas,
                "reasoning": persona_chain.reasoning,
            },
        )

    def _execute_sequential(self, user_input: str, persona_chain: PersonaChain) -> Dict[str, str]:
        """Sequential 실행: Persona를 순차적으로 실행

        각 Persona의 결과를 다음 Persona의 컨텍스트로 전달

        Args:
            user_input: 원본 사용자 입력
            persona_chain: 실행 체인

        Returns:
            Persona별 결과 딕셔너리

        Examples:
            >>> chain = PersonaChain(
            ...     personas=['Elro', 'Nana'],
            ...     execution_mode=ExecutionMode.SEQUENTIAL,
            ...     merge_strategy=MergeStrategy.HIERARCHICAL,
            ...     reasoning='기술 설계 후 팀 조율'
            ... )
            >>> results = pipeline._execute_sequential("API 설계", chain)
            >>> 'Elro' in results and 'Nana' in results
            True
        """
        results = {}
        accumulated_context = user_input

        for i, persona in enumerate(persona_chain.personas):
            print(f"  ⏳ {i+1}/{len(persona_chain.personas)}: {persona} 실행 중...")

            # 이전 Persona 결과를 컨텍스트에 포함
            if i > 0:
                prev_persona = persona_chain.personas[i - 1]
                accumulated_context = f"""원본 질문: {user_input}

    이전 단계 ({prev_persona}의 분석):
    {results[prev_persona]}

    위 분석을 고려하여 {persona}의 관점에서 답변해주세요."""

            # 단일 Persona로 실행 (force_single=True로 재귀 방지)
            response = self._execute_single_persona(accumulated_context, persona)
            results[persona] = response

            print(f"  ✅ {persona} 완료")

        return results

    def _execute_parallel(self, user_input: str, persona_chain: PersonaChain) -> Dict[str, str]:
        """Parallel 실행: 여러 Persona를 동시 실행

        ThreadPoolExecutor를 사용하여 병렬 처리

        Args:
            user_input: 사용자 입력
            persona_chain: 실행 체인

        Returns:
            Persona별 결과 딕셔너리

        Examples:
            >>> chain = PersonaChain(
            ...     personas=['Lua', 'Riri'],
            ...     execution_mode=ExecutionMode.PARALLEL,
            ...     merge_strategy=MergeStrategy.WEIGHTED,
            ...     reasoning='감정 지원과 데이터 분석 병렬'
            ... )
            >>> results = pipeline._execute_parallel("스트레스 분석", chain)
            >>> len(results)
            2
        """
        results = {}

        print(f"  🚀 {len(persona_chain.personas)}개 Persona 병렬 실행...")

        # ThreadPoolExecutor로 병렬 실행
        with ThreadPoolExecutor(max_workers=len(persona_chain.personas)) as executor:
            # 각 Persona에 대한 Future 생성
            future_to_persona = {
                executor.submit(self._execute_single_persona, user_input, persona): persona
                for persona in persona_chain.personas
            }

            # 결과 수집
            for future in future_to_persona:
                persona = future_to_persona[future]
                try:
                    result = future.result(timeout=30)  # 30초 타임아웃
                    results[persona] = result
                    print(f"  ✅ {persona} 완료")
                except Exception as e:
                    print(f"  ❌ {persona} 실패: {e}")
                    results[persona] = f"[{persona} 실행 오류: {str(e)}]"

        return results

    def _execute_hybrid(self, user_input: str, persona_chain: PersonaChain) -> Dict[str, str]:
        """Hybrid 실행: Sequential + Parallel 조합

        예: Elro → (Riri + Nana 병렬)

        Args:
            user_input: 사용자 입력
            persona_chain: 실행 체인

        Returns:
            Persona별 결과 딕셔너리
        """
        # 간단한 구현: 첫 번째 Sequential, 나머지 Parallel
        results = {}

        if len(persona_chain.personas) < 2:
            # Hybrid 불가능 → Sequential 폴백
            return self._execute_sequential(user_input, persona_chain)

        # Step 1: 첫 번째 Persona Sequential 실행
        first_persona = persona_chain.personas[0]
        print(f"  ⏳ 1단계: {first_persona} 실행 중...")
        first_result = self._execute_single_persona(user_input, first_persona)
        results[first_persona] = first_result
        print(f"  ✅ {first_persona} 완료")

        # Step 2: 나머지 Persona Parallel 실행 (첫 번째 결과 컨텍스트 포함)
        remaining_personas = persona_chain.personas[1:]
        context_input = f"""원본 질문: {user_input}

    이전 단계 ({first_persona}의 분석):
    {first_result}

    위 분석을 고려하여 답변해주세요."""

        print(f"  🚀 2단계: {len(remaining_personas)}개 Persona 병렬 실행...")

        with ThreadPoolExecutor(max_workers=len(remaining_personas)) as executor:
            future_to_persona = {
                executor.submit(self._execute_single_persona, context_input, persona): persona
                for persona in remaining_personas
            }

            for future in future_to_persona:
                persona = future_to_persona[future]
                try:
                    result = future.result(timeout=30)
                    results[persona] = result
                    print(f"  ✅ {persona} 완료")
                except Exception as e:
                    print(f"  ❌ {persona} 실패: {e}")
                    results[persona] = f"[{persona} 실행 오류: {str(e)}]"

        return results

    def _execute_single_persona(self, user_input: str, persona_name: str) -> str:
        """단일 Persona 실행 (Multi-Persona 내부용)

        Args:
            user_input: 입력 텍스트
            persona_name: 실행할 Persona 이름

        Returns:
            생성된 응답 텍스트
        """
        # 간소화된 단일 Persona 실행 (라우팅 생략)
        prompt = self._build_persona_prompt(
            persona_name=persona_name,
            user_input=user_input,
            resonance_key=f"{persona_name.lower()}-direct",
        )

        if self.phase_engine:
            prompt = self.phase_engine.inject_phase(prompt)

        # Vertex AI 호출
        response = self.vertex_client.send_prompt(prompt)
        return response


# CLI 테스트용 메인 블록
if __name__ == "__main__":
    print("PersonaPipeline 오프라인 테스트")
    print("=" * 60)

    # Mock Vertex Client
    class MockVertexClient:
        def send_prompt(self, prompt):
            return f"[Mock 응답] '{prompt[:30]}...'에 대한 답변입니다."

    # Pipeline 생성
    pipeline = PersonaPipeline(MockVertexClient())

    # 테스트 입력
    test_inputs = [
        "이 문제를 빨리 해결해야 해요!",
        "이게 왜 이렇게 작동하는지 궁금해요.",
        "데이터 패턴을 분석해주세요.",
    ]

    for user_input in test_inputs:
        print(f"\n입력: {user_input}")
        response = pipeline.process(user_input)
        print(f"페르소나: {response.persona_used}")
        print(f"파동키: {response.resonance_key}")
        print(f"신뢰도: {response.confidence:.2f}")
        print(f"응답: {response.content[:100]}...")
        print("-" * 60)
