"""
orchestrator/resonance_bridge.py
오케스트레이터 파이프라인과 Universal Resonance 시스템을 연결하는 브리지.
"""
from __future__ import annotations
from typing import Dict, Any, Optional, List
from pathlib import Path
import datetime

try:
    from fdo_agi_repo.universal.resonance import ResonanceStore, ResonanceEvent
    from fdo_agi_repo.universal.task_schema import AbstractIntent, DataType
except ModuleNotFoundError:
    from universal.resonance import ResonanceStore, ResonanceEvent  # type: ignore
    from universal.task_schema import AbstractIntent, DataType  # type: ignore


_RESONANCE_STORE: Optional[ResonanceStore] = None
_RESONANCE_CONFIG: Optional[Dict[str, Any]] = None
_RESONANCE_CONFIG_MTIME: Optional[float] = None
_RESONANCE_CONFIG_PATH: Optional[Path] = None
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
    global _RESONANCE_CONFIG, _RESONANCE_CONFIG_MTIME, _RESONANCE_CONFIG_PATH
    if _RESONANCE_CONFIG is not None and not force_reload:
        # If we have a cached path, check mtime and reload when changed
        try:
            if _RESONANCE_CONFIG_PATH is not None and _RESONANCE_CONFIG_PATH.exists():
                current_mtime = _RESONANCE_CONFIG_PATH.stat().st_mtime
                if _RESONANCE_CONFIG_MTIME is not None and current_mtime == _RESONANCE_CONFIG_MTIME:
                    return _RESONANCE_CONFIG
        except Exception:
            # If mtime check fails, fall back to returning cache
            return _RESONANCE_CONFIG

    import os
    cfg_path = os.environ.get("RESONANCE_CONFIG")
    if cfg_path:
        path_obj = Path(cfg_path)
        cfg = _load_json(path_obj)
        if isinstance(cfg, dict):
            _RESONANCE_CONFIG = cfg
            _RESONANCE_CONFIG_PATH = path_obj
            try:
                _RESONANCE_CONFIG_MTIME = path_obj.stat().st_mtime
            except Exception:
                _RESONANCE_CONFIG_MTIME = None
            return cfg

    # Default locations
    base = Path("configs")
    primary = base / "resonance_config.json"
    example = base / "resonance_config.example.json"

    # Prefer primary; remember which path was chosen for mtime tracking
    chosen_path = primary if primary.exists() else (example if example.exists() else None)
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

    # Optimization defaults (Phase 8.5)
    opt_cfg = cfg.get("optimization")
    if not isinstance(opt_cfg, dict):
        opt_cfg = {}
    if "enabled" not in opt_cfg:
        opt_cfg["enabled"] = True
    if "prefer_gateway" not in opt_cfg:
        opt_cfg["prefer_gateway"] = True
    if "prefer_peak_hours" not in opt_cfg:
        opt_cfg["prefer_peak_hours"] = True
    peak_defaults = {"start": 8, "end": 16}
    if "peak_hours" not in opt_cfg or not isinstance(opt_cfg.get("peak_hours"), dict):
        opt_cfg["peak_hours"] = peak_defaults.copy()
    else:
        peak_hours = opt_cfg["peak_hours"]
        if "start" not in peak_hours:
            peak_hours["start"] = peak_defaults["start"]
        if "end" not in peak_hours:
            peak_hours["end"] = peak_defaults["end"]
    if "offpeak_mode" not in opt_cfg:
        opt_cfg["offpeak_mode"] = "lightweight"
    if "batch_compression" not in opt_cfg:
        opt_cfg["batch_compression"] = "high"
    if "learning_bias" not in opt_cfg:
        opt_cfg["learning_bias"] = "gateway"
    cfg["optimization"] = opt_cfg

    _RESONANCE_CONFIG = cfg
    _RESONANCE_CONFIG_PATH = chosen_path
    try:
        _RESONANCE_CONFIG_MTIME = chosen_path.stat().st_mtime if chosen_path else None
    except Exception:
        _RESONANCE_CONFIG_MTIME = None
    return cfg


