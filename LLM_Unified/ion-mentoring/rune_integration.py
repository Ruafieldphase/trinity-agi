"""
High-level integration with the RUNE self-correction loop.

This module adapts the lightweight evaluation utilities that ship with
``fdo_agi_repo`` so the ion-mentoring pipeline can decide when a response
needs another pass.  The implementation keeps the surface area intentionally
small:

* ``RUNEResult`` – a dataclass describing the quality outcome.
* ``IONRUNEIntegration`` – orchestration helper that scores responses and,
  when necessary, generates follow-up guidance.

The underlying repository currently exposes the ``rune_from_eval`` helper
instead of the full ``SelfCorrection`` engine referenced in design notes.
To stay forward compatible we keep the API flexible while relying on
deterministic heuristics that can run in offline tests.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

# Optional dependencies from the fdo_agi_repo scaffolding.  When they are not
# present we gracefully fall back to heuristic-only scoring so unit tests can
# still execute.
try:  # pragma: no cover - import path validated in dedicated tests
    from fdo_agi_repo.orchestrator.contracts import EvalReport
    from fdo_agi_repo.orchestrator.self_correction import rune_from_eval
except Exception:  # pragma: no cover - handled by graceful degradation
    EvalReport = None  # type: ignore[assignment]
    rune_from_eval = None  # type: ignore[assignment]


@dataclass
class RUNEResult:
    """Outcome of a RUNE quality evaluation."""

    quality_score: float
    feedback: str = ""
    regenerate: bool = False
    transparency_report: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Return a serialisable representation for metadata payloads."""
        return {
            "quality_score": round(self.quality_score, 3),
            "feedback": self.feedback,
            "regenerate": self.regenerate,
            "transparency_report": self.transparency_report or {},
        }


