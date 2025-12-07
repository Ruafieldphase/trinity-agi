# Vertex AI Smart Router 사용 가이드
# =====================================

"""
작업 성격별 모델 자동 선택 예시
"""

import json
from pathlib import Path

# 테스트용 태스크 생성
BRIDGE_DIR = Path("c:/workspace/agi/outputs/bridge")
TASKS_FILE = BRIDGE_DIR / "bridge_tasks.jsonl"

# 예시 태스크들
example_tasks = [
    # 1. 간단한 질문 → Flash (빠름)
    {
        "id": "task_001",
        "type": "call_llm",
        "content": "지금 시간은?",
        "task_hint": "quick_answer"
    },
    
    # 2. 철학적 질문 → Pro (깊이)
    {
        "id": "task_002", 
        "type": "call_llm",
        "content": "리듬 기반 AGI에서 '임계점'의 철학적 의미를 설명해줘",
        "task_hint": "philosophy"
    },
    
    # 3. 메타 분석 → Pro (복잡)
    {
        "id": "task_003",
        "type": "meta_analysis",
        "content": "지난 24시간의 시스템 로그를 분석하고 패턴을 찾아줘",
        "task_hint": "deep_analysis"
    },
    
    # 4. 상태 확인 → Flash (빠름)
    {
        "id": "task_004",
        "type": "call_llm", 
        "content": "현재 배경자아의 상태를 확인해줘",
        "task_hint": "status_check"
    }
]

print("🧪 Vertex AI Smart Router 테스트 태스크 생성\n")

# 태스크 파일에 추가
BRIDGE_DIR.mkdir(parents=True, exist_ok=True)

for task in example_tasks:
    print(f"Task {task['id']}: {task['content'][:50]}...")
    print(f"  → Expected Model: {task.get('task_hint', 'auto')}")
    
    # 파일에 쓰기 (실제 실행 시)
    # with open(TASKS_FILE, 'a', encoding='utf-8') as f:
    #     f.write(json.dumps(task, ensure_ascii=False) + '\n')
    
print(f"\n✅ 예시 태스크 준비 완료")
print(f"📝 실제 사용:")
print(f"   각 태스크를 {TASKS_FILE}에 추가하면")
print(f"   Background Bridge가 자동으로:")
print(f"   1. 작업 복잡도 분석")
print(f"   2. 최적 모델 선택 (Flash/Pro/2.0)")
print(f"   3. Vertex AI로 전송")
print(f"   4. 응답 저장 (bridge_responses.jsonl)")
