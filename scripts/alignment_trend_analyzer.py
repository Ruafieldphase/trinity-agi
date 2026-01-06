#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alignment Trend Analyzer (v1)

목표:
- digital_twin_state.json의 이력을 분석하여 미스매치의 통계적 추세를 도출한다.
- 일시적인 노이즈(Outlier)와 지속적인 드리프트(Drift)를 구분한다.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from workspace_root import get_workspace_root

ROOT = get_workspace_root()
SYNC_CACHE = ROOT / "outputs" / "sync_cache"
TWIN_STATE = SYNC_CACHE / "digital_twin_state.json"
TREND_OUT = SYNC_CACHE / "alignment_trend_latest.json"
HISTORY_FILE = SYNC_CACHE / "digital_twin_history.jsonl"

def load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists(): return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except: return None

def append_history(state: Dict[str, Any]):
    try:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(state, ensure_ascii=False) + "\n")
    except: pass

def get_history(n: int = 50) -> List[Dict[str, Any]]:
    if not HISTORY_FILE.exists(): return []
    try:
        lines = HISTORY_FILE.read_text(encoding="utf-8").splitlines()
        return [json.loads(l) for l in lines[-n:]]
    except: return []

def analyze_trend():
    state = load_json(TWIN_STATE)
    if not state: return

    # 1. 아카이빙 (Best-effort)
    append_history(state)

    # 2. 이력 분석
    history = get_history(20)
    if not history: return

    mismatches = [float(s.get("mismatch_0_1", 0.0)) for s in history]
    
    # 이동 평균 (Window: 10)
    window = 10
    recent_mm = mismatches[-window:] if len(mismatches) >= window else mismatches
    moving_avg = sum(recent_mm) / len(recent_mm) if recent_mm else 0.0

    # 추세 계산 (기울기)
    trend = 0.0
    if len(mismatches) >= 2:
        trend = (mismatches[-1] - mismatches[0]) / len(mismatches)

    # 위험도 판정
    is_climbing = trend > 0.01 and moving_avg > 0.4
    status = "STABLE"
    if is_climbing: status = "DRIFTING"
    if moving_avg > 0.7: status = "CRITICAL_MISMATCH"

    trend_data = {
        "timestamp": time.time(),
        "moving_avg_mismatch": moving_avg,
        "mismatch_trend": trend,
        "status": status,
        "sample_count": len(history),
        "note": "이 데이터는 디지털 트윈의 통계적 정렬 상태를 나타냅니다."
    }

    TREND_OUT.parent.mkdir(parents=True, exist_ok=True)
    TREND_OUT.write_text(json.dumps(trend_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"📈 Trend Analysis: {status} (avg: {moving_avg:.2f}, trend: {trend:.3f})")

if __name__ == "__main__":
    analyze_trend()