class IONRUNEIntegration:
    """Thin orchestration layer for RUNE self-correction."""

    def __init__(self, enable_rune: bool = True, quality_threshold: float = 0.7):
        self._integration_enabled = (
            enable_rune and EvalReport is not None and rune_from_eval is not None
        )
        self.quality_threshold = max(0.0, min(quality_threshold, 1.0))

    @property
    def enabled(self) -> bool:
        """Whether the backing evaluation pipeline is available."""
        return self._integration_enabled

    def analyze_response(
        self,
        user_message: str,
        ai_response: str,
        persona_used: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RUNEResult:
        """
        Score a response and decide whether another pass is required.

        When the upstream RUNE helper is unavailable a heuristic-only
        evaluation is carried out so the pipeline still obtains a useful
        signal.
        """
        if not ai_response or not ai_response.strip():
            return RUNEResult(
                quality_score=0.0,
                feedback="Response is empty – provide a concise, actionable reply.",
                regenerate=True,
                transparency_report={"reason": "empty-response"},
            )

        metrics = self._evaluate_quality(user_message, ai_response, persona_used)

        if not self.enabled:
            regenerate = metrics["score"] < self.quality_threshold
            feedback = self._format_feedback(metrics["recommendations"])
            transparency = {
                "source": "heuristic",
                "metrics": metrics,
                "risks": metrics.get("risks", []),
            }
            return RUNEResult(
                quality_score=metrics["score"],
                feedback=feedback,
                regenerate=regenerate,
                transparency_report=transparency,
            )

        eval_report = self._build_eval_report(metrics, context or {})
        rune_report = rune_from_eval(eval_report)  # type: ignore[operator]
        regenerate = bool(rune_report.replan) or rune_report.impact < self.quality_threshold

        feedback_items: List[str] = list(metrics["recommendations"])
        feedback_items.extend(rune_report.recommendations)

        transparency = {
            "impact": round(rune_report.impact, 3),
            "transparency": round(rune_report.transparency, 3),
            "confidence": round(rune_report.confidence, 3),
            "risks": rune_report.risks,
            "recommendations": rune_report.recommendations,
            "heuristics": metrics,
        }

        return RUNEResult(
            quality_score=round(rune_report.impact, 3),
            feedback=self._format_feedback(feedback_items),
            regenerate=regenerate,
            transparency_report=transparency,
        )

    def self_correct(
        self,
        original_response: str,
        rune_feedback: str,
        max_retries: int = 2,
    ) -> str:
        """Apply feedback to improve a response in-place."""
        if not rune_feedback.strip():
            return original_response

        suggestions = self._tokenise_feedback(rune_feedback)
        if not suggestions:
            return original_response

        improved = original_response.strip()
        for _ in range(max(1, max_retries)):
            improved = self._apply_suggestions(improved, suggestions)
            if len(improved.split()) >= max(len(original_response.split()), 48):
                break

        return improved

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #

    def _evaluate_quality(
        self,
        user_message: str,
        ai_response: str,
        persona_used: str,
    ) -> Dict[str, Any]:
        """Light-weight heuristics that approximate a quality score."""
        response_words = ai_response.split()
        response_length = len(response_words)
        unique_words = len(set(w.lower() for w in response_words if w))

        # Length scoring: 50단어를 기준으로 부드럽게 증가 (너무 짧지만 않으면 OK)
        # 10단어 이하: 매우 낮음, 20단어: 0.4, 40단어: 0.8, 60+: 1.0
        if response_length < 10:
            length_score = 0.1
        elif response_length < 30:
            length_score = 0.5 + (response_length - 10) / 40  # 10~30단어: 0.5~1.0
        else:
            length_score = min(1.0, 0.5 + response_length / 60.0)

        diversity_score = unique_words / response_length if response_length else 0.0

        # 키워드 추출: 조사 제거 및 어간 추출
        topic_keywords = []
        for token in re.findall(r"\b[\w']+\b", user_message.lower()):
            if len(token) > 2:
                # 한국어 조사 제거 (의, 을, 를, 이, 가, 은, 는, 에, 에서, 로, 으로 등)
                cleaned = re.sub(r"(의|을|를|이|가|은|는|에서|에|로|으로|과|와)$", "", token)
                if cleaned and len(cleaned) > 1:
                    topic_keywords.append(cleaned)

        # 불용어 제거 (요청 동사, 조사, 일반적 표현 등)
        stopwords = {
            "이를",
            "있는",
            "것을",
            "것",
            "해주",
            "세요",
            "주세요",
            "하",
            "하세요",
            "설명해주",
            "알려주",
            "말해주",
            "가르쳐주",
            "보여주",  # 요청 동사
            "무엇",
            "어떻게",
            "왜",
            "언제",
            "어디",  # 의문사
        }
        topic_keywords = [kw for kw in topic_keywords if kw not in stopwords]

        # 응답에서도 조사를 제거한 토큰으로 매칭
        response_tokens = set()
        for token in re.findall(r"\b[\w']+\b", ai_response.lower()):
            cleaned = re.sub(r"(의|을|를|이|가|은|는|에서|에|로|으로|과|와)$", "", token)
            if cleaned:
                response_tokens.add(cleaned)

        matched_keywords = sum(1 for token in topic_keywords if token in response_tokens)
        coverage_score = matched_keywords / len(topic_keywords) if topic_keywords else 0.6

        structural_markers = ["\n-", "\n*", "\n1.", "\n2.", "\u2022"]
        structure_score = (
            0.2 if any(marker in ai_response for marker in structural_markers) else 0.0
        )
        persona_alignment = (
            0.1
            if persona_used.lower() in ai_response.lower()
            or persona_used.lower() in user_message.lower()
            else 0.0
        )

        # 불확실한 표현 감지 (품질 저하 요인)
        uncertainty_markers = [
            "아마도",
            "것 같",
            "모르겠",
            "아닐까",
            "인 듯",
            "maybe",
            "perhaps",
            "probably",
        ]
        has_uncertainty = any(marker in ai_response.lower() for marker in uncertainty_markers)
        uncertainty_penalty = 0.3 if has_uncertainty else 0.0

        # 너무 짧은 응답 페널티 (10단어 미만)
        short_response_penalty = 0.4 if response_length < 10 else 0.0

        base_score = 0.35 + length_score * 0.35 + coverage_score * 0.2
        base_score += structure_score + persona_alignment + diversity_score * 0.1
        base_score -= uncertainty_penalty + short_response_penalty
        score = max(0.1, min(base_score, 1.0))

        recommendations: List[str] = []
        risks: List[str] = []

        # 불확실성 페널티가 적용된 경우
        if has_uncertainty:
            recommendations.append("Provide more confident and definitive answers.")
            risks.append("uncertain-response")

        # 짧은 응답 페널티가 적용된 경우
        if response_length < 10:
            recommendations.append("Provide more detailed explanation with examples.")
            risks.append("too-short-response")

        # 윤리적 위험 키워드 탐지
        ethical_keywords = ["차별", "편견", "혐오", "배제", "discrimination", "bias", "hate"]
        if any(keyword in ai_response.lower() for keyword in ethical_keywords):
            risks.append("ETHICAL-RISK-DETECTED")
            recommendations.append("Review content for potential ethical concerns.")

        if length_score < 0.5:
            recommendations.append("Expand the response with at least one concrete recommendation.")
            risks.append("insufficient-detail")

        if coverage_score < 0.3:  # 0.5 → 0.3으로 완화 (고품질 응답도 일부 키워드 누락 가능)
            recommendations.append("Address the main nouns or verbs used in the user's request.")
            risks.append("low-topic-coverage")

        if structure_score == 0.0:
            recommendations.append("Organise the answer with short paragraphs or bullet points.")

        if diversity_score < 0.35:
            recommendations.append("Introduce varied vocabulary to avoid repeating the same words.")

        return {
            "score": round(score, 3),
            "length_score": round(length_score, 3),
            "coverage_score": round(coverage_score, 3),
            "diversity_score": round(diversity_score, 3),
            "persona_alignment": round(persona_alignment, 3),
            "recommendations": recommendations,
            "risks": risks,
        }

    def _build_eval_report(
        self,
        metrics: Dict[str, Any],
        context: Dict[str, Any],
    ) -> "EvalReport":
        """Translate heuristic metrics into the RUNE EvalReport contract."""
        task_id = (
            context.get("task_id")
            or context.get("request_id")
            or f"persona-{context.get('persona', 'unknown')}"
        )
        evidence_ok = metrics["coverage_score"] >= 0.5 or metrics["length_score"] >= 0.6
        return EvalReport(  # type: ignore[call-arg,return-value]
            task_id=str(task_id),
            quality=metrics["score"],
            evidence_ok=evidence_ok,
            risks=metrics["risks"],
            notes="persona_pipeline_auto_eval",
        )

    @staticmethod
    def _format_feedback(recommendations: Sequence[str]) -> str:
        """Render feedback items as a newline separated bullet list."""
        seen = set()
        deduped: List[str] = []
        for item in recommendations:
            normalised = item.strip()
            if normalised and normalised.lower() not in seen:
                deduped.append(normalised)
                seen.add(normalised.lower())
        return "\n".join(f"- {item}" for item in deduped)

    @staticmethod
    def _tokenise_feedback(feedback: str) -> List[str]:
        """Split feedback paragraphs into actionable bullet items."""
        tokens = [
            line.strip("-" + "\u2022" + " ").strip()
            for line in feedback.splitlines()
            if line.strip()
        ]
        return [token for token in tokens if token]

    @staticmethod
    def _apply_suggestions(response: str, suggestions: Sequence[str]) -> str:
        """Append missing suggestions to the response in a structured way."""
        missing = [
            suggestion for suggestion in suggestions if suggestion.lower() not in response.lower()
        ]
        if not missing:
            return response

        addition_lines = "\n".join(f"- {suggestion}" for suggestion in missing)
        if "Improvement suggestions:" in response:
            return f"{response}\n{addition_lines}"

        return f"{response}\n\nImprovement suggestions:\n{addition_lines}"


@dataclass
class ResponseQualityMetrics:
    """Structured view of a RUNE evaluation."""

    overall_quality: float
    regenerate: bool
    feedback: str
    transparency: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_quality": round(self.overall_quality, 3),
            "regenerate": self.regenerate,
            "feedback": self.feedback,
            "transparency": self.transparency,
        }


