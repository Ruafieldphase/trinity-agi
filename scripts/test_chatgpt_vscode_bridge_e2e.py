#!/usr/bin/env python3
"""
ChatGPT → VS Code Bridge E2E Test
====================================
실제 워크플로우 테스트:
1. ChatGPT가 요청 생성
2. Bridge가 처리
3. VS Code가 응답 확인
"""

import json
import time
import os
from pathlib import Path
from workspace_root import get_workspace_root
from datetime import datetime

# Paths
WORKSPACE = get_workspace_root()
REQUESTS_DIR = WORKSPACE / "outputs/lua_requests"
RESPONSES_DIR = WORKSPACE / "outputs/trinity_responses"

def test_e2e_workflow():
    """E2E 워크플로우 테스트"""
    print("🧪 ChatGPT → VS Code Bridge E2E Test")
    print("=" * 60)
    
    # 1. ChatGPT가 요청 생성 (시뮬레이션)
    request_id = f"e2e_test_{int(time.time())}"
    request = {
        "request_id": request_id,
        "type": "code_review",
        "content": "Review this Python function for potential bugs",
        "timestamp": datetime.now().isoformat()
    }
    
    request_file = REQUESTS_DIR / f"{request_id}.json"
    REQUESTS_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"\n✅ Step 1: ChatGPT creates request")
    print(f"   Request ID: {request_id}")
    with open(request_file, 'w', encoding='utf-8') as f:
        json.dump(request, f, indent=2)
    print(f"   File: {request_file}")
    
    # 2. Bridge 프로세서 실행 (PowerShell 스크립트 호출)
    print(f"\n✅ Step 2: Bridge processes request")
    print(f"   Waiting for bridge processor...")
    
    import subprocess
    bridge_script = WORKSPACE / "scripts/send_to_chatgpt_lua.ps1"
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(bridge_script), "-ProcessOnce"],
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE)
    )
    
    if result.returncode == 0:
        print(f"   ✅ Bridge processing completed")
    else:
        print(f"   ❌ Bridge processing failed")
        print(f"   Error: {result.stderr}")
        return False
    
    # 3. VS Code가 응답 확인
    print(f"\n✅ Step 3: VS Code checks response")
    
    max_wait = 10
    for i in range(max_wait):
        response_file = RESPONSES_DIR / f"{request_id}.json"
        if response_file.exists():
            with open(response_file, 'r', encoding='utf-8-sig') as f:  # BOM 처리
                response = json.load(f)
            print(f"   ✅ Response received!")
            print(f"   Response: {json.dumps(response, indent=2)}")
            
            # 성공 검증: metadata가 있고 추천 액션이 있으면 성공
            if response.get('metadata') and response.get('recommended_actions'):
                print(f"\n🎉 E2E Test PASSED!")
                print(f"   ✅ Response has metadata and recommendations")
                return True
            break
        time.sleep(1)
        print(f"   Waiting... ({i+1}/{max_wait})")
    
    print(f"\n❌ E2E Test FAILED: No response received")
    return False

def test_direct_enqueue():
    """Task Queue에 직접 enqueue 테스트"""
    print("\n" + "=" * 60)
    print("🧪 Direct Task Queue Test")
    print("=" * 60)
    
    import requests
    
    task = {
        "type": "chatgpt_bridge",
        "action": "process_request",
        "request_id": f"direct_test_{int(time.time())}",
        "content": "Test direct enqueue"
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:8091/api/task",
            json=task,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Task enqueued: {result.get('task_id')}")
            return True
        else:
            print(f"❌ Failed to enqueue: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Queue server not available: {e}")
        return False

if __name__ == "__main__":
    # Test 1: E2E Workflow
    success_e2e = test_e2e_workflow()
    
    # Test 2: Direct Queue (옵션)
    success_queue = test_direct_enqueue()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"E2E Workflow: {'✅ PASS' if success_e2e else '❌ FAIL'}")
    print(f"Direct Queue: {'✅ PASS' if success_queue else '❌ FAIL'}")
    
    exit(0 if success_e2e else 1)
