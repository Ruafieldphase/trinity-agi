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
_RESONANCE_CONFIG: Optional[Dict[str, Any]] = None
_LAST_SNAPSHOT_TS: Optional[float] = None


def init_resonance_store(store_path: Optional[Path] = None):
    """Initialize global resonance store for orchestrator."""
    global _RESONANCE_STORE
    if store_path is None:
        store_path = Path("outputs/orchestrator_resonance_events.jsonl")
    _RESONANCE_STORE = ResonanceStore(store_path)


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        if path.exists():
            import json
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def load_resonance_config(force_reload: bool = False) -> Dict[str, Any]:
    """Load resonance config from configs/resonance_config.json or example.

    Returns sane defaults when none found or invalid.
    """
    global _RESONANCE_CONFIG
    if _RESONANCE_CONFIG is not None and not force_reload:
        return _RESONANCE_CONFIG

    import os
    cfg_path = os.environ.get("RESONANCE_CONFIG")
    if cfg_path:
        cfg = _load_json(Path(cfg_path))
        if isinstance(cfg, dict):
            _RESONANCE_CONFIG = cfg
            return cfg

    # Default locations
    base = Path("configs")
    primary = base / "resonance_config.json"
    example = base / "resonance_config.example.json"

    cfg = _load_json(primary) or _load_json(example) or {}

    # Defaults
    if "active_mode" not in cfg:
        cfg["active_mode"] = "observe"
    if "default_policy" not in cfg:
        cfg["default_policy"] = "quality-first"
    if "policies" not in cfg or not isinstance(cfg.get("policies"), dict):
        cfg["policies"] = {
            "quality-first": {"min_quality": 0.8, "require_evidence": True, "max_latency_ms": 8000}
        }
    # Throttle period for closed-loop snapshot (sec)
    try:
        period = int(cfg.get("closed_loop_snapshot_period_sec", 300))
        cfg["closed_loop_snapshot_period_sec"] = max(1, period)
    except Exception:
        cfg["closed_loop_snapshot_period_sec"] = 300

    _RESONANCE_CONFIG = cfg
    return cfg


def get_active_mode() -> str:
    cfg = load_resonance_config()
    mode = str(cfg.get("active_mode", "observe")).lower()
    if mode not in {"disabled", "observe", "enforce"}:
        mode = "observe"
    return mode


def get_active_policy_name() -> str:
    cfg = load_resonance_config()
    name = str(cfg.get("active_policy") or cfg.get("default_policy") or "quality-first")
    return name


def get_closed_loop_period_sec() -> int:
    """Return configured closed-loop snapshot throttle period in seconds."""
    cfg = load_resonance_config()
    try:
        return int(cfg.get("closed_loop_snapshot_period_sec", 300))
    except Exception:
        return 300


def get_active_policy() -> Dict[str, Any]:
    cfg = load_resonance_config()
    name = get_active_policy_name()
    pol = cfg.get("policies", {}).get(name)
    if isinstance(pol, dict):
        return pol
    return {}


def get_closed_loop_snapshot() -> Dict[str, Any]:
    """Return a lightweight snapshot of closed-loop metrics if available.

    Best-effort: reads outputs from simulators/collectors when present and
    gracefully returns an empty dict when not.
    """
    try:
        base = Path("outputs")
        # Resonance simulator latest
        sim = _load_json(base / "resonance_simulation_latest.json")
        # Realtime resonance bridge pipeline output (optional)
        realtime = _load_json(base / "realtime_resonance_latest.json")
        # Aggregate minimal, stable keys
        snap: Dict[str, Any] = {}
        if isinstance(sim, dict):
            snap["resonance_simulator"] = {
                "summary": sim.get("summary"),
                "last_resonance": sim.get("last_resonance"),
                "last_entropy": sim.get("last_entropy"),
            }
        if isinstance(realtime, dict):
            snap["realtime_resonance"] = {
                "strength": realtime.get("strength"),
                "coherence": realtime.get("coherence"),
                "phase": realtime.get("phase"),
            }
        return snap
    except Exception:
        return {}


def evaluate_resonance_policy(eval_report: Dict[str, Any], duration_sec: Optional[float] = None) -> Dict[str, Any]:
    """Evaluate current task against active policy thresholds.

    Returns a dict with mode, policy, action (allow|warn|block), and reasons.
    Never raises; safe for observe-mode wiring in pipelines.
    """
    mode = get_active_mode()
    pol = get_active_policy()
    min_q = float(pol.get("min_quality", 0.8))
    req_ev = bool(pol.get("require_evidence", True))
    max_lat_ms = float(pol.get("max_latency_ms", 8000))

    q = float(eval_report.get("quality", 0.0)) if isinstance(eval_report, dict) else 0.0
    ev_ok = bool(eval_report.get("evidence_ok", False)) if isinstance(eval_report, dict) else False
    dur_ms = (duration_sec or 0.0) * 1000.0

    reasons: list[str] = []
    if q < min_q:
        reasons.append(f"quality {q:.2f} < min_quality {min_q:.2f}")
    if req_ev and not ev_ok:
        reasons.append("evidence_required_but_missing")
    if dur_ms > max_lat_ms:
        reasons.append(f"latency {dur_ms:.0f}ms > max_latency_ms {max_lat_ms:.0f}ms")

    ok = len(reasons) == 0
    action = "allow" if ok else ("block" if mode == "enforce" else "warn")
    return {
        "mode": mode,
        "policy": get_active_policy_name(),
        "thresholds": {"min_quality": min_q, "require_evidence": req_ev, "max_latency_ms": max_lat_ms},
        "observed": {"quality": q, "evidence_ok": ev_ok, "latency_ms": dur_ms},
        "action": action,
        "reasons": reasons,
    }


def should_emit_closed_loop(period_sec: int = 300) -> bool:
    """Return True if enough time elapsed since last closed-loop snapshot emission.

    Uses a simple in-memory timestamp; safe in single-process CLI/daemon contexts.
    """
    import time
    global _LAST_SNAPSHOT_TS
    now = time.time()
    if _LAST_SNAPSHOT_TS is None or (now - _LAST_SNAPSHOT_TS) >= max(1, int(period_sec)):
        _LAST_SNAPSHOT_TS = now
        return True
    return False


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
