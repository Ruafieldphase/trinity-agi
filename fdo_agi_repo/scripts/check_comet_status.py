#!/usr/bin/env python3
"""
Comet 상태 체크: Comet이 작업을 처리할 준비가 되었는지 확인

Usage:
    python check_comet_status.py
"""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent))
from shared_task_queue import TaskQueue, TASKS_DIR, RESULTS_DIR


def check_directories():
    """디렉토리 존재 확인"""
    print("=" * 60)
    print("1. 디렉토리 체크")
    print("=" * 60)
    
    print(f"\n📁 TASKS_DIR: {TASKS_DIR}")
    print(f"   존재: {'✅ Yes' if TASKS_DIR.exists() else '❌ No'}")
    
    print(f"\n📁 RESULTS_DIR: {RESULTS_DIR}")
    print(f"   존재: {'✅ Yes' if RESULTS_DIR.exists() else '❌ No'}")
    
    return TASKS_DIR.exists() and RESULTS_DIR.exists()


def check_pending_tasks():
    """대기 중인 작업 확인"""
    print("\n" + "=" * 60)
    print("2. 대기 작업 체크")
    print("=" * 60)
    
    queue = TaskQueue()
    pending = queue.list_pending_tasks()
    
    print(f"\n⏳ 대기 중인 작업: {len(pending)}개\n")
    
    if pending:
        print("작업 목록:")
        for task in pending[:5]:
            print(f"  - {task.id[:8]}... ({task.type})")
            print(f"    요청자: {task.requester}")
            print(f"    생성: {task.created_at}")
            print()
    
    return len(pending)


def send_ping_task():
    """Comet에게 ping 작업 전송"""
    print("\n" + "=" * 60)
    print("3. Comet Ping 테스트")
    print("=" * 60)
    
    queue = TaskQueue()
    
    print("\n📤 Ping 작업 전송...")
    task_id = queue.push_task(
        task_type="ping",
        data={"message": "Hello Comet!"},
        requester="copilot-check"
    )
    
    print(f"✅ 작업 생성: {task_id[:8]}...")
    print(f"📁 파일 위치: {TASKS_DIR / f'{task_id}.json'}")
    
    # 파일 생성 확인
    task_file = TASKS_DIR / f"{task_id}.json"
    if task_file.exists():
        print(f"✅ 작업 파일 존재 확인")
    else:
        print(f"❌ 작업 파일이 생성되지 않았습니다!")
        return None
    
    print("\n⏳ Comet 응답 대기 (10초)...")
    
    # 10초 대기
    for i in range(10, 0, -1):
        result = queue.get_result(task_id, timeout=0.5)
        if result:
            print(f"\n✅ Comet 응답 받음! ({10-i+1}초)")
            print(f"   Worker: {result.worker}")
            print(f"   Status: {result.status}")
            if result.data:
                print(f"   Data: {result.data}")
            return True
        
        print(f"   {i}초 남음...", end="\r")
        time.sleep(1)
    
    print("\n\n❌ 10초 내에 응답 없음")
    print("\n💡 Comet이 데몬을 실행하지 않았을 가능성:")
    print("   1. Comet 터미널에서 실행: python comet_worker_daemon.py")
    print("   2. Comet이 파일을 받지 못했을 가능성")
    print("   3. Comet의 Python 환경 문제")
    
    return False


def check_results_folder():
    """결과 폴더에 파일이 있는지 확인"""
    print("\n" + "=" * 60)
    print("4. 결과 폴더 체크")
    print("=" * 60)
    
    result_files = list(RESULTS_DIR.glob("*.json"))
    
    print(f"\n📊 결과 파일: {len(result_files)}개\n")
    
    if result_files:
        print("최근 결과:")
        for result_file in sorted(result_files, reverse=True)[:5]:
            print(f"  - {result_file.name}")
            print(f"    수정: {time.ctime(result_file.stat().st_mtime)}")
            print()
        return True
    else:
        print("  (결과 파일 없음 - Comet이 아직 작업을 처리하지 않음)")
        return False


def main():
    print("\n╔" + "═" * 58 + "╗")
    print("║" + " " * 20 + "Comet 상태 체크" + " " * 23 + "║")
    print("╚" + "═" * 58 + "╝\n")
    
    # 1. 디렉토리 체크
    dirs_ok = check_directories()
    
    if not dirs_ok:
        print("\n❌ 디렉토리가 생성되지 않았습니다.")
        print("   shared_task_queue.py를 한 번 실행해보세요:")
        print("   python -c \"from shared_task_queue import TaskQueue; TaskQueue()\"")
        return
    
    # 2. 대기 작업 체크
    pending_count = check_pending_tasks()
    
    # 3. 결과 폴더 체크
    has_results = check_results_folder()
    
    # 4. Ping 테스트
    comet_alive = send_ping_task()
    
    # 종합 결과
    print("\n" + "=" * 60)
    print("종합 결과")
    print("=" * 60 + "\n")
    
    if comet_alive:
        print("✅ Comet이 정상 작동 중입니다!")
        print("   Copilot ↔ Comet 협업 시스템이 준비되었습니다.")
    elif has_results:
        print("⚠️  Comet이 과거에는 작동했으나, 현재는 응답 없음")
        print("   Comet 데몬이 중단되었을 가능성:")
        print("   - Comet 터미널을 확인하세요")
        print("   - 재실행: python comet_worker_daemon.py")
    elif pending_count > 0:
        print("⚠️  작업이 쌓여있으나 처리되지 않음")
        print("   Comet 데몬이 실행되지 않았을 가능성 높음")
        print("   Comet에게 전달:")
        print("   1. comet_worker_daemon.py 파일")
        print("   2. shared_task_queue.py 파일")
        print("   3. 실행 명령: python comet_worker_daemon.py")
    else:
        print("❌ Comet이 작동하지 않음")
        print("\n📋 체크리스트:")
        print("   [ ] Comet에게 파일 전달 (comet_worker_daemon.py, shared_task_queue.py)")
        print("   [ ] Comet이 Python 3.8+ 환경 준비")
        print("   [ ] Comet이 터미널에서 실행: python comet_worker_daemon.py")
        print("   [ ] 경로 확인: Comet의 작업 디렉토리가 올바른지")
    
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
