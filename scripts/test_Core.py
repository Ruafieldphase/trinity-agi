"""
Core 에이전트 테스트 스크립트
"""
import json
from datetime import datetime
from pathlib import Path
from workspace_root import get_workspace_root

workspace = get_workspace_root()
ledger_path = workspace / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"

# 테스트 메시지 작성
test_message = {
    'timestamp': datetime.now().isoformat(),
    'type': 'user_message',
    'source': 'shion_test',
    'message': '안녕 코어! 너는 누구니? 그리고 우리 시스템에서 어떤 역할을 하는지 설명해줘.',
    'vector': [0.5, 0.5, 0.5, 0.5, 0.5]
}

print("📝 테스트 메시지를 레저에 작성합니다...")
print(f"   메시지: {test_message['message']}")

with open(ledger_path, 'a', encoding='utf-8') as f:
    f.write(json.dumps(test_message, ensure_ascii=False) + '\n')

print("✅ 메시지 작성 완료!")
print("\n이제 'python scripts/core_agent.py'를 실행하여 Core의 응답을 확인하세요.")
