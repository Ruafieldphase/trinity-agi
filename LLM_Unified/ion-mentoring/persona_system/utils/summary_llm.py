#!/usr/bin/env python3
"""
LLM 기반 대화 요약 (Gemini)
규칙 기반 요약 대비 품질 향상 목표
"""

import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class LLMSummarizer:
    """Gemini 기반 대화 요약"""

    def __init__(self, model: str = "gemini-2.0-flash-exp"):
        """
        초기화

        Args:
            model: Gemini 모델명
        """
        self.model = model
        self.client = None
        self.available = False

        # Gemini 클라이언트 초기화
        try:
            from google import genai
            from google.genai import types

            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                logger.warning("GOOGLE_API_KEY not set. LLM summarization unavailable.")
                return

            self.client = genai.Client(api_key=api_key)
            self.types = types
            self.available = True
            logger.info(f"Gemini LLM Summarizer initialized: {model}")

        except ImportError as e:
            logger.warning(f"Gemini import failed: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")

    def summarize(
        self,
        messages: List[Dict[str, str]],
        *,
        max_bullets: int = 6,
        max_chars: int = 600,
        temperature: float = 0.3,
    ) -> str:
        """
        대화 요약 (LLM 기반)

        Args:
            messages: 메시지 목록 [{"role": "user/assistant", "content": "..."}]
            max_bullets: 최대 불릿 수
            max_chars: 최대 글자 수
            temperature: LLM temperature

        Returns:
            요약 문자열 (불릿 리스트 형태)
        """
        if not self.available or not self.client:
            logger.warning("LLM summarizer not available. Use rule-based fallback.")
            return self._rule_based_fallback(messages, max_bullets, max_chars)

        # 프롬프트 생성
        prompt = self._build_prompt(messages, max_bullets, max_chars)

        try:
            # Gemini API 호출
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=self.types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_chars,
                    top_p=0.95,
                ),
            )

            # 응답 파싱
            if response.text:
                summary = response.text.strip()
                # 글자 수 제한
                if len(summary) > max_chars:
                    summary = summary[:max_chars] + "..."
                return summary
            else:
                logger.warning("Empty response from Gemini")
                return self._rule_based_fallback(messages, max_bullets, max_chars)

        except Exception as e:
            logger.error(f"Gemini summarization failed: {e}")
            return self._rule_based_fallback(messages, max_bullets, max_chars)

    def _build_prompt(
        self, messages: List[Dict[str, str]], max_bullets: int, max_chars: int
    ) -> str:
        """
        요약 프롬프트 생성

        Args:
            messages: 메시지 목록
            max_bullets: 최대 불릿 수
            max_chars: 최대 글자 수

        Returns:
            프롬프트 문자열
        """
        # 대화 텍스트 생성
        conversation = "\n".join(
            f"{msg.get('role', 'unknown').upper()}: {msg.get('content', '')}"
            for msg in messages
        )

        prompt = f"""다음 대화를 간결하게 요약해주세요.

<대화>
{conversation}
</대화>

<요구사항>
- 최대 {max_bullets}개의 불릿 포인트로 요약
- 각 불릿은 "- " 로 시작
- 전체 길이는 {max_chars}자 이내
- 핵심 주제와 결론에 집중
- 한국어로 작성

<출력 형식>
- 첫 번째 핵심 내용
- 두 번째 핵심 내용
...
"""
        return prompt

    def _rule_based_fallback(
        self, messages: List[Dict[str, str]], max_bullets: int, max_chars: int
    ) -> str:
        """
        규칙 기반 폴백 (LLM 실패 시)

        Args:
            messages: 메시지 목록
            max_bullets: 최대 불릿 수
            max_chars: 최대 글자 수

        Returns:
            규칙 기반 요약
        """
        from .summary_utils import update_running_summary

        # 규칙 기반 요약 사용
        return update_running_summary(
            running_summary=None,
            new_messages=messages,
            max_bullets=max_bullets,
            max_chars=max_chars,
        )


# 싱글톤 인스턴스
_llm_summarizer: Optional[LLMSummarizer] = None


def get_llm_summarizer(model: str = "gemini-2.0-flash-exp") -> LLMSummarizer:
    """LLM Summarizer 싱글톤 반환"""
    global _llm_summarizer
    if _llm_summarizer is None:
        _llm_summarizer = LLMSummarizer(model=model)
    return _llm_summarizer


def summarize_with_llm(
    messages: List[Dict[str, str]],
    *,
    max_bullets: int = 6,
    max_chars: int = 600,
    temperature: float = 0.3,
) -> str:
    """
    대화 요약 (편의 함수)

    Args:
        messages: 메시지 목록
        max_bullets: 최대 불릿 수
        max_chars: 최대 글자 수
        temperature: LLM temperature

    Returns:
        요약 문자열
    """
    summarizer = get_llm_summarizer()
    return summarizer.summarize(
        messages, max_bullets=max_bullets, max_chars=max_chars, temperature=temperature
    )
