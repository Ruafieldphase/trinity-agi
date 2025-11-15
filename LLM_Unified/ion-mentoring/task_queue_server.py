#!/usr/bin/env python3
"""
Minimal Task Queue Server for Integration Testing

Provides HTTP endpoints for Computer Use task queue:
- GET /api/health - Health check
- GET /api/tasks/next - Fetch next task from queue
- POST /api/tasks/{task_id}/result - Submit task result
- POST /api/tasks/create - Create new task (for testing)

Usage:
    python task_queue_server.py --port 8091
"""

import argparse
import json
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from threading import Lock
import time

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# In-memory task queue with priority support
# Priority queues: urgent (P0), normal (P1), low (P2)
task_queue_urgent: List[Dict[str, Any]] = []
task_queue_normal: List[Dict[str, Any]] = []
task_queue_low: List[Dict[str, Any]] = []
task_results: Dict[str, Dict[str, Any]] = {}
inflight_tasks: Dict[str, Dict[str, Any]] = {}
queue_lock = Lock()

# Priority levels
PRIORITY_URGENT = "urgent"
PRIORITY_NORMAL = "normal"
PRIORITY_LOW = "low"
VALID_PRIORITIES = {PRIORITY_URGENT, PRIORITY_NORMAL, PRIORITY_LOW}

# Re-delivery lease for at-least-once semantics
LEASE_TIMEOUT_SECONDS = 120

app = FastAPI(title="Computer Use Task Queue Server", version="1.0.0")


# === Helper Functions ===

def _get_queue_by_priority(priority: str) -> List[Dict[str, Any]]:
    """Get the appropriate queue based on priority"""
    if priority == PRIORITY_URGENT:
        return task_queue_urgent
    elif priority == PRIORITY_LOW:
        return task_queue_low
    else:  # default to normal
        return task_queue_normal


def _get_total_queue_size() -> int:
    """Get total queue size across all priorities"""
    return len(task_queue_urgent) + len(task_queue_normal) + len(task_queue_low)


def _get_next_task_from_queue() -> Optional[Dict[str, Any]]:
    """Get next task from queue respecting priority: urgent > normal > low"""
    if task_queue_urgent:
        return task_queue_urgent.pop(0)
    elif task_queue_normal:
        return task_queue_normal.pop(0)
    elif task_queue_low:
        return task_queue_low.pop(0)
    return None


def _requeue_task(task: Dict[str, Any]) -> None:
    """Requeue task to front of appropriate priority queue"""
    priority = task.get("priority", PRIORITY_NORMAL)
    queue = _get_queue_by_priority(priority)
    queue.insert(0, task)


def _enqueue_task(task: Dict[str, Any], priority: str = PRIORITY_NORMAL) -> int:
    """Enqueue task to appropriate priority queue"""
    task["priority"] = priority  # Store priority in task
    queue = _get_queue_by_priority(priority)
    queue.append(task)
    return _get_total_queue_size()

# === Request Logging Middleware ===
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"[IN] {request.method} {request.url.path} - Client: {request.client}")
    response = await call_next(request)
    logger.info(f"[OUT] {request.method} {request.url.path} - Status: {response.status_code}")
    return response


# === Models ===

class Task(BaseModel):
    task_id: str
    type: str
    data: Dict[str, Any]
    created_at: str


class TaskResult(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class CreateTaskRequest(BaseModel):
    type: str
    data: Dict[str, Any]


# === Endpoints ===

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "task-queue-server",
        "queue_size": _get_total_queue_size(),
        "queue_urgent": len(task_queue_urgent),
        "queue_normal": len(task_queue_normal),
        "queue_low": len(task_queue_low),
        "results_count": len(task_results),
        "timestamp": datetime.now().isoformat()
    }


