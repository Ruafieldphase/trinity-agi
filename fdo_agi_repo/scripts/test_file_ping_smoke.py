#!/usr/bin/env python3
"""
File-mode Ping smoke test (CI-friendly)

 - Pushes a 'ping' task via file queue
 - Processes it in-process using comet_simple_worker.process_one_task
 - Exits 0 on success within timeout, else non-zero

Usage:
    python fdo_agi_repo/scripts/test_file_ping_smoke.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Ensure local imports work
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from shared_task_queue import TaskQueue  # type: ignore
import comet_simple_worker as worker  # type: ignore


def main(timeout: float = 10.0) -> int:
    queue = TaskQueue()
    task_id = queue.push_task(task_type="ping", data={}, requester="ci-smoke")
    start = time.time()

    while time.time() - start < timeout:
        try:
            # Process at most one task per cycle
            worker.process_one_task(worker_id="ci-smoke")
        except Exception:
            # Even if worker errors, keep polling result in case it succeeded
            pass

        # Short, non-blocking check for result
        result = queue.get_result(task_id, timeout=0.1)
        if result is not None:
            ok = (result.status == "success")
            data = result.data or {}
            msg = data.get("message") or ("pong" if "pong" in data else None)
            print(f"[smoke] status={result.status} worker={result.worker} message={msg}")
            return 0 if ok else 2

        time.sleep(0.2)

    print(f"[smoke] timeout waiting for result: {task_id}")
    return 1


if __name__ == "__main__":
    sys.exit(main())

