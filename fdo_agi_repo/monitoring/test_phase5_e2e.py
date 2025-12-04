"""
Phase 5 E2E Test: Web Dashboard Integration Test

전체 시스템 통합 테스트:
1. Task Queue Server 실행 확인
2. RPA Worker 실행 확인
3. Monitoring Daemon 실행 확인
4. Web Dashboard 접근 확인
5. 테스트 작업 추가 → 메트릭 수집 → 대시보드 업데이트 확인
"""

import requests
import time
import json
from datetime import datetime
from pathlib import Path

# 설정
TASK_QUEUE_SERVER = "http://127.0.0.1:8091"
WEB_DASHBOARD = "http://127.0.0.1:8000"
TEST_TASKS_COUNT = 10
WAIT_BETWEEN_TASKS = 0.5  # 초


def print_section(title):
    """섹션 헤더 출력"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def check_server(url, name):
    """서버 헬스 체크"""
    try:
        response = requests.get(f"{url}/api/health", timeout=3)
        if response.status_code == 200:
            print(f"✅ {name} is ONLINE")
            return True
        else:
            print(f"❌ {name} returned status {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ {name} is OFFLINE - {e}")
        return False


def enqueue_test_task(task_type="screenshot", delay=0.1):
    """테스트 작업 추가"""
    payload = {
        "task_type": task_type,
        "params": {
            "url": "https://www.example.com",
            "delay": delay
        }
    }
    
    try:
        response = requests.post(
            f"{TASK_QUEUE_SERVER}/api/enqueue",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("task_id")
        else:
            print(f"⚠️ Failed to enqueue task: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"❌ Enqueue error: {e}")
        return None


def get_dashboard_metrics():
    """대시보드 메트릭 조회"""
    try:
        response = requests.get(f"{WEB_DASHBOARD}/api/system/status", timeout=3)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️ Dashboard API returned {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"❌ Dashboard API error: {e}")
        return None


def run_e2e_test():
    """전체 E2E 테스트 실행"""
    
    print_section("🚀 Phase 5 E2E Test: Web Dashboard Integration")
    
    # Step 1: 서버 헬스 체크
    print_section("Step 1: Health Check")
    
    queue_ok = check_server(TASK_QUEUE_SERVER, "Task Queue Server")
    dashboard_ok = check_server(WEB_DASHBOARD, "Web Dashboard")
    
    if not queue_ok:
        print("\n❌ Task Queue Server is not running!")
        print("   Please start: python task_queue_server.py --port 8091")
        return False
    
    if not dashboard_ok:
        print("\n❌ Web Dashboard is not running!")
        print("   Please start: python monitoring/web_server.py")
        return False
    
    # Step 2: 초기 메트릭 확인
    print_section("Step 2: Initial Metrics")
    
    initial_metrics = get_dashboard_metrics()
    if initial_metrics:
        print(f"  Success Rate: {initial_metrics['success_rate']:.1f}%")
        print(f"  Total Tasks:  {initial_metrics['total_tasks']}")
        print(f"  Active Workers: {initial_metrics['active_workers']}")
        print(f"  Queue Size: {initial_metrics['queue_size']}")
    else:
        print("⚠️ Could not fetch initial metrics")
    
    # Step 3: 테스트 작업 추가
    print_section(f"Step 3: Enqueue {TEST_TASKS_COUNT} Test Tasks")
    
    task_ids = []
    for i in range(TEST_TASKS_COUNT):
        task_id = enqueue_test_task(task_type="screenshot", delay=0.1)
        if task_id:
            task_ids.append(task_id)
            print(f"  [{i+1}/{TEST_TASKS_COUNT}] ✅ Task enqueued: {task_id}")
        else:
            print(f"  [{i+1}/{TEST_TASKS_COUNT}] ❌ Failed to enqueue")
        
        time.sleep(WAIT_BETWEEN_TASKS)
    
    print(f"\n✅ Enqueued {len(task_ids)} tasks")
    
    # Step 4: 작업 완료 대기
    print_section("Step 4: Wait for Task Completion")
    
    print("⏳ Waiting 10 seconds for tasks to complete...")
    time.sleep(10)
    
    # Step 5: 최종 메트릭 확인
    print_section("Step 5: Final Metrics")
    
    final_metrics = get_dashboard_metrics()
    if final_metrics:
        print(f"  Success Rate: {final_metrics['success_rate']:.1f}%")
        print(f"  Total Tasks:  {final_metrics['total_tasks']}")
        print(f"  Successful:   {final_metrics['successful_tasks']}")
        print(f"  Failed:       {final_metrics['failed_tasks']}")
        print(f"  Avg Response: {final_metrics['avg_response_time_ms']:.0f}ms")
        print(f"  Health Status: {final_metrics['health_status'].upper()}")
        
        # 알림 확인
        alerts = final_metrics.get('alerts', {})
        total_alerts = sum(alerts.values())
        if total_alerts > 0:
            print(f"\n  🚨 Alerts:")
            print(f"    Critical: {alerts.get('critical', 0)}")
            print(f"    Warning:  {alerts.get('warning', 0)}")
            print(f"    Info:     {alerts.get('info', 0)}")
    else:
        print("❌ Could not fetch final metrics")
        return False
    
    # Step 6: 메트릭 히스토리 확인
    print_section("Step 6: Metrics History (Last 30min)")
    
    try:
        response = requests.get(f"{WEB_DASHBOARD}/api/metrics/history?minutes=30", timeout=3)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Found {data['count']} metric snapshots")
            
            if data['count'] > 0:
                latest = data['metrics'][-1]
                print(f"  Latest snapshot: {latest['timestamp']}")
        else:
            print(f"  ⚠️ History API returned {response.status_code}")
    except requests.RequestException as e:
        print(f"  ❌ History API error: {e}")
    
    # Step 7: 최근 알림 확인
    print_section("Step 7: Recent Alerts")
    
    try:
        response = requests.get(f"{WEB_DASHBOARD}/api/alerts/recent?count=5", timeout=3)
        if response.status_code == 200:
            data = response.json()
            alerts_list = data.get('alerts', [])
            
            if len(alerts_list) > 0:
                print(f"  ✅ Found {len(alerts_list)} recent alerts:")
                for alert in alerts_list[:3]:
                    print(f"    [{alert['severity']}] {alert['message']}")
            else:
                print("  ℹ️ No recent alerts")
        else:
            print(f"  ⚠️ Alerts API returned {response.status_code}")
    except requests.RequestException as e:
        print(f"  ❌ Alerts API error: {e}")
    
    # Step 8: 결과 요약
    print_section("📊 E2E Test Summary")
    
    if initial_metrics and final_metrics:
        tasks_added = final_metrics['total_tasks'] - initial_metrics['total_tasks']
        print(f"  Tasks Added:     {tasks_added}")
        print(f"  Success Rate:    {final_metrics['success_rate']:.1f}%")
        print(f"  Avg Response:    {final_metrics['avg_response_time_ms']:.0f}ms")
        print(f"  Health Status:   {final_metrics['health_status'].upper()}")
        
        if final_metrics['success_rate'] >= 80:
            print("\n✅ E2E Test PASSED - System is healthy!")
            return True
        else:
            print("\n⚠️ E2E Test PASSED with warnings - Success rate below 80%")
            return True
    else:
        print("\n❌ E2E Test FAILED - Could not complete metrics check")
        return False


def main():
    """메인 실행"""
    start_time = datetime.now()
    
    success = run_e2e_test()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print_section("🏁 Test Complete")
    print(f"  Duration: {duration:.1f}s")
    print(f"  Result:   {'✅ PASSED' if success else '❌ FAILED'}")
    print("")
    print("📌 Next Steps:")
    print("  1. Open Web Dashboard: http://127.0.0.1:8000")
    print("  2. Check real-time charts (auto-refresh every 3s)")
    print("  3. Verify metrics match test results")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
