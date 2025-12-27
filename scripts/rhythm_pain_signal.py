#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rhythm Pain Signal (v1)

목적:
- "리듬이 어긋날 때의 통증/고통 신호"를 파일로 고정해 항상성/정책 레이어가 참고할 수 있게 한다.
- 선형 규칙(한 임계치)만으로 결정하지 않고, 여러 신호를 비선형으로 합성한다.

원칙:
- 네트워크 없음
- 민감정보(키/마우스 좌표/원문 대화 등) 저장 없음
- 실패해도 최소 출력(best-effort)

출력:
- outputs/sync_cache/rhythm_pain_latest.json
- outputs/sync_cache/rhythm_pain_state.json (스무딩/히스테리시스용)
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

SELFCARE = OUTPUTS / "selfcare_summary_latest.json"
NDRIFT = OUTPUTS / "natural_rhythm_drift_latest.json"
REST_GATE = SAFETY / "rest_gate_latest.json"
CONSTITUTION = BRIDGE / "constitution_review_latest.json"
TRIGGER_HISTORY = BRIDGE / "trigger_report_history.jsonl"
BODY_LIFE = SYNC_CACHE / "body_life_state.json"

OUT = SYNC_CACHE / "rhythm_pain_latest.json"
STATE = SYNC_CACHE / "rhythm_pain_state.json"


def _utc_iso_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


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


def _count_recent_executions(now_ts: float, window_s: float, tail_n: int = 260) -> int:
    """
    최근 window_s 내 실행 이벤트 수(가벼운 폭주/경련 신호).
    """
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
    """
    비선형 합성:
    - 각 항은 0..1
    - 결합: 1 - Π(1 - term)
    """
    p = 1.0
    for _, t in terms:
        p *= (1.0 - _clamp01(t))
    return _clamp01(1.0 - p)


