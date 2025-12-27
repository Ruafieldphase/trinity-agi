#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Digital Twin / Quantum Digital Twin State (v1)

목적:
- 현재 '운영 중인' 리듬 파이프라인의 핵심 상태를 디지털 트윈으로 고정한다.
- "퀀텀 디지털 트윈"은 실행을 하지 않고, 가능한 다음 행동 후보의 확률(중첩)만 기록한다.
- 선형 규칙이 아니라, (pain/phase/drift/rest/safety) 같은 신호를 조합해
  '불일치(mismatch)'를 계산하고 라우팅 힌트를 제공한다.

원칙:
- 네트워크 없음
- 민감정보 원문 저장 없음(키 입력/마우스 좌표/대화 원문/URL 원문 등)
- 실패해도 최소 출력(best-effort)
- 과도한 실행 방지: 최소 주기(min_interval) 적용

출력:
- outputs/sync_cache/digital_twin_state.json
- outputs/sync_cache/quantum_digital_twin_state.json
"""

from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
BRIDGE = OUTPUTS / "bridge"
SAFETY = OUTPUTS / "safety"
SYNC_CACHE = OUTPUTS / "sync_cache"
MEMORY = ROOT / "memory"

TRIGGER_LATEST = BRIDGE / "trigger_report_latest.json"
TRIGGER_HISTORY = BRIDGE / "trigger_report_history.jsonl"

INTERNAL_STATE = MEMORY / "agi_internal_state.json"
NATURAL_CLOCK = OUTPUTS / "natural_rhythm_clock_latest.json"
NATURAL_DRIFT = OUTPUTS / "natural_rhythm_drift_latest.json"
MITO = OUTPUTS / "mitochondria_state.json"
REST_GATE = SAFETY / "rest_gate_latest.json"
PAIN = SYNC_CACHE / "rhythm_pain_latest.json"
CONSTITUTION = BRIDGE / "constitution_review_latest.json"
BODY_LIFE = SYNC_CACHE / "body_life_state.json"

OUT_TWIN = SYNC_CACHE / "digital_twin_state.json"
OUT_QTWIN = SYNC_CACHE / "quantum_digital_twin_state.json"
STATE = SYNC_CACHE / "digital_twin_state_cache.json"


def _utc_iso_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _atomic_write_json(path: Path, obj: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
    except Exception:
        return


def _safe_float(v: Any, default: float | None = None) -> float | None:
    try:
        if v is None:
            return default
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return default
            return float(s)
        return default
    except Exception:
        return default


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _phase_of_action(action: str) -> str:
    a = (action or "").strip()
    if a in {"full_cycle", "self_acquire", "self_tool", "sync_clean"}:
        return "EXPANSION"
    if a in {"self_compress"}:
        return "CONTRACTION"
    return "INTEGRATION"


def _count_recent_executions(now_ts: float, window_s: float, tail_n: int = 260) -> int:
    if not TRIGGER_HISTORY.exists():
        return 0
    try:
        lines = TRIGGER_HISTORY.read_text(encoding="utf-8", errors="replace").splitlines()[-tail_n:]
    except Exception:
        return 0
    c = 0
    for l in lines:
        l = (l or "").strip()
        if not l:
            continue
        try:
            e = json.loads(l)
        except Exception:
            continue
        st = str(e.get("status") or "")
        if st not in {"executed", "failed", "blocked"}:
            continue
        ts = e.get("timestamp")
        try:
            if isinstance(ts, str) and ts.strip():
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                age = now_ts - dt.timestamp()
                if 0.0 <= age <= float(window_s):
                    c += 1
        except Exception:
            continue
    return c


def _combine_non_linear(terms: list[tuple[str, float]]) -> float:
    p = 1.0
    for _, t in terms:
        p *= (1.0 - _clamp01(t))
    return _clamp01(1.0 - p)


def _normalize_weights(weights: dict[str, float]) -> list[dict[str, Any]]:
    items = [(k, float(v)) for k, v in weights.items() if float(v) > 0]
    if not items:
        return [{"action": "idle", "p": 1.0}]
    s = sum(v for _, v in items)
    if s <= 0:
        return [{"action": "idle", "p": 1.0}]
    out = [{"action": k, "p": float(v) / s} for k, v in items]
    out.sort(key=lambda x: x["p"], reverse=True)
    return out


def main() -> int:
    SYNC_CACHE.mkdir(parents=True, exist_ok=True)
    now = time.time()

    # min interval
    last = _load_json(STATE) or {}
    last_ts = _safe_float(last.get("last_run_ts"), default=0.0) or 0.0
    if last_ts and (now - last_ts) < 60.0:
        return 0

    trig = _load_json(TRIGGER_LATEST) or {}
    internal = _load_json(INTERNAL_STATE) or {}
    clock = _load_json(NATURAL_CLOCK) or {}
    drift = _load_json(NATURAL_DRIFT) or {}
    mito = _load_json(MITO) or {}
    rest = _load_json(REST_GATE) or {}
    pain = _load_json(PAIN) or {}
    const = _load_json(CONSTITUTION) or {}
    body = _load_json(BODY_LIFE) or {}

    last_action = str(trig.get("action") or "")
    last_reason = ""
    try:
        params = trig.get("params") if isinstance(trig.get("params"), dict) else {}
        last_reason = str((params or {}).get("reason") or "")
    except Exception:
        last_reason = ""

    recommended_phase = str(clock.get("recommended_phase") or "").upper().strip()
    time_phase = str(clock.get("time_phase") or "").strip()
    action_phase = _phase_of_action(last_action)

    drift_ok = bool(drift.get("ok")) if isinstance(drift, dict) and "ok" in drift else True
    rest_status = str(rest.get("status") or "").upper().strip()
    safety_status = str(const.get("status") or "").upper().strip()

    atp = _safe_float(mito.get("atp_level"), default=None)
    pain_level = _safe_float(pain.get("pain_0_1"), default=0.0) or 0.0
    pain_rec = str(pain.get("recommendation") or "").strip().upper() or "OK"
    body_mode = str(body.get("mode") or "").strip()

    trig_60s = _count_recent_executions(now, 60.0)
    trig_5m = _count_recent_executions(now, 5 * 60.0)

    # Mismatch(불일치) 계산: "지금의 관측"과 "자연/몸/통증 신호"의 충돌
    mm_phase = 0.0
    if recommended_phase in {"EXPANSION", "CONTRACTION", "INTEGRATION"}:
        if action_phase != recommended_phase:
            mm_phase = 0.35

    mm_pain = 0.0
    if pain_rec in {"REST"} and last_action in {"full_cycle", "self_acquire", "self_tool", "sync_clean"}:
        mm_pain = 0.65
    elif pain_rec in {"STABILIZE"} and last_action in {"full_cycle", "self_acquire"}:
        mm_pain = 0.45

    mm_rest = 0.0
    if rest_status == "REST" and last_action not in {"idle", "heartbeat_check"}:
        mm_rest = 0.55

    mm_safety = 0.0
    if safety_status == "BLOCK" and last_action not in {"heartbeat_check", "idle"}:
        mm_safety = 1.0
    elif safety_status == "REVIEW" and last_action not in {"heartbeat_check", "idle"}:
        mm_safety = 0.75

    mm_thr = 0.0
    if trig_60s >= 3:
        mm_thr = _clamp01(0.35 + (float(trig_60s) - 3.0) * 0.10)
    elif trig_5m >= 25:
        mm_thr = 0.40

    mm_body = 0.0
    if body_mode in {"STOP_FILE", "KILL_SWITCH"} and last_action in {"self_acquire", "full_cycle"}:
        mm_body = 0.15

    mm_atp = 0.0
    if atp is not None:
        # ATP가 낮을수록(0.3 이하) 불일치 증가
        if atp < 0.3:
            mm_atp = _clamp01((0.3 - atp) / 0.3)

    # 위상(Phase)에 따른 가중치 조정
    # EXPANSION 로직에서는 pain에 더 민감하게 반응하여 과부하 방지
    pain_weight = 1.25 if recommended_phase == "EXPANSION" else 1.00
    atp_weight = 0.85

    mismatch_raw = _combine_non_linear(
        [
            ("phase", 1.00 * mm_phase),
            ("pain", pain_weight * mm_pain),
            ("atp", atp_weight * mm_atp),
            ("rest", 0.85 * mm_rest),
            ("safety", 1.00 * mm_safety),
            ("thrash", 0.90 * mm_thr),
            ("body", 0.50 * mm_body),
        ]
    )

    # Smoothing: mismatch는 급등은 빠르게, 하강은 느리게
    prev = _load_json(STATE) or {}
    prev_m = _safe_float(prev.get("mismatch_0_1"), default=0.0) or 0.0
    prev_ts = _safe_float(prev.get("mismatch_ts"), default=now) or now
    dt = max(0.0, float(now - prev_ts))
    try:
        decay = math.exp(-dt / (25.0 * 60.0))
    except Exception:
        decay = 1.0
    carried = float(prev_m) * float(decay)
    target = max(mismatch_raw, carried)
    alpha = 0.55 if target >= prev_m else 0.15
    mismatch = _clamp01(prev_m + alpha * (target - prev_m))

    # Routing hint (not a goal)
    route = "OK"
    if safety_status == "BLOCK":
        route = "HALT"
    elif mismatch >= 0.85 or pain_rec == "REST" or rest_status == "REST":
        route = "REST"
    elif mismatch >= 0.60:
        route = "STABILIZE"
    elif mismatch >= 0.35:
        route = "SLOW"

    twin = {
        "generated_at_utc": _utc_iso_now(),
        "observed": {
            "last_action": last_action or None,
            "last_reason": last_reason or None,
            "action_phase": action_phase,
            "time_phase": time_phase or None,
            "recommended_phase": recommended_phase or None,
            "drift_ok": bool(drift_ok),
            "rest_gate": rest_status or None,
            "safety": safety_status or None,
            "atp": float(atp) if atp is not None else None,
            "pain_0_1": float(pain_level),
            "pain_recommendation": pain_rec,
            "body_mode": body_mode or None,
            "trigger_exec_60s": int(trig_60s),
            "trigger_exec_5m": int(trig_5m),
        },
        "mismatch_0_1": float(mismatch),
        "mismatch_raw_0_1": float(mismatch_raw),
        "mismatch_components": {
            "phase": float(mm_phase),
            "pain": float(mm_pain),
            "rest": float(mm_rest),
            "safety": float(mm_safety),
            "thrash": float(mm_thr),
            "body": float(mm_body),
        },
        "route_hint": route,
        "note": "Digital Twin은 '복사'가 아니라 관측 고정이며, route_hint는 reward가 아닌 routing 신호다.",
    }

    # Quantum Digital Twin: action candidates (superposition) — NO execution
    drives = internal.get("drives") if isinstance(internal.get("drives"), dict) else {}
    dom = ""
    try:
        if drives:
            dom = max(drives.items(), key=lambda kv: float(kv[1] or 0.0))[0]
    except Exception:
        dom = ""

    weights: dict[str, float] = {"idle": 1.0, "heartbeat_check": 0.25}

    # Safety gates
    if safety_status in {"BLOCK"}:
        weights = {"idle": 1.0, "heartbeat_check": 0.35}
    else:
        # Pain/rest gates
        if pain_rec == "REST" or rest_status == "REST":
            weights["idle"] += 2.5
            weights["self_compress"] = weights.get("self_compress", 0.0) + 0.8
            weights["heartbeat_check"] += 0.35
        elif pain_rec in {"STABILIZE"}:
            weights["self_compress"] = weights.get("self_compress", 0.0) + 1.1
            weights["idle"] += 1.0
        elif recommended_phase == "EXPANSION" and mismatch < 0.35:
            weights["self_acquire"] = weights.get("self_acquire", 0.0) + 1.2
            weights["full_cycle"] = weights.get("full_cycle", 0.0) + 0.6
        elif recommended_phase == "CONTRACTION":
            weights["self_compress"] = weights.get("self_compress", 0.0) + 1.1

        # Drive bias (local rhythm)
        if dom == "explore":
            weights["self_acquire"] = weights.get("self_acquire", 0.0) + 0.9
        elif dom == "rest":
            weights["idle"] += 0.9
        elif dom == "self_focus":
            weights["self_compress"] = weights.get("self_compress", 0.0) + 0.7

        # Thrash penalty: prefer idle
        if trig_60s >= 3:
            weights["idle"] += 1.3
            weights["heartbeat_check"] += 0.3

    candidates = _normalize_weights(weights)[:6]
    qtwin = {
        "generated_at_utc": _utc_iso_now(),
        "dominant_drive": dom or None,
        "candidates": candidates,
        "note": "Quantum Digital Twin은 후보의 확률만 제공하며, 실행은 다른 레이어(정책/감독/트리거)가 담당한다.",
    }

    _atomic_write_json(OUT_TWIN, twin)
    _atomic_write_json(OUT_QTWIN, qtwin)
    _atomic_write_json(STATE, {"last_run_ts": float(now), "mismatch_0_1": float(mismatch), "mismatch_ts": float(now)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