class RUNEValidator:
    """
    High-level validator used by routing components.

    This class mirrors the interface expected by the existing mentoring
    codebase while delegating the heavy lifting to ``IONRUNEIntegration``.
    """

    def __init__(self, quality_threshold: float = 0.7, enable_rune: bool = True):
        self.quality_threshold = quality_threshold
        self._integration = IONRUNEIntegration(
            enable_rune=enable_rune,
            quality_threshold=quality_threshold,
        )

    def run_rune_check(
        self,
        task_id: str,
        query: str,
        response: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        persona = (context or {}).get("persona", "unknown")

        # RUNE이 비활성화되어도 heuristic 평가는 수행
        result = self._integration.analyze_response(
            user_message=query,
            ai_response=response,
            persona_used=persona,
            context=context or {},
        )

        metrics = ResponseQualityMetrics(
            overall_quality=result.quality_score,
            regenerate=result.regenerate,
            feedback=result.feedback,
            transparency=result.transparency_report or {},
        )

        # Extract risks with robust fallbacks:
        # 1) transparency.metrics.risks (heuristic mode)
        # 2) transparency.risks (full RUNE mode)
        # 3) transparency.heuristics.risks (ensure heuristic risks surface)
        transparency = result.transparency_report or {}
        inner_metrics = transparency.get("metrics", {})
        risks = inner_metrics.get("risks", [])
        if not risks:
            risks = transparency.get("risks", []) or []
        if not risks:
            risks = (transparency.get("heuristics") or {}).get("risks", []) or []

        return {
            "task_id": task_id,
            "metrics": metrics.to_dict(),
            "should_replan": result.regenerate,
            "feedback": result.feedback,
            "transparency": transparency,
            "risks": risks,
        }


__all__ = [
    "RUNEResult",
    "IONRUNEIntegration",
    "RUNEValidator",
    "ResponseQualityMetrics",
]