def get_resonance_config_path() -> Optional[Path]:
    """Return the path of the currently active resonance config file, if any.

    Ensures the config loader has run at least once so callers (e.g., detectors
    or dashboards) can display the effective path. Falls back to default
    locations when nothing has been loaded yet.
    """
    # Ensure loader ran to populate _RESONANCE_CONFIG_PATH if possible
    try:
        load_resonance_config()
    except Exception:
        pass

    if _RESONANCE_CONFIG_PATH is not None:
        return _RESONANCE_CONFIG_PATH

    # Derive default locations without creating files
    try:
        import os as _os
        env_path = _os.environ.get("RESONANCE_CONFIG")
        if env_path:
            p = Path(env_path)
            if p.exists():
                return p
    except Exception:
        pass

    base = Path("configs")
    primary = base / "resonance_config.json"
    example = base / "resonance_config.example.json"
    if primary.exists():
        return primary
    if example.exists():
        return example
    return None


def get_resonance_optimization(now: Optional[datetime.datetime] = None) -> Dict[str, Any]:
    """Return sanitized optimization guidance derived from resonance config."""

    def _safe_hour(value: Any, default: int) -> int:
        try:
            val = int(value)
        except Exception:
            val = default
        return max(0, min(23, val))

    cfg = load_resonance_config()
    opt_cfg = cfg.get("optimization") if isinstance(cfg.get("optimization"), dict) else {}

    enabled = bool(opt_cfg.get("enabled", True))
    prefer_gateway = bool(opt_cfg.get("prefer_gateway", False))
    prefer_peak = bool(opt_cfg.get("prefer_peak_hours", False))

    peak_hours_cfg = opt_cfg.get("peak_hours") if isinstance(opt_cfg.get("peak_hours"), dict) else {}
    start_hour = _safe_hour(peak_hours_cfg.get("start", 8), 8)
    end_hour = _safe_hour(peak_hours_cfg.get("end", 16), 16)

    tz_name = opt_cfg.get("timezone")
    current_dt = now
    if current_dt is None:
        if tz_name:
            try:
                from zoneinfo import ZoneInfo  # type: ignore

                current_dt = datetime.datetime.now(ZoneInfo(str(tz_name)))
            except Exception:
                current_dt = datetime.datetime.now()
        else:
            current_dt = datetime.datetime.now()

    hour = current_dt.hour

    def _in_window(h: int, start: int, end: int) -> bool:
        if start == end:
            return True  # Degenerate window -> treat as always peak
        if start < end:
            return start <= h < end
        return h >= start or h < end

    is_peak_now = _in_window(hour, start_hour, end_hour)

    preferred_channels_cfg = opt_cfg.get("preferred_channels")
    preferred_channels: List[str]
    if isinstance(preferred_channels_cfg, list) and preferred_channels_cfg:
        preferred_channels = [str(ch).strip() for ch in preferred_channels_cfg if str(ch).strip()]
    else:
        preferred_channels = [
            "gemini",
            "gateway",
            "cloud_ai",
            "local_llm",
        ] if prefer_gateway else [
            "local_llm",
            "gemini",
            "cloud_ai",
            "gateway",
        ]

    if prefer_peak and not is_peak_now:
        offpeak_channels_cfg = opt_cfg.get("offpeak_channels")
        if isinstance(offpeak_channels_cfg, list) and offpeak_channels_cfg:
            preferred_channels = [str(ch).strip() for ch in offpeak_channels_cfg if str(ch).strip()]
        else:
            preferred_channels = list(reversed(preferred_channels))

    batch_level = str(opt_cfg.get("batch_compression", "auto") or "auto").lower()
    batch_compression = batch_level not in {"auto", "none", "off", "normal"}
    learning_bias = str(opt_cfg.get("learning_bias", "balanced") or "balanced").lower()
    offpeak_mode = str(opt_cfg.get("offpeak_mode", "normal") or "normal").lower()

    should_throttle_offpeak = bool(prefer_peak and not is_peak_now and offpeak_mode in {"lightweight", "throttle", "conserve"})

    timeout_cfg = opt_cfg.get("timeouts") if isinstance(opt_cfg.get("timeouts"), dict) else {}
    peak_timeout_ms = int(timeout_cfg.get("peak_ms", 260))
    offpeak_timeout_ms = int(timeout_cfg.get("offpeak_ms", max(peak_timeout_ms, 360)))
    timeout_ms = peak_timeout_ms if is_peak_now else offpeak_timeout_ms

    retry_cfg = opt_cfg.get("retry_attempts") if isinstance(opt_cfg.get("retry_attempts"), dict) else {}
    peak_retries = int(retry_cfg.get("peak", 2))
    offpeak_retries = int(retry_cfg.get("offpeak", max(peak_retries, 3)))
    retry_attempts = peak_retries if is_peak_now else offpeak_retries

    return {
        "enabled": enabled,
        "prefer_gateway": prefer_gateway,
        "prefer_peak_hours": prefer_peak,
        "is_peak_now": is_peak_now,
        "phase": "peak" if is_peak_now else "off-peak",
        "current_hour": hour,
        "preferred_channels": preferred_channels,
        "offpeak_mode": offpeak_mode,
        "batch_compression": batch_compression,
        "batch_compression_level": batch_level,
        "learning_bias": learning_bias,
        "peak_window": {
            "start": start_hour,
            "end": end_hour,
            "timezone": tz_name or "local",
        },
        "should_throttle_offpeak": should_throttle_offpeak,
        "timeout_ms": timeout_ms,
        "retry_attempts": retry_attempts,
    }


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
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            metrics=metrics,
            tags=tags,
        )
        
        _RESONANCE_STORE.append(event)
    except Exception:
        # Logging system not wired; silently ignore
        pass


