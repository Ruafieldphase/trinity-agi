#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent API Server - REST API를 통한 에이전트 시스템 접근

이 모듈은 Flask를 사용하여 REST API를 제공합니다:
1. POST /api/tasks - 새 작업 생성
2. GET /api/tasks/{task_id} - 작업 상태 조회
3. GET /api/agents - 에이전트 목록 및 상태 조회
4. GET /api/agents/{agent_id}/status - 특정 에이전트 상태 조회
5. POST /api/agents/{agent_id}/execute - 특정 에이전트에 작업 요청
"""

import sys
import io
import json
import logging
from typing import Dict, Any, Tuple
from datetime import datetime
from functools import wraps

# UTF-8 인코딩 강제 설정 (Windows 호환)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Flask import (서버 실행 시에만 필요)
try:
    from flask import Flask, request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("[Warning] Flask not installed. API server not available.")

from integrated_agent_system import IntegratedAgentSystem
from agent_interface import AgentRole


# ============================================================================
# API Response 클래스
# ============================================================================

class APIResponse:
    """API 응답 표준화"""

    @staticmethod
    def success(data: Any, message: str = "성공") -> Dict[str, Any]:
        """성공 응답"""
        return {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def error(error: str, code: int = 400, details: Any = None) -> Tuple[Dict[str, Any], int]:
        """에러 응답"""
        response = {
            "success": False,
            "message": error,
            "timestamp": datetime.now().isoformat()
        }
        if details:
            response["details"] = details
        return response, code


# ============================================================================
# Agent API Server
# ============================================================================

class AgentAPIServer:
    """에이전트 시스템 REST API 서버"""

    def __init__(self, host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
        """API 서버 초기화"""
        if not FLASK_AVAILABLE:
            raise RuntimeError("Flask is required for API server")

        self.app = Flask(__name__)
        self.host = host
        self.port = port
        self.debug = debug

        # 통합 에이전트 시스템
        self.agent_system = IntegratedAgentSystem()

        # 로깅 설정
        self.setup_logging()

        # 라우트 등록
        self.register_routes()

    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s: %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def register_routes(self):
        """API 라우트 등록"""

        # 1. 에이전트 초기화
        @self.app.route('/api/init', methods=['POST'])
        def init_agents():
            """에이전트 시스템 초기화"""
            try:
                if self.agent_system.initialize_agents():
                    return jsonify(APIResponse.success(
                        {"agents": list(self.agent_system.agents.keys())},
                        "에이전트 초기화 완료"
                    ))
                else:
                    return jsonify(*APIResponse.error("에이전트 초기화 실패", 500))
            except Exception as e:
                self.logger.error(f"Error initializing agents: {e}")
                return jsonify(*APIResponse.error(str(e), 500))

        # 2. 작업 생성 및 실행
        @self.app.route('/api/tasks', methods=['POST'])
        def create_task():
            """새 작업 생성 및 실행"""
            try:
                data = request.get_json()

                if not data or 'problem' not in data:
                    return jsonify(*APIResponse.error(
                        "problem 필드가 필요합니다",
                        400
                    ))

                problem = data.get('problem')

                # 에이전트가 초기화되지 않았으면 초기화
                if not self.agent_system.agents:
                    self.agent_system.initialize_agents()

                # 워크플로우 실행
                result = self.agent_system.execute_workflow(problem)

                if result['success']:
                    return jsonify(APIResponse.success(
                        result,
                        "작업 완료"
                    ))
                else:
                    return jsonify(APIResponse.success(
                        result,
                        "작업 실패"
                    ))

            except Exception as e:
                self.logger.error(f"Error creating task: {e}")
                return jsonify(*APIResponse.error(str(e), 500))

        # 3. 작업 목록 조회
        @self.app.route('/api/tasks', methods=['GET'])
        def list_tasks():
            """작업 목록 조회"""
            try:
                tasks = self.agent_system.task_history
                return jsonify(APIResponse.success(
                    {"tasks": tasks, "count": len(tasks)},
                    "작업 목록 조회 완료"
                ))
            except Exception as e:
                self.logger.error(f"Error listing tasks: {e}")
                return jsonify(*APIResponse.error(str(e), 500))

        # 4. 특정 작업 조회
        @self.app.route('/api/tasks/<task_id>', methods=['GET'])
        def get_task(task_id):
            """특정 작업 조회"""
            try:
                for task in self.agent_system.task_history:
                    if task.get('task_id') == task_id:
                        return jsonify(APIResponse.success(
                            task,
                            "작업 조회 완료"
                        ))

                return jsonify(*APIResponse.error(f"작업을 찾을 수 없습니다: {task_id}", 404))

            except Exception as e:
                self.logger.error(f"Error getting task: {e}")
                return jsonify(*APIResponse.error(str(e), 500))

        # 5. 에이전트 목록 및 상태
        @self.app.route('/api/agents', methods=['GET'])
        def list_agents():
            """에이전트 목록 및 상태 조회"""
            try:
                agents_info = {}
                for role_value, agent in self.agent_system.agents.items():
                    status = agent.get_status()
                    agents_info[role_value] = status

                return jsonify(APIResponse.success(
                    agents_info,
                    "에이전트 목록 조회 완료"
                ))

            except Exception as e:
                self.logger.error(f"Error listing agents: {e}")
                return jsonify(*APIResponse.error(str(e), 500))

        # 6. 특정 에이전트 상태
        @self.app.route('/api/agents/<agent_id>/status', methods=['GET'])
        def get_agent_status(agent_id):
            """특정 에이전트 상태 조회"""
            try:
                for role_value, agent in self.agent_system.agents.items():
                    if agent.agent_id == agent_id or role_value == agent_id:
                        return jsonify(APIResponse.success(
                            agent.get_status(),
                            "에이전트 상태 조회 완료"
                        ))

                return jsonify(*APIResponse.error(f"에이전트를 찾을 수 없습니다: {agent_id}", 404))

            except Exception as e:
                self.logger.error(f"Error getting agent status: {e}")
                return jsonify(*APIResponse.error(str(e), 500))

        # 7. 시스템 상태
        @self.app.route('/api/system/status', methods=['GET'])
        def system_status():
            """시스템 전체 상태 조회"""
            try:
                agents_count = len(self.agent_system.agents)
                tasks_count = len(self.agent_system.task_history)
                successful_tasks = sum(1 for t in self.agent_system.task_history if t.get('success'))

                status = {
                    "agents": {
                        "total": agents_count,
                        "initialized": agents_count > 0
                    },
                    "tasks": {
                        "total": tasks_count,
                        "successful": successful_tasks,
                        "failed": tasks_count - successful_tasks,
                        "success_rate": (successful_tasks / tasks_count * 100) if tasks_count > 0 else 0
                    },
                    "message_count": len(self.agent_system.message_log),
                    "timestamp": datetime.now().isoformat()
                }

                return jsonify(APIResponse.success(
                    status,
                    "시스템 상태 조회 완료"
                ))

            except Exception as e:
                self.logger.error(f"Error getting system status: {e}")
                return jsonify(*APIResponse.error(str(e), 500))

        # 8. API 문서
        @self.app.route('/api/docs', methods=['GET'])
        def api_docs():
            """API 문서"""
            docs = {
                "title": "Agent Orchestration System API",
                "version": "1.0",
                "endpoints": [
                    {
                        "method": "POST",
                        "path": "/api/init",
                        "description": "에이전트 시스템 초기화",
                        "request": {},
                        "response": {"agents": ["sena", "lubit", "gitcode", "rune"]}
                    },
                    {
                        "method": "POST",
                        "path": "/api/tasks",
                        "description": "새 작업 생성 및 실행",
                        "request": {"problem": "문제 설명"},
                        "response": {"task_id": "...", "final_verdict": "...", "success": True}
                    },
                    {
                        "method": "GET",
                        "path": "/api/tasks",
                        "description": "작업 목록 조회",
                        "response": {"tasks": [...], "count": 0}
                    },
                    {
                        "method": "GET",
                        "path": "/api/tasks/<task_id>",
                        "description": "특정 작업 조회",
                        "response": {"task_id": "...", "final_verdict": "...", "success": True}
                    },
                    {
                        "method": "GET",
                        "path": "/api/agents",
                        "description": "에이전트 목록 및 상태",
                        "response": {"sena": "...", "lubit": "...", "gitcode": "...", "rune": "..."}
                    },
                    {
                        "method": "GET",
                        "path": "/api/agents/<agent_id>/status",
                        "description": "특정 에이전트 상태",
                        "response": {"agent_id": "...", "role": "...", "is_initialized": True}
                    },
                    {
                        "method": "GET",
                        "path": "/api/system/status",
                        "description": "시스템 전체 상태",
                        "response": {"agents": "...", "tasks": "..."}
                    },
                    {
                        "method": "GET",
                        "path": "/api/docs",
                        "description": "API 문서",
                        "response": {"title": "...", "endpoints": [...]}
                    }
                ]
            }

            return jsonify(APIResponse.success(
                docs,
                "API 문서"
            ))

        # 9. 헬스 체크
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """헬스 체크"""
            return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

        # 10. 에러 핸들러
        @self.app.errorhandler(404)
        def not_found(error):
            """404 에러 핸들러"""
            return jsonify(*APIResponse.error("엔드포인트를 찾을 수 없습니다", 404))

        @self.app.errorhandler(500)
        def internal_error(error):
            """500 에러 핸들러"""
            self.logger.error(f"Internal server error: {error}")
            return jsonify(*APIResponse.error("내부 서버 에러", 500))

    def run(self):
        """API 서버 실행"""
        print("=" * 80)
        print(f"Agent API Server 시작")
        print("=" * 80)
        print(f"URL: http://{self.host}:{self.port}")
        print(f"API 문서: http://{self.host}:{self.port}/api/docs")
        print("=" * 80 + "\n")

        self.app.run(host=self.host, port=self.port, debug=self.debug)


# ============================================================================
# 데모: API 서버 사용 예시 (curl 명령어)
# ============================================================================

def print_api_examples():
    """API 사용 예시 출력"""
    print("=" * 80)
    print("Agent API Server - 사용 예시")
    print("=" * 80)

    examples = {
        "1. 에이전트 초기화": {
            "method": "POST",
            "url": "http://localhost:5000/api/init",
            "curl": 'curl -X POST http://localhost:5000/api/init'
        },
        "2. 새 작업 생성": {
            "method": "POST",
            "url": "http://localhost:5000/api/tasks",
            "curl": 'curl -X POST http://localhost:5000/api/tasks -H "Content-Type: application/json" -d \'{"problem": "데이터 분석"}\'',
            "python": """
