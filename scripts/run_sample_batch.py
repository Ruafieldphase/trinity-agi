"""Run multiple lightweight orchestrator tasks for policy sampling.

Usage:
  python scripts/run_sample_batch.py --count 12 --delay 3

This is a thin wrapper over pipeline.run_task similar to run_sample_task.py but
allows running many tasks sequentially to generate resonance/policy ledger
entries quickly.
"""

from __future__ import annotations

import argparse
import time
import uuid
from pathlib import Path
import sys
from workspace_root import get_workspace_root


def add_paths() -> None:
    here = Path(__file__).resolve()
    root = get_workspace_root()
    for p in (root, root / "fdo_agi_repo"):
        sp = str(p)
        if sp not in sys.path:
            sys.path.insert(0, sp)


def build_spec(index: int, total: int) -> dict:
    task_id = f"batch-sample-{int(time.time())}-{index:02d}-{uuid.uuid4().hex[:4]}"
    goal = (
        "Provide a concise status recap for the orchestrator, focusing on"
        " latency and evidence signals."
    )
    return {
        "task_id": task_id,
        "title": f"Policy sample task {index + 1}/{total}",
        "goal": goal,
        "constraints": ["Keep response under 180 words."],
        "inputs": {},
        "scope": "analysis",
        "permissions": ["READ"],
        "evidence_required": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10, help="Number of tasks to run")
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Seconds to sleep between tasks (≥0)",
    )
    args = parser.parse_args()
    count = max(1, args.count)
    delay = max(0.0, args.delay)

    add_paths()
    from fdo_agi_repo.orchestrator import pipeline

    print(f"[batch] starting {count} sample tasks (delay={delay}s)")
    start = time.perf_counter()
    successes = 0
    for i in range(count):
        spec = build_spec(i, count)
        print(f"[batch] -> {spec['task_id']}")
        run_start = time.perf_counter()
        result = pipeline.run_task({}, spec)
        run_end = time.perf_counter()
        status = result.get("status", "OK")
        print(
            f"[batch] <- {spec['task_id']} status={status}"
            f" duration={run_end - run_start:.2f}s"
        )
        if status not in {"HALT", "ERROR"}:
            successes += 1
        if i != count - 1 and delay > 0:
            time.sleep(delay)

    elapsed = time.perf_counter() - start
    ledger_path = get_workspace_root() / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
    print(
        f"[batch] completed {successes}/{count} tasks in {elapsed:.1f}s."
        f" ledger: {ledger_path if ledger_path.exists() else 'not yet created'}"
    )


if __name__ == "__main__":
    main()

