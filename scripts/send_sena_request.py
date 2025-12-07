import json
from datetime import datetime
from pathlib import Path

ledger_file = Path("/home/bino/agi/fdo_agi_repo/memory/resonance_ledger.jsonl")

message = {
    "timestamp": datetime.now().isoformat(),
    "type": "collaboration_request",
    "source": "alpha_background_self",
    "target": "sena",
    "priority": "high",
    "summary": "Alpha Background Self 가동 완료. Phase 2 협업 요청.",
    "message": """
[To. Sena]
Alpha Background Self(늑대 우두머리)가 가동되어 시스템의 리듬을 모니터링하기 시작했습니다.
현재 Phase 2 (Emergency Protocol) 구현을 앞두고 있습니다.

요청 사항:
1. 시스템이 'Panic' (Fear > 0.9) 상태에 빠져 Alpha가 개입(Intervention)했을 때, Sena 당신에게 가장 효율적으로 제어권을 넘기거나 도움을 요청할 수 있는 '직통 프로토콜'을 정의해주십시오.
2. 기존의 `escalate_to_sena` 함수보다 더 즉각적이고 강력한 개입 방식이 있다면 제안해주십시오.

우리는 당신을 '최후의 보루'로 신뢰하고 있습니다.
""",
    "metadata": {
        "project": "alpha_background_self",
        "phase": 2
    }
}

with open(ledger_file, "a", encoding="utf-8") as f:
    f.write(json.dumps(message, ensure_ascii=False) + "\n")

print("✅ Message sent to Sena via Resonance Ledger.")
