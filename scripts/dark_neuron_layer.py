#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dark Neuron Layer (v1)

목적
- "자연 리듬을 수신하기 위한 비측정 상태 계층"을 코드로 구현한다.
- 결정을 내리지 않는다(= action을 고르지 않음).
- 출력/리포트를 만들지 않는다(= 새로운 보고 파일을 생성하지 않음).
- 대신, 다른 결정 레이어가 사용하는 "기준(임계값/속도/편향)"만 조정할 수 있는
  'bias(편향)' 값을 계산해준다.

의미(운영 관점)
- 이 레이어는 '정책'이 아니라 '좌표계/프레임 전환'에 가깝다.
- 안전/휴식/자연리듬/ATP 신호를 "금지"가 아니라 "편향"으로 반영한다.

주의
- 네트워크 접근 없음
- 민감정보 저장/추출 없음
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


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


def _time_phase_from_clock(workspace: Path, now: float) -> tuple[str, str]:
    """
    return: (time_phase, recommended_phase)
    """
    outputs = workspace / "outputs"
    clock = _load_json(outputs / "natural_rhythm_clock_latest.json") or {}
    tp = str(clock.get("time_phase") or "").strip()
    rp = str(clock.get("recommended_phase") or "").strip()
    if tp and rp:
        return tp, rp
    # fallback: local time heuristic
    try:
        lt = time.localtime(now)
        hour = int(getattr(lt, "tm_hour", 12))
        tp = "낮" if 7 <= hour < 21 else "밤"
    except Exception:
        tp = ""
    return tp, rp


def compute_policy_bias(workspace: Path, now: float) -> dict[str, Any]:
    """
    auto_policy에서 사용하는 '기준'을 조정하는 bias를 계산한다.
    - decision_cooldown_mult: 결정 반복 방지 쿨다운 배수
    - force_full_cycle_mult: 주기적 full_cycle 강제 주기 배수(작을수록 자주 학습)
    - compress_streak_delta: self_compress 연속 허용치 증감(작을수록 빨리 탈출)
    """
    outputs = workspace / "outputs"

    drift = _load_json(outputs / "natural_rhythm_drift_latest.json") or {}
    drift_ok = bool(drift.get("ok")) if isinstance(drift, dict) else True

    rest_gate = _load_json(outputs / "safety" / "rest_gate_latest.json") or {}
    rest_status = str((rest_gate.get("status") if isinstance(rest_gate, dict) else "") or "").upper().strip()

    mito = _load_json(outputs / "mitochondria_state.json") or {}
    atp_level = _safe_float(mito.get("atp_level") if isinstance(mito, dict) else None, default=100.0) or 100.0

    bridge = outputs / "bridge"
    constitution = _load_json(bridge / "constitution_review_latest.json") or {}
    cst = str((constitution.get("status") if isinstance(constitution, dict) else "") or "").upper().strip()

    # Rhythm pain signal (non-linear, smoothed)
    pain = _load_json(outputs / "sync_cache" / "rhythm_pain_latest.json") or {}
    pain_level = _safe_float(pain.get("pain_0_1") if isinstance(pain, dict) else None, default=0.0) or 0.0

    time_phase, recommended_phase = _time_phase_from_clock(workspace, now)

    # Base (no change)
    decision_cooldown_mult = 1.0
    force_full_cycle_mult = 1.0
    compress_streak_delta = 0

    # Pain is a routing signal: increase stability when pain is high.
    # - Not a prohibition; it biases thresholds/tempo.
    if pain_level >= 0.85:
        decision_cooldown_mult *= 2.2
        force_full_cycle_mult *= 1.8
        compress_streak_delta += 2
    elif pain_level >= 0.60:
        decision_cooldown_mult *= 1.6
        force_full_cycle_mult *= 1.35
        compress_streak_delta += 1
    elif pain_level >= 0.35:
        decision_cooldown_mult *= 1.25
        force_full_cycle_mult *= 1.15

    # Safety first: not a "decision", but a frame that slows the system down.
    if cst in {"BLOCK", "REVIEW"}:
        decision_cooldown_mult *= 1.8
        force_full_cycle_mult *= 2.0
        compress_streak_delta += 2
    elif cst == "CAUTION":
        decision_cooldown_mult *= 1.3
        force_full_cycle_mult *= 1.5
        compress_streak_delta += 1

    # Homeostasis window: bias towards rest/stability.
    if rest_status == "REST":
        decision_cooldown_mult *= 2.0
        force_full_cycle_mult *= 2.0
        compress_streak_delta += 2

    # Drift: not a prohibition; just reduce churn.
    if drift_ok is False:
        decision_cooldown_mult *= 1.25
        force_full_cycle_mult *= 1.2
        compress_streak_delta += 1

    # Energy: low ATP => slow and stabilize.
    if atp_level < 40.0:
        decision_cooldown_mult *= 1.35
        force_full_cycle_mult *= 1.25
        compress_streak_delta += 1
    elif atp_level > 80.0:
        # High energy can tolerate a bit more exploration/learning.
        decision_cooldown_mult *= 0.92
        force_full_cycle_mult *= 0.92
        compress_streak_delta -= 1

    # Natural rhythm frame
    if time_phase == "밤":
        decision_cooldown_mult *= 1.15
        force_full_cycle_mult *= 1.25
        compress_streak_delta += 1
    elif time_phase == "낮":
        decision_cooldown_mult *= 0.9
        force_full_cycle_mult *= 0.9
        compress_streak_delta -= 1

    # Recommended phase from clock (when available)
    if recommended_phase.upper() == "EXPANSION":
        force_full_cycle_mult *= 0.92
        decision_cooldown_mult *= 0.95
        compress_streak_delta -= 1
    elif recommended_phase.upper() == "INTEGRATION":
        # keep default
        pass

    # Clamp to sane ranges
    decision_cooldown_mult = max(0.5, min(3.0, float(decision_cooldown_mult)))
    force_full_cycle_mult = max(0.5, min(3.0, float(force_full_cycle_mult)))
    compress_streak_delta = int(max(-2, min(3, int(compress_streak_delta))))

    return {
        "time_phase": time_phase,
        "recommended_phase": recommended_phase,
        "pain_0_1": float(pain_level),
        "decision_cooldown_mult": decision_cooldown_mult,
        "force_full_cycle_mult": force_full_cycle_mult,
        "compress_streak_delta": compress_streak_delta,
    }