def consolidate_to_hippocampus(
    hours: int = 24,
    min_importance: float = 0.7,
    workspace_root: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Resonance Ledger 이벤트를 Hippocampus long-term memory로 consolidation
    
    Args:
        hours: 최근 몇 시간의 이벤트를 처리할지
        min_importance: 이 이상의 importance를 가진 이벤트만 저장
        workspace_root: Workspace 루트 (None이면 자동 감지)
    
    Returns:
        Consolidation 결과 (저장된 메모리 수 등)
    """
    if workspace_root is None:
        workspace_root = Path(__file__).parent.parent.parent
    
    # Hippocampus 로드
    try:
        from fdo_agi_repo.copilot.hippocampus import CopilotHippocampus
    except ModuleNotFoundError:
        from copilot.hippocampus import CopilotHippocampus  # type: ignore
    
    hippocampus = CopilotHippocampus(workspace_root)
    
    # Resonance 이벤트 로드
    if _RESONANCE_STORE is None:
        init_resonance_store()
    
    cutoff_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
    all_events = _RESONANCE_STORE.read_all()
    recent_events = [
        e for e in all_events
        if e.timestamp >= cutoff_time
    ]
    
    consolidated = {
        "processed": 0,
        "stored": 0,
        "skipped_low_importance": 0,
        "memories": [],
    }
    
    for event in recent_events:
        consolidated["processed"] += 1
        
        # Importance 계산 (quality + evidence 기반)
        quality = event.metrics.get("quality", 0.0)
        evidence = event.metrics.get("evidence", 0.0)
        importance = (quality * 0.7 + evidence * 0.3)
        
        if importance < min_importance:
            consolidated["skipped_low_importance"] += 1
            continue
        
        # Memory 포맷으로 변환
        memory_item = {
            "timestamp": event.timestamp.isoformat(),
            "resonance_key": event.resonance_key,
            "task_id": event.tags.get("task_id", ""),
            "goal": event.tags.get("task_goal_snippet", ""),
            "metrics": event.metrics,
            "importance": importance,
            "type": "episodic",  # Resonance 이벤트는 사건 기억
        }
        
        # Hippocampus에 저장
        hippocampus.add_to_working_memory(memory_item)
        consolidated["stored"] += 1
        consolidated["memories"].append(memory_item)
    
    # Consolidation 실행 (단기 → 장기)
    result = hippocampus.consolidate(force=False)
    consolidated["consolidation_result"] = result
    
    return consolidated
