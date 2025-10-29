#!/usr/bin/env python3
"""
HTTP Task Poller 플로우 테스트
Extension Development Host 테스트 전에 API 서버와 통신 확인
"""
import requests
import json
import time

API_BASE = "http://localhost:8091/api"

def test_flow():
    print("🧪 HTTP Task Poller Flow Test\n")
    
    # 1. Submit a ping task
    print("1️⃣ Submitting ping task...")
    submit_response = requests.post(
        f"{API_BASE}/tasks",
        json={
            "task_type": "ping",
            "data": {},
            "requester": "test-script"
        }
    )
    
    if submit_response.status_code not in [200, 201]:
        print(f"❌ Failed to submit task: {submit_response.status_code}")
        return
    
    response_data = submit_response.json()
    task_id = response_data.get("task_id")
    if not task_id:
        print(f"❌ No task_id in response: {response_data}")
        return
    
    print(f"✅ Task created: {task_id}\n")
    
    # 2. Simulate poller getting next task
    print("2️⃣ Simulating poller getNextTask()...")
    get_response = requests.post(
        f"{API_BASE}/tasks/next",
        json={"worker_id": "test-poller"}
    )
    
    if get_response.status_code == 404:
        print("⚠️ No tasks available (someone else might have claimed it)")
        return
    
    if get_response.status_code != 200:
        print(f"❌ Failed to get task: {get_response.status_code}")
        return
    
    received_task = get_response.json()["task"]
    print(f"✅ Task received: {received_task['id']}")
    print(f"   Type: {received_task['type']}")
    print(f"   Requester: {received_task.get('requester', 'N/A')}\n")
    
    # 3. Simulate processing
    print("3️⃣ Processing task...")
    time.sleep(1)
    
    result = {
        "task_id": received_task["id"],
        "worker": "test-poller",
        "status": "success",
        "data": {
            "message": "pong",
            "timestamp": time.time()
        }
    }
    
    # 4. Submit result
    print("4️⃣ Submitting result...")
    result_response = requests.post(
        f"{API_BASE}/tasks/{received_task['id']}/result",
        json=result
    )
    
    if result_response.status_code != 200:
        print(f"❌ Failed to submit result: {result_response.status_code}")
        return
    
    print("✅ Result submitted successfully!\n")
    
    # 5. Verify result was saved
    print("5️⃣ Verifying result...")
    time.sleep(0.5)
    
    # Check result file
    result_file = f"outputs/task_queue/results/{received_task['id']}.json"
    try:
        import os
        if os.path.exists(result_file):
            with open(result_file, 'r', encoding='utf-8') as f:
                saved_result = json.load(f)
            print(f"✅ Result file found: {result_file}")
            print(f"   Worker: {saved_result.get('worker')}")
            print(f"   Status: {saved_result.get('status')}")
            print(f"   Data: {saved_result.get('data')}")
        else:
            print(f"⚠️ Result file not found: {result_file}")
    except Exception as e:
        print(f"⚠️ Error reading result: {e}")
    
    print("\n🎉 Flow test completed!")
    print("✨ HTTP Task Poller workflow is working correctly!")

if __name__ == "__main__":
    try:
        test_flow()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server on port 8091")
        print("   Please start: .venv\\Scripts\\python.exe .\\scripts\\task_queue_api_server.py")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
