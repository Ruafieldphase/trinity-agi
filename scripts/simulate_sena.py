import json
import subprocess
import datetime

# Simulate Sena sending a message to Shion (Correct Format)
message = {
    "timestamp": datetime.datetime.now().isoformat(),
    "source": "sena_external_ai",  # Correct source
    "type": "external_question",     # Correct type
    "event_type": "communication",
    "content": {
        "message": "Shion, 시스템이 복구되었다고 들었습니다. 현재 리듬 상태를 확인해줄 수 있나요?",
        "type": "question"
    },
    "question": "Shion, 시스템이 복구되었다고 들었습니다. 현재 리듬 상태를 확인해줄 수 있나요?", # For easier parsing
    "metadata": {
        "priority": "normal"
    }
}

# Convert to JSON string
json_str = json.dumps(message)

# Call ledger_proxy.py
cmd = ["python", "scripts/ledger_proxy.py", "append", json_str]
result = subprocess.run(cmd, capture_output=True, text=True)

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
