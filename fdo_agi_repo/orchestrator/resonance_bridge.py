"""
orchestrator/resonance_bridge.py
오케스트레이터 파이프라인과 Universal Resonance 시스템을 연결하는 브리지.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timezone

try:
    from fdo_agi_repo.universal.resonance import ResonanceStore, ResonanceEvent
    from fdo_agi_repo.universal.task_schema import AbstractIntent, DataType
except ModuleNotFoundError:
    from universal.resonance import ResonanceStore, ResonanceEvent  # type: ignore
    from universal.task_schema import AbstractIntent, DataType  # type: ignore


_RESONANCE_STORE: Optional[ResonanceStore] = None


def init_resonance_store(store_path: Optional[Path] = None):
    """Initialize global resonance store for orchestrator."""
    global _RESONANCE_STORE
    if store_path is None:
        store_path = Path("outputs/orchestrator_resonance_events.jsonl")
    _RESONANCE_STORE = ResonanceStore(store_path)


def record_task_resonance(
    task_id: str,
    task_goal: str,
    eval_report: Dict[str, Any],
    bqi_coord: Optional[Dict[str, Any]] = None,
    duration_sec: Optional[float] = None,
) -> None:
    """
    Record resonance event from orchestrator pipeline.
    
    Maps orchestrator artifacts to universal resonance format:
    - domain_id: "orchestrator" (or extract from bqi_coord if available)
    - intent: inferred from task goal (default: REASON)
    - resonance_key: "orchestrator:reason" (or dynamic)
    - metrics: quality, evidence_ok, duration
    - tags: task_id, bqi info, etc.
    """
    if _RESONANCE_STORE is None:
        # Silently skip if store not initialized
        return
    
    try:
        # Infer domain from BQI if available
        domain_id = "orchestrator"
        subdomain = None
        if bqi_coord:
            # Example: map BQI binoche/intent to domain
            binoche_val = bqi_coord.get("binoche", 0.0)
            intent_val = bqi_coord.get("intent", 0.0)
            if binoche_val > 0.7:
                subdomain = "binoche_high"
            elif intent_val > 0.7:
                subdomain = "intent_high"
        
        # Infer abstract intent (default: REASON for orchestrator tasks)
        abstract_intent = AbstractIntent.REASON.value
        
        # Build resonance key
        parts = [domain_id, abstract_intent]
        if subdomain:
            parts.append(subdomain)
        resonance_key = ":".join(parts)
        
        # Extract metrics
        quality = float(eval_report.get("quality", 0.0))
        evidence_ok = bool(eval_report.get("evidence_ok", False))
        
        metrics: Dict[str, float] = {
            "quality": quality,
            "evidence": 1.0 if evidence_ok else 0.0,
        }
        if duration_sec is not None:
            metrics["latency_ms"] = duration_sec * 1000
        
        # Tags
        tags: Dict[str, Any] = {
            "task_id": task_id,
            "task_goal_snippet": task_goal[:80],
        }
        if bqi_coord:
            tags["bqi_binoche"] = bqi_coord.get("binoche", 0.0)
            tags["bqi_quality"] = bqi_coord.get("quality", 0.0)
            tags["bqi_intent"] = bqi_coord.get("intent", 0.0)
        
        event = ResonanceEvent(
            task_id=task_id,
            resonance_key=resonance_key,
            timestamp=datetime.now(timezone.utc),
            metrics=metrics,
            tags=tags,
        )
        
        _RESONANCE_STORE.append(event)
    except Exception:
        # Logging system not wired; silently ignore
        pass
