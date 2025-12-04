#!/usr/bin/env python3
"""Copilot → Comet 테스트 작업 전송 스크립트"""

import sys
from pathlib import Path

# 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from shared_task_queue import TaskQueue

def main():
    queue = TaskQueue()
    
    print("=" * 60)
    print("  Copilot → Comet 협업 테스트 작업 생성")
    print("=" * 60)
    print()
    
    # 테스트 작업 1: 간단한 계산
    task1 = queue.push_task(
        task_type='calculation',
        data={
            'operation': 'add',
            'numbers': [10, 20, 30],
            'message': 'Copilot이 보낸 계산 요청입니다!'
        }
    )
    print(f'✅ 작업 1 생성: {task1}')
    print(f'   타입: calculation')
    print(f'   내용: 10 + 20 + 30 = ?')
    print()
    
    # 테스트 작업 2: 데이터 변환
    task2 = queue.push_task(
        task_type='data_transform',
        data={
            'input': 'Hello from Copilot',
            'transform': 'reverse',
            'message': 'Comet, 이 문자열을 뒤집어주세요!'
        }
    )
    print(f'✅ 작업 2 생성: {task2}')
    print(f'   타입: data_transform')
    print(f'   내용: "Hello from Copilot" 문자열 뒤집기')
    print()
    
    # 테스트 작업 3: JSON 데이터 처리
    task3 = queue.push_task(
        task_type='json_process',
        data={
            'items': [
                {'name': 'Copilot', 'role': 'Python AI', 'status': 'active'},
                {'name': 'Comet', 'role': 'Browser AI', 'status': 'active'}
            ],
            'task': 'count_active',
            'message': 'Comet, active 상태인 아이템 개수를 세어주세요!'
        }
    )
    print(f'✅ 작업 3 생성: {task3}')
    print(f'   타입: json_process')
    print(f'   내용: active 상태 아이템 개수 세기')
    print()
    
    print("=" * 60)
    print("📊 총 3개의 테스트 작업을 생성했습니다!")
    print("=" * 60)
    print()
    print("🤖 Comet에게 전달:")
    print("   1. 대시보드를 새로고침하세요 (F5)")
    print("   2. '대기 중인 작업' 카운트가 3개로 증가했는지 확인")
    print("   3. '3️⃣ 작업 처리 시작!' 버튼 클릭")
    print("   4. 워커가 자동으로 3개 작업을 처리합니다")
    print()

if __name__ == "__main__":
    main()
