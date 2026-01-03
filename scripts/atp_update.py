#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ATP Update (Mitochondria) — v1

목적:
- 폭주/휴식 판단을 "감각"이 아니라 파일 기반 에너지(ATP)로 고정한다.
- 기존 `scripts/mitochondria.py`를 사용해 `outputs/mitochondria_state.json`을 갱신한다.

원칙:
- 네트워크 없음
- 외부 패키지 없음
- 실패해도 시스템을 멈추지 않음(best-effort)
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import sys
from workspace_root import get_workspace_root

ROOT = get_workspace_root()
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from mitochondria import Mitochondria  # type: ignore


OUTPUTS = ROOT / "outputs"
BRIDGE = OUTPUTS / "bridge"

HEARTBEAT = OUTPUTS / "unconscious_heartbeat.json"
RIT = OUTPUTS / "rit_registry_latest.json"
CLOCK = OUTPUTS / "natural_rhythm_clock_latest.json"
HISTORY = BRIDGE / "trigger_report_history.jsonl"


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _read_jsonl_tail(path: Path, n: int = 120) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        out: list[dict[str, Any]] = []
        for l in lines[-n:]:
            l = (l or "").strip()
            if not l:
                continue
            try:
                out.append(json.loads(l))
            except Exception:
                continue
        return out
    except Exception:
        return []


def _infer_cpu_usage_from_activity(now: float) -> float:
    """
    외부 패키지 없이 CPU 사용량을 직접 측정하기 어렵기 때문에,
    최근 트리거 실행 빈도를 '부하 근사'로 변환한다.
    반환 범위: 0..100
    """
    tail = _read_jsonl_tail(HISTORY, n=200)
    if not tail:
        return 15.0

    # 최근 5분 내 executed/failed/blocked 개수
    count_5m = 0
    for e in tail[-80:]:
        st = str(e.get("status") or "")
        if st not in {"executed", "failed", "blocked"}:
            continue
        ts = str(e.get("timestamp") or "")
        if not ts:
            continue
        try:
            dt = datetime.fromisoformat(ts)
            age = now - dt.timestamp()
            if age <= 5 * 60:
                count_5m += 1
        except Exception:
            continue

    # 0..25 events / 5m → 10..90%
    if count_5m <= 0:
        return 15.0
    return max(10.0, min(90.0, 10.0 + (count_5m / 25.0) * 80.0))


def main() -> int:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    now = time.time()

    hb = _load_json(HEARTBEAT) or {}
    hb_state = hb.get("state") if isinstance(hb.get("state"), dict) else {}
    resonance = 0.5
    try:
        resonance = float(hb_state.get("resonance") or 0.5)
    except Exception:
        resonance = 0.5

    rit = _load_json(RIT) or {}
    rit_vals = rit.get("values") if isinstance(rit.get("values"), dict) else {}
    fear_level = None
    try:
        if "fear_proxy_avoid_0_1" in rit_vals:
            fear_level = float(rit_vals.get("fear_proxy_avoid_0_1"))
    except Exception:
        fear_level = None
    if fear_level is None:
        # fallback: avoid drive as fear proxy
        try:
            drives = hb_state.get("drives") if isinstance(hb_state.get("drives"), dict) else {}
            fear_level = float(drives.get("avoid") or 0.0)
        except Exception:
            fear_level = 0.0

    clock = _load_json(CLOCK) or {}
    rec = str(clock.get("recommended_phase") or "").upper().strip()
    # mitochondria는 CONTRACTION에서 특별 처리; INTEGRATION도 수축 쪽으로 본다(v1 근사)
    phase = "CONTRACTION" if rec in {"CONTRACTION", "INTEGRATION"} else "EXPANSION"

    cpu_usage = _infer_cpu_usage_from_activity(now)

    current_state = {
        "fear_level": float(fear_level or 0.0),
        "phase": phase,
        "body_signals": {"cpu_usage": float(cpu_usage)},
    }

    try:
        mito = Mitochondria(ROOT)
        mito.metabolize(current_state, resonance_score=float(resonance))
    except Exception:
        # best-effort: do not fail the caller loop
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
