from __future__ import annotations

from typing import Any, Dict

from .metrics import calculate_session_summary


def summarise_session(log_entries: Dict[str, Any]) -> Dict[str, Any]:
    """Backward compatible helper to produce session summary payloads."""
    return calculate_session_summary(log_entries)
