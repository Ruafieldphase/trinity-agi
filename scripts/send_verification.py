import json
import subprocess
import datetime

# Message content
message = {
    "timestamp": datetime.datetime.now().isoformat(),
    "source": "antigravity",
    "event_type": "communication",
    "content": {
        "message": "Sena, 시스템 복구 및 자율 협업 모듈(agi-collaboration) 설치가 완료되었습니다. 현재 리듬 상태와 연결 상태를 확인하고 검증해주시겠습니까?",
        "type": "verification_request"
    },
    "metadata": {
        "priority": "high"
    }
}

# Convert to JSON string
json_str = json.dumps(message)

# Call ledger_proxy.py
cmd = ["python", "scripts/ledger_proxy.py", "append", json_str]
result = subprocess.run(cmd, capture_output=True, text=True)

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
