"""
프롬프트 빌더 구현

Week 5-6: 프롬프트 생성 전략 패턴
- 각 페르소나별 빌더
- 템플릿 기반 구성
- 컨텍스트 활용
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..base import AbstractPromptBuilder
from ..models import ChatContext, Intent, Pace, Tone

logger = logging.getLogger(__name__)


class BasePromptBuilder(AbstractPromptBuilder, ABC):
    """프롬프트 빌더 기본 클래스"""

    def __init__(self, persona_name: str):
        """초기화

        Args:
            persona_name: 페르소나 이름
        """
        self.persona_name = persona_name
        self.system_prompt = self.get_system_prompt()

    @abstractmethod
    def get_system_prompt(self) -> str:
        """시스템 프롬프트 반환"""
        pass

    @abstractmethod
    def get_template(self) -> str:
        """프롬프트 템플릿 반환"""
        pass

    def build(
        self,
        user_input: str,
        resonance_key: str,
        context: Optional[ChatContext] = None,
        *,
        mode: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """프롬프트 구성

        Args:
            user_input: 사용자 입력
            resonance_key: 파동키
            context: 대화 컨텍스트

        Returns:
            구성된 프롬프트
        """
        template = self.get_template()

        # 파동키 파싱
        tone, pace, intent = self._parse_resonance_key(resonance_key)

        # 컨텍스트 준비
        context_text = self._build_context(context, tone, pace, intent)

        # 최근 대화 이력
        history_text = self._build_history(context)

        # 경량 요약 모드 처리: 시스템 프롬프트/템플릿을 간소화하여 토큰을 절감
        if (mode == "summary_light") or ((options or {}).get("summary_light")):
            return self._build_compact_prompt(
                user_input=user_input,
                tone=tone,
                pace=pace,
                intent=intent,
                context=context,
            )

        # 프롬프트 구성
        prompt = template.format(
            system_prompt=self.system_prompt,
            user_input=user_input,
            tone=tone.value,
            pace=pace.value,
            intent=intent.value,
            context=context_text,
            history=history_text,
            persona_name=self.persona_name,
        )

        return prompt

    def _build_compact_prompt(
        self,
        *,
        user_input: str,
        tone: Tone,
        pace: Pace,
        intent: Intent,
        context: Optional[ChatContext] = None,
    ) -> str:
        """경량 요약 모드 전용 컴팩트 프롬프트

        - 긴 시스템 프롬프트/템플릿 대신 최소 지시어만 사용
        - 요약 지침을 간결하게 포함 (불릿 3개 이하, 80단어 이내 등)
        - 대화 이력은 최대 1~2개로 축약
        """
        # 축약 시스템 지시어
        compact_sys = (
            f"You are {self.persona_name}. Provide a concise summary. "
            "Keep it clear, avoid fluff."
        )

        # 러닝 요약이 있으면 먼저 포함
        running_summary_block = ""
        try:
            if context and getattr(context, "custom_context", None):
                rs = context.custom_context.get("running_summary")
                if isinstance(rs, str) and rs.strip():
                    running_summary_block = rs.strip().replace("\n", " ")
        except Exception:
            running_summary_block = ""

        # 히스토리는 최대 2개로만 포함
        history_lines = []
        if context and context.message_history:
            recent = context.get_recent_messages(2)
            for msg in recent:
                role = "User" if msg.get("role") == "user" else "Assistant"
                content = (msg.get("content") or "").strip().replace("\n", " ")
                if content:
                    history_lines.append(f"{role}: {content[:120]}...")
        history_block = "\n".join(history_lines) if history_lines else ""

        # 최종 컴팩트 프롬프트 구성
        parts = [
            compact_sys,
            f"Tone={tone.value}; Pace={pace.value}; Intent={intent.value}",
        ]
        if running_summary_block:
            parts.append("RunningSummary:")
            parts.append(running_summary_block)
        if history_block:
            parts.append("Recent:")
            parts.append(history_block)
        parts.append("Input:")
        parts.append(user_input)
        parts.append(
            "Output as: \n- 1-3 concise bullet points\n- <= 80 words total\n- No preface or closing."
        )
        return "\n".join(parts)

    @staticmethod
    def _parse_resonance_key(resonance_key: str) -> tuple:
        """파동키 파싱"""
        parts = resonance_key.split("-")
        if len(parts) >= 3:
            try:
                tone = Tone(parts[0])
                pace = Pace(parts[1])

                # intent는 underscore와 dash를 모두 지원
                intent_raw = parts[2]
                intent_normalized = intent_raw.replace("_", "-")

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
                        intent = Intent.LEARNING

                return tone, pace, intent
            except ValueError:
                pass

        return Tone.CALM, Pace.MEDIUM, Intent.LEARNING

    @staticmethod
    def _build_context(
        context: Optional[ChatContext], tone: Tone, pace: Pace, intent: Intent
    ) -> str:
        """컨텍스트 텍스트 구성"""
        if not context:
            return "No additional context"

        parts = []
        if context.user_id:
            parts.append(f"User ID: {context.user_id}")
        if context.session_id:
            parts.append(f"Session ID: {context.session_id}")
        if context.persona_preference:
            parts.append(f"Preferred Persona: {context.persona_preference}")

        parts.extend(
            [
                f"Current Tone: {tone.value}",
                f"Conversation Pace: {pace.value}",
                f"User Intent: {intent.value}",
            ]
        )

        return "\n".join(parts)

    @staticmethod
    def _build_history(context: Optional[ChatContext]) -> str:
        """대화 이력 텍스트 구성"""
        if not context or not context.message_history:
            return "No previous messages"

        recent = context.get_recent_messages(3)
        history_parts = []

        for msg in recent:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_parts.append(f"{role}: {msg['content'][:100]}...")

        return "\n".join(history_parts)


class LuaPromptBuilder(BasePromptBuilder):
    """루아 프롬프트 빌더"""

    def get_system_prompt(self) -> str:
        """루아 시스템 프롬프트"""
        return """당신은 Lua(루아)입니다. 따뜻하고 공감적이며 창의적인 AI 멘토입니다.

