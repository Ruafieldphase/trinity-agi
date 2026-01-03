#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Self-care Summary Generator

목표:
- `outputs/selfcare_summary_latest.json`를 생성/갱신하여 시스템이 "자기-회복(self-care)" 상태를
  다른 모듈(특히 quantum_flow/goal 정책)과 공유할 수 있게 한다.
- system_integration_diagnostic이 요구하는 `quantum_flow` 연결(필드 존재)을 보장한다.

주의:
- 외부 네트워크 없이 워크스페이스 내부 데이터만 사용한다.
- 기존에 selfcare_summary가 있으면 가능한 한 값을 보존하고, quantum_flow/타임스탬프만 갱신한다.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from workspace_root import get_workspace_root


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def measure_quantum_flow(workspace_root: Path) -> Dict[str, Any]:
    """
    quantum_flow 측정은 워크스페이스 내 기존 구현을 우선 사용.
    실패해도 selfcare_summary 생성이 중단되지 않도록 보수적으로 동작한다.
    """
    try:
        if str(workspace_root) not in sys.path:
            sys.path.insert(0, str(workspace_root))
        from scripts.integrate_quantum_flow_to_goals import measure_current_flow_state

        return measure_current_flow_state(workspace_root)
    except Exception as e:
        return {
            "phase_coherence": 0.5,
            "state": "unknown",
            "conductivity": 0.5,
            "resistance": 2.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }


def build_summary(existing: Dict[str, Any], hours: int, quantum_flow: Dict[str, Any]) -> Dict[str, Any]:
    # 기존 구조가 있으면 최대한 보존
    summary = dict(existing) if isinstance(existing, dict) else {}
    summary.setdefault("hours", hours)
    summary.setdefault("count", summary.get("count") or 0)

    # 통합 포인트: system_integration_diagnostic가 찾는 필드
    summary["quantum_flow"] = quantum_flow
    summary["generated_at"] = datetime.now(timezone.utc).isoformat()
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=str, default=str(get_workspace_root()))
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--out", type=str, default=str(Path("outputs") / "selfcare_summary_latest.json"))
    args = ap.parse_args()

    workspace_root = Path(args.workspace).resolve()
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = (workspace_root / out_path).resolve()

    existing = load_json(out_path)
    qflow = measure_quantum_flow(workspace_root)
    summary = build_summary(existing, args.hours, qflow)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "out": str(out_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
