import json
import time
import os
from pathlib import Path

# 경로 설정
WORKSPACE_ROOT = Path("c:/workspace/agi")
BRIDGE_DIR = WORKSPACE_ROOT / "outputs/bridge"
TASKS_FILE = BRIDGE_DIR / "bridge_tasks.jsonl"
RESPONSES_FILE = BRIDGE_DIR / "bridge_responses.jsonl"

# 테스트 태스크 정의
tasks = [
    # 1. 바이브 명령 테스트 (Orchestrator가 처리)
    {
        "id": "test_vibe_001",
        "type": "vibe_command",
        "vibe": "요즘 리듬이 너무 빨라, 좀 천천히 가자",
        "timestamp": time.time()
    },
    # 2. Vertex AI 호출 테스트 (Background Bridge가 처리)
    {
        "id": "test_vertex_001",
        "type": "call_llm",
        "content": "리듬 기반 AGI 시스템에서 '임계점(Critical Point)'이 가지는 철학적 의미를 한 문장으로 정의해줘.",
        "task_hint": "philosophy", # Pro 모델 유도
        "timestamp": time.time()
    }
]

def monitor_responses(target_ids, timeout=15):
    print(f"👀 응답 모니터링 중... (최대 {timeout}초)")
    start_time = time.time()
    found_ids = set()
    
    current_pos = 0
    if RESPONSES_FILE.exists():
        current_pos = RESPONSES_FILE.stat().st_size

    while time.time() - start_time < timeout:
        if RESPONSES_FILE.exists():
            file_size = RESPONSES_FILE.stat().st_size
            if file_size > current_pos:
                with open(RESPONSES_FILE, 'r', encoding='utf-8') as f:
                    f.seek(current_pos)
                    lines = f.readlines()
                    current_pos = f.tell()
                
                for line in lines:
                    try:
                        resp = json.loads(line)
                        tid = resp.get('task_id')
                        if tid in target_ids:
                            print(f"\n✅ 응답 수신 ({tid}):")
                            print(json.dumps(resp.get('result'), indent=2, ensure_ascii=False))
                            found_ids.add(tid)
                    except:
                        pass
        
        if len(found_ids) == len(target_ids):
            print("\n✨ 모든 테스트 성공!")
            return
            
        time.sleep(1)
    
    print("\n⚠️ 시간 초과: 일부 응답을 받지 못했습니다.")
    print(f"미수신: {set(target_ids) - found_ids}")

def main():
    print("🚀 바이브 코딩 & Vertex AI 통합 테스트 시작")
    
    # 디렉토리 생성
    BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
    
    # 태스크 주입
    print(f"📨 태스크 {len(tasks)}개 전송 중...")
    with open(TASKS_FILE, 'a', encoding='utf-8') as f:
        for task in tasks:
            f.write(json.dumps(task, ensure_ascii=False) + '\n')
            
    # 응답 대기
    monitor_responses([t['id'] for t in tasks])

if __name__ == "__main__":
    main()