@app.api_route("/api/tasks/next", methods=["GET", "POST"])
async def get_next_task(request: Request):
    """Fetch next task from queue (priority-based) - Supports both GET and POST for compatibility"""
    logger.info(f"{request.method} /api/tasks/next - Client: {request.client}")
    with queue_lock:
        # Requeue expired inflight tasks (lease timeout)
        now = time.time()
        expired: List[str] = []
        for tid, meta in inflight_tasks.items():
            leased_at = meta.get("leased_at", 0)
            if now - float(leased_at) >= LEASE_TIMEOUT_SECONDS:
                # push back to front for faster retry
                _requeue_task(meta["task"])
                expired.append(tid)
                logger.warning(f"Lease expired -> requeued task: {tid}")
        for tid in expired:
            inflight_tasks.pop(tid, None)

        # Get next task respecting priority
        task = _get_next_task_from_queue()
        if not task:
            # Empty object instead of 204 to prevent JSON parse error
            return {"task": None}
        
        # Register lease
        worker_name = request.headers.get("X-Worker-Name") or "unknown"
        inflight_tasks[task["task_id"]] = {
            "task": task,
            "leased_at": now,
            "worker": worker_name,
        }
        priority = task.get("priority", PRIORITY_NORMAL)
        logger.info(f"Dequeued task: {task['task_id']} (type: {task['type']}, priority: {priority}) | lease to {worker_name}")
        return task


@app.post("/api/tasks/{task_id}/result")
async def submit_task_result(task_id: str, result: TaskResult):
    """Submit task execution result"""
    with queue_lock:
        # Clear from inflight on result
        inflight_tasks.pop(task_id, None)
        task_results[task_id] = {
            "task_id": task_id,
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "submitted_at": datetime.now().isoformat()
        }
    
    logger.info(f"Received result for task {task_id}: {'SUCCESS' if result.success else 'FAILED'}")
    
    if result.error:
        logger.warning(f"  Error: {result.error}")
    
    return {"message": f"Result for task {task_id} recorded", "success": result.success}


@app.post("/api/tasks/create")
async def create_task(
    request: CreateTaskRequest,
    priority: str = Query(default=PRIORITY_NORMAL, description="Task priority: urgent, normal, or low")
):
    """Create new task with optional priority (urgent, normal, low)"""
    # Validate priority
    if priority not in VALID_PRIORITIES:
        logger.warning(f"Invalid priority '{priority}', defaulting to 'normal'")
        priority = PRIORITY_NORMAL
    
    task_id = str(uuid.uuid4())
    task = {
        "task_id": task_id,
        "type": request.type,
        "data": request.data,
        "priority": priority,
        "created_at": datetime.now().isoformat()
    }
    
    with queue_lock:
        immediate_handled = False

        # Handle certain task types immediately to facilitate simple integrations/tests
        # 1) ping task: return success immediately
        if task["type"] == 'ping':
            task_results[task_id] = {
                "success": True,
                "data": {
                    "pong": True,
                    "ts": time.time()
                }
            }
            immediate_handled = True

        # 2) computer_use.scan task: optional kill-switch via env
        elif task["type"] == 'computer_use.scan':
            enable_env = os.getenv('ENABLE_COMPUTER_USE_OVER_HTTP', '0').strip().lower()
            enabled = enable_env in ('1', 'true', 'yes', 'on')
            if enabled:
                # We don't actually scan here; return an empty element list as a stub
                task_results[task_id] = {
                    "success": True,
                    "data": {
                        "elements": [],
                        "note": "computer_use.scan handled by server stub"
                    }
                }
            else:
                task_results[task_id] = {
                    "success": False,
                    "error": (
                        "Computer Use over HTTP disabled by kill-switch. "
                        "Set ENABLE_COMPUTER_USE_OVER_HTTP=1 to enable. "
                        "(kill-switch: enableComputerUseOverHttp)"
                    )
                }
            immediate_handled = True

        # 3) default: enqueue for an external worker to process
        if not immediate_handled:
            queue_position = _enqueue_task(task, priority)
    
    logger.info(f"Created task: {task_id} (type: {request.type}, priority: {priority})")
    return {
        "task_id": task_id,
        "message": "Task created",
        "priority": priority,
        "queue_position": queue_position
    }