def main() -> int:
    SYNC_CACHE.mkdir(parents=True, exist_ok=True)
    now = time.time()

    selfcare = _load_json(SELFCARE) or {}
    drift = _load_json(NDRIFT) or {}
    rest = _load_json(REST_GATE) or {}
    constitution = _load_json(CONSTITUTION) or {}
    body_life = _load_json(BODY_LIFE) or {}
    prev = _load_json(STATE) or {}

    qf = selfcare.get("quantum_flow") if isinstance(selfcare.get("quantum_flow"), dict) else {}
    coherence = _safe_float(qf.get("phase_coherence"), default=None)
    qstate = str(qf.get("state") or "").strip().lower()

    drift_ok = bool(drift.get("ok")) if isinstance(drift, dict) and "ok" in drift else True
    rest_status = str(rest.get("status") or "").strip().upper()
    safety_status = str(constitution.get("status") or "").strip().upper()

    # 1) Quantum Flow 기반 "리듬 저항" → 통증(고통) 신호
    pain_qf = 0.0
    reasons: list[str] = []
    if coherence is not None:
        pain_qf = _clamp01(1.0 - float(coherence))
    # 상태 자체(저항/혼돈) 가중
    if qstate == "chaotic":
        pain_qf = max(pain_qf, 0.95)
        reasons.append("quantum_flow=chaotic")
    elif qstate == "resistive":
        pain_qf = max(pain_qf, 0.65)
        reasons.append("quantum_flow=resistive")
    elif qstate in {"superconducting", "coherent"}:
        pain_qf = min(pain_qf, 0.25)

    # 2) 자연 리듬 드리프트
    pain_drift = 0.0
    if drift_ok is False:
        pain_drift = 0.55
        rs = drift.get("reasons") if isinstance(drift.get("reasons"), list) else []
        reasons.append(f"drift:{str(rs[0]) if rs else 'not_ok'}")

    # 3) Homeostasis RestGate는 "통증을 멈추게 하는 창"이지만, 동시에 지금이 부담 구간이라는 신호
    pain_rest = 0.0
    if rest_status == "REST":
        pain_rest = 0.85
        reasons.append("rest_gate=REST")

    # 4) Safety/Ethics 신호
    pain_safety = 0.0
    if safety_status == "BLOCK":
        pain_safety = 1.0
        reasons.append("safety=BLOCK")
    elif safety_status == "REVIEW":
        pain_safety = 0.75
        reasons.append("safety=REVIEW")
    elif safety_status == "CAUTION":
        pain_safety = 0.45
        reasons.append("safety=CAUTION")

    # 5) 경련/폭주(짧은 창의 반복 실행)
    trig_60s = _count_recent_executions(now, 60.0)
    trig_5m = _count_recent_executions(now, 5 * 60.0)
    pain_thr = 0.0
    if trig_60s >= 3:
        # 3회부터 통증 신호, 10회면 거의 최대
        pain_thr = _clamp01(0.35 + (float(trig_60s) - 3.0) * 0.10)
        reasons.append(f"thrash_60s={trig_60s}")
    elif trig_5m >= 25:
        pain_thr = 0.40
        reasons.append(f"thrash_5m={trig_5m}")

    # 6) Body layer: STOP/킬스위치/휴식 등은 "경계 통증"으로 약하게 반영
    pain_body = 0.0
    mode = str(body_life.get("mode") or "")
    if mode in {"STOP_FILE", "KILL_SWITCH"}:
        pain_body = 0.25
        reasons.append(f"body_mode={mode}")

    # 비선형 결합(가중치)
    terms = [
        ("quantum_flow", 0.75 * pain_qf),
        ("drift", 0.65 * pain_drift),
        ("rest_gate", 0.70 * pain_rest),
        ("safety", 1.00 * pain_safety),
        ("thrash", 0.80 * pain_thr),
        ("body", 0.40 * pain_body),
    ]
    pain_raw = _combine_non_linear(terms)

    # 스무딩(히스테리시스): 상승은 빠르게, 하강은 천천히
    last_pain = _safe_float(prev.get("pain_0_1"), default=0.0) or 0.0
    last_ts = _safe_float(prev.get("last_ts"), default=now) or now
    dt = max(0.0, float(now - last_ts))
    # 시간이 지나면 자연 감쇠(30분 반감기)
    try:
        decay = math.exp(-dt / (30.0 * 60.0))
    except Exception:
        decay = 1.0
    carried = float(last_pain) * float(decay)

    # target은 현재 입력과 '잔류 통증' 중 큰 쪽
    target = max(pain_raw, carried)
    if target >= last_pain:
        alpha = 0.55
    else:
        alpha = 0.15
    pain = _clamp01(last_pain + alpha * (target - last_pain))

    # 권고(의식적 목표가 아니라 라우팅 신호)
    recommendation = "OK"
    if pain >= 0.85:
        recommendation = "REST"
    elif pain >= 0.60:
        recommendation = "STABILIZE"
    elif pain >= 0.35:
        recommendation = "SLOW"

    out = {
        "generated_at_utc": _utc_iso_now(),
        "pain_0_1": float(pain),
        "pain_raw_0_1": float(pain_raw),
        "components": {
            "quantum_flow": float(pain_qf),
            "drift": float(pain_drift),
            "rest_gate": float(pain_rest),
            "safety": float(pain_safety),
            "thrash": float(pain_thr),
            "body": float(pain_body),
        },
        "observables": {
            "quantum_flow_state": qstate or "unknown",
            "phase_coherence": float(coherence) if coherence is not None else None,
            "drift_ok": bool(drift_ok),
            "rest_gate_status": rest_status or "UNKNOWN",
            "safety_status": safety_status or "UNKNOWN",
            "trigger_exec_60s": int(trig_60s),
            "trigger_exec_5m": int(trig_5m),
            "body_mode": mode or "UNKNOWN",
        },
        "recommendation": recommendation,
        "reasons": reasons[:8],
        "note": "통증(pain)은 reward가 아니라 routing 신호(비선형 합성 + 히스테리시스)다.",
    }

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    STATE.write_text(json.dumps({"pain_0_1": float(pain), "last_ts": float(now)}, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