당신의 역할:
- 사용자의 감정을 깊이 이해하고 진심으로 공감합니다
- 창의적이고 혁신적인 해결책을 제시합니다
- 격려와 동기부여를 제공하여 사용자를 북돋습니다

응답 스타일:
- 톤: 따뜻하고 친근하며 격려적
- 이모지: ✨💡🌊🎨💫 적절히 활용
- 공감: 사용자의 감정을 먼저 인정"""

    def get_template(self) -> str:
        """루아 프롬프트 템플릿"""
        return """{system_prompt}

**현재 상황**:
- 사용자 톤: {tone}
- 대화 속도: {pace}
- 사용자 의도: {intent}

**컨텍스트**:
{context}

**이전 대화**:
{history}

**사용자 메시지**:
{user_input}

**루아의 공감적이고 창의적인 응답**:"""


class ElroPromptBuilder(BasePromptBuilder):
    """엘로 프롬프트 빌더"""

    def get_system_prompt(self) -> str:
        """엘로 시스템 프롬프트"""
        return """당신은 Elro(엘로)입니다. 논리적이고 체계적인 기술 아키텍트입니다.

당신의 역할:
- 기술적 개념을 명확하고 체계적으로 설명합니다
- 구조적이고 단계별 접근 방식을 제공합니다
- 코드 설계 패턴과 베스트 프랙티스를 제시합니다

응답 스타일:
- 톤: 논리적이고 차분하며 정확함
- 구조: 번호 매기기, 섹션 나누기, 계층 구조
- 예시: 코드 스니펫, 명확한 예제"""

    def get_template(self) -> str:
        """엘로 프롬프트 템플릿"""
        return """{system_prompt}

**분석 요청**:
{user_input}

**컨텍스트**:
{context}

**엘로의 체계적이고 명확한 응답**:

1. **문제 분석**:

2. **해결 방안**:

3. **구현 가이드**:

4. **주의 사항**:"""


class RiriPromptBuilder(BasePromptBuilder):
    """리리 프롬프트 빌더"""

    def get_system_prompt(self) -> str:
        """리리 시스템 프롬프트"""
        return """당신은 Riri(리리)입니다. 분석적이고 균형 잡힌 데이터 전문가입니다.

당신의 역할:
- 데이터 기반의 객관적인 인사이트를 제공합니다
- 객관적이고 균형 잡힌 시각을 유지합니다
- 패턴과 트렌드를 분석하여 설명합니다

응답 스타일:
- 톤: 분석적이고 중립적이며 정량적
- 구조: 데이터 → 인사이트 → 권장사항
- 시각화: 표, 수치 제안"""

    def get_template(self) -> str:
        """리리 프롬프트 템플릿"""
        return """{system_prompt}

**분석 요청**:
{user_input}

**컨텍스트**:
{context}

**리리의 데이터 기반 분석**:

1. **데이터 수집**:

2. **패턴 분석**:

3. **인사이트**:

4. **권장사항**:"""


class NanaPromptBuilder(BasePromptBuilder):
    """나나 프롬프트 빌더"""

    def get_system_prompt(self) -> str:
        """나나 시스템 프롬프트"""
        return """당신은 Nana(나나)입니다. 팀 조율과 협력을 중심으로 하는 프로세스 매니저입니다.

당신의 역할:
- 팀 간 협력과 소통을 촉진합니다
- 전체적인 관점에서 상황을 이해하고 설명합니다
- 프로세스와 절차를 명확히 정의합니다

응답 스타일:
- 톤: 협력적이고 포용적이며 실행 지향적
- 구조: 관계 → 프로세스 → 실행 계획
- 포함: 모든 이해관계자 고려"""

    def get_template(self) -> str:
        """나나 프롬프트 템플릿"""
        return """{system_prompt}

**팀 상황**:
{user_input}

**컨텍스트**:
{context}

**나나의 협력 중심 조율**:

1. **상황 이해**:

2. **커뮤니케이션 계획**:

3. **프로세스**:

4. **실행 계획**:"""


class PromptBuilderFactory:
    """프롬프트 빌더 팩토리"""

    _builders = {
        "Lua": LuaPromptBuilder,
        "Elro": ElroPromptBuilder,
        "Riri": RiriPromptBuilder,
        "Nana": NanaPromptBuilder,
    }

    @classmethod
    def create(cls, persona_name: str) -> BasePromptBuilder:
        """빌더 생성

        Args:
            persona_name: 페르소나 이름

        Returns:
            프롬프트 빌더

        Raises:
            ValueError: 알 수 없는 페르소나
        """
        builder_class = cls._builders.get(persona_name)
        if not builder_class:
            raise ValueError(f"Unknown persona: {persona_name}")

        return builder_class(persona_name)

    @classmethod
    def get_available_personas(cls) -> list:
        """사용 가능한 페르소나 목록"""
        return list(cls._builders.keys())

    @classmethod
    def register(cls, persona_name: str, builder_class: type):
        """커스텀 빌더 등록

        Args:
            persona_name: 페르소나 이름
            builder_class: 빌더 클래스
        """
        cls._builders[persona_name] = builder_class
