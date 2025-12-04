#!/usr/bin/env python3
"""
HTTP-mode Ping smoke test

- Starts the API server and HTTP poller as subprocesses
- Forces HTTP mode ping via send_ping.py and verifies result

Usage:
    python fdo_agi_repo/scripts/test_http_ping_smoke.py
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

try:
    import requests  # type: ignore
except Exception:
    print("[http_smoke] 'requests' not installed. Please install requests.")
    sys.exit(2)


def wait_for_health(url: str, timeout: float = 8.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=1.0)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.2)
    return False


def terminate(proc: subprocess.Popen | None) -> None:
    if not proc:
        return
    if proc.poll() is None:
        try:
            proc.terminate()
        except Exception:
            pass
        try:
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


def main() -> int:
    scripts_dir = Path(__file__).parent.resolve()
    py = sys.executable

    api_proc = None
    poller_proc = None
    try:
        # Start API server
        api_proc = subprocess.Popen([py, str(scripts_dir / "task_queue_api_server.py")])
        if not wait_for_health("http://localhost:8091/health", timeout=8.0):
            print("[http_smoke] API health did not come up on :8091")
            return 2

        # Start HTTP poller
        poller_proc = subprocess.Popen([
            py,
            str(scripts_dir / "http_task_poller.py"),
            "--worker-id", "comet-http-smoke",
            "--interval", "0.5",
        ])

        # Import and send ping via HTTP (forced)
        sys.path.insert(0, str(scripts_dir))
        import send_ping as sp  # type: ignore

        task_id = sp.send_ping_task(force="http", timeout=10.0, api_base="http://localhost:8091/api")
        if not task_id:
            print("[http_smoke] No task_id returned from send_ping")
            return 3

        # Verify result via HTTP
        url = f"http://localhost:8091/api/tasks/{task_id}/result"
        start = time.time()
        while time.time() - start < 10.0:
            try:
                r = requests.get(url, timeout=1.5)
                if r.status_code == 200:
                    js = r.json()
                    status = js.get("status")
                    data = js.get("data") or {}
                    ok = (status == "success") and (data.get("message") == "pong" or ("pong" in data))
                    print(f"[http_smoke] status={status} data={data}")
                    return 0 if ok else 4
            except Exception:
                pass
            time.sleep(0.3)

        print("[http_smoke] Timeout waiting for result")
        return 5

    finally:
        terminate(poller_proc)
        terminate(api_proc)


if __name__ == "__main__":
    sys.exit(main())