import requests
response = requests.post('http://localhost:5000/api/tasks',
    json={'problem': '데이터 분석'})
print(response.json())
            """
        },
        "3. 작업 목록 조회": {
            "method": "GET",
            "url": "http://localhost:5000/api/tasks",
            "curl": "curl http://localhost:5000/api/tasks"
        },
        "4. 특정 작업 조회": {
            "method": "GET",
            "url": "http://localhost:5000/api/tasks/{task_id}",
            "curl": "curl http://localhost:5000/api/tasks/task_001"
        },
        "5. 에이전트 목록": {
            "method": "GET",
            "url": "http://localhost:5000/api/agents",
            "curl": "curl http://localhost:5000/api/agents"
        },
        "6. 시스템 상태": {
            "method": "GET",
            "url": "http://localhost:5000/api/system/status",
            "curl": "curl http://localhost:5000/api/system/status"
        },
        "7. API 문서": {
            "method": "GET",
            "url": "http://localhost:5000/api/docs",
            "curl": "curl http://localhost:5000/api/docs"
        }
    }

    for title, example in examples.items():
        print(f"\n{title}")
        print(f"  메서드: {example['method']}")
        print(f"  URL: {example['url']}")
        print(f"  명령어: {example['curl']}")
        if 'python' in example:
            print(f"  Python:{example['python']}")

    print("\n" + "=" * 80)
    print("API 서버 시작: python agent_api_server.py")
    print("=" * 80)


# ============================================================================
# 메인 실행
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Agent API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=5000, help="Server port")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    parser.add_argument("--examples", action="store_true", help="Show API examples")

    args = parser.parse_args()

    if args.examples:
        print_api_examples()
    else:
        if FLASK_AVAILABLE:
            server = AgentAPIServer(host=args.host, port=args.port, debug=args.debug)
            server.run()
        else:
            print("Flask is required to run the API server.")
            print("Install it with: pip install flask")
            print_api_examples()
