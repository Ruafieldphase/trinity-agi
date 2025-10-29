#!/usr/bin/env python3
"""
Comet Browser용 간소화 워커

브라우저 AI가 직접 실행할 수 있도록 단순화된 버전
파일을 브라우저에서 열면 자동으로 작동하도록 설계

Usage (Comet Browser):
    1. 이 파일을 다운로드
    2. Python 환경에서 실행 (브라우저 내 Python 실행 기능 사용)
    또는
    3. 로컬에 저장 후 더블클릭 실행 (Python 설치되어 있다면)
"""

import json
import time
from pathlib import Path
from datetime import datetime


# 설정: 작업 큐 디렉토리 (절대 경로로 지정)
QUEUE_BASE = Path(r"D:\nas_backup\fdo_agi_repo\outputs\task_queue")
TASKS_DIR = QUEUE_BASE / "tasks"
RESULTS_DIR = QUEUE_BASE / "results"

# 디렉토리 생성
TASKS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def simulate_web_scraping(url: str, selector: str, extract: list) -> dict:
    """
    웹 스크래핑 시뮬레이션
    
    Comet Browser가 실제 구현할 부분:
    - 브라우저 API를 사용하여 실제 페이지 로드
    - DOM 요소 추출
    """
    print(f"🌐 Scraping: {url}")
    print(f"   Selector: {selector}")
    
    # 시뮬레이션 데이터
    if "github.com/trending" in url:
        return {
            "repositories": [
                {"name": "openai/whisper", "href": "/openai/whisper"},
                {"name": "facebook/react", "href": "/facebook/react"},
                {"name": "microsoft/vscode", "href": "/microsoft/vscode"}
            ]
        }
    elif "youtube.com" in url:
        return {
            "videos": [
                {"title": "AI가 만드는 미래", "href": "/watch?v=abc123"},
                {"title": "프로그래밍 튜토리얼", "href": "/watch?v=def456"}
            ]
        }
    else:
        return {"html": "<html>...</html>", "text": ["Sample", "Data"]}


def process_one_task(worker_id: str = "comet-simple"):
    """한 번에 하나의 작업만 처리"""
    
    # 대기 중인 작업 찾기
    task_files = list(TASKS_DIR.glob("*.json"))
    
    if not task_files:
        return False
    
    # 첫 번째 작업 가져오기
    task_file = task_files[0]
    
    try:
        with open(task_file, 'r', encoding='utf-8') as f:
            task = json.load(f)
        
        task_id = task['id']
        task_type = task['type']
        task_data = task['data']
        
        print(f"\n📥 Task found: {task_id[:8]} ({task_type})")
        
        # 작업 처리
        if task_type == "web_scraping":
            result_data = simulate_web_scraping(
                url=task_data.get('url', ''),
                selector=task_data.get('selector', ''),
                extract=task_data.get('extract', [])
            )
            status = "success"
            error_msg = None
            
        elif task_type == "ping":
            result_data = {"pong": "Hello from Comet!", "message": task_data.get('message')}
            status = "success"
            error_msg = None
            
        elif task_type == "screenshot":
            result_data = {
                "filename": task_data.get('filename', 'screenshot.png'),
                "url": task_data.get('url', ''),
                "saved": True
            }
            status = "success"
            error_msg = None
            
        else:
            result_data = {}
            status = "error"
            error_msg = f"Unknown task type: {task_type}"
        
        # 결과 저장
        result = {
            "task_id": task_id,
            "worker": worker_id,
            "status": status,
            "data": result_data,
            "completed_at": datetime.now().isoformat(),
            "error_message": error_msg
        }
        
        result_file = RESULTS_DIR / f"{task_id}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # 작업 파일 삭제
        task_file.unlink()
        
        print(f"✅ Task {task_id[:8]} completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error processing task: {e}")
        
        # 에러 결과 저장
        result = {
            "task_id": task.get('id', 'unknown'),
            "worker": worker_id,
            "status": "error",
            "data": {},
            "completed_at": datetime.now().isoformat(),
            "error_message": str(e)
        }
        
        result_file = RESULTS_DIR / f"{task.get('id', 'error')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # 실패한 작업 파일도 삭제 (재시도 방지)
        if task_file.exists():
            task_file.unlink()
        
        return False


def run_simple_worker(max_cycles: int = 100, interval: float = 5.0):
    """
    단순 워커: 주기적으로 작업 확인 및 처리
    
    Args:
        max_cycles: 최대 실행 사이클 (기본 100회 = 약 8분)
        interval: 체크 간격 (초)
    """
    print("=" * 60)
    print("Comet Simple Worker Started")
    print("=" * 60)
    print(f"Worker ID: comet-simple")
    print(f"Check Interval: {interval}s")
    print(f"Max Cycles: {max_cycles}")
    print(f"Task Queue: {TASKS_DIR}")
    print()
    print(f"⏰ Will run for approximately {max_cycles * interval / 60:.1f} minutes")
    print("=" * 60)
    print()
    
    for cycle in range(1, max_cycles + 1):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 🔍 Cycle {cycle} - Checking for tasks...")
        
        # 작업 처리
        processed = process_one_task()
        
        if not processed:
            print(f"[{timestamp}] ⏸️ No tasks found. Waiting {interval}s...")
        
        # 마지막 사이클이 아니면 대기
        if cycle < max_cycles:
            time.sleep(interval)
    
    print()
    print("=" * 60)
    print(f"✅ Worker finished after {max_cycles} cycles")
    print("=" * 60)


if __name__ == "__main__":
    print("\n🤖 Comet Simple Worker")
    print("이 스크립트는 자동으로 작업을 처리합니다.\n")
    
    try:
        # 100 사이클 실행 (약 8분 동안 작동)
        run_simple_worker(max_cycles=100, interval=5.0)
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Worker stopped by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