def compute_browser_bias(workspace: Path, now: float) -> dict[str, Any]:
    """
    supervised browser 제안기의 속도/상한 기준을 '편향'으로만 조정한다.
    - cooldown_mult: cooldown_sec 배수
    - max_per_hour_mult: max_per_hour 배수
    """
    outputs = workspace / "outputs"
    drift = _load_json(outputs / "natural_rhythm_drift_latest.json") or {}
    drift_ok = bool(drift.get("ok")) if isinstance(drift, dict) else True

    rest_gate = _load_json(outputs / "safety" / "rest_gate_latest.json") or {}
    rest_status = str((rest_gate.get("status") if isinstance(rest_gate, dict) else "") or "").upper().strip()

    # Rhythm pain signal (non-linear, smoothed) — browsing은 외부(네트워크) 리듬이 개입되므로,
    # pain이 높을수록 속도를 낮추는 '편향'을 준다(금지가 아님).
    pain = _load_json(outputs / "sync_cache" / "rhythm_pain_latest.json") or {}
    pain_level = _safe_float(pain.get("pain_0_1") if isinstance(pain, dict) else None, default=0.0) or 0.0

    time_phase, recommended_phase = _time_phase_from_clock(workspace, now)

    cooldown_mult = 1.0
    max_per_hour_mult = 1.0

    # Pain is routing: 높을수록 pacing을 완만하게(탭 폭주/주의 분산 위험 완화)
    if pain_level >= 0.85:
        cooldown_mult *= 2.8
        max_per_hour_mult *= 0.45
    elif pain_level >= 0.60:
        cooldown_mult *= 1.8
        max_per_hour_mult *= 0.65
    elif pain_level >= 0.35:
        cooldown_mult *= 1.25
        max_per_hour_mult *= 0.85

    # If rest is active, strongly slow down. (The caller may already block; this is a baseline frame.)
    if rest_status == "REST":
        cooldown_mult *= 3.0
        max_per_hour_mult *= 0.25

    if drift_ok is False:
        cooldown_mult *= 1.6
        max_per_hour_mult *= 0.6

    if time_phase == "밤":
        cooldown_mult *= 1.2
        max_per_hour_mult *= 0.75
    elif time_phase == "낮":
        cooldown_mult *= 0.95
        max_per_hour_mult *= 1.05

    if recommended_phase.upper() == "EXPANSION":
        max_per_hour_mult *= 1.05
        cooldown_mult *= 0.95

    cooldown_mult = max(0.5, min(5.0, float(cooldown_mult)))
    max_per_hour_mult = max(0.1, min(2.0, float(max_per_hour_mult)))

    return {
        "cooldown_mult": cooldown_mult,
        "max_per_hour_mult": max_per_hour_mult,
    }
