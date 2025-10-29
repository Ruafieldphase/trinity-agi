#!/usr/bin/env python3
"""
HTTP Task Poller for Comet (Python test implementation)

이 스크립트는 Comet extension의 HTTP poller 로직을 Python으로 테스트하기 위한 것입니다.
실제 Comet은 TypeScript로 구현됩니다.

Usage:
    python scripts/http_task_poller.py [--api-url URL] [--worker-id ID] [--once]
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import requests
except ImportError:
    print("❌ requests 모듈이 필요합니다: pip install requests")
    sys.exit(1)


class HttpTaskPoller:
    """HTTP API 기반 Task Poller"""

    def __init__(
        self,
        api_base: str = "http://localhost:8091/api",
        worker_id: str = "http-poller-test",
        poll_interval: float = 2.0
    ):
        self.api_base = api_base.rstrip('/')
        self.worker_id = worker_id
        self.poll_interval = poll_interval
        self.is_polling = False

    def start_polling(self, once: bool = False):
        """Start polling for tasks"""
        print(f"🔄 HTTP Poller 시작 ({self.api_base})")
        print(f"   Worker ID: {self.worker_id}")
        print(f"   Polling Interval: {self.poll_interval}s")
        
        if once:
            print("   Mode: One-shot")
        else:
            print("   Mode: Continuous (Ctrl+C to stop)")
        
        self.is_polling = True
        
        try:
            while self.is_polling:
                task = self.get_next_task()
                
                if task:
                    print(f"\n📥 Task received: {task['id']} ({task['type']})")
                    self.handle_task(task)
                
                if once:
                    break
                
                # Wait before next poll
                time.sleep(self.poll_interval)
        
        except KeyboardInterrupt:
            print("\n\n⏹️ Polling stopped by user")
        finally:
            self.is_polling = False

    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """Get next task from server"""
        try:
            url = f"{self.api_base}/tasks/next"
            response = requests.post(
                url,
                json={"worker_id": self.worker_id},
                timeout=5
            )
            
            if response.status_code == 404:
                # No tasks available (expected when queue is empty)
                return None
            
            if response.status_code != 200:
                print(f"⚠️ Unexpected status code: {response.status_code}")
                return None
            
            data = response.json()
            return data.get('task')
        
        except requests.exceptions.ConnectionError:
            print(f"❌ API 서버에 연결할 수 없습니다: {self.api_base}")
            print("   서버가 실행 중인지 확인하세요:")
            print("   python scripts/task_queue_api_server.py")
            sys.exit(1)
        
        except Exception as e:
            print(f"❌ Error getting next task: {e}")
            return None

    def handle_task(self, task: Dict[str, Any]):
        """Handle task based on type"""
        task_id = task['id']
        task_type = task['type']
        task_data = task.get('data', {})
        
        try:
            # Handle different task types
            if task_type == 'ping':
                result_data = self._handle_ping()
            
            elif task_type == 'calculation':
                result_data = self._handle_calculation(task_data)
            
            elif task_type == 'data_transform':
                result_data = self._handle_data_transform(task_data)
            
            elif task_type == 'batch_calculation':
                result_data = self._handle_batch_calculation(task_data)
            
            else:
                raise ValueError(f"Unknown task type: {task_type}")
            
            # Build success result
            result = {
                'task_id': task_id,
                'worker': self.worker_id,
                'status': 'success',
                'data': result_data
            }
            
            print(f"✅ Task processed successfully")
        
        except Exception as e:
            # Build error result
            result = {
                'task_id': task_id,
                'worker': self.worker_id,
                'status': 'error',
                'data': {},
                'error_message': str(e)
            }
            
            print(f"❌ Task failed: {e}")
        
        # Submit result
        self.submit_result(task_id, result)

    def submit_result(self, task_id: str, result: Dict[str, Any]):
        """Submit task result to server"""
        try:
            url = f"{self.api_base}/tasks/{task_id}/result"
            response = requests.post(
                url,
                json=result,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"📤 Result submitted for task {task_id}")
            else:
                print(f"⚠️ Failed to submit result: HTTP {response.status_code}")
        
        except Exception as e:
            print(f"❌ Error submitting result: {e}")

    # ==================== Task Handlers ====================

    def _handle_ping(self) -> Dict[str, Any]:
        """Handle ping task"""
        return {
            'message': 'pong',
            'worker': self.worker_id,
            'timestamp': datetime.now().isoformat(),
            'implementation': 'python-test'
        }

    def _handle_calculation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle calculation task"""
        operation = data['operation']
        numbers = data['numbers']
        
        if operation == 'add':
            result = sum(numbers)
        elif operation == 'multiply':
            result = 1
            for n in numbers:
                result *= n
        elif operation == 'divide' and len(numbers) == 2:
            result = numbers[0] / numbers[1]
        else:
            raise ValueError(f"Unsupported operation: {operation}")
        
        return {'result': result}

    def _handle_data_transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle data transformation task"""
        operation = data['operation']
        text = data['text']
        
        if operation == 'uppercase':
            result = text.upper()
        elif operation == 'lowercase':
            result = text.lower()
        elif operation == 'reverse':
            result = text[::-1]
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        return {'result': result}

    def _handle_batch_calculation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle batch calculation task"""
        calculations = data.get('calculations', [])
        results = []
        
        for calc in calculations:
            calc_id = calc['id']
            operation = calc['operation']
            numbers = calc['numbers']
            multiply_by = calc.get('multiply_by')
            
            if operation == 'divide' and len(numbers) == 2:
                result = numbers[0] / numbers[1]
                if multiply_by:
                    result *= multiply_by
            elif operation == 'average':
                result = sum(numbers) / len(numbers)
            elif operation == 'multiply':
                result = 1
                for n in numbers:
                    result *= n
            else:
                result = 0
            
            results.append({'id': calc_id, 'result': result})
        
        return {'calculations': results}


def main():
    parser = argparse.ArgumentParser(description='HTTP Task Poller (Test Implementation)')
    parser.add_argument('--api-url', default='http://localhost:8091/api',
                        help='API base URL (default: http://localhost:8091/api)')
    parser.add_argument('--worker-id', default='http-poller-test',
                        help='Worker ID (default: http-poller-test)')
    parser.add_argument('--interval', type=float, default=2.0,
                        help='Polling interval in seconds (default: 2.0)')
    parser.add_argument('--once', action='store_true',
                        help='Poll once and exit (for testing)')
    
    args = parser.parse_args()
    
    poller = HttpTaskPoller(
        api_base=args.api_url,
        worker_id=args.worker_id,
        poll_interval=args.interval
    )
    
    poller.start_polling(once=args.once)


if __name__ == '__main__':
    main()
