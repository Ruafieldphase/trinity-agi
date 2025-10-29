from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from scripts.evaluation.metrics import calculate_resonance_metrics


@dataclass
class ResonanceReport:
    summary: str
    metrics: Dict[str, Any]
    plan_adjustment: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "type": "resonance_report",
            "summary": self.summary,
            "metrics": self.metrics,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if self.plan_adjustment:
            payload["plan_adjustment"] = self.plan_adjustment
        return payload


class RUNEAnalyzer:
    """Analyse synthesis output and generate resonance-aware feedback."""

    def __init__(self) -> None:
        self._last_metrics: Optional[Dict[str, Any]] = None

    def analyse(self, results: List[Dict[str, Any]], plan: Any) -> Optional[ResonanceReport]:
        if not results:
            return None

        synthesis_payload = self._pick_latest_synthesis(results)
        if synthesis_payload is None:
            return None

        response_text = synthesis_payload.get("content", "")
        tools_used = plan.metadata.get("tools_used", []) if hasattr(plan, "metadata") else []
        facts_verified = synthesis_payload.get("facts_verified", 0)
        facts_total = synthesis_payload.get("facts_total", 0)
        reproducible = synthesis_payload.get("reproducible", True)
        external_refs = synthesis_payload.get("references", [])

        metrics = calculate_resonance_metrics(
            response=response_text,
            tools_used=tools_used,
            facts_verified=facts_verified,
            facts_total=facts_total,
            reproducible=reproducible,
            external_references=external_refs,
        )
        self._last_metrics = metrics

        summary = self._summarise(metrics, response_text)
        plan_adjustment = self._maybe_adjust_plan(metrics)
        return ResonanceReport(summary=summary, metrics=metrics, plan_adjustment=plan_adjustment)

    def last_metrics(self) -> Optional[Dict[str, Any]]:
        return self._last_metrics

    @staticmethod
    def _summarise(metrics: Dict[str, Any], response_text: str) -> str:
        impact = metrics["impact_score"]
        transparency = metrics["transparency"]
        reproducibility = metrics["reproducibility"]
        verifiability = metrics["verifiability"]

        headline = (
            f"Impact {impact:.2f} / Transparency {transparency:.2f} / "
            f"Reproducibility {reproducibility:.2f} / Verifiability {verifiability:.2f}"
        )
        excerpt = response_text[:180].replace("\n", " ").strip()
        return f"{headline}\nExcerpt: {excerpt}"

    @staticmethod
    def _maybe_adjust_plan(metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        adjustments: Dict[str, Any] = {}
        if metrics["verifiability"] < 0.6:
            adjustments["stage"] = "recap"
            adjustments["action"] = "increase_fact_checking"
        elif metrics["impact_score"] < 0.5:
            adjustments["stage"] = "explore"
            adjustments["action"] = "expand_thesis_examples"

        if adjustments:
            return adjustments
        return None

    @staticmethod
    def _pick_latest_synthesis(results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        for item in reversed(results):
            if item.get("persona") == "synthesis":
                return item
        return None
