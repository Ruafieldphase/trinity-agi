#!/usr/bin/env python3
"""
Copilot ↔ Comet 협업 테스트

이 스크립트는 Copilot이 실행하여 Comet에게 작업을 요청하고
결과를 받아서 분석합니다.

Prerequisites:
    1. Comet이 comet_worker_daemon.py 실행 중이어야 함
    2. shared_task_queue.py 모듈 사용 가능해야 함

Usage:
    python test_copilot_comet_collaboration.py
"""

import sys
from pathlib import Path
import json
import time
from datetime import datetime

# shared_task_queue 모듈 import
sys.path.insert(0, str(Path(__file__).parent))
from shared_task_queue import TaskQueue, TaskResult


def test_github_trending():
    """
    테스트 1: GitHub 트렌딩 저장소 수집
    
    Comet의 웹 스크래핑 능력을 테스트합니다.
    """
    print("=" * 70)
    print("Test 1: GitHub Trending Repositories")
    print("=" * 70)
    print()
    
    queue = TaskQueue()
    
    # 작업 생성
    print("📤 Copilot → Comet: 작업 요청")
    print("   URL: https://github.com/trending")
    print("   Target: 트렌딩 저장소 이름 및 설명")
    print()
    
    task_id = queue.push_task(
        task_type="web_scraping",
        data={
            "url": "https://github.com/trending",
            "selector": "article.Box-row h2 a",
            "extract": ["text", "href"]
        },
        requester="copilot-test"
    )
    
    print(f"✅ 작업 생성 완료: {task_id}")
    print()
    
    # 결과 대기
    print("⏳ Comet의 처리 대기 중... (최대 60초)")
    start_time = time.time()
    
    result = queue.get_result(task_id, timeout=60.0)
    
    elapsed = time.time() - start_time
    print()
    
    if result:
        print(f"✅ 결과 수신 완료 ({elapsed:.1f}초)")
        print(f"   Worker: {result.worker}")
        print(f"   Status: {result.status}")
        print()
        
        if result.status == "success":
            print("📊 수집된 데이터:")
            print(json.dumps(result.data, indent=2, ensure_ascii=False))
            print()
            return True
        else:
            print(f"❌ 작업 실패: {result.error_message}")
            return False
    else:
        print(f"❌ 타임아웃: {elapsed:.1f}초 내에 결과를 받지 못했습니다.")
        print("   Comet 데몬이 실행 중인지 확인하세요:")
        print("   python comet_worker_daemon.py")
        return False


def test_youtube_trending():
    """
    테스트 2: YouTube 트렌딩 동영상 수집
    
    동적 웹페이지 스크래핑 테스트
    """
    print("=" * 70)
    print("Test 2: YouTube Trending Videos")
    print("=" * 70)
    print()
    
    queue = TaskQueue()
    
    print("📤 Copilot → Comet: 작업 요청")
    print("   URL: https://www.youtube.com/feed/trending")
    print("   Target: 트렌딩 동영상 제목")
    print()
    
    task_id = queue.push_task(
        task_type="web_scraping",
        data={
            "url": "https://www.youtube.com/feed/trending",
            "selector": "ytd-video-renderer h3 a",
            "extract": ["text", "href"]
        },
        requester="copilot-test"
    )
    
    print(f"✅ 작업 생성 완료: {task_id}")
    print()
    
    print("⏳ Comet의 처리 대기 중... (최대 60초)")
    start_time = time.time()
    
    result = queue.get_result(task_id, timeout=60.0)
    
    elapsed = time.time() - start_time
    print()
    
    if result:
        print(f"✅ 결과 수신 완료 ({elapsed:.1f}초)")
        print(f"   Worker: {result.worker}")
        print(f"   Status: {result.status}")
        print()
        
        if result.status == "success":
            print("📊 수집된 데이터:")
            print(json.dumps(result.data, indent=2, ensure_ascii=False))
            print()
            return True
        else:
            print(f"❌ 작업 실패: {result.error_message}")
            return False
    else:
        print(f"❌ 타임아웃: {elapsed:.1f}초 내에 결과를 받지 못했습니다.")
        return False


