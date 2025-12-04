#!/usr/bin/env python3
"""
Shared Task Queue: AI 간 협업을 위한 파일 기반 메시지 큐

GitHub Copilot ↔ Task Queue ↔ Comet Browser AI

Usage:
    # Copilot이 웹 작업 요청
    queue.push_task("web_scraping", {"url": "https://example.com", "selector": ".content"})
    
    # Comet이 작업 가져가기
    task = queue.pop_task("comet-browser")
    
    # Comet이 결과 반환
    queue.push_result(task.id, {"html": "...", "status": "success"})
    
    # Copilot이 결과 확인
    result = queue.get_result(task_id)
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import uuid
import time


QUEUE_DIR = Path(__file__).parent.parent / "outputs" / "task_queue"
QUEUE_DIR.mkdir(parents=True, exist_ok=True)

TASKS_DIR = QUEUE_DIR / "tasks"
RESULTS_DIR = QUEUE_DIR / "results"
INBOX_DIR = QUEUE_DIR / "inbox"

TASKS_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)
INBOX_DIR.mkdir(exist_ok=True)


@dataclass
class Task:
    """작업 요청"""
    id: str
    type: str  # "web_scraping", "web_interaction", "api_call", etc.
    requester: str  # "copilot", "comet", "cursor", etc.
    data: Dict[str, Any]
    status: str  # "pending", "in_progress", "completed", "failed"
    created_at: str
    assigned_to: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class TaskResult:
    """작업 결과"""
    task_id: str
    worker: str
    status: str  # "success", "error"
    data: Dict[str, Any]
    completed_at: str
    error_message: Optional[str] = None


class TaskQueue:
    """AI 간 협업을 위한 작업 큐"""
    
    def push_task(self, task_type: str, data: Dict[str, Any], requester: str = "copilot") -> str:
        """작업 추가 (Copilot → Comet)"""
        task = Task(
            id=str(uuid.uuid4()),
            type=task_type,
            requester=requester,
            data=data,
            status="pending",
            created_at=datetime.now().isoformat()
        )
        
        task_file = TASKS_DIR / f"{task.id}.json"
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(task), f, indent=2, ensure_ascii=False)
        
        print(f"[TaskQueue] Task {task.id} pushed: {task_type}")
        return task.id
    
    def pop_task(self, worker: str = "comet-browser", task_type: Optional[str] = None) -> Optional[Task]:
        """작업 가져가기 (Comet이 실행)"""
        pending_tasks = sorted(TASKS_DIR.glob("*.json"))
        
        for task_file in pending_tasks:
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    task_data = json.load(f)
                
                task = Task(**task_data)
                
                # 이미 처리 중이면 스킵
                if task.status != "pending":
                    continue
                
                # 특정 타입만 가져가기
                if task_type and task.type != task_type:
                    continue
                
                # 작업 할당
                task.status = "in_progress"
                task.assigned_to = worker
                task.updated_at = datetime.now().isoformat()
                
                with open(task_file, 'w', encoding='utf-8') as f:
                    json.dump(asdict(task), f, indent=2, ensure_ascii=False)
                
                print(f"[TaskQueue] Task {task.id} assigned to {worker}")
                return task
            except json.JSONDecodeError:
                # 파일이 쓰기 중일 수 있음 — 잠시 후 재시도 위해 건너뜀 (소음 억제)
                continue
            except Exception as e:
                print(f"[TaskQueue] Error reading task {task_file}: {e}")
                continue
        
        return None
    
    def push_result(self, task_id: str, data: Dict[str, Any], worker: str = "comet-browser", 
                    status: str = "success", error: Optional[str] = None):
        """결과 반환 (Comet → Copilot)"""
        result = TaskResult(
            task_id=task_id,
            worker=worker,
            status=status,
            data=data,
            completed_at=datetime.now().isoformat(),
            error_message=error
        )
        
        result_file = RESULTS_DIR / f"{task_id}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(result), f, indent=2, ensure_ascii=False)
        
        # 작업 상태 업데이트
        task_file = TASKS_DIR / f"{task_id}.json"
        if task_file.exists():
            with open(task_file, 'r', encoding='utf-8') as f:
                task_data = json.load(f)
            
            task_data['status'] = 'completed' if status == 'success' else 'failed'
            task_data['updated_at'] = datetime.now().isoformat()
            
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task_data, f, indent=2, ensure_ascii=False)
        
        print(f"[TaskQueue] Result for {task_id}: {status}")
    
    def get_result(self, task_id: str, timeout: float = 60.0) -> Optional[TaskResult]:
        """결과 대기 (Copilot이 확인)"""
        result_file = RESULTS_DIR / f"{task_id}.json"
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if result_file.exists():
                try:
                    with open(result_file, 'r', encoding='utf-8') as f:
                        result_data = json.load(f)
                    return TaskResult(**result_data)
                except Exception as e:
                    print(f"[TaskQueue] Error reading result: {e}")
            
            time.sleep(0.5)
        
        print(f"[TaskQueue] Timeout waiting for result {task_id}")
        return None
    
    def list_pending_tasks(self, task_type: Optional[str] = None) -> List[Task]:
        """대기 중인 작업 목록"""
        tasks = []
        for task_file in TASKS_DIR.glob("*.json"):
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    task_data = json.load(f)
                
                task = Task(**task_data)
                if task.status == "pending":
                    if task_type is None or task.type == task_type:
                        tasks.append(task)
            except Exception:
                continue
        
        return sorted(tasks, key=lambda t: t.created_at)
    
    def cleanup_old_tasks(self, max_age_hours: float = 24):
        """오래된 완료 작업 정리"""
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
        
        cleaned = 0
        for task_file in TASKS_DIR.glob("*.json"):
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    task_data = json.load(f)
                
                if task_data['status'] in ['completed', 'failed']:
                    created = datetime.fromisoformat(task_data['created_at']).timestamp()
                    if created < cutoff:
                        task_file.unlink()
                        
                        # 결과 파일도 삭제
                        result_file = RESULTS_DIR / f"{task_data['id']}.json"
                        if result_file.exists():
                            result_file.unlink()
                        
                        cleaned += 1
            except Exception:
                continue
        
        print(f"[TaskQueue] Cleaned {cleaned} old tasks")


# ============================================================
# 사용 예시 (협업 시나리오)
# ============================================================

def example_copilot_requests_web_task():
    """Copilot이 Comet에게 웹 작업 요청"""
    queue = TaskQueue()
    
    # 웹 스크래핑 요청
    task_id = queue.push_task("web_scraping", {
        "url": "https://www.python.org/downloads/",
        "selector": ".download-list-widget a",
        "extract": ["href", "text"],
        "reason": "최신 Python 버전 확인 필요"
    }, requester="copilot")
    
    print(f"Task created: {task_id}")
    print("Waiting for Comet to process...")
    
    # 결과 대기 (60초)
    result = queue.get_result(task_id, timeout=60)
    
    if result and result.status == "success":
        print(f"Success! Data: {result.data}")
    else:
        print(f"Failed or timeout")


def example_comet_processes_tasks():
    """Comet이 작업 처리"""
    queue = TaskQueue()
    
    print("[Comet] Checking for tasks...")
    
    # 웹 작업 가져가기
    task = queue.pop_task("comet-browser", task_type="web_scraping")
    
    if task:
        print(f"[Comet] Processing task {task.id}: {task.type}")
        print(f"[Comet] URL: {task.data['url']}")
        
        # 실제 웹 작업 수행 (Comet의 기능 사용)
        # ... Comet의 브라우저 API로 스크래핑 ...
        
        # 결과 반환
        queue.push_result(task.id, {
            "links": [
                {"href": "/downloads/release/python-3130/", "text": "Python 3.13.0"},
                {"href": "/downloads/release/python-3129/", "text": "Python 3.12.9"}
            ],
            "scraped_at": datetime.now().isoformat()
        }, worker="comet-browser", status="success")
        
        print(f"[Comet] Task {task.id} completed")
    else:
        print("[Comet] No tasks available")


if __name__ == '__main__':
    # 테스트: Copilot 역할
    import sys
    
    queue = TaskQueue()
    
    if len(sys.argv) > 1 and sys.argv[1] == "request":
        # Copilot이 작업 요청
        task_id = queue.push_task("web_scraping", {
            "url": "https://example.com",
            "selector": "h1",
            "extract": ["text"]
        })
        print(f"Task ID: {task_id}")
        print("Run with 'process' argument to simulate Comet")
    
    elif len(sys.argv) > 1 and sys.argv[1] == "process":
        # Comet이 작업 처리
        task = queue.pop_task("comet-test")
        if task:
            print(f"Processing: {task.id}")
            queue.push_result(task.id, {"example": "result"})
        else:
            print("No tasks")
    
    elif len(sys.argv) > 1 and sys.argv[1] == "list":
        # 대기 작업 확인
        tasks = queue.list_pending_tasks()
        print(f"Pending tasks: {len(tasks)}")
        for t in tasks:
            print(f"  - {t.id}: {t.type} from {t.requester}")
    
    else:
        print("Usage:")
        print("  python shared_task_queue.py request   # Copilot requests task")
        print("  python shared_task_queue.py process   # Comet processes task")
        print("  python shared_task_queue.py list      # List pending tasks")
