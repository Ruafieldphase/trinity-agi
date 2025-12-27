#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vertex AI / Google AI Studio Smart Router (minimal, safe-by-default)

왜 필요한가
- 여러 스크립트가 `VertexAISmartRouter` 또는 `get_router()`를 임포트하지만,
  파일이 비어있으면(0 bytes) "접속 실패처럼 보이는" import error가 계속 로그에 쌓인다.
- 이 라우터는 네트워크가 가능한 환경에서만 실제 LLM 호출을 수행한다.

원칙
- 키/자격증명 원문 출력 금지
- 실패해도 "프로세스가 죽지 않게" 예외 메시지를 간단히 전달
- 기본은 Google AI Studio(API Key) → Vertex AI(Project) 순으로 시도
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Optional


def _extract_text(resp: Any) -> str:
    """
    genai/vertex 응답 객체에서 텍스트를 최대한 안전하게 뽑는다.
    """
    if resp is None:
        return ""
    # google.generativeai response
    t = getattr(resp, "text", None)
    if isinstance(t, str):
        return t
    # vertexai response candidates fallback
    try:
        candidates = getattr(resp, "candidates", None)
        if candidates:
            parts = []
            for cand in candidates:
                content = getattr(cand, "content", None)
                if not content:
                    continue
                for part in getattr(content, "parts", []) or []:
                    pt = getattr(part, "text", None)
                    if isinstance(pt, str):
                        parts.append(pt)
            return "\n".join([p for p in parts if p])
    except Exception:
        pass
    return str(resp)


@dataclass
class RouterStatus:
    backend: str
    ok: bool
    reason: str


class VertexAISmartRouter:
    """
    목적: task_hint(작업 힌트)에 따라 모델 후보를 선택하고, LLM 호출을 수행한다.

    호환성:
    - `generate(prompt, task_hint=...)` 형태를 제공(레거시 스크립트 호환)
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.logger = logger or logging.getLogger("VertexAISmartRouter")
        self.project_id = project_id or os.getenv("VERTEXAI_PROJECT") or os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location or os.getenv("VERTEXAI_LOCATION") or os.getenv("GCP_LOCATION") or os.getenv("GOOGLE_CLOUD_LOCATION") or "us-central1"

        # Lazy import: services/model_selector.py (centralized backend selection)
        self._selector = None

    def _get_selector(self):
        if self._selector is not None:
            return self._selector
        try:
            from services.model_selector import ModelSelector  # type: ignore

            self._selector = ModelSelector(project=self.project_id, location=self.location, logger=self.logger)
        except Exception as e:
            self._selector = None
            self.logger.warning(f"ModelSelector unavailable: {e}")
        return self._selector

    def status(self) -> RouterStatus:
        sel = self._get_selector()
        if sel is None:
            return RouterStatus(backend="none", ok=False, reason="ModelSelector import/init failed")
        if not getattr(sel, "available", False):
            return RouterStatus(backend="none", ok=False, reason="No backend available (missing key/credentials)")
        return RouterStatus(backend=str(getattr(sel, "backend", "unknown")), ok=True, reason="ok")

    def generate(self, prompt: str, task_hint: str = "auto", **kwargs) -> str:
        """
        task_hint 예:
        - quick_answer / status_check: 빠른 응답
        - deep_analysis / philosophy: 고정밀
        """
        sel = self._get_selector()
        if sel is None or not getattr(sel, "available", False):
            raise RuntimeError("No AI backend available (check GOOGLE_API_KEY or Vertex credentials)")

        hint = (task_hint or "").lower().strip()
        high_precision = hint in {"deep_analysis", "philosophy", "complex", "analysis", "modify", "create", "verify"}
        urgency = hint in {"quick_answer", "status_check", "fast", "quick"}
        text_length = len(prompt or "")

        resp, model_used = sel.try_generate_content(
            prompt,
            intent="MODIFY" if high_precision else "READ",
            text_length=text_length,
            urgency=urgency,
            high_precision=high_precision,
            generation_config={"temperature": 0.3 if high_precision else 0.35},
            **kwargs,
        )
        if resp is None:
            raise RuntimeError("LLM call failed (see prior warnings for details)")
        out = _extract_text(resp).strip()
        if not out:
            raise RuntimeError(f"Empty response from model={model_used or 'unknown'}")
        return out


_ROUTER_SINGLETON: VertexAISmartRouter | None = None


def get_router(project_id: Optional[str] = None, location: Optional[str] = None) -> VertexAISmartRouter:
    global _ROUTER_SINGLETON
    if _ROUTER_SINGLETON is None:
        _ROUTER_SINGLETON = VertexAISmartRouter(project_id=project_id, location=location)
    return _ROUTER_SINGLETON

