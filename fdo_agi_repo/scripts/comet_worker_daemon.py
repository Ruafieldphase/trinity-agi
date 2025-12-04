#!/usr/bin/env python3
"""
Comet Worker Daemon: 백그라운드에서 계속 작업 처리

Comet Browser AI가 이 파일만 실행하면
자동으로 작업 큐를 모니터링하고 처리합니다.

Usage (Comet이 실행):
    python comet_worker_daemon.py
    
    또는
    
    python comet_worker_daemon.py --interval 5 --worker-id my-comet
"""

import time
import argparse
from pathlib import Path
from datetime import datetime
from shared_task_queue import TaskQueue, TASKS_DIR


def simulate_web_scraping(url: str, selector: str, extract: list) -> dict:
    """
    실제 Comet은 브라우저 API를 사용하겠지만,
    여기서는 시뮬레이션
    
    Comet이 실제로 구현할 부분:
    - comet.browser.navigate(url)
    - comet.browser.wait_for_selector(selector)
    - elements = comet.browser.query_selector_all(selector)
    - return [element.get_attribute(attr) for attr in extract]
    """
    print(f"  [Comet] Navigating to {url}")
    print(f"  [Comet] Finding elements: {selector}")
    print(f"  [Comet] Extracting: {extract}")
    
    # 시뮬레이션 결과
    time.sleep(2)  # 실제 브라우저 로딩 시뮬레이션
    
    return {
        "elements": [
            {"href": "/example1", "text": "Example 1"},
            {"href": "/example2", "text": "Example 2"}
        ],
        "scraped_at": datetime.now().isoformat(),
        "success": True
    }


def simulate_web_interaction(action: str, target: str, value: str = None) -> dict:
    """
    웹 인터랙션 시뮬레이션
    
    Comet이 실제로 구현:
    - comet.browser.click(target)
    - comet.browser.type(target, value)
    - comet.browser.screenshot()
    """
    print(f"  [Comet] Action: {action} on {target}")
    if value:
        print(f"  [Comet] Value: {value}")
    
    time.sleep(1)
    
    return {
        "action": action,
        "target": target,
        "success": True,
        "timestamp": datetime.now().isoformat()
    }


def process_task(task, worker_id: str):
    """작업 처리 (Comet이 커스터마이즈)"""
    queue = TaskQueue()
    
    print(f"[Comet Worker] Processing task {task.id}")
    print(f"  Type: {task.type}")
    print(f"  From: {task.requester}")
    print(f"  Data: {task.data}")
    
    try:
        if task.type == "web_scraping":
            # 웹 스크래핑 처리
            result_data = simulate_web_scraping(
                task.data.get('url'),
                task.data.get('selector'),
                task.data.get('extract', [])
            )
            queue.push_result(task.id, result_data, worker=worker_id, status="success")
        
        elif task.type == "web_interaction":
            # 웹 인터랙션 처리
            result_data = simulate_web_interaction(
                task.data.get('action'),
                task.data.get('target'),
                task.data.get('value')
            )
            queue.push_result(task.id, result_data, worker=worker_id, status="success")
        
        elif task.type == "screenshot":
            # 스크린샷 캡처
            result_data = {
                "screenshot_path": f"outputs/screenshots/task_{task.id}.png",
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            queue.push_result(task.id, result_data, worker=worker_id, status="success")
        
        else:
            # 알 수 없는 작업 타입
            queue.push_result(
                task.id,
                {"error": f"Unknown task type: {task.type}"},
                worker=worker_id,
                status="error",
                error=f"Unsupported task type: {task.type}"
            )
        
        print(f"[Comet Worker] Task {task.id} completed\n")
    
    except Exception as e:
        print(f"[Comet Worker] Task {task.id} failed: {e}\n")
        queue.push_result(
            task.id,
            {"error": str(e)},
            worker=worker_id,
            status="error",
            error=str(e)
        )


def run_worker(worker_id: str, interval: float = 5.0, max_tasks_per_cycle: int = 5):
    """
    워커 데몬 실행
    
    Args:
        worker_id: 워커 ID (예: "comet-browser-1")
        interval: 체크 간격 (초)
        max_tasks_per_cycle: 한 번에 처리할 최대 작업 수
    """
    queue = TaskQueue()
    
    print("=" * 60)
    print("Comet Worker Daemon Started")
    print("=" * 60)
    print(f"Worker ID: {worker_id}")
    print(f"Check Interval: {interval}s")
    print(f"Max Tasks/Cycle: {max_tasks_per_cycle}")
    print(f"Task Queue: {TASKS_DIR}")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()
    
    cycle = 0
    
    try:
        while True:
            cycle += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] Cycle {cycle}: Checking for tasks...")
            
            tasks_processed = 0
            
            for _ in range(max_tasks_per_cycle):
                task = queue.pop_task(worker_id)
                
                if task:
                    tasks_processed += 1
                    process_task(task, worker_id)
                else:
                    break  # 더 이상 작업 없음
            
            if tasks_processed == 0:
                print(f"  No tasks. Waiting {interval}s...\n")
            else:
                print(f"  Processed {tasks_processed} task(s)\n")
            
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\n[Comet Worker] Shutting down gracefully...")
        print("Worker stopped.")


def main():
    parser = argparse.ArgumentParser(description="Comet Worker Daemon")
    parser.add_argument('--worker-id', default='comet-browser',
                       help='Worker identifier (default: comet-browser)')
    parser.add_argument('--interval', type=float, default=5.0,
                       help='Check interval in seconds (default: 5.0)')
    parser.add_argument('--max-tasks', type=int, default=5,
                       help='Max tasks per cycle (default: 5)')
    
    args = parser.parse_args()
    
    run_worker(
        worker_id=args.worker_id,
        interval=args.interval,
        max_tasks_per_cycle=args.max_tasks
    )


if __name__ == '__main__':
    main()
