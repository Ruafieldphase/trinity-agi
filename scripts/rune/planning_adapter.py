from __future__ import annotations

from collections import deque
from typing import Any, Deque, Dict, Iterable, List, Optional


class PersonaScheduler:
    """Adjust the persona cycle based on BQI coordinates and safety flags."""

    def reorder_cycle(
        self,
        base_cycle: Iterable[str],
        bqi_coordinate: Optional[Dict[str, Any]],
        safety_flags: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        order: Deque[str] = deque(base_cycle)
        if not order:
            return []

        safety_flags = safety_flags or {}
        bqi_coordinate = bqi_coordinate or {}

        # High-risk results from SAFE_pre → start from antithesis
        if safety_flags.get("dangerous_commands") or safety_flags.get("high_risk"):
            self._rotate_to(order, "antithesis")

        rhythm_phase = bqi_coordinate.get("rhythm_phase")
        if rhythm_phase == "integration":
            self._rotate_to(order, "synthesis")
        elif rhythm_phase == "reflection":
            self._rotate_to(order, "antithesis")
        elif rhythm_phase == "planning":
            self._rotate_to(order, "thesis")

        priority = bqi_coordinate.get("priority", 1)
        if priority >= 4:
            # Insert synthesis after antithesis for rapid consolidation
            if "synthesis" in order and "antithesis" in order:
                order.remove("synthesis")
                idx = list(order).index("antithesis") + 1
                order.insert(idx, "synthesis")

        return list(order)

    @staticmethod
    def _rotate_to(order: Deque[str], target: str) -> None:
        if target not in order:
            return
        while order[0] != target:
            order.rotate(-1)
