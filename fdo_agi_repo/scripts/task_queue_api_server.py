#!/usr/bin/env python3
"""
Task Queue HTTP API Server

브라우저 AI (Comet)가 HTTP 요청으로 작업을 처리할 수 있도록
간단한 REST API 제공

Usage:
    python task_queue_api_server.py
    
Then access:
    http://localhost:8091/api/tasks         - 대기 작업 목록
    http://localhost:8091/api/tasks/:id     - 작업 상세
    POST /api/tasks/:id/result              - 결과 제출
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
from pathlib import Path
import json

# shared_task_queue 모듈 import
sys.path.insert(0, str(Path(__file__).parent))
from shared_task_queue import TaskQueue, Task, TaskResult, TASKS_DIR, RESULTS_DIR

app = Flask(__name__)
CORS(app)  # 브라우저에서 접근 허용

queue = TaskQueue()


@app.route('/')
def index():
    """API 정보 페이지"""
    return jsonify({
        "name": "Task Queue API",
        "version": "1.0.0",
        "description": "Copilot ↔ Comet 협업 API",
        "endpoints": {
            "GET /api/tasks": "대기 중인 작업 목록",
            "GET /api/tasks/:id": "작업 상세 정보",
            "POST /api/tasks": "새 작업 생성",
            "POST /api/tasks/:id/claim": "작업 할당받기",
            "POST /api/tasks/:id/result": "작업 결과 제출",
            "GET /api/tasks/:id/result": "작업 결과 조회",
            "POST /api/tasks/next": "다음 작업 가져오기",
            "GET /api/stats": "통계 정보",
            "GET /health": "서버 상태 확인"
        }
    })


@app.route('/health')
def health():
    """서버 상태 확인"""
    return jsonify({
        "status": "ok",
        "tasks_dir": str(TASKS_DIR),
        "results_dir": str(RESULTS_DIR)
    })


@app.route('/api/tasks', methods=['GET', 'POST'])
def tasks():
    """
    GET: 대기 중인 작업 목록 반환
    POST: 새로운 작업 생성
    """
    if request.method == 'GET':
        # 대기 중인 작업 목록 반환
        limit = int(request.args.get('limit', 10))
        task_type = request.args.get('type', None)
        
        pending_tasks = queue.list_pending_tasks(task_type=task_type)
        
        # 최대 개수 제한
        tasks_to_return = pending_tasks[:limit]
        
        return jsonify({
            "count": len(tasks_to_return),
            "total_pending": len(pending_tasks),
            "tasks": [
                {
                    "id": task.id,
                    "type": task.type,
                    "requester": task.requester,
                    "data": task.data,
                    "status": task.status,
                    "created_at": task.created_at
                }
                for task in tasks_to_return
            ]
        })
    
    elif request.method == 'POST':
        # 새로운 작업 생성
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        task_type = data.get('task_type')
        task_data = data.get('data', {})
        requester = data.get('requester', 'http-client')
        
        if not task_type:
            return jsonify({"error": "task_type is required"}), 400
        
        # 작업 생성
        task_id = queue.push_task(task_type, task_data, requester)
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "message": f"Task created: {task_type}"
        }), 201


@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """특정 작업 상세 정보"""
    task_file = TASKS_DIR / f"{task_id}.json"
    
    if not task_file.exists():
        return jsonify({"error": "Task not found"}), 404
    
    with open(task_file, 'r', encoding='utf-8') as f:
        task_data = json.load(f)
    
    return jsonify(task_data)


@app.route('/api/tasks/<task_id>/claim', methods=['POST'])
def claim_task(task_id):
    """
    작업 할당받기
    
    Body:
        {"worker_id": "comet-browser"}
    """
    data = request.get_json()
    worker_id = data.get('worker_id', 'unknown')
    
    task = queue.pop_task(worker_id)
    
    if task and task.id == task_id:
        return jsonify({
            "success": True,
            "task": {
                "id": task.id,
                "type": task.type,
                "data": task.data,
                "assigned_to": task.assigned_to
            }
        })
    else:
        return jsonify({"error": "Task not available"}), 404


@app.route('/api/tasks/<task_id>/result', methods=['POST'])
def submit_result(task_id):
    """
    작업 결과 제출
    
    Body:
        {
            "worker_id": "comet-browser",
            "status": "success",
            "data": {...},
            "error_message": null
        }
    """
    data = request.get_json()
    
    worker_id = data.get('worker_id', 'comet-browser')
    status = data.get('status', 'success')
    result_data = data.get('data', {})
    error_message = data.get('error_message', None)
    
    # 결과 저장
    queue.push_result(
        task_id=task_id,
        worker=worker_id,
        status=status,
        data=result_data,
        error=error_message
    )
    
    return jsonify({
        "success": True,
        "task_id": task_id,
        "message": "Result saved successfully"
    })


@app.route('/api/tasks/<task_id>/result', methods=['GET'])
def get_result(task_id):
    """작업 결과 조회
    
    결과 파일이 존재하면 내용을 반환하고, 없으면 404를 반환합니다.
    """
    result_file = RESULTS_DIR / f"{task_id}.json"
    if not result_file.exists():
        return jsonify({"error": "Result not found"}), 404
    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        return jsonify(result_data)
    except Exception as e:
        return jsonify({"error": f"Failed to read result: {e}"}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """통계 정보"""
    pending_tasks = queue.list_pending_tasks()
    result_files = list(RESULTS_DIR.glob("*.json"))
    
    return jsonify({
        "pending_tasks": len(pending_tasks),
        "completed_tasks": len(result_files),
        "tasks_dir": str(TASKS_DIR),
        "results_dir": str(RESULTS_DIR)
    })


@app.route('/api/tasks/next', methods=['POST'])
def get_next_task():
    """
    다음 작업 가져오기 (claim과 동시에)
    
    Body:
        {"worker_id": "comet-browser"}
    
    Response:
        {"task": {...}} 또는 {"task": null} (작업 없음)
    """
    data = request.get_json()
    worker_id = data.get('worker_id', 'comet-browser')
    
    task = queue.pop_task(worker_id)
    
    if task:
        return jsonify({
            "task": {
                "id": task.id,
                "type": task.type,
                "data": task.data,
                "requester": task.requester,
                "created_at": task.created_at
            }
        })
    else:
        return jsonify({"task": None})


if __name__ == '__main__':
    print("=" * 60)
    print("Task Queue HTTP API Server")
    print("=" * 60)
    print()
    print("📡 Server starting on http://localhost:8091")
    print()
    print("🌐 API Endpoints:")
    print("   GET  /api/tasks           - 대기 작업 목록")
    print("   POST /api/tasks           - 새 작업 생성")
    print("   POST /api/tasks/next      - 다음 작업 가져오기")
    print("   POST /api/tasks/:id/result - 결과 제출")
    print("   GET  /api/tasks/:id/result - 결과 조회")
    print("   GET  /api/stats           - 통계")
    print("   GET  /health              - 서버 상태")
    print()
    print("🤖 Comet Browser에서 접근:")
    print("   fetch('http://localhost:8091/api/tasks/next', {")
    print("       method: 'POST',")
    print("       headers: {'Content-Type': 'application/json'},")
    print("       body: JSON.stringify({worker_id: 'comet-browser'})")
    print("   })")
    print()
    print("=" * 60)
    print()
    
    app.run(host='0.0.0.0', port=8091, debug=False, use_reloader=False)
