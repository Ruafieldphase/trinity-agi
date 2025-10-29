from __future__ import annotations
import os
import sys
import time
import json
import uuid
from typing import Any, Dict, List

HERE = os.path.dirname(__file__)
REPO = os.path.dirname(HERE)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from orchestrator.pipeline import run_task
from orchestrator.memory_bus import LEDGER_PATH, COORD_PATH


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def _filter_ledger(task_id: str) -> List[Dict[str, Any]]:
    return [r for r in _read_jsonl(LEDGER_PATH) if r.get("task_id") == task_id]


def scenario_long_input() -> bool:
    task_id = str(uuid.uuid4())
    long_goal = "요구사항 상세:\n" + ("데이터" * 10000)
    spec = {
        "task_id": task_id,
        "title": "EdgeCase: 매우 긴 입력 처리",
        "goal": long_goal,
        "constraints": [],
        "inputs": {},
        "scope": "doc",
        "permissions": ["READ"],
        "evidence_required": False,
    }
    t0 = time.perf_counter()
    result = run_task(tool_cfg={}, spec=spec)
    t1 = time.perf_counter()
    ok = isinstance(result, dict) and result.get("task_id") == task_id
    took = t1 - t0
    print(f"[Scenario: Long Input] ok={ok} duration={took:.3f}s summary_len={len((result or {}).get('summary',''))}")
    return ok


def scenario_meta_cognition_logged() -> bool:
    task_id = str(uuid.uuid4())
    spec = {
        "task_id": task_id,
        "title": "EdgeCase: 메타인지 로깅 검증",
        "goal": "복잡한 모델 학습 파이프라인을 구현하라 (웹, 데이터, 파일 저장 포함)",
        "constraints": ["고급 ML 모델 사용"],
        "inputs": {},
        "scope": "doc",
        "permissions": ["READ"],
        "evidence_required": False,
    }
    _ = run_task(tool_cfg={}, spec=spec)
    events = _filter_ledger(task_id)
    mc = next((e for e in events if e.get("event") == "meta_cognition"), None)
    ok = bool(mc and isinstance(mc.get("confidence"), (int, float)))
    dom = mc.get("domain") if mc else None
    print(f"[Scenario: Meta-Cognition Logged] domain={dom} confidence={mc.get('confidence') if mc else None} ok={ok}")
    return ok


def scenario_force_second_pass() -> bool:
    task_id = str(uuid.uuid4())
    spec = {
        "task_id": task_id,
        "title": "EdgeCase: 저품질 -> Second Pass 유도",
        "goal": "증거가 빈약한 상태에서도 개선을 시도하라",
        "constraints": [],
        "inputs": {},
        "scope": "doc",
        "permissions": ["READ"],
        "evidence_required": True,
    }
    old_rag = os.environ.get("RAG_DISABLE")
    old_corr = os.environ.get("CORRECTIONS_ENABLED")
    try:
        os.environ["RAG_DISABLE"] = "1"
        os.environ["CORRECTIONS_ENABLED"] = "true"
        _ = run_task(tool_cfg={}, spec=spec)
    finally:
        if old_rag is None:
            os.environ.pop("RAG_DISABLE", None)
        else:
            os.environ["RAG_DISABLE"] = old_rag
        if old_corr is None:
            os.environ.pop("CORRECTIONS_ENABLED", None)
        else:
            os.environ["CORRECTIONS_ENABLED"] = old_corr
    events = _filter_ledger(task_id)
    ok = any(e.get("event") == "second_pass" for e in events)
    print(f"[Scenario: Force Second Pass] second_pass={ok}")
    return ok


def main():
    results = []
    results.append(("long_input", scenario_long_input()))
    results.append(("meta_cognition_logged", scenario_meta_cognition_logged()))
    results.append(("force_second_pass", scenario_force_second_pass()))

    failures = [name for name, ok in results if not ok]
    if failures:
        print("Edge case tests FAILED:", ", ".join(failures))
        sys.exit(1)
    else:
        print("All edge case tests PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
