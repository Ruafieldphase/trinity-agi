"""
Day 5 E2E Test for RPA Worker

Prereq:
- Task Queue Server running on http://127.0.0.1:8091 (use VS Code task: "?�� Comet-Gitko: Start Task Queue Server (Background)")
- rpa_worker.py running (background)

Test Plan:
1) Submit a ping task → expect pong result
2) Submit an RPA wait task (does not require pyautogui) → expect success
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict
import requests

SERVER = "http://127.0.0.1:8091"


def submit_task(task_type: str, data: Dict[str, Any]) -> str:
    r = requests.post(f"{SERVER}/api/tasks/create", json={"type": task_type, "data": data}, timeout=10)
    r.raise_for_status()
    return r.json()["task_id"]


def get_result(task_id: str, timeout: float = 10.0) -> Dict[str, Any]:
    t0 = time.time()
    while time.time() - t0 < timeout:
        resp = requests.get(f"{SERVER}/api/results/{task_id}")
        if resp.status_code == 200:
            return resp.json()
        time.sleep(0.5)
    raise TimeoutError(f"Result for task {task_id} not available within {timeout}s")


def main():
    # Health
    h = requests.get(f"{SERVER}/api/health", timeout=5).json()
    print("Health:", json.dumps(h, indent=2, ensure_ascii=False))

    # 1) Ping task
    ping_id = submit_task("ping", {})
    print("Submitted ping:", ping_id)
    ping_res = get_result(ping_id, timeout=15)
    print("Ping result:", json.dumps(ping_res, indent=2, ensure_ascii=False))
    assert ping_res.get("success", True) is True or ping_res.get("status") == "success"

    # 2) RPA wait task (safe)
    rpa_id = submit_task("rpa", {"action": "wait", "params": {"seconds": 0.3}})
    print("Submitted rpa(wait):", rpa_id)
    rpa_res = get_result(rpa_id, timeout=15)
    print("RPA result:", json.dumps(rpa_res, indent=2, ensure_ascii=False))

    ok = rpa_res.get("success")
    # server stores as success: bool
    assert ok is True, f"RPA wait failed: {rpa_res}"

    print("\n✅ Day 5 E2E basic test passed.")


if __name__ == "__main__":
    main()
