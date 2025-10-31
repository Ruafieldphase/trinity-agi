#!/usr/bin/env python3
"""
Comet Ping task (auto-detect HTTP, fallback to file queue)

Usage:
    python fdo_agi_repo/scripts/send_ping.py [--force http|file] [--timeout 10] [--api http://localhost:8091/api]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
from shared_task_queue import TaskQueue  # file-based queue


API_BASE = "http://localhost:8091/api"


def _http_available() -> bool:
    """Return True if HTTP API server is reachable, else False.

    Falls back to file-based queue if requests is missing or server is down.
    """
    try:
        import requests  # type: ignore
    except Exception:
        return False

    try:
        r = requests.get(f"{API_BASE}/health", timeout=1.5)
        return r.status_code == 200
    except Exception:
        return False


def _submit_http_ping() -> Optional[str]:
    """Submit ping task via HTTP. Returns task_id or None on failure."""
    try:
        import requests  # type: ignore
    except Exception:
        return None

    url = f"{API_BASE}/tasks/create"
    payload = {"type": "ping", "data": {}}
    try:
        resp = requests.post(url, json=payload, timeout=5)
        resp.raise_for_status()
        return resp.json().get("task_id")
    except Exception:
        return None


def _wait_http_result(task_id: str, timeout: float = 10.0) -> Optional[dict]:
    """Poll HTTP API for result until timeout. Returns result dict or None."""
    try:
        import requests  # type: ignore
    except Exception:
        return None

    url = f"{API_BASE}/results/{task_id}"
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                return r.json()
            # 404 means not ready yet
        except Exception:
            pass
        time.sleep(0.4)
    return None


def send_ping_task(force: Optional[str] = None, timeout: float = 10.0, api_base: Optional[str] = None) -> str:
    """Send a ping task using HTTP if available, else file queue.

    Args:
        force: 'http' 또는 'file' 강제 모드. None이면 자동 감지.
        timeout: 결과 대기 시간(초)
        api_base: 커스텀 API base URL (기본: http://localhost:8091/api)
    """
    global API_BASE
    if api_base:
        API_BASE = api_base.rstrip("/")

    use_http = _http_available()
    if force == "http":
        use_http = True
    elif force == "file":
        use_http = False

    if use_http:
        print("[send_ping] HTTP API 감지(8091 포트). HTTP 클라이언트 사용")
        task_id = _submit_http_ping()
        if not task_id:
            print("[send_ping] HTTP submission failed. Falling back to file queue.")
        else:
            print(f"[send_ping] 태스크 제출 완료. Task ID: {task_id}")
            result = _wait_http_result(task_id, timeout=timeout)
            if result:
                data = result.get("data", {}) or {}
                msg = data.get("message") or ("pong" if "pong" in data else None)
                status = result.get("status")
                worker = result.get("worker")
                print(f"[send_ping] HTTP 결과 -> status={status}, worker={worker}, message={msg}")
            else:
                print(f"[send_ping] No result within {timeout}s. Verify Comet worker is running.")
                print(f"[send_ping] 상태 URL: {API_BASE}/results/{task_id}")
            return task_id or ""

    # Fallback: file-based queue
    queue = TaskQueue()
    task_id = queue.push_task(task_type="ping", data={}, requester="copilot")
    print(f"[send_ping] 파일 큐 제출. Task ID: {task_id}")
    print(f"[send_ping] 최대 {timeout}초 동안 결과 파일 대기...")
    result = queue.get_result(task_id, timeout=timeout)
    if result:
        data = result.data or {}
        msg = data.get("message") or ("pong" if "pong" in data else None)
        print(f"[send_ping] 파일 결과 -> status={result.status}, worker={result.worker}, message={msg}")
    else:
        print(f"[send_ping] No result within {timeout}s. If using Comet browser worker, ensure it is active.")
        res_path = Path(__file__).parent.parent / "outputs" / "task_queue" / "results" / f"{task_id}.json"
        print(f"[send_ping] 나중에 직접 확인 가능: {res_path}")
    return task_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a ping task (HTTP-first with file fallback)")
    parser.add_argument("--force", choices=["http", "file"], help="강제 실행 모드 선택 (http | file)")
    parser.add_argument("--timeout", type=float, default=10.0, help="결과 대기 시간(초), 기본 10")
    parser.add_argument("--api", type=str, default=None, help="커스텀 API base URL (예: http://localhost:8091/api)")
    args = parser.parse_args()

    send_ping_task(force=args.force, timeout=args.timeout, api_base=args.api)