def test_screenshot_capture():
    """
    테스트 3: 웹페이지 스크린샷 캡처
    
    브라우저 자동화 테스트
    """
    print("=" * 70)
    print("Test 3: Screenshot Capture")
    print("=" * 70)
    print()
    
    queue = TaskQueue()
    
    print("📤 Copilot → Comet: 작업 요청")
    print("   URL: https://github.com/trending")
    print("   Action: 스크린샷 캡처")
    print()
    
    task_id = queue.push_task(
        task_type="screenshot",
        data={
            "url": "https://github.com/trending",
            "filename": "github_trending_screenshot.png"
        },
        requester="copilot-test"
    )
    
    print(f"✅ 작업 생성 완료: {task_id}")
    print()
    
    print("⏳ Comet의 처리 대기 중... (최대 60초)")
    start_time = time.time()
    
    result = queue.get_result(task_id, timeout=60.0)
    
    elapsed = time.time() - start_time
    print()
    
    if result:
        print(f"✅ 결과 수신 완료 ({elapsed:.1f}초)")
        print(f"   Worker: {result.worker}")
        print(f"   Status: {result.status}")
        print()
        
        if result.status == "success":
            print("📊 스크린샷 정보:")
            print(json.dumps(result.data, indent=2, ensure_ascii=False))
            print()
            return True
        else:
            print(f"❌ 작업 실패: {result.error_message}")
            return False
    else:
        print(f"❌ 타임아웃: {elapsed:.1f}초 내에 결과를 받지 못했습니다.")
        return False


def test_list_pending_tasks():
    """
    테스트 4: 대기 중인 작업 확인
    
    큐 상태 모니터링 테스트
    """
    print("=" * 70)
    print("Test 4: List Pending Tasks")
    print("=" * 70)
    print()
    
    queue = TaskQueue()
    
    pending_tasks = queue.list_pending_tasks()
    
    print(f"📋 대기 중인 작업: {len(pending_tasks)}개")
    print()
    
    if pending_tasks:
        for task in pending_tasks[:5]:  # 최대 5개만 표시
            print(f"  - {task.id[:8]}... ({task.type})")
            print(f"    요청자: {task.requester}")
            print(f"    생성: {task.created_at}")
            print()
    else:
        print("  (대기 중인 작업 없음)")
        print()
    
    return True


def run_all_tests():
    """모든 테스트 실행"""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "Copilot ↔ Comet 협업 테스트" + " " * 25 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("⚠️  중요: Comet 데몬이 실행 중이어야 합니다!")
    print("   터미널에서 실행: python comet_worker_daemon.py")
    print()
    
    input("준비되었으면 Enter를 누르세요... ")
    print()
    
    results = []
    
    # Test 1: GitHub Trending
    results.append(("GitHub Trending", test_github_trending()))
    print()
    time.sleep(2)  # 테스트 간 대기
    
    # Test 2: YouTube Trending
    results.append(("YouTube Trending", test_youtube_trending()))
    print()
    time.sleep(2)
    
    # Test 3: Screenshot
    results.append(("Screenshot", test_screenshot_capture()))
    print()
    time.sleep(2)
    
    # Test 4: List Tasks
    results.append(("List Tasks", test_list_pending_tasks()))
    print()
    
    # 결과 요약
    print("=" * 70)
    print("테스트 결과 요약")
    print("=" * 70)
    print()
    
    for test_name, success in results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{status}  {test_name}")
    
    print()
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    print(f"총 {success_count}/{total_count} 테스트 성공")
    print()
    
    if success_count == total_count:
        print("🎉 모든 테스트 통과! Copilot ↔ Comet 협업 시스템이 정상 작동합니다.")
    else:
        print("⚠️  일부 테스트 실패. Comet 데몬 상태를 확인하세요.")
    
    print()


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print()
        print("테스트 중단됨")
    except Exception as e:
        print()
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
