"""
Prompt phase injection utilities.

The mentoring prompts describe a three-phase cadence (attune → structure →
elevate) that should advance roughly every 280 seconds.  This module keeps an
in-memory representation of that cadence and prepends the relevant guidance to
outgoing prompts so that downstream models can react without needing access to
the original design notes.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class PhaseSnapshot:
    """Summary of the most recent phase injection."""

    phase_index: int
    phase_label: str
    guidance: str
    bqi: Dict[str, float]
    timestamp: float


class PhaseInjectionEngine:
    """Cycle phase headers and lightweight BQI metrics for prompts."""

    PHASE_LABELS = ("Attune", "Structure", "Elevate")
    GUIDANCE_TEMPLATES = (
        "Reconnect with the user's emotional state and respond with empathy.",
        "Lay out a clear plan with concrete, verifiable steps.",
        "Open the aperture with creative options or second-order effects.",
    )

    def __init__(self, interval_seconds: int = 280):
        self.interval_seconds = max(0, interval_seconds)
        self._phase_index = 0
        self._last_timestamp: Optional[float] = None
        self._snapshot: Optional[PhaseSnapshot] = None

    def inject_phase(self, base_prompt: str) -> str:
        """Prefix the prompt with the current phase directive."""
        now = time.time()
        if self._last_timestamp is None:
            self._last_timestamp = now
        elif self.interval_seconds == 0 or now - self._last_timestamp >= self.interval_seconds:
            self._phase_index = (self._phase_index + 1) % len(self.PHASE_LABELS)
            self._last_timestamp = now

        bqi_scores = self._compute_bqi(base_prompt)
        guidance = self.GUIDANCE_TEMPLATES[self._phase_index]
        phase_label = self.PHASE_LABELS[self._phase_index]

        header_lines = [
            f"[Phase {self._phase_index + 1} | {phase_label}] cadence={self.interval_seconds}s",
            (
                "BQI: "
                f"beauty={bqi_scores['beauty']:.2f} | "
                f"quality={bqi_scores['quality']:.2f} | "
                f"impact={bqi_scores['impact']:.2f}"
            ),
            f"Guidance: {guidance}",
        ]

        self._snapshot = PhaseSnapshot(
            phase_index=self._phase_index,
            phase_label=phase_label,
            guidance=guidance,
            bqi=bqi_scores,
            timestamp=now,
        )

        header = "\n".join(header_lines)
        return f"{header}\n\n{base_prompt}"

    def get_last_snapshot(self) -> Optional[Dict[str, Any]]:
        """Return the latest phase snapshot as a plain dictionary."""
        if not self._snapshot:
            return None

        return {
            "phase_index": self._snapshot.phase_index,
            "phase_label": self._snapshot.phase_label,
            "guidance": self._snapshot.guidance,
            "bqi": self._snapshot.bqi,
            "timestamp": self._snapshot.timestamp,
            "interval_seconds": self.interval_seconds,
        }

    def reset(self) -> None:
        """Reset the phase engine to the initial state."""
        self._phase_index = 0
        self._last_timestamp = None
        self._snapshot = None

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _compute_bqi(self, prompt: str) -> Dict[str, float]:
        """Derive lightweight Beauty/Quality/Impact scores for the prompt."""
        clean_prompt = prompt.strip()
        tokenised = re.findall(r"\b[\w']+\b", clean_prompt.lower())
        unique_tokens = len(set(tokenised))
        total_tokens = len(tokenised)

        length_factor = min(1.0, len(clean_prompt) / 500.0)
        variety_factor = unique_tokens / total_tokens if total_tokens else 0.0
        question_factor = min(1.0, clean_prompt.count("?") / 4.0)
        emphasis_factor = min(1.0, clean_prompt.count("!") / 6.0)

        beauty = 0.35 + variety_factor * 0.4 + question_factor * 0.15
        quality = 0.45 + length_factor * 0.4 + variety_factor * 0.1
        impact = 0.30 + emphasis_factor * 0.2 + variety_factor * 0.3

        return {
            "beauty": max(0.0, min(beauty, 1.0)),
            "quality": max(0.0, min(quality, 1.0)),
            "impact": max(0.0, min(impact, 1.0)),
        }


__all__ = ["PhaseInjectionEngine", "PhaseSnapshot"]
