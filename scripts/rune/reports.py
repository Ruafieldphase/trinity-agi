from __future__ import annotations

from typing import Dict


def format_resonance_summary(metrics: Dict[str, float]) -> str:
    """Human readable summary line for CLI output."""
    return (
        f"Impact {metrics.get('impact_score', 0):.2f} / "
        f"Transparency {metrics.get('transparency', 0):.2f} / "
        f"Reproducibility {metrics.get('reproducibility', 0):.2f} / "
        f"Verifiability {metrics.get('verifiability', 0):.2f}"
    )


def resonance_badge(metrics: Dict[str, float]) -> str:
    """Return a short badge string for logs."""
    impact = metrics.get("impact_score", 0)
    verifiability = metrics.get("verifiability", 0)
    if impact >= 0.75 and verifiability >= 0.75:
        return "[resonance:high]"
    if impact >= 0.5:
        return "[resonance:medium]"
    return "[resonance:low]"