# Compatibility endpoint for existing E2E scripts expecting /api/enqueue
@app.post("/api/enqueue")
async def enqueue_compat(request: Request):
    """Compatibility shim to accept {task_type, params, priority} and enqueue a task.

    Maps to the canonical /api/tasks/create endpoint.
    Supports optional priority parameter (urgent, normal, low).
    """
    try:
        payload = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    task_type = payload.get("task_type") or payload.get("type") or "generic"
    data = payload.get("params") or payload.get("data") or {}
    priority = payload.get("priority", PRIORITY_NORMAL)

    # Validate priority
    if priority not in VALID_PRIORITIES:
        logger.warning(f"Invalid priority '{priority}' in /api/enqueue, defaulting to 'normal'")
        priority = PRIORITY_NORMAL

    try:
        req = CreateTaskRequest(type=task_type, data=data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")

    return await create_task(req, priority=priority)


@app.get("/api/tasks")
async def list_tasks():
    """List all tasks in queue by priority (for debugging)"""
    return {
        "queue_urgent": task_queue_urgent,
        "queue_normal": task_queue_normal,
        "queue_low": task_queue_low,
        "total_queue_size": _get_total_queue_size()
    }


@app.get("/api/inflight")
async def list_inflight():
    """List inflight leased tasks (for debugging/recovery visibility)"""
    with queue_lock:
        items = []
        for tid, meta in inflight_tasks.items():
            items.append({
                "task_id": tid,
                "type": meta["task"].get("type"),
                "leased_at": meta.get("leased_at"),
                "worker": meta.get("worker"),
                "age_sec": time.time() - float(meta.get("leased_at", 0)),
            })
    return {"inflight": items, "count": len(items)}


@app.get("/api/results")
async def list_results():
    """List all task results (for debugging)"""
    return {
        "results": list(task_results.values()),
        "count": len(task_results)
    }


@app.get("/api/results/{task_id}")
async def get_task_result(task_id: str):
    """Get specific task result"""
    if task_id not in task_results:
        raise HTTPException(status_code=404, detail=f"Result for task {task_id} not found")
    
    return task_results[task_id]


@app.get("/api/stats")
async def get_stats():
    """Get queue statistics for monitoring"""
    with queue_lock:
        # Calculate statistics
        total_completed = len(task_results)
        successful = sum(1 for r in task_results.values() if r.get("success"))
        failed = total_completed - successful
        
        # Calculate average duration if available
        durations = []
        for result in task_results.values():
            if result.get("data") and "duration_ms" in result["data"]:
                durations.append(result["data"]["duration_ms"])
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Worker count (unique workers from inflight tasks)
        workers = set(meta.get("worker", "unknown") for meta in inflight_tasks.values())
        active_workers = len([w for w in workers if w != "unknown"])
        
        return {
            "pending": _get_total_queue_size(),
            "pending_urgent": len(task_queue_urgent),
            "pending_normal": len(task_queue_normal),
            "pending_low": len(task_queue_low),
            "inflight": len(inflight_tasks),
            "completed": total_completed,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total_completed * 100) if total_completed > 0 else 0,
            "workers": active_workers,
            "avg_duration_ms": avg_duration,
            "timestamp": datetime.now().isoformat()
        }


# === Main ===

def main():
    parser = argparse.ArgumentParser(description="Task Queue Server for Integration Testing")
    parser.add_argument('--port', type=int, default=8091, help='Server port (default: 8091)')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Server host (default: 127.0.0.1)')
    args = parser.parse_args()
    
    logger.info(f"Starting Task Queue Server on {args.host}:{args.port}...")
    logger.info("Endpoints:")
    logger.info(f"  Health: http://{args.host}:{args.port}/api/health")
    logger.info(f"  Next Task: http://{args.host}:{args.port}/api/tasks/next")
    logger.info(f"  Submit Result: http://{args.host}:{args.port}/api/tasks/{{task_id}}/result")
    logger.info(f"  Create Task: http://{args.host}:{args.port}/api/tasks/create")
    
    try:
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level="info",
            access_log=False
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")


if __name__ == "__main__":
    main()
