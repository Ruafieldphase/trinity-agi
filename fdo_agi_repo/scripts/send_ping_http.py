#!/usr/bin/env python3
"""
HTTP-based Task Queue Client (Deprecated)

Deprecated: 통합 스크립트 `fdo_agi_repo/scripts/send_ping.py` 사용을 권장합니다.

권장 사용 예:
    python fdo_agi_repo/scripts/send_ping.py --force http

기존 사용(하위호환 유지):
    python scripts/send_ping_http.py
"""

import requests
import time
import sys

API_BASE = "http://localhost:8091/api"


def submit_task(task_type: str, data: dict, requester: str = "copilot"):
    """Submit task via HTTP POST"""
    url = f"{API_BASE}/tasks"

    payload = {
        "task_type": task_type,
        "data": data,
        "requester": requester
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API 요청 실패: {e}")
        sys.exit(1)


def get_task_status(task_id: str):
    """Get task status via HTTP GET"""
    url = f"{API_BASE}/tasks/{task_id}"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"상태 조회 실패: {e}")
        return None


def get_result(task_id: str):
    """Get task result via HTTP GET"""
    url = f"{API_BASE}/tasks/{task_id}/result"

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"결과 조회 실패: {e}")
        return None


def wait_for_result(task_id: str, timeout: int = 10):
    """Poll for result with timeout"""
    start_time = time.time()

    while time.time() - start_time < timeout:
        result = get_result(task_id)
        if result:
            return result

        time.sleep(0.5)

    return None


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  ⚠️ Deprecated: send_ping_http.py 대신 send_ping.py 사용 권장")
    print("  예: python fdo_agi_repo/scripts/send_ping.py --force http")
    print("="*60 + "\n")

    # Submit ping task
    print("핑 태스크 전송 중...")
    response = submit_task(
        task_type="ping",
        data={},
        requester="copilot-http"
    )

    task_id = response.get('task_id')
    print("태스크 전송 완료!")
    print(f"Task ID: {task_id}")

    # Wait for result
    print("\nComet 응답 대기(최대 10초)...")
    result = wait_for_result(task_id, timeout=10)

    if result:
        print("\n" + "="*60)
        print("  결과 수신 완료!")
        print("="*60)
        print(f"Worker:  {result.get('worker')}")
        print(f"Status:  {result.get('status')}")
        data = result.get('data', {}) or {}
        msg = data.get('message') or ("pong" if 'pong' in data else None)
        print(f"Message: {msg}")
        print(f"Completed: {result.get('completed_at')}")
        print("="*60 + "\n")
    else:
        print("\n10초 내 응답이 없어 종료합니다.")
        print("Comet extension 또는 폴러가 실행 중인지 확인하세요.")
        print(f"상태 확인: curl {API_BASE}/tasks/{task_id}")
        sys.exit(1)

